"""Try the decoded activation protocol; this does not supply an SSH login key.

Default mode only describes the action. --send prompts privately for the router
admin password, sends one UDP packet, and checks TCP 22. No credential is printed,
written to a file, or placed in a subprocess argument.
"""
import argparse
import getpass
import ipaddress
import socket
import sys
import time

from activation_packet import build_packet, normalize_mac


def port_open(host, port=22):
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="192.168.1.1", help="Router LAN IPv4 address")
    parser.add_argument("--mac", required=True, help="Router LAN/bridge MAC from Advanced > Router Information")
    parser.add_argument("--send", action="store_true", help="Prompt for the password and send one activation packet")
    args = parser.parse_args()
    try:
        host = str(ipaddress.IPv4Address(args.host))
        mac = normalize_mac(args.mac)
    except ValueError as exc:
        parser.error(str(exc))
    if not args.send:
        print(f"Dry run: would check {host}:22, prompt privately for the admin password,")
        print(f"send one authenticated 248-byte UDP packet to {host}:23 using LAN MAC {mac},")
        print("and check TCP 22 again. No network request or credential prompt occurred.")
        print("SSH still requires the authorized private key; activation alone does not grant a shell.")
        return 0
    if not sys.stdin.isatty():
        parser.error("Run --send in an interactive terminal for a hidden password prompt")
    if port_open(host):
        print("TCP 22 already accepts connections; no activation packet sent.")
        print("SSH still requires the authorized private key.")
        return 0
    password = getpass.getpass("Router admin password (hidden): ")
    if not password:
        parser.error("Password was empty; no activation packet sent")
    packet = build_packet(mac, password)
    del password
    acknowledged = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            udp.settimeout(3)
            udp.connect((host, 23))
            udp.send(packet)
            try:
                acknowledged = udp.recv(64) == b"ACK"
            except (socket.timeout, ConnectionRefusedError):
                pass
    except OSError as exc:
        print(f"Activation request failed: {exc}", file=sys.stderr)
        return 1
    del packet
    listening = port_open(host)
    if acknowledged and not listening:
        time.sleep(0.5)
        listening = port_open(host)
    print("Activation ACK:", "received" if acknowledged else "not received")
    print("TCP 22:", "accepts connections" if listening else "not accepting connections")
    print("SSH still requires the authorized private key; this helper does not bypass authentication.")
    return 0 if acknowledged and listening else 1


if __name__ == "__main__":
    raise SystemExit(main())

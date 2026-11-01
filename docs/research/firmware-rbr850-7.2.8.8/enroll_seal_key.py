"""Owner-credential SeAL key enrollment. Default: offline preview only.

Use --check for read-only checks; --send makes one enrollment request after
checking model, firmware, TLS pin, and that TCP 22 is free. No automatic reboot.
"""
import argparse
import base64
import getpass
import hashlib
import http.client
import ipaddress
import json
from pathlib import Path
import re
import shlex
import socket
import ssl
import struct
import sys

BASE = Path(__file__).resolve().parent
DEFAULT_KEY = Path.home() / '.ssh/orbi_rbr850_bootstrap_rsa.pub'


def validate_key(text):
    text = text.strip()
    if not re.fullmatch(r'ssh-rsa [A-Za-z0-9+/]+={0,2}( [A-Za-z0-9_.@ -]+)?', text):
        raise ValueError('Expected one RSA public key with a plain comment')
    blob = base64.b64decode(text.split()[1], validate=True)
    assert len(blob) >= 4
    size = struct.unpack('>I', blob[:4])[0]
    if blob[4:4+size] != b'ssh-rsa':
        raise ValueError('Public key blob is not RSA')
    return text


def make_payload(password, key):
    if not password or '\x00' in password or re.fullmatch(r'-[neE]+', password):
        raise ValueError('Password cannot be represented safely by this firmware echo command')
    # Firmware concatenates this field into echo -n without quoting. Supply a
    # single literal shell word so spaces and shell syntax stay password data.
    return json.dumps(dict(username='admin', password=shlex.quote(password), pubkey=key)).encode()


def ssh_banner(host):
    try:
        with socket.create_connection((host, 22), 3) as sock:
            sock.settimeout(3)
            return sock.recv(256).partition(b'\n')[0].decode(errors='replace').strip() or 'TCP 22 occupied'
    except ConnectionRefusedError:
        return None


def request(host, pin, method, path, body=None):
    conn = http.client.HTTPSConnection(host, timeout=8, context=ssl._create_unverified_context())
    try:
        conn.connect()
        observed = hashlib.sha256(conn.sock.getpeercert(binary_form=True)).hexdigest()
        if observed != pin:
            raise ValueError('Router TLS certificate differs from the recorded LAN certificate')
        conn.request(method, path, body=body, headers={'Content-Type': 'application/json'} if body else {})
        response = conn.getresponse()
        data = response.read(65536)
        return response.status, data
    finally:
        conn.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Read-only model, TLS, API and port checks')
    mode.add_argument('--send', action='store_true', help='Privately prompt for admin password and enroll once')
    ap.add_argument('--public-key', type=Path, default=DEFAULT_KEY)
    args = ap.parse_args(argv)
    try:
        key = validate_key(args.public_key.read_text())
        print('Target: RBR850 V7.2.8.8_5.1.24 at 192.168.1.1')
        print('Public key:', args.public_key)
        print('Router effects: update /etc/shells; replace Dropbear authorized_keys;')
        print('delete its RSA host key; start key-only Dropbear on TCP 22.')
        if not (args.check or args.send):
            print('Preview only. No network connection or password prompt.')
            return 0
        host = '192.168.1.1'
        assert ipaddress.ip_address(host).is_private
        banner = ssh_banner(host)
        print('SSH:', banner or 'TCP 22 closed')
        if args.send and banner:
            raise ValueError('TCP 22 is occupied. Enrollment was NOT sent. A router reboot can free it; do not run the UDP activator afterward.')
        pin_info = json.loads((BASE/'evidence/router-tls-pin.json').read_text())
        assert pin_info['host'] == host
        pin = pin_info['sha256']
        status, settings = request(host, pin, 'GET', '/currentsetting.htm')
        fields = dict(line.split('=', 1) for line in settings.decode().splitlines() if '=' in line)
        if status != 200 or fields.get('Model') != 'RBR850' or fields.get('Firmware') != 'V7.2.8.8_5.1.24':
            raise ValueError('Router model/firmware did not match the inspected image')
        status, meta = request(host, pin, 'GET', '/api/meta')
        if status != 200 or not json.loads(meta).get('seal_version', '').startswith('v2.2.9.6'):
            raise ValueError('SeAL metadata did not match the inspected image')
        print('TLS pin, model, firmware and SeAL metadata matched.')
        if args.check:
            return 0
        if not sys.stdin.isatty():
            raise ValueError('Run --send in an interactive terminal for the private password prompt')
        secret = getpass.getpass('Router admin password (hidden): ')
        payload = make_payload(secret, key)
        del secret
        status, _ = request(host, pin, 'POST', '/api/v1/enable_ssh', payload)
        del payload
        if status != 200:
            raise ValueError(f'Enrollment returned HTTP {status}. No automatic retry; five rejected credentials block further attempts until the counter is cleared.')
        banner = ssh_banner(host)
        if not banner or 'dropbear' not in banner.lower():
            raise ValueError('API reported success, but Dropbear was not observed. SSH access is unverified; do not repeat enrollment.')
        print('Dropbear banner observed:', banner)
        print('Key installation and login still require an SSH authentication test.')
        print('ssh -F /dev/null -i ~/.ssh/orbi_rbr850_bootstrap_rsa -o IdentitiesOnly=yes -o IdentityAgent=none -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa -o UserKnownHostsFile='+shlex.quote(str(BASE/'evidence/dropbear_known_hosts'))+' -o StrictHostKeyChecking=ask root@192.168.1.1')
        return 0
    except (OSError, ValueError, AssertionError, http.client.HTTPException) as exc:
        # Never print server bodies, payloads, passwords or exception reprs.
        print(str(exc) if isinstance(exc, (ValueError, AssertionError)) else 'Network or file operation failed; no automatic retry.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

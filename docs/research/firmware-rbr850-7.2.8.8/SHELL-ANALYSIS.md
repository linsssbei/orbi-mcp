# Shell activation investigation: exact RBR850 build

> Historical research from 2026-10-27–29; consolidated on 2026-11-01.
> Use the [current MCP guide](../../../README.md) for supported setup and behavior.
> Earlier implementation status below describes the investigation date.
> Device MACs, key fingerprints and personal home paths are replaced with placeholders.
> Evidence and firmware links require the [local research archive](../README.md);
> they are excluded from Git and the npm package. Run repository-relative commands from the repo root.

Investigation date: 2026-10-27.

## Result

For the working owner-key route and MCP prerequisite, see
[Router access setup](../router-audit/docs/router-access.md). This document
analyzes the original UDP/OpenSSH path, whose authentication differs from the
subsequently verified Dropbear enrollment path.

The SSH activation mechanism has been decoded and checked against the ARM
instructions in `remoteshellenable` from RBR850-V7.2.8.8_5.1.24.

It is a credential-derived UDP packet, not SOAP. The firmware accepts the packet,
invokes `/etc/init.d/sshd start`, and replies `ACK` in an offline emulator.

**This does not grant a shell.** The SSH server first requires a private key
matching its bundled authorized public key, and then separately requests the
router's admin username/password. The admin password by itself does not satisfy
the first authentication stage.

During the offline phase, no activation packet or login attempt was sent to the
real router. The user subsequently ran the helper and reported `ACK` and TCP 22
accepting connections. A follow-up dedicated-key login test was rejected; see
the owner-key section below.

## Read-only device observations

The device at `192.168.1.1` returned these unauthenticated `currentsetting.htm`
fields during this investigation:

```text
Model=RBR850
Firmware=V7.2.8.8_5.1.24
Region=us
InternetConnectionStatus=Up
SOAPVersion=3.46
```

Both TCP 22 and TCP 23 refused a connection. The target-specific local ARP entry
was `<recorded-router-mac>` on `en0`. This MAC is the best initial bridge-MAC candidate;
it has not been verified against an authenticated Router Information page.
TCP 23 refusing a connection does not establish whether UDP 23 is listening.

## Decoded activation flow

From `evidence/remoteshellenable-disassembly.txt`:

| Address | Meaning |
| --- | --- |
| `0x0c58`–`0x0d1c` | Create an IPv4 UDP socket and bind port 23. |
| `0x0e1c` | Receive up to 512 bytes. |
| `0x0e28`–`0x0e3c` | Invoke the fixed script `/usr/sbin/ssh_update_ntgr.sh`. |
| `0x0e40`–`0x0e64` | Reconstruct the expected credential packet; require identical length and bytes. |
| `0x0ea4`–`0x0ec8` | First successful packet invokes `/etc/init.d/sshd start`. |
| `0x0e74`–`0x0e9c` | Reply with the three bytes `ACK`. |
| `0x2484`–`0x2748` | Expected-packet generator. |

The helper script reads the router's `http_passwd_digest`, converts it to upper
case, and writes `/tmp/httpwd`. The generator reads that temporary value and
obtains the current `br-lan` hardware address through `SIOCGIFHWADDR`.

The generator constructs 248 bytes:

1. LAN MAC represented as twelve uppercase hexadecimal characters in a
   zero-padded 16-byte field.
2. Hardcoded username `admin`, zero-padded to 16 bytes.
3. Uppercase hexadecimal SHA-256 digest of the admin password, zero-padded to
   80 bytes.
4. MD5 of those 112 field bytes, prepended as a 16-byte digest.
5. Zero padding to a total of 248 bytes.
6. Blowfish ECB encryption using the literal prefix `AMBIT_TELNET_ENABLE+`
   followed by the uppercase password digest. The implementation accepts its
   long key and uses little-endian block words; generic library defaults must
   not be substituted without checking their behavior.

The bundled daemon recreates the expected encrypted packet and compares it
against the received one; it does not treat packet bytes as shell commands.
The temporary digest file is removed. All subprocess paths observed in this
flow are fixed firmware strings.

## Authentication after activation

`rootfs/etc/ssh/sshd_config` specifies:

- line 13: port 22.
- line 49: public-key authentication enabled.
- line 53: authorized-key file `/etc/ssh/id_rsa.pub`.
- line 71: password authentication disabled.
- line 75: challenge-response authentication disabled.
- line 136: forced command `/bin/ssh_login_ntgr.sh`.

The authorized public key is an RSA key with a 2048-bit modulus. Its public
fingerprint is `SHA256:<recorded-fingerprint>`.
No private key was sought or used.

`rootfs/bin/ssh_login_ntgr.sh` checks the admin credentials **after** successful
SSH authentication, then launches a command or shell. This explains why knowing
the admin password is enough to construct the activation packet but is not
enough to log in over SSH.

`rootfs/etc/init.d/sshd` copies its configuration from ROM at startup. A future
configuration-change approach would have to account for that behavior and for
the authorized-key file; no such modification has been attempted.

## Hidden Telnet form: backend check

The `httpd` route table maps `DebugWP.cgi` to handler address `0x0da2d0`.
The handler reads `form_name` and recognizes `debugLogForm` and `sentLogForm`.
The legacy `telnetEnableForm` does not take a Telnet-enabling branch.

This was verified by emulating the actual handler using synthetic form values:

| Input form | Observed behavior in emulator |
| --- | --- |
| `telnetEnableForm` with `action_telnet_enable=1` | Reads only `form_name`; no NVRAM value writes or command launches; saves existing settings and renders the debug redirect. |
| `debugLogForm` with the boot-capture checkbox | Five NVRAM writes, including setting boot capture to 1. |
| `sentLogForm` | Writes `dbg_log_collect_send=1`. |

The positive control cases establish that the harness can exercise the real
form-processing branches. The hidden HTML checkbox is not a working shell
activation method through this handler in the inspected build.

Evidence: `evidence/DebugWP-handler-disassembly.txt`,
`evidence/DebugWP-handler-strings.json`, and
`evidence/offline-probe-results.json`.

## Verification method

`offline_probe.py` loads the ELF segments into Unicorn's ARM emulator. Every
imported library function is intercepted; unsupported imports cause failure.
Filesystem reads, sockets, interface queries, process execution, NVRAM writes,
and page rendering use Python stubs. The firmware instruction stream has no
direct host-network or process access.

The native packet generator's 248-byte output exactly matched the independent
Python implementation for synthetic credentials. The daemon then:

- accepted the correct packet and would start SSH and reply `ACK`;
- rejected a packet for the wrong MAC;
- rejected a packet for the wrong password;
- rejected a truncated packet;
- rejected a corrupted packet.

Together with the three web-handler cases, all eight cases pass. This is strong
evidence of protocol behavior; it does not prove that the actual router currently
runs the UDP service or that SSH will start successfully there.

Firmware daemon SHA-256:
`1d4ac86700e4a6b8993ed5ed2a576642a08565c294e087f55124c99e7eabe8de`.

## Optional local activation check

`activate_ssh.py` defaults to a dry run. It uses only the Python standard library
and the saved reference's pure-Python cipher class. No emulation packages are
needed for this helper. To inspect the planned action:

```sh
python3 activate_ssh.py --host 192.168.1.1 --mac "$ROUTER_LAN_MAC"
```

To test activation from the home network:

```sh
python3 activate_ssh.py --host 192.168.1.1 --mac "$ROUTER_LAN_MAC" --send
```

The helper prompts for the admin password using `getpass`; do not pass it on the
command line or paste it into chat. It sends one UDP authentication packet,
checks for `ACK`, and checks whether TCP 22 accepts connections. If TCP 22 is
already open, it sends no activation packet and does not ask for the password.
It never attempts SSH authentication and does not install or replace keys.

An `ACK` plus open TCP 22 would confirm activation on the device. It would not
confirm a usable shell. An absent reply does not establish whether the MAC,
password, service state, routing, or firmware behavior caused failure.

## Reproduce offline checks

```sh
.venv/bin/python -m pip install -r requirements-emulation.txt
.venv/bin/python offline_probe.py
```

Reference: <https://github.com/bkerler/netgear_telnet>. The saved reference has
SHA-256 `ec650fc11cd7d7a00b706aed044b5cc84e3227fc2117293d6338fbaca628839d`;
its MIT license is saved alongside it. Only the cipher class is loaded from its
AST. The original networking functions and command-line routine are not loaded.

## Initial conclusion (UDP/OpenSSH path only)

**Update:** [SEAL-SSH-ENROLLMENT.md](SEAL-SSH-ENROLLMENT.md) documents a newly
identified admin-credential REST endpoint that installs a public key for
Dropbear. Original Lua instructions passed ten offline cases. After the user's
reboot, enrollment succeeded and RSA-key SSH returned `uid=0(root) gid=0(root)`.
The initial conclusion below applies to the UDP/OpenSSH path alone.

The firmware contains an authenticated listener-activation route, but no
password-only SSH login route has been established. Full owner-controlled shell
access still requires a legitimate matching key or an additional means of
changing the router's authorized-key/configuration files. Hardware or firmware
modification would be a separate investigation.

## Original Ed25519 key and OpenSSH login attempt

The user reported successful listener activation. A dedicated Ed25519 owner key
pair was then generated locally:

- Private key: `$HOME/.ssh/orbi_rbr850_ed25519`.
- Public key: `$HOME/.ssh/orbi_rbr850_ed25519.pub`.
- Public fingerprint: `SHA256:<recorded-fingerprint>`.
- Private-key permissions: 0600. No passphrase, for local automation.
- The private key was not copied into this research folder or sent to the router.

A single public-key authentication attempt as `root`, explicitly using only
this identity, returned `Permission denied (publickey)`. No password was supplied
and no remote command ran. The SSH host key observed on first connection has
fingerprint `SHA256:<recorded-fingerprint>`; its local
record is `evidence/router_known_hosts`.

The firmware contains OpenSSH 7.9p1. Its active configuration selects the fixed
file `/etc/ssh/id_rsa.pub` for client public-key authorization. No enrollment
route for adding an owner key through this activation packet
has been established. Creating a new key does not make it match the existing
authorized key.

To use the dedicated key, its **public** line must be added to that router-side
file through an existing privileged access route. `ssh-copy-id` would also need
working initial authentication. A bootstrap method remains necessary before
installation can be completed. The subsequent SeAL investigation above
identifies a candidate software route.
The key pair is ready; it is **not installed or authorized** on the router.

# SeAL SSH enrollment in RBR850 V7.2.8.8_5.1.24

> Historical research from 2026-10-27–29; consolidated on 2026-11-01.
> Use the [current MCP guide](../../../README.md) for supported setup and behavior.
> Earlier implementation status below describes the investigation date.
> Device MACs, key fingerprints and personal home paths are replaced with placeholders.
> Evidence and firmware links require the [local research archive](../README.md);
> they are excluded from Git and the npm package. Run repository-relative commands from the repo root.

**Status: live enrollment and root SSH login succeeded.** After the user
rebooted the router, one POST using the host-specific saved Keychain login
returned HTTP 200. Dropbear started, accepted the dedicated RSA key, and ran
`id`, returning `uid=0(root) gid=0(root)`. A second check succeeded with strict
host-key checking and password authentication disabled. No VPN, DHCP or Wi-Fi
settings were changed. Persistence across another reboot remains untested.
[Further inspection](DROPBEAR-PERSISTENCE.md) confirms the key files are on
persistent flash, but the stock Dropbear startup script is missing. A late boot
hook can start it without re-enrollment; no boot change has been applied.

Evidence: `evidence/seal-live-enrollment.json`. Dropbear host-key fingerprint:
`SHA256:<recorded-fingerprint>`.

## Connect now

```sh
ssh -F /dev/null -i ~/.ssh/orbi_rbr850_bootstrap_rsa \
  -o IdentitiesOnly=yes -o IdentityAgent=none \
  -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=docs/research/firmware-rbr850-7.2.8.8/evidence/dropbear_known_hosts \
  root@192.168.1.1
```

The original findings and enrollment procedure below are retained for reference.
Do not repeat enrollment on the already-running service.

## Online research

The [netgear_telnet maintainer's discussion](https://github.com/bkerler/netgear_telnet/issues/44)
confirms the 7.2 transition to vendor-key SSH, describing UART/eMMC as possible
ways to change authentication settings. A separate
[RBR850 report](https://github.com/bkerler/netgear_telnet/issues/52) reports that
the old activation method does not open Telnet. Neither establishes an owner
key enrollment procedure for this release. Searches for the SeAL development
helper did not produce a relevant published procedure.

## Firmware discovery

`rootfs/www-seal/rest/rest.lua` registers:

```text
POST /api/v1/enable_ssh
JSON: {"username":"admin", "password":"...", "pubkey":"ssh-rsa ..."}
```

The handler is child prototype `main.10`, source lines 169–182. It calls
`seal-development.enable_ssh(username,password,pubkey)` and returns HTTP 200
or 418. Registration is in main instructions 84–96. This endpoint is in the
always-available route group; no debug flag is required. Other service
management routes have a separate debug/internal-proxy gate.

`rootfs/etc/lighttpd_conf.ltp` proxies `/api/` to root-privileged lighttpd on
loopback TCP 16667, whose configuration rewrites API URLs to `rest/rest.lua`.
HTTPS terminates at lighttpd and forwards API requests through this path.

`rootfs/usr/share/lua/seal-development.lua` checks a failed-attempt counter,
then reads admin username and SHA-256 password digest through `seal plat` and
`/ntgr/sealplat.sh`, which use `fnvram`. Failed credentials increment
`/tmp/enable-ssh-attempt-counter`; five failures block subsequent attempts.
With matching credentials it executes:

```sh
/bin/sed -i 's#/bin/ash#/bin/sh#' /etc/shells
/bin/echo '<supplied public key>' > /etc/dropbear/authorized_keys
/bin/rm -f /etc/dropbear/dropbear_rsa_host_key
/usr/sbin/dropbear -P /var/run/dropbear.pid -s -g -p 22 -K 300 -T 3 -R || true
```

It replaces Dropbear's authorized-key file and deletes its existing RSA host
key. `-s` disables password login; root key login is allowed. Dropbear is
separate from OpenSSH and uses a separate authorized-key file.

The ROM passwd file uses `/bin/ash`, but `acos_service` contains a startup
command recreating root's account with `/bin/sh`. This explains the helper's
shell-list adjustment; live account contents have not been read.

## Constraints

- Dropbear package version is **2019.78-2**. The executable contains `ssh-rsa`
  and `/etc/dropbear/authorized_keys`, with no Ed25519 algorithm identifier.
  A separate 3072-bit RSA bootstrap key was generated locally, preserving the
  existing Ed25519 key. RSA fingerprint:
  `SHA256:<recorded-fingerprint>`.
  Private file: `$HOME/.ssh/orbi_rbr850_bootstrap_rsa`, mode 0600.
  Only its `.pub` file is used for enrollment.
- Before reboot, TCP 22 responded with **SSH-2.0-OpenSSH_7.9**. The helper refuses
  enrollment while any listener occupies that port. A reboot should clear the
  UDP-started service, but this must be checked. Do not rerun the UDP activator
  before attempting SeAL enrollment.
- The development code ignores command failures and can return HTTP 200 even
  when no server starts. A Dropbear banner and actual key authentication must
  both be checked; a banner alone does not prove successful enrollment.
- Digest comparison is case-sensitive. Offline tests show rejection if the
  stored digest is uppercase and computed digest lowercase. The live stored
  digest has not been read.
- The password field is inserted unquoted into `echo -n ... | sha256sum ...`.
  Our helper supplies one shell-quoted literal word so spaces and shell syntax
  stay password data. Empty/NUL and echo-option-only passwords are rejected.
  No command injection workaround is used.
- `cut -f0` initially looked suspicious, but upstream
  [BusyBox 1.30.1 source](https://raw.githubusercontent.com/mirror/busybox/1_30_1/coreutils/cut.c)
  treats field zero as field one. It is not by itself a broken-password check.
- Live password acceptance, LAN SSH key authentication and root shell access
  are now verified. Persistence and WAN firewall reachability remain unverified.

## Evidence and verification

`inspect_lua51.py` parses OpenWrt Lua 5.1/LNUM chunks and converts their layout
to standard host Lua 5.1. Integer constants become doubles; **instructions are
preserved** and original files remain unchanged. `offline_seal_probe.py`
executes those instructions with all process, filesystem and CGI operations
mocked. Ten cases passed: credentials, attempt limit, debug/proxy behavior,
digest case, ignored process failures, GET rejection and non-Orbi behavior.
The Dropbear executable itself is not emulated by this harness.

Live read-only observations:

- `/api/meta`: HTTP 200, SeAL `v2.2.9.6-0-gc6614a48`, API version `1.0`.
- `GET /api/v1/enable_ssh`: HTTP 404; the route requires POST.
- `enroll_seal_key.py --check`: exact model, firmware, SeAL metadata and
  recorded TLS fingerprint match. First-observed TLS pin is a local LAN
  observation, not independently authenticated device identity.

Evidence: `evidence/lua/*.txt`, `evidence/seal-offline-results.json`,
`evidence/seal-read-only-probe.json`, `evidence/router-tls-pin.json`.
Seven helper tests passed, covering literal password handling, unsafe key/input
rejection, dry-run behavior, occupied-port refusal and one-request enrollment
without printing credentials, and excluding binary key-exchange data from
the displayed SSH banner. Network and password prompts are mocked there.

After the reboot, the router presented a newly generated HTTPS certificate.
Before refreshing the local certificate pin, the same LAN MAC address
`<recorded-router-mac>`, exact model/firmware and SeAL version were verified.
Firmware startup in `rootfs/etc/startup.d.in/lighty.yaml` supports regenerating
the certificate. The previous fingerprint is retained in the pin history.

## Original enrollment procedure (completed)

From this directory, preview or check without making changes:

```sh
python3 enroll_seal_key.py
python3 enroll_seal_key.py --check
```

When a brief network interruption is acceptable, reboot normally, wait for
connectivity, and **do not run `activate_ssh.py`**. Then:

```sh
python3 enroll_seal_key.py --send
```

The helper privately prompts in your terminal, uses HTTPS pinned to the
certificate observed on this LAN, and makes one credential-bearing POST. It
never logs the password or sends the private key. There are no automatic
retries or reboot commands. Investigate HTTP 418 without repeatedly retrying.
A Dropbear banner is followed by a printed SSH command using the RSA bootstrap
identity, legacy RSA compatibility options and an independent known-hosts file.

The enrolled RSA key already provides key-only access suitable for an MCP
connection layer. Migrating to Ed25519/OpenSSH is optional and has not been
implemented or performed. See the consolidated
[MCP access setup guide](../router-audit/docs/router-access.md) for the current
connection contract and remaining boot setup.

Reproduce offline verification:

```sh
.venv/bin/python -m pip install -r requirements-emulation.txt
.venv/bin/python offline_seal_probe.py
.venv/bin/python -m unittest discover
```

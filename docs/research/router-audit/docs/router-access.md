# Router access setup for a future Orbi MCP server

> Historical research from 2026-10-27–29; consolidated on 2026-11-01.
> Use the [current MCP guide](../../../../README.md) for supported setup and behavior.
> Earlier implementation status below describes the investigation date.
> Device MACs, key fingerprints and personal home paths are replaced with placeholders.
> Evidence and firmware links require the [local research archive](../../README.md);
> they are excluded from Git and the npm package. Run repository-relative commands from the repo root.

This is the access prerequisite and implementation handoff for an MCP server
that manages the owner's home Orbi. It records a working connection method;
the MCP server itself has not been implemented.

Verified device: **NETGEAR Orbi RBR850, V7.2.8.8_5.1.24**, LAN address
`192.168.1.1`. Findings apply to this exact build. Recheck other models and
firmware versions before enrolling keys or changing startup behavior.

## Current state

| Item | Status |
| --- | --- |
| Owner-controlled SSH | Verified: dedicated RSA key authenticates as root. |
| Admin password needed for each SSH connection | No. SSH key authentication was tested with password authentication disabled. |
| Admin password needed for initial access setup | Yes: SeAL verifies it before installing the public key and starting Dropbear. |
| Key storage | Confirmed on persistent flash; survival across a subsequent reboot has not been tested. |
| Automatic SSH startup after reboot | Not configured. Stock startup links point to a missing service script. |
| Proposed startup repair | A guarded, key-only, LAN-bound launch in `/etc/rc.local`; not applied or reboot-tested. |
| Ed25519 key | Generated earlier, but not enrolled. It is not the working Dropbear identity. |
| MCP readiness | Key-only SSH is available now; unattended recovery after reboot remains unfinished. |

Live evidence was captured on 2026-10-27 Pacific time / 2026-10-28 UTC. The
successful SSH command returned `uid=0(root) gid=0(root)` with exit code 0.
Treat this as a recorded observation, not a continuously monitored health check.

The subsequent [feature validation report](router-capabilities.md) lists
verified operations, the observed hardware boundary, and operations left
unvalidated to preserve the network. Failed SOAP actions and missing commands
are interface notes, not proof that a feature cannot be implemented over SSH.
During that audit IPv4 management from this client was rejected by the observed
Bitdefender/Armor path. IPv6 LAN access with the same pinned host identities
worked; no firewall or security configuration was changed. The IPv4 command
below records the original setup and may not connect while that runtime block
is present.

## The access flow

1. **One-time setup:** use the router admin password to enroll the owner's
   **public** RSA key through SeAL and start Dropbear.
2. **Normal operation:** the local MCP process connects with the matching
   **private** key and a pinned SSH host key. No admin password is sent.
3. **After reboot:** the stored keys should remain, but a startup hook must
   launch Dropbear. Until that hook is installed and tested, SSH availability
   after reboot is not assured. SeAL can start it again using admin credentials,
   but re-enrollment also replaces keys and should not be an automatic retry.

Do not confuse the two SSH servers in this firmware:

| Path | Server | Authentication | Suitability |
| --- | --- | --- | --- |
| Credential-derived packet to UDP 23 | NETGEAR OpenSSH on TCP 22 | Vendor-authorized SSH key, then a separate admin credential check | Starts a listener but did not accept our owner key. |
| `POST /api/v1/enable_ssh` | Dropbear on TCP 22 | Admin credentials during enrollment; owner RSA key during later SSH connections | Verified working path for MCP access. |

Creating a key locally does not authorize it on either server. The enrollment
step installs the public key into Dropbear's authorization file.

## This installation's connection settings

These are local paths and public fingerprints, not portable defaults:

| Setting | Value |
| --- | --- |
| Host / port / user | `192.168.1.1` / `22` / `root` |
| Private identity file | `$HOME/.ssh/orbi_rbr850_bootstrap_rsa` |
| Public identity file | `$HOME/.ssh/orbi_rbr850_bootstrap_rsa.pub` |
| Client key | RSA 3072, fingerprint `SHA256:<recorded-fingerprint>` |
| Known-hosts file | `docs/research/firmware-rbr850-7.2.8.8/evidence/dropbear_known_hosts` |
| Pinned server host key | `SHA256:<recorded-fingerprint>` |
| Router authorized-key file | `/etc/dropbear/authorized_keys` |
| Router host-key file | `/etc/dropbear/dropbear_rsa_host_key` |

The private identity file has mode 0600 and was generated without a passphrase
for local automation. Keep it outside the project and MCP tool payloads. Pass
only its filesystem path to the local connection layer. The private key is
never uploaded to the router.

Read-only verification command:

```sh
ssh -F /dev/null -i ~/.ssh/orbi_rbr850_bootstrap_rsa \
  -o IdentitiesOnly=yes -o IdentityAgent=none -o BatchMode=yes \
  -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no \
  -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile=docs/research/firmware-rbr850-7.2.8.8/evidence/dropbear_known_hosts \
  -o ConnectTimeout=8 root@192.168.1.1 id
```

This Dropbear build requires the shown RSA compatibility options with the
tested OpenSSH client. Scope them to this connection. The future MCP connection
layer should use these explicit settings and bounded command execution time,
without relying on a user's SSH agent or interactive password prompts.

## Reproduce initial enrollment on this exact build

The helper is [enroll_seal_key.py](../../firmware-rbr850-7.2.8.8/enroll_seal_key.py).
It uses Python's standard library and defaults to an offline preview.

```sh
cd docs/research/firmware-rbr850-7.2.8.8
python3 enroll_seal_key.py
python3 enroll_seal_key.py --check
```

Enrollment requires TCP 22 to be free. If the old UDP-activated OpenSSH server
occupies it, a normal router reboot cleared it in our test. Do not send another
UDP activation packet afterward. When ready to make the enrollment changes:

```sh
python3 enroll_seal_key.py --send
```

The helper checks the exact model/firmware, SeAL version and recorded HTTPS
certificate pin, then privately prompts for the admin password and sends one
POST. The interactive helper does not automatically retrieve Keychain secrets.
Our agent-run enrollment used the same request functions with the password
captured in process memory from the exact macOS Keychain entry:

- Service: `local-orbi-tools:192.168.1.1`
- Account: `admin`

The existing `npm run auth` command stores that host-specific entry using a
hidden terminal prompt. Do not print the password, put it in command-line
arguments or project files, or return it through MCP.

Endpoint request shape, with placeholders only:

```text
POST https://192.168.1.1/api/v1/enable_ssh
Content-Type: application/json
{"username":"admin","password":"<encoded by the helper>","pubkey":"ssh-rsa <public-key>"}
```

Use the helper's password encoding: the firmware places this field into an
unquoted shell command, and the helper quotes it as one literal shell word.
The raw request shape is documentation, not a suggested manual credential
submission method.

Enrollment effects observed in the firmware:

- Replace `/bin/ash` with `/bin/sh` in `/etc/shells`.
- **Replace** `/etc/dropbear/authorized_keys` with the supplied public key.
- **Delete** the existing Dropbear RSA host key.
- Start Dropbear with password logins disabled; a missing host key is generated.

Consequently, re-enrollment is not a harmless connection check. HTTP 200 can
also be returned when process startup fails. Require a successful SSH command
before marking access ready. Five failed credential checks block later
attempts through a temporary counter; do not retry credentials automatically.

On reboot the router regenerated its HTTPS certificate in our test. The local
pin was refreshed only after checking the same LAN MAC, exact model/firmware
and SeAL version; the old fingerprint was retained. A future setup flow must
handle certificate identity changes explicitly rather than ignoring pin errors.
The SeAL HTTPS certificate and Dropbear SSH host key are separate identities.

## Reboot persistence: remaining setup step

Read-only inspection confirmed both key files are in the root overlay upper
layer on UBIFS flash. It also confirmed that `S19dropbear` and `K50dropbear`
point to an absent `/etc/init.d/dropbear` script.

The preferred candidate is a guarded Dropbear launch in `/etc/rc.local` before
its `exit 0`. The firmware's `S95done` boot function executes this file after
the normal network, account initialization and firewall startup phases. Bind
the listener to the LAN address and reuse the enrolled public key and existing
host key. No password belongs in that boot file.

The startup change has **not** been applied. Completion criteria are:

1. Preserve the existing boot file and add only the guarded startup block.
2. Reboot once at an agreed time.
3. Authenticate using the existing RSA identity and strict host-key checking.
4. Confirm the same server host key and root identity, without SeAL enrollment
   or admin password retrieval.
5. Verify rollback by removing only the added startup block when needed.

See [the persistence investigation](../../firmware-rbr850-7.2.8.8/DROPBEAR-PERSISTENCE.md)
for source paths, live mount evidence and the proposed launch arguments.
Ordinary reboot testing does not establish behavior through firmware upgrades
or factory resets.

## Handoff to the MCP implementation

The access setup should be a separate prerequisite from ordinary router tools.
Suggested behavior for the connection layer:

| Observation | Behavior |
| --- | --- |
| Pinned-host SSH succeeds and `id` confirms the expected identity | Access is ready; use key-only connections. |
| Connection refused or timed out | Report unavailable; do not infer that the key was erased or trigger enrollment. |
| Public-key authentication rejected | Check selected identity and server banner; the vendor OpenSSH service is a different path. |
| SSH host key changed | Stop and require explicit identity verification; do not automatically replace the pin. |
| No owner key enrolled | Run the local setup flow with admin credentials before enabling normal MCP operations. |

Successful root access establishes command execution, not a validated API for
every router setting. Discover and verify each management operation separately.
Earlier goals include device inventory, DHCP reservations by MAC, configuration
backup and VPN configuration. Firmware web forms for those operations were
identified, but their modifying requests have not been tested live. Existing
SOAP helpers remain available in this project where appropriate.

Prefer specific MCP operations with validated arguments and explicit results.
Do not make ordinary tool calls accept arbitrary shell text, expose the private
key or admin password, or silently alter boot configuration. The current SSH
session has root privileges, so command selection belongs in the implementation.
MCP schemas, transports and management operations remain future work.

## Evidence index

- [Firmware and extraction](../../firmware-rbr850-7.2.8.8/README.md)
- [SeAL endpoint analysis and enrollment](../../firmware-rbr850-7.2.8.8/SEAL-SSH-ENROLLMENT.md)
- [Live enrollment and successful root authentication](../../firmware-rbr850-7.2.8.8/evidence/seal-live-enrollment.json)
- [Persistence observations](../../firmware-rbr850-7.2.8.8/evidence/dropbear-persistence-live.json)
- [Offline SeAL cases](../../firmware-rbr850-7.2.8.8/evidence/seal-offline-results.json)
- [Original UDP/OpenSSH investigation](../../firmware-rbr850-7.2.8.8/SHELL-ANALYSIS.md)

Ten original-bytecode SeAL cases and seven helper checks passed during the
investigation. These tests cover enrollment handling and helper behavior, not
reboot autostart or future MCP management features.

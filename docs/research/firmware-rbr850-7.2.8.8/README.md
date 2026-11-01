# RBR850 7.2.8.8 offline inspection

> Historical research from 2026-10-27–29; consolidated on 2026-11-01.
> Use the [current MCP guide](../../../README.md) for supported setup and behavior.
> Earlier implementation status below describes the investigation date.
> Device MACs, key fingerprints and personal home paths are replaced with placeholders.
> Evidence and firmware links require the [local research archive](../README.md);
> they are excluded from Git and the npm package. Run repository-relative commands from the repo root.

Firmware image downloaded and filesystem extracted on 2026-10-27. The initial
extraction did not contact the router or execute firmware programs. Subsequent
work used offline ARM/Lua execution with mocked host interfaces, read-only
device checks, and one successful owner-key enrollment through SeAL. The user
also tested UDP activation and rebooted before enrollment. No firmware was
flashed. Enrollment changed the SSH-related files described below; automatic
startup and other router configuration were not changed.

For the consolidated MCP prerequisite and implementation handoff, see
[Router access setup](../router-audit/docs/router-access.md).

[Feature validation report](../router-audit/docs/router-capabilities.md)
classifies all 164 UI catalogue entries and additional SSH capabilities as
verified, hardware-limited, or unvalidated to preserve the network. Its live
evidence includes 39 authenticated pages and 28 verified reads. Only the
absence of 6 GHz radio capability is classified as a hardware boundary;
failed API calls and missing commands remain scoped interface observations.
No setters or restart/reboot actions
were sent during that audit; 36 tracked configuration hashes matched. It also
documents observed HTTP/RPC instability and an IPv4 Armor rejection, rather
than treating every getter as safe or every connection failure as a lost key.

See [SHELL-ANALYSIS.md](SHELL-ANALYSIS.md) for the decoded activation protocol,
eight passing emulation cases, SSH authentication requirements, and optional
local activation helper.

**Additional finding:** [SEAL-SSH-ENROLLMENT.md](SEAL-SSH-ENROLLMENT.md) traces an
admin-credential REST endpoint that can install a supplied key for Dropbear.
Ten original-bytecode cases and seven local helper checks pass. After the user
rebooted, one enrollment request succeeded and dedicated-key root SSH access
was verified using `id`. See the report for the connection command. The helper
defaults to an offline preview and refuses to send while TCP 22 is busy.

[Persistence investigation](DROPBEAR-PERSISTENCE.md): enrolled keys are on
persistent flash; automatic startup is missing. A late boot hook can start
Dropbear without admin credentials. Boot settings have not been modified.

## Downloads

- Firmware release: <https://kb.netgear.com/000070916/>
- Download: <https://www.downloads.netgear.com/files/GDC/RBK852/RBR850-V7.2.8.8.zip>
- ZIP size: 52,136,269 bytes.
- ZIP SHA-256: `e6a43045c6cd044d433a95e7d1c9b73f8df46e2111b57c744268e9d20795ad2f`.
- ZIP member: `RBR850-V7.2.8.8_5.1.24.chk`, matching the user's complete version.
- NETGEAR GPL index: <https://www.downloads.netgear.com/files/GDC/2649_GPLv1.html>.
- Listed source URL: <https://www.downloads.netgear.com/files/GPL/RBK850_7.2.8.8_GPL.tar>.
- That exact source URL returned HTTP 404. The GPL source archive was **not**
  downloaded. The saved index HTML records the published link. Nearby listed
  archives and several extension variants also returned 404.

The extracted scripts and web pages come from the compiled firmware image;
they are not a substitute for the missing complete GPL source package. The ARM
executables are stripped binaries, not C source.

## Files on disk

- `downloads/`: original ZIP.
- `firmware/`: original CHK and release-note HTML from the ZIP.
- `volumes/`: reconstructed UBI volume payloads and `rootfs.squashfs`.
- `rootfs/`: 5,235 regular files extracted for reading.
- `filesystem-inventory.json`: 6,339 entries, including uncreated symlinks and
  skipped special nodes, with SHA-256 hashes for regular files. `path` is the
  original Linux path; `extracted_path` is its path beneath the local `rootfs/`.
- `ubi-blocks.json`: the UBI erase-block map used for extraction.
- `download-manifest.json`: artifact hashes, provenance, and source-link status.
- `evidence/`: selected binary strings; string presence alone does not prove a
  reachable or functioning route.

Symlinks and device nodes were recorded rather than created. Firmware programs
were never executed natively; selected instruction streams were subsequently
emulated offline. Files in `rootfs/` were not given execute permissions.
Eight pairs of regular files differ only in letter case. To preserve both on
case-insensitive macOS storage, the second name in each pair gets a deterministic
`__case_<hash>` suffix. The inventory preserves the original-to-extracted mapping.

## SSH and debug findings

### Confirmed from readable files in this exact image

1. `rootfs/etc/ssh/sshd_config`:
   - line 13: port 22.
   - lines 48-53: public-key authentication, using `/etc/ssh/id_rsa.pub`.
   - line 71: password authentication disabled.
   - line 75: challenge-response authentication disabled.
   - line 136: forced command `/bin/ssh_login_ntgr.sh`.
2. `rootfs/bin/ssh_login_ntgr.sh`, lines 3-19:
   - after SSH authentication, asks for the router admin username/password;
   - checks a SHA-256 password digest against router/satellite configuration;
   - then executes the requested command or login shell.
   - Therefore the admin password check is a second stage, not a replacement
     for the first SSH public-key requirement.
3. `rootfs/etc/init.d/sshd`, lines 26-38:
   - copies the SSH configuration from ROM when starting;
   - sets ListenAddress to the current `br-lan` IPv4 address;
   - starts `/usr/sbin/sshd` through procd.
4. `rootfs/etc/init.d/init_sshenable`, line 7:
   - starts `/usr/sbin/remoteshellenable`.
   - `rootfs/etc/hotplug.d/iface/95-ssh`, lines 3-8, invokes that startup script
     for `br-lan` interface up/update events.
5. `rootfs/www/debug.htm`:
   - lines 40-45 comment out the Telnet checkbox initialization with the note
     `MR2.0 enforce disabled telnet`;
   - lines 162-168 retain a hidden `telnetEnableForm` pointing to `DebugWP.cgi`.
   - This proves the form remains in the image. It does **not** establish that
     posting it enables a shell on this version.

### Binary evidence and unresolved questions

- `/usr/sbin/remoteshellenable`, `/usr/sbin/sshd`,
  `/usr/sbin/telnetenabled`, `/usr/sbin/utelnetd`, and `/usr/sbin/dropbear`
  are present in the image.
- `remoteshellenable` is an ARM ELF binary. Its strings include an SSH-enabled
  message and `/etc/init.d/sshd`; this is consistent with a gated startup
  mechanism. The trigger was subsequently decoded and tested in an offline
  emulator; see `SHELL-ANALYSIS.md` for the newer findings.
- The opkg metadata identifies its build source as
  `package/utils/remoteshellenable`.
- The user's port check reported TCP 22 refusing a connection. This is
  consistent with a stopped listener, but does not identify why it is stopped.
  There was no port-23 result in the provided output.
- Owner-controlled root SSH was subsequently established through the SeAL
  public-key enrollment route; see `SEAL-SSH-ENROLLMENT.md`.
- No vendor private key was sought or used, and no key contents are included
  in this report.

## Non-SOAP configuration paths

These are confirmed from the firmware's web forms. They are **not live-tested**
requests and do not establish a stable public API contract. Authentication,
server-rendered values, session handling, and all validation must be reproduced
from the live authenticated page before using them.

| Operation | Evidence | Details |
| --- | --- | --- |
| Add DHCP reservation | `rootfs/www/LAN_reserv_add.htm:150` | POST to `reserv.cgi`; fields include `rsv_ip1` through `rsv_ip4`, `rsv_mac`, `dv_name`, hidden `rsv_ip`, and `rsv_mode=add`. |
| Edit DHCP reservation | `rootfs/www/LAN_reserv_edit.htm:120` | POST to `reserv.cgi`; `rsv_mode=edit` and original-entry fields. |
| Download backup | `rootfs/www/BAK_backup.htm:75` | Backup button navigates to `NETGEAR_<server-rendered-model>.cfg`; the exact model string must be obtained from the authenticated live page. |
| Restore backup | `rootfs/www/BAK_backup.htm:59` | Multipart POST to `backup.cgi`, file field `mtenRestoreCfg`; this is a separate modifying operation. |
| Configure OpenVPN | `rootfs/www/OPENVPN.htm:208` | POST to `openvpn.cgi`; enable checkbox, protocols, ports, and access scope. |
| Export VPN profiles | `rootfs/www/OPENVPN.htm:240` | Links for `windows.zip`, `nonwindows.zip`, `smartphone.zip`; UI checks service/DDNS prerequisites. |

The form JavaScript matters: `rootfs/www/script/script.js:2` rewrites the clicked
button's name/value during submission. A naive request that ignores this may
not reproduce the browser's behavior. Strings for `reserv.cgi`, `openvpn.cgi`,
and `DebugWP.cgi` are also present in the bundled `httpd` binary.

## Reproduce extraction

From this directory, with the ZIP already in `downloads/`:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-inspection.txt
.venv/bin/python extract_firmware.py
```

The extractor removes UBI erase-block headers and reconstructs logical volumes
before opening SquashFS. Simply cutting the image at the `hsqs` signature would
leave interleaved UBI headers and would not reconstruct the filesystem correctly.

## Next investigation

1. Owner-key root SSH is verified. Apply and reboot-test the separately
   documented startup addition if unattended recovery is required.
2. Reproduce an authenticated backup download for the management layer.
3. Read DHCP reservation state and inspect actual form submissions before
   proposing a reversible reservation change.
4. Add VPN operations after checking settings and download prerequisites.

The MCP can use the verified SSH access as a prerequisite and choose SOAP or
authenticated HTTP for particular operations after validation. Local access
helpers exist; the MCP server and modifying DHCP/VPN operations are future work.

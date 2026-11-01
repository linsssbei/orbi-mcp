# Local Orbi tools

> Historical research from 2026-10-27–29; consolidated on 2026-11-01.
> Use the [current MCP guide](../../../README.md) for supported setup and behavior.
> Earlier implementation status below describes the investigation date.
> Device MACs, key fingerprints and personal home paths are replaced with placeholders.
> Evidence and firmware links require the [local research archive](../README.md);
> they are excluded from Git and the npm package. Run repository-relative commands from the repo root.

For the future MCP server, start with the [router access setup guide](docs/router-access.md).
It documents the verified admin-password-to-public-key enrollment flow,
normal key-only SSH access, connection settings, evidence and the remaining
reboot-autostart step. Root SSH is verified on RBR850 `V7.2.8.8_5.1.24`;
the MCP server and automatic Dropbear startup have not been implemented.

The [feature validation report](docs/router-capabilities.md) lists all 164 UI
catalogue entries and the additional SSH capabilities in three categories:
verified operations, hardware limitations, and operations left unvalidated to
avoid disturbing the network. It records 28 verified reads and one hardware
boundary (no 6 GHz radio capability). Failed SOAP actions and missing stock
commands are separate interface notes, not proof that SSH cannot implement a
feature. Configuration hash comparisons and runtime stability evidence remain
linked in the report.

Uses `netgear` (netgear.js) 5.2.0 with Node.js 22 or newer.
Authenticated commands also use Python 3's built-in `getpass`.

```sh
cd docs/research/router-audit
npm run discover
npm run info
npm run devices
npm run config
```

`discover` reads the router's advertised model, firmware and SOAP connection settings without logging in.
Authenticated commands first check the host-specific macOS Keychain item. Without one,
they prompt for the **router admin password** in your terminal, with input hidden.
The password is not saved in project files or passed in command-line arguments.
They log in, read information, and log out; these commands do not change router configuration.

To let the agent run authenticated commands without asking you to enter the password each time:

```sh
npm run auth
```

This command uses macOS's `security` utility to prompt for the password and store it
in your default Keychain, under service `local-orbi-tools:192.168.1.1`, account `admin`.
Subsequent commands retrieve only that item into process memory without printing it.
Use `ORBI_HOST` with both `auth` and subsequent commands if the router IP changes.
You can remove this saved login from the Keychain Access app when finished.

The default router address is `192.168.1.1`. To use another address:

```sh
ORBI_HOST=192.168.0.1 npm run discover
```

Discovery was verified against an RBR850 running `V7.2.8.2_5.1.18`, advertising SOAP 3.46 over HTTPS on port 443.
Authenticated operations still require verification with your admin password.

`config` uses Keychain or prompts once, then reads the LAN/DHCP and WAN/DNS settings, guest Wi-Fi status,
channels, port mappings, access control, QoS, traffic-meter status, time zone, and
attached devices, then writes `router-config-report.json` in this folder. Passwords
are not requested from the router; sensitive field names and the entered password
are redacted from the report. The report is saved with owner-only permissions and
ignored by Git. Unsupported SOAP queries are listed as unavailable, not as disabled.
It does not change settings. It does not capture every setting from the web interface.

Do not use the dependency's `npm test` as a connectivity check: its hardware tests may perform operations beyond these read-only commands.

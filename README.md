# Orbi MCP

A local MCP server that reads a NETGEAR Orbi router over key-only SSH.

This first release provides **`setup`**, **`doctor`**, **`serve`**, and one
read-only MCP tool: **`get_router_status`**. Setup can reuse existing SSH or
guide an owner through firmware-specific public-key enrollment.

Validated target: **RBR850, firmware V7.2.8.8_5.1.24**. Enrollment also requires
SeAL **v2.2.9.6-0-gc6614a48**. This is a community implementation, not an official NETGEAR
API or a claim of compatibility with other models/builds.

## Requirements

- Node.js **22 or newer**, npm, and a macOS or Linux computer on the router LAN.
- OpenSSH client tools: `ssh`, `ssh-keygen`, and `ssh-keyscan`.
- Router administrator password for first enrollment only, or an existing
  authorized private key and trusted SSH known-hosts file.

No software is installed on the router. Setup changes SSH authorization when
explicitly requested; `doctor`, `serve`, and the status tool do not change
router configuration.

## Build and set up

From the project folder:

```sh
npm ci
npm run build
node dist/src/cli.js setup --host 192.168.1.1
node dist/src/cli.js doctor
```

The setup wizard verifies compatibility, asks you to verify the router's
HTTPS certificate fingerprint, generates a dedicated RSA key if needed, and
privately prompts for the admin password. Before enrollment it explains the
router changes and requires you to type `enable`. After enrollment it asks you
to verify/trust the SSH server fingerprint and confirms a key-only login.
First-use fingerprints require independent identity verification; scanning a
key alone does not authenticate a router. The private/public key pair is checked
before enrollment. A saved pending-attempt marker prevents a failed or uncertain
enrollment from being repeated by rerunning setup.

Passwords are not saved, printed or accepted as command-line arguments. The
private key stays on the computer. Generated keys are unencrypted for local
automation and stored with owner-only permissions. Treat access to that key
as root access to the router. Passwords containing backslashes, NUL/newline,
or only echo option flags are currently refused because the firmware handler
cannot safely represent all such inputs. See [access details](docs/access.md).

Setup prints an MCP client entry using absolute paths. It does not edit your
client's configuration automatically.

### Already have SSH access?

Reuse your existing key and trusted server identity without enrollment:

```sh
node dist/src/cli.js setup \
  --host 192.168.1.1 \
  --identity "$HOME/.ssh/orbi_rsa" \
  --known-hosts "$HOME/.ssh/orbi_known_hosts" \
  --host-key-alias 192.168.1.1 \
  --non-interactive
```

`--host-key-alias` must match the router entry in that known-hosts file. The
supplied files are referenced, not copied or overwritten. Private keys must be
owner-only (0600 or 0400); the known-hosts file must not be writable by others.
The current connection disables agent/password prompts, so imported encrypted
keys that require an interactive passphrase are not supported.

For IPv6 link-local access, include the local interface scope, for example
`--host 'fe80::1%en0'` on macOS. You can use an existing IPv4 known-host alias
with that IPv6 address if it identifies the same already-verified router key.
Public Internet targets and hostnames are not accepted.

### Settings location

By default, local settings and generated keys live under:

```text
$XDG_CONFIG_HOME/orbi-mcp/    # if XDG_CONFIG_HOME is set
~/.config/orbi-mcp/          # otherwise
```

The default files are `config.json`, `id_rsa`, `id_rsa.pub`, and `known_hosts`.
Connection settings contain only the address, file paths and SSH host alias.
Use `--config /absolute/path/config.json` on each command to select another
configuration. With no explicit key paths, setup uses the configuration
file's directory for its generated keys/trust file. Keep it outside a checkout.

## Connect an MCP client

Use the entry printed by setup, or adapt:

```json
{
  "mcpServers": {
    "orbi": {
      "command": "/absolute/path/to/node",
      "args": ["/absolute/path/to/orbi-mcp/dist/src/cli.js", "serve"]
    }
  }
}
```

Launch `node` directly: npm's startup banners can interfere with the stdio
protocol. No network-facing MCP HTTP listener is started. The standard stream
is reserved for MCP messages; diagnostics go to stderr.

`serve` can start before setup is complete, so clients can discover its tool.
Calling it without configured access returns `SETUP_REQUIRED` with terminal
setup instructions. There is no password/enrollment MCP tool.

## First tool: `get_router_status`

No arguments. Returns structured JSON with:

- Model and firmware.
- Uptime in seconds; CPU load averages over 1, 5 and 15 minutes.
- Total and available memory in **bytes**, from native kernel metrics.
- Physical WAN interface link state, speed in Mb/s and duplex.
- Observation timestamp and `source: "ssh"`.

CPU load averages are not CPU utilization percentages. A physical WAN link
being up does not prove Internet connectivity. Missing or malformed data
returns an error; it is not replaced with healthy defaults.

The implementation uses a fixed read script: platform/version files,
`/proc/uptime`, `/proc/loadavg`, `/proc/meminfo`, and `ethtool eth4`. Calls have
execution/output limits. Neither tool arguments nor user configuration can
supply remote shell commands.

## Current limits

- **SSH startup after reboot is unvalidated.** Keys were found on persistent
  storage, but no startup repair is implemented. See [validation TODO](TODO.md).
- No automatic re-enrollment, reboot, certificate/key replacement, firmware
  upgrade, firewall change or service restart on connection failure.
- No device inventory, DHCP edits, VPN control, backup/restore or other
  configuration tools yet.
- The new wizard is tested with a local HTTPS router simulator. Existing-key
  setup, doctor and MCP status have also been checked against the stated router
  build on **2026-10-30 UTC**; enrollment was not repeated during this implementation.

## Roadmap

See [remaining work](TODO.md) for delivery order and the
[feature coverage backlog](docs/feature-backlog.md) for every inventoried UI
entry, audited read capability and unresolved interface. Candidate coverage is
not a claim of model support or a promise to implement every shared template.

The [research archive](docs/research/README.md) consolidates the original
router audit, firmware analysis, SSH enrollment investigation and historical
helper sources. Its index distinguishes versioned notes from local-only raw
evidence and firmware artifacts.

## Development

```sh
npm test
npm run check
npm audit --omit=dev
npm pack --dry-run
```

Tests use synthetic metrics and a temporary local TLS server; `openssl` must
be available for those tests. They do not contact a home router, enroll keys,
reboot or change network settings. CI runs the same suite on macOS and Linux.

The repository contains source, synthetic tests, package lock, CI, usage
notes and historical research sources. Raw firmware, extracted filesystems
and private device evidence in the local research archive are ignored by Git;
the entire research archive is excluded from the npm package. Credentials,
keys and runtime configuration remain excluded. The package is marked private
and UNLICENSED.

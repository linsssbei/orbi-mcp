# Access and enrollment

## Supported path

The validated enrollment path on **RBR850 V7.2.8.8_5.1.24 / SeAL v2.2.9.6-0-gc6614a48** is:

1. Verify the LAN target and trust its HTTPS certificate fingerprint explicitly.
2. Read `/currentsetting.htm` and `/api/meta`; require the exact tested build.
3. Ask for the router admin password in a hidden terminal prompt.
4. Send one administrator-authenticated `POST /api/v1/enable_ssh` containing
   the owner public RSA key, using the inspected handler's password encoding.
5. Verify and trust the resulting SSH server identity.
6. Confirm key-only root login and native status before saving configuration.

This firmware endpoint is not a documented general-purpose public API. Do not
remove its compatibility guard based on similar model names or endpoint URLs.

The firmware handler passes the password through a shell command. The client
encodes it as one literal shell word; empty/NUL/newline, backslash-containing
and echo-option-only passwords are refused. Backslashes are not accepted until
the exact target echo behavior has a discriminating validation. Public-key blobs are parsed, restricted to RSA >=2048
bits, stripped of comments and never replaced with private-key contents.
Generated client keys are RSA 3072 for compatibility with the tested Dropbear.
The public key is also derived from the private key and compared with its
`.pub` file before any enrollment; a stale/mismatched pair stops setup.

## Enrollment changes

Enrollment is a modifying administrative operation. The inspected handler:

- Updates `/etc/shells` to permit the SSH shell.
- Replaces `/etc/dropbear/authorized_keys` with the supplied public key.
- Deletes/regenerates the Dropbear RSA host key.
- Starts Dropbear with password login disabled.

Re-enrollment can invalidate other authorized keys and the previous server
pin. It is not a connectivity check. Setup refuses enrollment when TCP 22 is
occupied and never sends an automatic second POST. An uncertain result needs
inspection, not another enrollment attempt. Rejected credentials can lock the
endpoint after repeated failures.

Immediately before an attempt, setup writes an owner-only
`<config-path>.enrollment-pending.json` containing target/key fingerprints and
the attempt time, never a password. It remains after an error or uncertain
response. Rerunning setup cannot send another enrollment while it exists.
After independently verifying the router and supplying trusted existing SSH
files, setup can verify key-only access, save configuration and clear its
pending marker. Do not remove the marker just to make enrollment run again.
Inspect an uncertain outcome before choosing a separate recovery action.

The older UDP activation route starts a different vendor SSH service; it did
not accept the owner's key in our investigation. This package does not use it.
If that service already occupies TCP 22, setup reports it and asks for existing
authorized access. It never reboots the router to clear the port.

## Trust and credential handling

Every enrollment HTTPS request verifies the same certificate fingerprint on
its own connection **before HTTP headers or the credential body are sent**.
This uses an explicit certificate pin rather than accepting a self-signed
certificate silently. The initial fingerprint still requires owner verification.

An SSH key scan supplies a candidate key; user confirmation establishes the
initial local trust record. Subsequent SSH connections enforce strict host-key
checking. The HTTPS certificate and SSH server key are separate identities.
A changed identity is an error, never an automatic pin update.

Normal MCP operation needs no admin password. The unencrypted client identity
is kept outside the project with owner-only permissions; no private key is
uploaded. An imported identity/trust file remains untouched. Legacy `ssh-rsa`
compatibility options are scoped to this one invocation, with user/global SSH
configuration and agent use disabled.

## Read-only diagnostics

`doctor` checks local connection files, key permissions, pinned SSH
authentication and native telemetry. It reports JSON and exits nonzero when
not ready. It never prompts for credentials or attempts repair. If an IPv4
management path is blocked, an independently verified LAN IPv6 address can be
configured through setup; the package does not alter security rules to connect.

A connection refusal does not prove the stored key was erased. A host-key
mismatch does not prove a reboot occurred. Neither triggers enrollment.

## References

- [NETGEAR RBR850-family manual](https://www.downloads.netgear.com/files/GDC/RBK852/RBK852_UM_EN.pdf)
- [NETGEAR 7.2.8.8 firmware release](https://kb.netgear.com/000070916/)
- [Official MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)

The community enrollment findings above come from inspection and validation
of the stated firmware; they are not instructions from NETGEAR's manual.

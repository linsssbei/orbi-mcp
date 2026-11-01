# Remaining work

Updated **2026-11-01** against the implemented source, the 2026-10-28 router
audit and the 2026-10-30 UTC MCP validation. This is a backlog, not a claim
that all candidate features are supported or a commitment to ship them all.
No router requests or configuration changes were made for this update.

The [feature coverage backlog](docs/feature-backlog.md) tracks all **164 UI
catalogue entries in 35 families**, **28 audited read capabilities**, interface
failures and additional SSH research. This file tracks delivery order and work
that spans features. Router validation and MCP implementation are separate
milestones; neither a page nor a working SSH login proves a setter works.

## Completed baseline

- [x] Standalone TypeScript project with setup, doctor and stdio serve commands.
- [x] Existing-key setup and guided firmware-specific enrollment implementation.
- [x] First read-only get_router_status tool: identity, uptime, load, memory and
      physical WAN link telemetry.
- [x] Guided enrollment simulator tests, hidden terminal prompt check,
      independent review and 31 passing tests on Node 22 and 26 in the initial
      build; existing-key setup, doctor and MCP tool checked against the router.
- [x] Package/repository exclusions for credentials, keys, firmware and private
      evidence. These are initial checks, not a substitute for a release check.

## 1. Access validation and recovery

- [ ] Validate the new guided wizard end to end on the exact supported router
      build at an approved time. Prior enrollment research and a simulator are
      not a live test of this new implementation; enrollment replaces keys.
- [ ] Improve the first-use HTTPS/SSH fingerprint verification guide with a
      concrete independent verification procedure.
- [ ] Exercise complete uncertain-enrollment recovery using trusted existing
      access; document how to distinguish a known rejection from an applied
      request with a lost response. Never clear state merely to retry a POST.
- [ ] Improve doctor diagnostics for pending enrollment, missing local files,
      changed identities, occupied vendor SSH, IPv4 rejection and scoped IPv6
      connectivity. Doctor must remain read-only and never repair access.
- [ ] Validate exact firmware echo behavior for backslash/special-case
      passwords before expanding accepted inputs; do not weaken quoting.
- [ ] Decide whether to support encrypted identities/SSH agents or OS key
      storage. Current unencrypted, owner-only RSA identities are deliberate.
- [ ] Establish a compatibility record for each additional model, firmware,
      SeAL version and platform before expanding the enrollment allowlist.

## 2. Reboot persistence — not validated

Do not advertise unattended access after reboot until this is complete.

- [ ] Recheck persistent authorized-key and server-key storage on the target
      build, and identify the missing stock Dropbear startup script.
- [ ] Design a guarded, LAN-bound, key-only startup hook that reuses the
      existing authorization and server keys. Preserve the existing boot file
      and provide a rollback that removes only the added block.
- [ ] Validate the hook at an owner-approved maintenance time; reboot testing
      interrupts the network and is outside ordinary MCP operations.
- [ ] After reboot, confirm root login with the same client key and pinned
      server key, without the admin password or SeAL re-enrollment.
- [ ] Validate rollback and record behavior separately for firmware upgrades
      and factory resets. A successful ordinary reboot does not prove either.

No boot hook is installed. Do not add automatic re-enrollment or startup
repair to doctor, serve or status retrieval.

## 3. Read-only MCP coverage

- [ ] Add attached-device and satellite inventory first. Preserve distinctions
      between attached clients, DHCP leases and neighbors.
- [ ] Add LAN/DHCP settings/leases and WAN address/DNS/MTU/negotiation reads.
- [ ] Add radio/channel/guest/access-control/QoS/traffic-meter/port-map reads;
      disabled flags and zero counters do not validate their engines.
- [ ] Add system/kernel logs, storage, routes, policy rules, interfaces,
      neighbors, bridges, firewall counters and connection statistics.
- [ ] Add process/listener, software/module and existing-container inventory,
      selected nonsecret configuration reads and raw thermal/capture inventory.
- [ ] Add configuration inspection and backup download. Treat backup contents
      as sensitive, store them outside source control, and validate downloaded
      content without claiming restore compatibility.
- [ ] Resolve or exclude failed SOAP/vendor RPC paths and bad telemetry fields
      using the interface checklist in the feature backlog. Keep reliable
      alternatives and do not make a failed SOAP action a feature-level ban.
- [ ] For each new adapter, test real output shape, units, freshness, errors and
      privacy handling; mark MCP coverage only after an end-to-end tool call.

## 4. Foundation for configuration-changing tools

- [ ] Define typed, narrowly scoped changes with input validation and a
      reviewable before/after preview. Do not expose arbitrary shell commands.
- [ ] Read the current values before applying; reject stale previews or
      conflicting operations and serialize changes to the same router.
- [ ] Implement bounded apply, read-back verification and an operation-specific
      rollback/recovery procedure; do not retry uncertain writes automatically.
- [ ] Keep secrets out of previews, logs, MCP responses and retained evidence;
      document when a profile or backup creates/contains credentials.
- [ ] Define explicit confirmation and maintenance-window handling for changes
      that interrupt access, radios, routing, services or mesh connectivity.
- [ ] Validate DHCP reservation add/edit/delete, apply behavior, lease behavior,
      rollback and persistence as the first configuration-changing feature.

## 5. Configuration and active-operation coverage

Use the [full UI checklist](docs/feature-backlog.md#ui-feature-catalogue) for
individual settings, conditional variants and stable inventory IDs.

- [ ] LAN/DHCP and Internet/WAN settings, ISP modes and WAN aggregation.
- [ ] Main/guest/IoT Wi-Fi, security, radio controls, schedules and mesh settings.
- [ ] WPS/satellite pairing, device/satellite metadata and backhaul operations.
- [ ] Access control, site/service filters, schedules and email notifications.
- [ ] Routes, NAT/DMZ/forwarding/triggering, UPnP, IPv6 and router/AP mode.
- [ ] VLAN/IPTV; research custom isolated LANs separately from ISP bridging.
- [ ] Dynamic DNS, timezone/NTP, local HTTPS and supported remote management.
- [ ] Traffic metering, limits and QoS policies/enforcement where applicable.
- [ ] OpenVPN remote-access server enable/configure/profile/tunnel behavior;
      outbound/provider and site-to-site VPN are separate research items.
- [ ] Backup restore, admin/recovery credentials, reboot/reset and firmware
      management; test these only with a concrete recovery procedure.
- [ ] Armor, parental controls, Router Protection and Anywhere Access where
      account, region, entitlement and an actual control interface permit.
- [ ] Bounded speed/cable/scan/capture/debug operations with explicit side
      effects and sensitive-output handling.
- [ ] Resolve hidden/shared/legacy feature applicability before implementation;
      document exclusions instead of promising every template works.

**Excluded by observed hardware:** 6 GHz Wi-Fi on this RBR850. Missing software
commands and failed API calls are not hardware limitations. Optional custom
VPNs, runtimes, containers and routing extensions are tracked in the feature
backlog rather than promised as stock capabilities.

## 6. Reliability and release

- [ ] Add cancellation/concurrency/session-lifecycle tests as tools expand;
      keep command/output limits and explicit freshness timestamps. Avoid
      polling unstable endpoints or hiding stale data behind a successful read.
- [ ] Run clean-install/build/tests/package checks on the configured macOS and
      Linux CI matrix after repository publication; a workflow file alone does
      not establish a passing hosted run.
- [ ] Validate the printed client configuration in the intended MCP clients
      and document any client-specific setup differences.
- [ ] Review the publishable file set, dependencies and secret exclusions again
      before each release. Keep raw validation artifacts private and outside
      the distributable; ship only sanitized compatibility summaries.
- [ ] Choose a license, GitHub owner/repository name and visibility with the
      owner. The current package remains private and UNLICENSED.
- [ ] With explicit approval, create scoped commits, publish the repository and
      open the PR into master. Nothing has been committed or pushed yet.
- [ ] Decide separately whether to distribute via npm; only then change the
      private-package setting and validate the installable CLI artifact.

Recommended next implementation: **read attached-device and satellite
inventory**, while scheduling reboot-persistence validation separately.

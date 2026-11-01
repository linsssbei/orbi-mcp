# Feature coverage backlog

Coverage snapshot: **2026-11-01**. The source audit was captured **2026-10-28**
on **RBR850 V7.2.8.8_5.1.24**; the initial MCP status tool was live-validated
**2026-10-30 UTC**. This backlog update did not contact the router.

This is a sanitized, standalone transcription of the saved feature inventory.
It includes **35 UI families / 164 entries**, **28 audited read capabilities**,
and **20 scoped interface/hardware observations**. No private observations,
firmware files, household identifiers or dependency on the research checkout
are included. These counts describe an inventory, not 164 supported tools.

Use [TODO.md](../TODO.md) for delivery order and cross-cutting work. Stable IDs
below preserve the original inventory identifiers. An unchecked item means
“resolve applicability, validate the operation, and implement if supported.”
It is not a promise to implement every shared template. A documented exclusion
can close a research item without adding a tool. Multiple capabilities may
share one MCP tool.

A prior successful router read is **not** an implemented MCP feature. Reading
a flag is also not validation of a setter or enforcement. GUI parity means
the underlying management operation, not rebuilding the router web UI.

## Audited reads: MCP coverage

All 28 rows had successful read observations in the dated audit. Tool presence
only establishes inventory; packet capture, VPN tunnels and new containers
were not exercised. Reuse validated observations as starting evidence, then
test each shipped adapter end to end.

| Capability ID | Audited operation | Current MCP coverage / remaining scope |
| --- | --- | --- |
| `identity` | Read model, firmware and hardware identity. | Partial: get_router_status exposes model/firmware; extra hardware identity is not exposed. |
| `devices` | List attached clients, IP/MAC, connection type and access state. | Not exposed; implement and test an appropriate read-only adapter. |
| `satellites` | Read satellite inventory, firmware, parent and backhaul metadata. | Not exposed; implement and test an appropriate read-only adapter. |
| `dhcp` | Read current DHCP leases and LAN/DHCP settings. | Not exposed; implement and test an appropriate read-only adapter. |
| `wan` | Read WAN connection type, addresses, DNS and configured MTU. | Not exposed; implement and test an appropriate read-only adapter. |
| `ethernet` | Read physical WAN link speed, duplex and negotiation state. | Partial: get_router_status exposes link/speed/duplex; negotiation capabilities are not exposed. |
| `wifi_radios` | Read active radio interfaces, channel/frequency, width and transmit power. | Not exposed; implement and test an appropriate read-only adapter. |
| `wifi_configuration` | Read configured primary channels and allowed 2.4/5 GHz channels. | Not exposed; implement and test an appropriate read-only adapter. Second 5 GHz SOAP getter is unsupported; its operating channel is readable through iw. |
| `guest_state` | Read 2.4 GHz and primary 5 GHz guest enable state. | Not exposed; implement and test an appropriate read-only adapter. |
| `access_control_state` | Read access-control enable state and attached-device allow/block labels. | Not exposed; implement and test an appropriate read-only adapter. Setting allow/block rules was not tested. |
| `traffic_meter` | Read traffic-meter enable state, options and returned stored counters. | Not exposed; implement and test an appropriate read-only adapter. Disabled meter returns zero counters; traffic collection accuracy not validated. |
| `qos_state` | Read the QoS enabled flag. | Not exposed; implement and test an appropriate read-only adapter. QoS rule configuration was not tested. |
| `port_mapping` | Read the port-mapping table. | Not exposed; implement and test an appropriate read-only adapter. |
| `backup_download` | Download the current configuration backup. | Not exposed; implement and test an appropriate read-only adapter. |
| `logs` | Read system/kernel logs and SOAP log details. | Not exposed; implement and test an appropriate read-only adapter. |
| `uptime` | Read uptime and load/memory metrics through kernel/procd sources. | Implemented subset: get_router_status exposes uptime and native load/memory values. |
| `hardware_resources` | Read CPU identity/counters and native memory information. | Partial: native total/available RAM exposed; CPU identity/counters are not exposed. |
| `storage` | Read filesystem capacity, mounts, MTD layout and persistent-overlay location. | Not exposed; implement and test an appropriate read-only adapter. |
| `routes` | Read IPv4/IPv6 routes and policy-routing rules. | Not exposed; implement and test an appropriate read-only adapter. |
| `network_topology` | Read interfaces, neighbors and bridge membership. | Not exposed; implement and test an appropriate read-only adapter. |
| `firewall` | Read current IPv4/IPv6 firewall rules and counters. | Not exposed; implement and test an appropriate read-only adapter. |
| `conntrack` | Read connection-tracking counts and per-CPU statistics. | Not exposed; implement and test an appropriate read-only adapter. |
| `services` | Read listening sockets and process identities associated with them. | Not exposed; implement and test an appropriate read-only adapter. |
| `lxc_inventory` | List running LXC containers and inspect container state. | Not exposed; implement and test an appropriate read-only adapter. Launching or modifying containers not tested. |
| `temperature_raw` | Read thermal-sensor raw values. | Not exposed; implement and test an appropriate read-only adapter. Sensor-specific units/scaling not normalized; no Celsius interpretation claimed. |
| `software_inventory` | Read installed packages, kernel modules and tool availability. | Not exposed; implement and test an appropriate read-only adapter. |
| `capture_inventory` | Enumerate packet-capture interfaces; identify tcpdump/libpcap versions. | Not exposed; implement and test an appropriate read-only adapter. Version output recorded in ssh-batch-stderr.txt. No live capture performed. |
| `read_config_value` | Read a selected nonsecret configuration value with fnvram get. | Not exposed; implement and test an appropriate read-only adapter. No set/commit/dump command used. |

## UI feature catalogue

Entries that configure or activate something require the change/rollback
foundation in TODO.md and a separately approved validation window. Pure reads
can be added first. Hidden, regional, subscription and shared-template entries
require support research before any live action.

### Internet connection (`internet`)

ISP/region templates are candidates; WAN PPTP/L2TP login does not establish a provider VPN client.

- [ ] `internet/1` — Automatic IPv4/DHCP or fixed IPv4.
- [ ] `internet/2` — Manual DNS server addresses.
- [ ] `internet/3` — WAN MAC default/clone/custom.
- [ ] `internet/4` — Host/system name and domain.
- [ ] `internet/5` — DHCP vendor class and client identifier options 60/61.
- [ ] `internet/6` — PPPoE username/password/service.
- [ ] `internet/7` — PPPoE connection policy and idle timeout.
- [ ] `internet/8` — PPTP WAN ISP login.
- [ ] `internet/9` — L2TP WAN ISP login.
- [ ] `internet/10` — Orange regional ISP templates.

### WAN preference and Internet aggregation (`wan_aggregation`)

WAN aggregation does not establish LAN LACP or dual-WAN failover.

- [ ] `wan_aggregation/1` — Internet-only versus aggregated WAN preference.

### Main WiFi (`main_wifi`)

Shared 2.4/5 GHz front-haul; legacy security controls require applicability checks. The 6 GHz entry is a hardware exclusion.

- [ ] `main_wifi/1` — Main SSID.
- [ ] `main_wifi/2` — 2.4 GHz front-haul channel.
- [ ] `main_wifi/3` — 5 GHz front-haul channel.
- [ ] `main_wifi/4` — 802.11ax enable independently for 2.4/5 GHz.
- [ ] `main_wifi/5` — WPA2-Personal security and passphrase.
- [ ] `main_wifi/6` — Mixed WPA/WPA2 security option in template.
- [ ] `main_wifi/7` — WPA2/WPA3 transition and WPA3-Personal radio controls in template.
- [ ] `main_wifi/8` — Open WiFi choice in RBR850-specific branch.
- [ ] `main_wifi/9` — Legacy WEP and WPA-PSK choices carried in shared template.
- **Excluded — `main_wifi/10`:** 6 GHz fields from shared template. No 6 GHz operating channels were exposed by the live RBR850 radios; no implementation task.

### IoT WiFi (`iot_wifi`)

An IoT SSID does not establish a separately isolated LAN or VLAN.

- [ ] `iot_wifi/1` — Enable IoT network.
- [ ] `iot_wifi/2` — IoT 2.4+5 GHz, 2.4 GHz-only, 5 GHz-only band selection.
- [ ] `iot_wifi/3` — IoT SSID.
- [ ] `iot_wifi/4` — IoT WPA2 or mixed WPA/WPA2 security and passphrase.

### Guest WiFi (`guest_wifi`)

- [ ] `guest_wifi/1` — Enable guest network.
- [ ] `guest_wifi/2` — Guest SSID.
- [ ] `guest_wifi/3` — Guest SSID broadcast.
- [ ] `guest_wifi/4` — Allow guests to see each other and access local network.
- [ ] `guest_wifi/5` — Guest security options including WPA2/WPA3 template branches.
- [ ] `guest_wifi/6` — Guest passphrase.

### Advanced WiFi settings (`advanced_wifi`)

Some daisy-chain, beamforming, MU-MIMO, fast-roaming and broadcast controls are hidden/shared markup; prove current applicability before implementation.

- [ ] `advanced_wifi/1` — Region selection (region/firmware dependent).
- [ ] `advanced_wifi/2` — Enable 2.4 GHz radio template control.
- [ ] `advanced_wifi/3` — 20/40 MHz coexistence.
- [ ] `advanced_wifi/4` — RTS threshold.
- [ ] `advanced_wifi/5` — Preamble mode per band.
- [ ] `advanced_wifi/6` — Transmit power control per band.
- [ ] `advanced_wifi/7` — WiFi on/off schedule templates.
- [ ] `advanced_wifi/8` — Generate new backhaul password.
- [ ] `advanced_wifi/9` — SSID broadcast control hidden in main advanced variant.
- [ ] `advanced_wifi/10` — Daisy chain topology toggle.
- [ ] `advanced_wifi/11` — Implicit beamforming toggle.
- [ ] `advanced_wifi/12` — MU-MIMO toggle.
- [ ] `advanced_wifi/13` — Fast roaming toggle.
- [ ] `advanced_wifi/14` — WMM toggles in no6G shared variant.

### WPS onboarding (`wps`)

Software wizard exposure on this build is unproven; pairing is an active operation.

- [ ] `wps/1` — Software WPS push-button wizard.
- [ ] `wps/2` — Software WPS PIN wizard.

### Attached devices and satellite inventory (`attached_devices`)

Client and satellite reads succeeded in the audit; UI refresh/edit/sync/LED actions were not exercised.

- [ ] `attached_devices/1` — Attached devices display and refresh.
- [ ] `attached_devices/2` — Device name/model/type editing.
- [ ] `attached_devices/3` — Satellite connection inventory.
- [ ] `attached_devices/4` — Satellite LED brightness/schedule/sync fields in shared editor.

### Satellite onboarding and backhaul (`mesh`)

- [ ] `mesh/1` — Add/sync satellite wizard.
- [ ] `mesh/2` — Regenerate backhaul password confirmation.

### Network access control (`access_control`)

State and device labels were read successfully. Applying rules and enforcement remain untested.

- [ ] `access_control/1` — Enable access control.
- [ ] `access_control/2` — Default allow or block new devices.
- [ ] `access_control/3` — Allow/block selected attached device.
- [ ] `access_control/4` — Known-device allowed/blocked lists.
- [ ] `access_control/5` — Add MAC/name to access-control list.

### Site and service blocking (`site_service_blocking`)

- [ ] `site_service_blocking/1` — Keyword/domain block list.
- [ ] `site_service_blocking/2` — Trusted computer exemption.
- [ ] `site_service_blocking/3` — Block-services schedules/modes.
- [ ] `site_service_blocking/4` — Service TCP/UDP protocol and port ranges.
- [ ] `site_service_blocking/5` — Block service by source computer or address range.
- [ ] `site_service_blocking/6` — Days and times schedule.
- [ ] `site_service_blocking/7` — SMTP server/port/authentication email alerts.
- [ ] `site_service_blocking/8` — Immediate and scheduled event email.

### LAN and DHCP (`lan_dhcp`)

- [ ] `lan_dhcp/1` — Router device name.
- [ ] `lan_dhcp/2` — LAN IPv4 address and subnet mask.
- [ ] `lan_dhcp/3` — DHCP server enable.
- [ ] `lan_dhcp/4` — DHCP address pool start/end.
- [ ] `lan_dhcp/5` — RIP direction/version shared-template controls.
- [ ] `lan_dhcp/6` — DHCP static address reservations (MAC/IP/name).

### WAN security and MTU (`wan`)

- [ ] `wan/1` — SPI firewall disable control.
- [ ] `wan/2` — Default DMZ host.
- [ ] `wan/3` — Respond to WAN ping.
- [ ] `wan/4` — IGMP proxy control.
- [ ] `wan/5` — MTU.
- [ ] `wan/6` — NAT filtering secured/open.
- [ ] `wan/7` — SIP ALG disable control.
- [ ] `wan/8` — PPPoE/IPsec/PPTP/L2TP passthrough and IPTV fields in shared template.

### Dynamic DNS (`ddns`)

- [ ] `ddns/1` — Enable Dynamic DNS.
- [ ] `ddns/2` — Provider and hostname/account credentials.
- [ ] `ddns/3` — NETGEAR mynetgear.com registration/account workflow.

### IPv4 static routing (`static_routes`)

- [ ] `static_routes/1` — Route name, private and active flags.
- [ ] `static_routes/2` — Destination/subnet/gateway/metric.

### Router / AP operating mode (`operating_mode`)

- [ ] `operating_mode/1` — Router versus access-point operating mode.
- [ ] `operating_mode/2` — AP management IP automatic versus fixed.

### UPnP (`upnp`)

- [ ] `upnp/1` — UPnP enable.
- [ ] `upnp/2` — Advertisement period and TTL.
- [ ] `upnp/3` — UPnP port mapping table.

### VLAN/IPTV bridging (`vlan_iptv`)

ISP bridge/tag groups do not prove arbitrary routed LAN VLANs or inter-VLAN isolation.

- [ ] `vlan_iptv/1` — Enable VLAN/IPTV and bridge mode.
- [ ] `vlan_iptv/2` — Bridge port group membership.
- [ ] `vlan_iptv/3` — IPTV VLAN enable/id.
- [ ] `vlan_iptv/4` — VLAN tag group name/id/priority/ports.

### IPv6 Internet (`ipv6`)

Modes may depend on SKU, region and ISP; a working IPv6 WAN was not established.

- [ ] `ipv6/1` — Auto detect.
- [ ] `ipv6/2` — Auto configuration.
- [ ] `ipv6/3` — 6to4 tunnel.
- [ ] `ipv6/4` — 6rd tunnel.
- [ ] `ipv6/5` — IPv6 passthrough.
- [ ] `ipv6/6` — Fixed IPv6.
- [ ] `ipv6/7` — DHCPv6 Internet.
- [ ] `ipv6/8` — IPv6 PPPoE.
- [ ] `ipv6/9` — DS-Lite.
- [ ] `ipv6/10` — IPv6 Plus.
- [ ] `ipv6/11` — Orange IPv6.

### OpenVPN remote access service (`openvpn`)

OpenVPN and TUN are present. Server activation, profile generation and working tunnels remain unvalidated; outbound/provider VPN is separate.

- [ ] `openvpn/1` — Enable OpenVPN service.
- [ ] `openvpn/2` — TUN/TAP UDP or TCP protocol and service ports.
- [ ] `openvpn/3` — VPN client Internet versus home-LAN access policy.
- [ ] `openvpn/4` — Download client profiles for Windows/Mac/smartphone.

### Port forwarding and port triggering (`forwarding_triggering`)

- [ ] `forwarding_triggering/1` — Port forwarding predefined/custom services.
- [ ] `forwarding_triggering/2` — Custom forwarding TCP/UDP/external/internal ports/LAN IP.
- [ ] `forwarding_triggering/3` — Port triggering enable/timeout/rule list.
- [ ] `forwarding_triggering/4` — Triggering source/protocol/trigger/inbound port rules.

### Internet traffic meter (`traffic_meter`)

- [ ] `traffic_meter/1` — Enable traffic meter.
- [ ] `traffic_meter/2` — Volume or connection-time monthly limit.
- [ ] `traffic_meter/3` — Monthly counter reset schedule.
- [ ] `traffic_meter/4` — Threshold warning and Internet block at limit.
- [ ] `traffic_meter/5` — Traffic statistics.

### Speed test / QoS templates (`qos_speedtest`)

Shared legacy QoS panels are not validated current UI controls. Enabled-state reads do not establish policy editing or enforcement.

- [ ] `qos_speedtest/1` — Built-in Internet bandwidth test.
- [ ] `qos_speedtest/2` — Manual/dynamic QoS and device/service/LAN-port priority rule controls.

### Status, logs and statistics (`logs_status`)

get_router_status exposes a native health subset. It does not implement dashboard actions, log changes or lease release/renew.

- [ ] `logs_status/1` — Router Internet/WiFi/device status dashboard.
- [ ] `logs_status/2` — Internet interface statistics and connection status.
- [ ] `logs_status/3` — Refresh/clear/email logs.
- [ ] `logs_status/4` — Event categories included in logs.
- [ ] `logs_status/5` — Internet connection status release/renew/connect dialogs.
- [ ] `logs_status/6` — Router reboot confirmation.

### Setup and interface management (`interface_setup`)

- [ ] `interface_setup/1` — Web UI language selector.
- [ ] `interface_setup/2` — Automatic Internet setup versus manual setup or saved configuration.

### Time zone and NTP (`ntp`)

- [ ] `ntp/1` — Default versus preferred NTP server.
- [ ] `ntp/2` — Time zone and daylight-saving adjustment.

### Configuration backup, restore and reset (`backup_reset`)

Backup download succeeded in the audit; it is not exposed by this MCP yet. Restoration/reset remain untested.

- [ ] `backup_reset/1` — Download configuration backup.
- [ ] `backup_reset/2` — Restore uploaded configuration file.
- [ ] `backup_reset/3` — Erase configuration/factory reset confirmation.

### Administrator password and recovery (`admin_password`)

- [ ] `admin_password/1` — Change administrator password.
- [ ] `admin_password/2` — Password recovery and two security questions.

### Local HTTPS and remote management (`management`)

The classic WAN web-admin editor is absent in the observed current page. Local HTTPS and app Anywhere Access are separate capabilities.

- [ ] `management/1` — Always use HTTPS for local management.
- [ ] `management/2` — Classic WAN web remote management, source IP allowlist and port.
- [ ] `management/3` — Orbi app remote-access status/opt-in template.

### Firmware management (`firmware`)

Version inspection, update checking and firmware application are separate operations; do not perform an update to test a reader.

- [ ] `firmware/1` — Check router and satellite firmware versions/updates.
- [ ] `firmware/2` — Manual firmware file upload.
- [ ] `firmware/3` — Router and satellite update orchestration.
- [ ] `firmware/4` — Automatic firmware update setting template.

### NETGEAR Armor (`armor`)

Running security containers do not establish subscription entitlements or active protection.

- [ ] `armor/1` — Armor dashboard state.
- [ ] `armor/2` — Network threat blocking and malicious-web protection.
- [ ] `armor/3` — Device/network vulnerability scans.
- [ ] `armor/4` — Companion-device protection and Armor VPN (plan dependent).

### Smart Parental Controls and legacy parental templates (`parental`)

Account, region and subscription dependencies remain unverified; legacy Circle/OpenDNS markup is not proof of support.

- [ ] `parental/1` — SPC supported product, app management (no exact native SPC HTML page established).
- [ ] `parental/2` — Legacy Circle/OpenDNS switching form.
- [ ] `parental/3` — Pause Internet across a child's devices.
- [ ] `parental/4` — Child profiles and assigned devices.
- [ ] `parental/5` — Internet/app usage and website history.
- [ ] `parental/6` — Age-based content filtering.
- [ ] `parental/7` — Daily time limits and bedtimes.
- [ ] `parental/8` — Internet breaks and extra-time rewards.
- [ ] `parental/9` — My Time companion mobile-device management.

### NETGEAR Router Protection (`router_protection`)

Release-lineage support is not proof of a working current UI or controllable service.

- [ ] `router_protection/1` — Router Protection support in model release lineage.

### Diagnostics/debug artifact (`diagnostics`)

The debug page was observed; record/export/capture/telnet controls were not executed. A diagnostic getter can have side effects.

- [ ] `diagnostics/1` — Diagnostic recording and debug-file download controls.
- [ ] `diagnostics/2` — LAN/WAN packet capture and roaming debug template.
- [ ] `diagnostics/3` — Telnet/RSTP/beta controls in debug template.

### Other shared UI artifacts (`shared_residue`)

Shared USB/ReadySHARE/DLNA/WDS/ACL artifacts are research candidates, not supported RBR850 features.

- [ ] `shared_residue/1` — ReadySHARE/USB storage placeholder.
- [ ] `shared_residue/2` — USB advanced tab placeholder.
- [ ] `shared_residue/3` — DLNA control artifact.
- [ ] `shared_residue/4` — Wireless WDS template.
- [ ] `shared_residue/5` — Legacy wireless-only MAC ACL template.

## Interface failures and workarounds

These are scoped observations from the audit, not blanket feature failures.
For each unchecked entry, validate an alternative or document its exclusion
from the MCP allowlist; do not retry disruptive readers just to retest them.

- [ ] `soap_getWANDNSLookUpStatus` — urn:NETGEAR-ROUTER:service:WANIPConnection:1#GetDNSLookUpStatus.
- [ ] `soap_getBandwidthControlOptions` — urn:NETGEAR-ROUTER:service:AdvancedQoS:1#GetBandwidthControlOptions.
- [ ] `soap_get5GGuestAccessEnabled2` — urn:NETGEAR-ROUTER:service:WLANConfiguration:1#Get5GGuestAccessEnabled2.
- [ ] `soap_get5G1ChannelInfo` — urn:NETGEAR-ROUTER:service:WLANConfiguration:1#Get5G1ChannelInfo.
- [ ] `soap_getSmartConnectEnabled` — urn:NETGEAR-ROUTER:service:WLANConfiguration:1#IsSmartConnectEnabled.
- [ ] `soap_getAvailableChannel(5G1)` — urn:NETGEAR-ROUTER:service:WLANConfiguration:1#GetAvailableChannel.
- [ ] `soap_get5G1GuestAccessEnabled2` — urn:NETGEAR-ROUTER:service:WLANConfiguration:1#Get5G1GuestAccessEnabled.
- **Hardware exclusion — `no_6ghz_radio`:** No 6 GHz channels exposed. Tracked above; not an engineering task.
- [ ] `device_list_all_failure` — GetDeviceListAll is not a usable validated reader here: HTTP 500, followed by service errors and lost authentication.
- [ ] `system_info_unreliable` — GetSystemInfo returns physical-memory value 256, inconsistent with the native 894960 KiB memory view under the expected units.
- [ ] `timezone_invalid` — GetTimeZoneInfo returns a namespace URI as NewTimeZone, not a usable timezone value.
- [ ] `internet_port_payload` — GetInternetPortInfo returns a WAN-config-shaped payload, without the expected internet-port information field.
- [ ] `wireless_rpc_unreliable` — Vendor wireless RPC timed out; subsequent wireless/satellite object calls returned Not found. Objects appeared again later.
- [ ] `ipv4_management_block` — This client could not connect to router IPv4 management ports during the audit; a controlled refusal correlated with Bitdefender TCP REJECT counter increments.
- [ ] `classic_wan_web_editor` — The current Web Services Management page renders local-HTTPS management; conventional WAN remote-management fields are hidden state fields.
- [ ] `no_wg_cli` — WireGuard wg command is not installed/available in the current router host environment.
- [ ] `no_docker_cli` — Docker command is not installed/available in the current router host environment.
- [ ] `no_python_cli` — Python 3 command is not installed/available in the current router host environment.
- [ ] `no_node_cli` — Node.js command is not installed/available in the current router host environment.
- [ ] `no_systemd_cli` — systemd systemctl command is not installed/available in the current router host environment.

## Additional SSH research beyond GUI parity

- [ ] Validate mesh/hybrid-bridge topology and per-link backhaul signal/bitrate getters; SOAP inventory alone does not validate native driver telemetry.
- [ ] Validate complete client/station attribution across router and satellites; do not equate DHCP leases, neighbors and connected-client lists.
- [ ] Validate CPU utilization and I/O sampling with explicit intervals/units; load average is not CPU percentage.
- [ ] Normalize thermal sensor units only after identifying each sensor and its scale; raw values alone are not Celsius.
- [ ] Inspect orbistats/vendor getters for cache/log writes and secret exposure before treating them as read-only.
- [ ] Evaluate bounded nftables inspection separately from firewall migration; an empty ruleset does not establish a functioning replacement firewall.
- [ ] Research custom routing persistence through vendor configuration; runtime route edits do not establish reboot persistence.
- [ ] Evaluate outbound/provider and site-to-site OpenVPN profiles, routing and tunnel validation separately from the GUI remote-access server.
- [ ] Investigate WireGuard, Docker, alternative runtimes and custom LXC workloads only as optional extensions. Missing stock commands do not prove hardware impossibility.
- [ ] Treat actual packet capture, active scans, speed/cable tests and container/service changes as active operations requiring their own limits and validation.

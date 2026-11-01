# Orbi feature validation status for an MCP server

> Historical research from 2026-10-27–29; consolidated on 2026-11-01.
> Use the [current MCP guide](../../../../README.md) for supported setup and behavior.
> Earlier implementation status below describes the investigation date.
> Device MACs, key fingerprints and personal home paths are replaced with placeholders.
> Evidence and firmware links require the [local research archive](../../README.md);
> they are excluded from Git and the npm package. Run repository-relative commands from the repo root.

Device: **RBR850 V7.2.8.8_5.1.24**, in router mode. Live audit:
**2026-10-28**. Classification revised **2026-10-29** using saved evidence;
this documentation update made no router requests or configuration changes.

We have **verified root SSH access**. A failed SOAP action or missing command
is an interface observation, not proof that a feature cannot be implemented
through SSH. Root access lets us investigate configuration files, vendor tools
and services; it does not by itself validate a write/apply/persistence procedure.

## The three categories

| Category | Meaning |
| --- | --- |
| **1. Verified** | The stated operation actually worked on this router. Most verified operations are reads. Reading a setting does not validate changing it. |
| **2. Not verified due to hardware** | Live hardware/driver evidence identifies a capability absent from this model. Currently this applies only to 6 GHz Wi-Fi. |
| **3. Not validated to avoid disturbing the network** | We did not change settings, activate services, install software or run active operations. Candidate features remain unproven; hidden templates and cloud/subscription dependencies can also affect feasibility. |

There is no general “cannot do through SSH” category. Interface failures and
missing stock programs are recorded separately below. **Category 3 does not
promise eventual support**, and category 2 is not used merely because an API
failed or software is missing.

The inventory covers **164 documentation/template entries in 35 UI families**,
**39 authenticated live UI pages**, and **28 verified read capabilities**.
The complete UI catalogue below assigns a category to every entry. Historical
access setup is documented separately in [Router access setup](router-access.md).

The sources combine the [official RBR850-family manual](https://www.downloads.netgear.com/files/GDC/RBK852/RBK852_UM_EN.pdf),
[exact firmware release](https://kb.netgear.com/000070916/), extracted firmware,
authenticated UI GETs, authenticated SOAP getter responses and pinned-key SSH.
Documentation and page markup identify candidates; live results establish the
scope of each verified operation.

## 1. Verified

### SSH access

Dedicated RSA-key login as **root** worked with password authentication
disabled. Normal SSH connections use the private key. Persistent key files were
identified; automatic SSH startup and access after another reboot remain in
category 3. See the [access evidence and connection guide](router-access.md).

### Router operations

Each row names the exact verified operation. All 28 are backed by saved live
observations. A tool's presence verifies inventory only, not its execution for
an untested purpose.

| ID | Verified operation | Observed scope / limits | Evidence |
| --- | --- | --- | --- |
| `identity` | Read model, firmware and hardware identity. | Read/inventory only; no configuration change tested. | [soap-getter-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-getter-results.json), [system_board_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/system_board_ipv6.json) |
| `devices` | List attached clients, IP/MAC, connection type and access state. | attached devices: 18 | [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json) |
| `satellites` | Read satellite inventory, firmware, parent and backhaul metadata. | satellites: 1; observed satellite model: RBS850; observed satellite firmware: V7.2.8.2 | [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json) |
| `dhcp` | Read current DHCP leases and LAN/DHCP settings. | Read/inventory only; no configuration change tested. | [dhcp_leases_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/dhcp_leases_ipv6.json), [soap-getter-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-getter-results.json) |
| `wan` | Read WAN connection type, addresses, DNS and configured MTU. | Read/inventory only; no configuration change tested. | [soap-getter-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-getter-results.json), [wan_state_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/wan_state_ipv6.json) |
| `ethernet` | Read physical WAN link speed, duplex and negotiation state. | observed speed: 2500Mb/s; observed duplex: Full | [ethernet_phy_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/ethernet_phy_ipv6.json) |
| `wifi_radios` | Read active radio interfaces, channel/frequency, width and transmit power. | Read/inventory only; no configuration change tested. | [wireless_interfaces.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/wireless_interfaces.json), [driver_capabilities_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/driver_capabilities_ipv6.json) |
| `wifi_configuration` | Read configured primary channels and allowed 2.4/5 GHz channels. | Second 5 GHz SOAP getter is unsupported; its operating channel is readable through iw. | [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json) |
| `guest_state` | Read 2.4 GHz and primary 5 GHz guest enable state. | observed enabled: False | [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json) |
| `access_control_state` | Read access-control enable state and attached-device allow/block labels. | Setting allow/block rules was not tested.; observed enabled: False | [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json), [http-ui-pages.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/http-ui-pages.json) |
| `traffic_meter` | Read traffic-meter enable state, options and returned stored counters. | Disabled meter returns zero counters; traffic collection accuracy not validated.; observed enabled: False | [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json) |
| `qos_state` | Read the QoS enabled flag. | QoS rule configuration was not tested.; observed enabled: False | [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json) |
| `port_mapping` | Read the port-mapping table. | observed entries: 0 | [soap-getter-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-getter-results.json) |
| `backup_download` | Download the current configuration backup. | bytes received: 131096; backup payload saved: False; restore tested: False | [backup-download.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/backup-download.json) |
| `logs` | Read system/kernel logs and SOAP log details. | Read/inventory only; no configuration change tested. | [logs_readable_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/logs_readable_ipv6.json), [kernel_logs_readable_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/kernel_logs_readable_ipv6.json), [soap-phase2-results.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json) |
| `uptime` | Read uptime and load/memory metrics through kernel/procd sources. | Read/inventory only; no configuration change tested. | [uptime.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/uptime.json), [system_metrics_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/system_metrics_ipv6.json) |
| `hardware_resources` | Read CPU identity/counters and native memory information. | Read/inventory only; no configuration change tested. | [cpu.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/cpu.json), [memory.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/memory.json), [cpu_counters_sample1_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/cpu_counters_sample1_ipv6.json) |
| `storage` | Read filesystem capacity, mounts, MTD layout and persistent-overlay location. | Read/inventory only; no configuration change tested. | [filesystems.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/filesystems.json), [mounts.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/mounts.json), [mtd_partitions_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/mtd_partitions_ipv6.json) |
| `routes` | Read IPv4/IPv6 routes and policy-routing rules. | Read/inventory only; no configuration change tested. | [routes_ipv4.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/routes_ipv4.json), [routes_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/routes_ipv6.json), [routing_rules_final_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/routing_rules_final_ipv6.json) |
| `network_topology` | Read interfaces, neighbors and bridge membership. | Read/inventory only; no configuration change tested. | [interfaces.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/interfaces.json), [neighbors.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/neighbors.json), [bridge.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/bridge.json) |
| `firewall` | Read current IPv4/IPv6 firewall rules and counters. | Read/inventory only; no configuration change tested. | [firewall_rules.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/firewall_rules.json), [firewall_ipv6_rules.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/firewall_ipv6_rules.json), [ipv4-rejection-counter-validation.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/ipv4-rejection-counter-validation.json) |
| `conntrack` | Read connection-tracking counts and per-CPU statistics. | Read/inventory only; no configuration change tested. | [connection_count.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/connection_count.json), [conntrack_stats_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/conntrack_stats_ipv6.json) |
| `services` | Read listening sockets and process identities associated with them. | Read/inventory only; no configuration change tested. | [listeners.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/listeners.json), [current_listeners_after_soap_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/current_listeners_after_soap_ipv6.json) |
| `lxc_inventory` | List running LXC containers and inspect container state. | Launching or modifying containers not tested.; running containers: ['armor-bd', 'spc-circle'] | [container_inventory_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/container_inventory_ipv6.json), [container_state_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/container_state_ipv6.json), [lxc_version_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/lxc_version_ipv6.json) |
| `temperature_raw` | Read thermal-sensor raw values. | Sensor-specific units/scaling not normalized; no Celsius interpretation claimed. | [kernel_temperature_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/kernel_temperature_ipv6.json) |
| `software_inventory` | Read installed packages, kernel modules and tool availability. | Read/inventory only; no configuration change tested. | [packages.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/packages.json), [kernel_modules.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/kernel_modules.json), [command_inventory.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/command_inventory.json) |
| `capture_inventory` | Enumerate packet-capture interfaces; identify tcpdump/libpcap versions. | Version output recorded in ssh-batch-stderr.txt. No live capture performed. | [capture_interfaces_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/capture_interfaces_ipv6.json) |
| `read_config_value` | Read a selected nonsecret configuration value with fnvram get. | No set/commit/dump command used. | [config_getter_lan_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/config_getter_lan_ipv6.json), [current_routing_mode_ipv6.json](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/current_routing_mode_ipv6.json) |

Configuration backup download is operationally verified: HTTP 200,
`application/configuration`, **131,096 bytes**. The payload was hashed in memory
and not retained. Backup restoration is category 3.

## 2. Not verified due to hardware

| Feature | Validated hardware boundary | Evidence |
| --- | --- | --- |
| 6 GHz Wi-Fi / enabling a 6 GHz band | None of the three live radios exposes 6 GHz operating channels. The observed radios are 2.4/5 GHz. Shared firmware form fields do not add a radio; SSH cannot create the missing band. | [Driver capabilities](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/driver_capabilities_ipv6.json), [radio inventory](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/wireless_interfaces.json) |

**No other feature is classified as hardware-blocked by this audit.** In
particular, unavailable `wg`, Docker, Python, Node.js or systemd commands are
not evidence of hardware limitations. Shared USB/ReadySHARE/WDS templates
remain unproven candidates rather than newly asserted hardware limitations.

## 3. Not validated to avoid disturbing the network

We preserved the current network configuration. These operations were not
attempted; neither success nor impossibility has been established.

| Feature / operation | What remains unvalidated |
| --- | --- |
| DHCP reservations by MAC | Add/edit/delete reservations; correct apply mechanism; lease behavior and persistence. Existing LAN/DHCP settings and leases are readable. |
| LAN and DHCP service | Change LAN address, mask, DHCP pool/server settings, device name or RIP behavior. |
| Internet/WAN | Change DHCP/static/PPPoE/PPTP/L2TP/ISP templates, DNS, MAC, MTU, aggregation or WAN security. WAN aggregation does not establish LAN LACP or dual-WAN failover. |
| Main, guest and IoT Wi-Fi | Enable/disable networks/radios, change SSIDs/passwords/security/AX/channels/power/coexistence/schedules; per-band primary SSIDs. No IoT isolation claim follows from an extra SSID. |
| Mesh, WPS and satellites | Pair/sync, edit device/satellite metadata, LED settings, regenerate backhaul credentials or alter mesh behavior. |
| Access control and filtering | Add/apply allow/block rules, new-device policies, site/service filters, schedules or email alerts; verify enforcement. |
| QoS and traffic meter | Apply priorities/limits, enable metering and validate collection accuracy. Existing disabled-state flags and stored counters were read. |
| Routing, NAT and UPnP | Add/change routes, port forwarding/triggering, DMZ or UPnP mappings; verify traffic forwarding. |
| VLAN/IPTV and isolated LANs | Apply ISP VLAN/bridge settings or build custom isolated LANs/inter-VLAN firewall policy. Existing templates do not prove arbitrary LAN segmentation. |
| IPv6 and router/AP mode | Change ISP modes, establish IPv6 WAN connectivity, or switch operating mode. |
| Dynamic DNS, NTP and management | Update DDNS/accounts, timezone/NTP, local HTTPS or remote access; validate account/service behavior. |
| OpenVPN server | Enable/configure/start the service, generate/download profiles that may create credentials, or establish a working remote-access tunnel. OpenVPN 2.4.7 and TUN are present. |
| Outbound/provider or site-to-site VPN | Build and test client profiles, routing and working tunnels. Installed OpenVPN and samples do not establish a complete configuration. |
| Backup restoration and factory reset | Restore a backup or erase/reset settings. Backup download alone is category 1. |
| Firmware and service lifecycle | Check for updates, upload/apply firmware, reboot the router/satellites, or restart services. |
| Credentials and SSH persistence | Change passwords/recovery questions/keys, apply a Dropbear boot hook, or reboot to test persistence. |
| Packages, runtimes and custom containers | Install/run WireGuard, Docker, Python or Node.js; launch custom LXC workloads; replace service-management tools or firmware. Existing LXC inventory/state is readable. |
| Firewall changes | Apply rules, alter security integrations or test packet enforcement. Existing rules/counters are readable. |
| App/cloud/security features | Exercise Armor, Smart Parental Controls, Router Protection, Anywhere Access and subscription/account workflows. Running containers do not prove entitlements or enforcement. |
| Diagnostics | Active Wi-Fi scans, speed/cable tests, packet captures, debug recording/export, clearing/emailing logs or lease release/renew. Capture-interface inventory and log reads alone are verified. |
| Other shared-template features | Exercise legacy/hidden QoS, WMM, WDS, wireless ACL, Circle/OpenDNS, USB/ReadySHARE/DLNA or region-specific controls. Presence in firmware is not support validation. |

Some category 3 features also need backend research, model/region checks,
credentials or entitlements; avoiding changes is not their only open question.
No category 3 operation was tried simply to make a test pass.

### Complete UI feature catalogue

All **164 entries** from the source inventory are listed below, including
legacy/shared candidates. The number identifies one of the three categories
above. Category **1 + 3** splits an entry that combines a verified read with an
untested UI refresh/action. For configurable entries in category 3, related
read-only observations in section 1 remain valid; changing/applying the setting
is what has not been validated. No browser form was submitted or UI control
action executed. HTTP page retrieval alone is not category 1 validation of
the advertised feature.

| UI family | Feature / catalogue entry | Category and scope |
| --- | --- | --- |
| Internet connection | Automatic IPv4/DHCP or fixed IPv4 | 3: operation / apply behavior untested |
| Internet connection | Manual DNS server addresses | 3: operation / apply behavior untested |
| Internet connection | WAN MAC default/clone/custom | 3: operation / apply behavior untested |
| Internet connection | Host/system name and domain | 3: operation / apply behavior untested |
| Internet connection | DHCP vendor class and client identifier options 60/61 | 3: operation / apply behavior untested |
| Internet connection | PPPoE username/password/service | 3: operation / apply behavior untested |
| Internet connection | PPPoE connection policy and idle timeout | 3: operation / apply behavior untested |
| Internet connection | PPTP WAN ISP login | 3: operation / apply behavior untested |
| Internet connection | L2TP WAN ISP login | 3: operation / apply behavior untested |
| Internet connection | Orange regional ISP templates | 3: operation / apply behavior untested |
| WAN preference and Internet aggregation | Internet-only versus aggregated WAN preference | 3: operation / apply behavior untested |
| Main WiFi | Main SSID | 3: operation / apply behavior untested |
| Main WiFi | 2.4 GHz front-haul channel | 3: operation / apply behavior untested |
| Main WiFi | 5 GHz front-haul channel | 3: operation / apply behavior untested |
| Main WiFi | 802.11ax enable independently for 2.4/5 GHz | 3: operation / apply behavior untested |
| Main WiFi | WPA2-Personal security and passphrase | 3: operation / apply behavior untested |
| Main WiFi | Mixed WPA/WPA2 security option in template | 3: operation / apply behavior untested |
| Main WiFi | WPA2/WPA3 transition and WPA3-Personal radio controls in template | 3: operation / apply behavior untested |
| Main WiFi | Open WiFi choice in RBR850-specific branch | 3: operation / apply behavior untested |
| Main WiFi | Legacy WEP and WPA-PSK choices carried in shared template | 3: operation / apply behavior untested |
| Main WiFi | 6 GHz fields from shared template | 2: no 6 GHz radio channels exposed |
| IoT WiFi | Enable IoT network | 3: operation / apply behavior untested |
| IoT WiFi | IoT 2.4+5 GHz, 2.4 GHz-only, 5 GHz-only band selection | 3: operation / apply behavior untested |
| IoT WiFi | IoT SSID | 3: operation / apply behavior untested |
| IoT WiFi | IoT WPA2 or mixed WPA/WPA2 security and passphrase | 3: operation / apply behavior untested |
| Guest WiFi | Enable guest network | 3: operation / apply behavior untested |
| Guest WiFi | Guest SSID | 3: operation / apply behavior untested |
| Guest WiFi | Guest SSID broadcast | 3: operation / apply behavior untested |
| Guest WiFi | Allow guests to see each other and access local network | 3: operation / apply behavior untested |
| Guest WiFi | Guest security options including WPA2/WPA3 template branches | 3: operation / apply behavior untested |
| Guest WiFi | Guest passphrase | 3: operation / apply behavior untested |
| Advanced WiFi settings | Region selection (region/firmware dependent) | 3: operation / apply behavior untested |
| Advanced WiFi settings | Enable 2.4 GHz radio template control | 3: operation / apply behavior untested |
| Advanced WiFi settings | 20/40 MHz coexistence | 3: operation / apply behavior untested |
| Advanced WiFi settings | RTS threshold | 3: operation / apply behavior untested |
| Advanced WiFi settings | Preamble mode per band | 3: operation / apply behavior untested |
| Advanced WiFi settings | Transmit power control per band | 3: operation / apply behavior untested |
| Advanced WiFi settings | WiFi on/off schedule templates | 3: operation / apply behavior untested |
| Advanced WiFi settings | Generate new backhaul password | 3: operation / apply behavior untested |
| Advanced WiFi settings | SSID broadcast control hidden in main advanced variant | 3: operation / apply behavior untested |
| Advanced WiFi settings | Daisy chain topology toggle | 3: operation / apply behavior untested |
| Advanced WiFi settings | Implicit beamforming toggle | 3: operation / apply behavior untested |
| Advanced WiFi settings | MU-MIMO toggle | 3: operation / apply behavior untested |
| Advanced WiFi settings | Fast roaming toggle | 3: operation / apply behavior untested |
| Advanced WiFi settings | WMM toggles in no6G shared variant | 3: operation / apply behavior untested |
| WPS onboarding | Software WPS push-button wizard | 3: operation / apply behavior untested |
| WPS onboarding | Software WPS PIN wizard | 3: operation / apply behavior untested |
| Attached devices and satellite inventory | Attached devices display and refresh | 1: client inventory read; 3: UI refresh action |
| Attached devices and satellite inventory | Device name/model/type editing | 3: operation / apply behavior untested |
| Attached devices and satellite inventory | Satellite connection inventory | 1: satellite inventory read |
| Attached devices and satellite inventory | Satellite LED brightness/schedule/sync fields in shared editor | 3: operation / apply behavior untested |
| Satellite onboarding and backhaul | Add/sync satellite wizard | 3: operation / apply behavior untested |
| Satellite onboarding and backhaul | Regenerate backhaul password confirmation | 3: operation / apply behavior untested |
| Network access control | Enable access control | 3: operation / apply behavior untested |
| Network access control | Default allow or block new devices | 3: operation / apply behavior untested |
| Network access control | Allow/block selected attached device | 3: operation / apply behavior untested |
| Network access control | Known-device allowed/blocked lists | 3: operation / apply behavior untested |
| Network access control | Add MAC/name to access-control list | 3: operation / apply behavior untested |
| Site and service blocking | Keyword/domain block list | 3: operation / apply behavior untested |
| Site and service blocking | Trusted computer exemption | 3: operation / apply behavior untested |
| Site and service blocking | Block-services schedules/modes | 3: operation / apply behavior untested |
| Site and service blocking | Service TCP/UDP protocol and port ranges | 3: operation / apply behavior untested |
| Site and service blocking | Block service by source computer or address range | 3: operation / apply behavior untested |
| Site and service blocking | Days and times schedule | 3: operation / apply behavior untested |
| Site and service blocking | SMTP server/port/authentication email alerts | 3: operation / apply behavior untested |
| Site and service blocking | Immediate and scheduled event email | 3: operation / apply behavior untested |
| LAN and DHCP | Router device name | 3: operation / apply behavior untested |
| LAN and DHCP | LAN IPv4 address and subnet mask | 3: operation / apply behavior untested |
| LAN and DHCP | DHCP server enable | 3: operation / apply behavior untested |
| LAN and DHCP | DHCP address pool start/end | 3: operation / apply behavior untested |
| LAN and DHCP | RIP direction/version shared-template controls | 3: operation / apply behavior untested |
| LAN and DHCP | DHCP static address reservations (MAC/IP/name) | 3: operation / apply behavior untested |
| WAN security and MTU | SPI firewall disable control | 3: operation / apply behavior untested |
| WAN security and MTU | Default DMZ host | 3: operation / apply behavior untested |
| WAN security and MTU | Respond to WAN ping | 3: operation / apply behavior untested |
| WAN security and MTU | IGMP proxy control | 3: operation / apply behavior untested |
| WAN security and MTU | MTU | 3: operation / apply behavior untested |
| WAN security and MTU | NAT filtering secured/open | 3: operation / apply behavior untested |
| WAN security and MTU | SIP ALG disable control | 3: operation / apply behavior untested |
| WAN security and MTU | PPPoE/IPsec/PPTP/L2TP passthrough and IPTV fields in shared template | 3: operation / apply behavior untested |
| Dynamic DNS | Enable Dynamic DNS | 3: operation / apply behavior untested |
| Dynamic DNS | Provider and hostname/account credentials | 3: operation / apply behavior untested |
| Dynamic DNS | NETGEAR mynetgear.com registration/account workflow | 3: operation / apply behavior untested |
| IPv4 static routing | Route name, private and active flags | 3: operation / apply behavior untested |
| IPv4 static routing | Destination/subnet/gateway/metric | 3: operation / apply behavior untested |
| Router / AP operating mode | Router versus access-point operating mode | 3: operation / apply behavior untested |
| Router / AP operating mode | AP management IP automatic versus fixed | 3: operation / apply behavior untested |
| UPnP | UPnP enable | 3: operation / apply behavior untested |
| UPnP | Advertisement period and TTL | 3: operation / apply behavior untested |
| UPnP | UPnP port mapping table | 1: port-mapping table read (empty) |
| VLAN/IPTV bridging | Enable VLAN/IPTV and bridge mode | 3: operation / apply behavior untested |
| VLAN/IPTV bridging | Bridge port group membership | 3: operation / apply behavior untested |
| VLAN/IPTV bridging | IPTV VLAN enable/id | 3: operation / apply behavior untested |
| VLAN/IPTV bridging | VLAN tag group name/id/priority/ports | 3: operation / apply behavior untested |
| IPv6 Internet | Auto detect | 3: operation / apply behavior untested |
| IPv6 Internet | Auto configuration | 3: operation / apply behavior untested |
| IPv6 Internet | 6to4 tunnel | 3: operation / apply behavior untested |
| IPv6 Internet | 6rd tunnel | 3: operation / apply behavior untested |
| IPv6 Internet | IPv6 passthrough | 3: operation / apply behavior untested |
| IPv6 Internet | Fixed IPv6 | 3: operation / apply behavior untested |
| IPv6 Internet | DHCPv6 Internet | 3: operation / apply behavior untested |
| IPv6 Internet | IPv6 PPPoE | 3: operation / apply behavior untested |
| IPv6 Internet | DS-Lite | 3: operation / apply behavior untested |
| IPv6 Internet | IPv6 Plus | 3: operation / apply behavior untested |
| IPv6 Internet | Orange IPv6 | 3: operation / apply behavior untested |
| OpenVPN remote access service | Enable OpenVPN service | 3: operation / apply behavior untested |
| OpenVPN remote access service | TUN/TAP UDP or TCP protocol and service ports | 3: operation / apply behavior untested |
| OpenVPN remote access service | VPN client Internet versus home-LAN access policy | 3: operation / apply behavior untested |
| OpenVPN remote access service | Download client profiles for Windows/Mac/smartphone | 3: operation / apply behavior untested |
| Port forwarding and port triggering | Port forwarding predefined/custom services | 3: operation / apply behavior untested |
| Port forwarding and port triggering | Custom forwarding TCP/UDP/external/internal ports/LAN IP | 3: operation / apply behavior untested |
| Port forwarding and port triggering | Port triggering enable/timeout/rule list | 3: operation / apply behavior untested |
| Port forwarding and port triggering | Triggering source/protocol/trigger/inbound port rules | 3: operation / apply behavior untested |
| Internet traffic meter | Enable traffic meter | 3: operation / apply behavior untested |
| Internet traffic meter | Volume or connection-time monthly limit | 3: operation / apply behavior untested |
| Internet traffic meter | Monthly counter reset schedule | 3: operation / apply behavior untested |
| Internet traffic meter | Threshold warning and Internet block at limit | 3: operation / apply behavior untested |
| Internet traffic meter | Traffic statistics | 1: stored counter read (zero while disabled); 3: enabled-meter collection accuracy |
| Speed test / QoS templates | Built-in Internet bandwidth test | 3: operation / apply behavior untested |
| Speed test / QoS templates | Manual/dynamic QoS and device/service/LAN-port priority rule controls | 3: operation / apply behavior untested |
| Status, logs and statistics | Router Internet/WiFi/device status dashboard | 3: operation / apply behavior untested |
| Status, logs and statistics | Internet interface statistics and connection status | 3: operation / apply behavior untested |
| Status, logs and statistics | Refresh/clear/email logs | 3: operation / apply behavior untested |
| Status, logs and statistics | Event categories included in logs | 3: operation / apply behavior untested |
| Status, logs and statistics | Internet connection status release/renew/connect dialogs | 3: operation / apply behavior untested |
| Status, logs and statistics | Router reboot confirmation | 3: operation / apply behavior untested |
| Setup and interface management | Web UI language selector | 3: operation / apply behavior untested |
| Setup and interface management | Automatic Internet setup versus manual setup or saved configuration | 3: operation / apply behavior untested |
| Time zone and NTP | Default versus preferred NTP server | 3: operation / apply behavior untested |
| Time zone and NTP | Time zone and daylight-saving adjustment | 3: operation / apply behavior untested |
| Configuration backup, restore and reset | Download configuration backup | 1: configuration backup download |
| Configuration backup, restore and reset | Restore uploaded configuration file | 3: operation / apply behavior untested |
| Configuration backup, restore and reset | Erase configuration/factory reset confirmation | 3: operation / apply behavior untested |
| Administrator password and recovery | Change administrator password | 3: operation / apply behavior untested |
| Administrator password and recovery | Password recovery and two security questions | 3: operation / apply behavior untested |
| Local HTTPS and remote management | Always use HTTPS for local management | 3: operation / apply behavior untested |
| Local HTTPS and remote management | Classic WAN web remote management, source IP allowlist and port | 3: operation / apply behavior untested |
| Local HTTPS and remote management | Orbi app remote-access status/opt-in template | 3: operation / apply behavior untested |
| Firmware management | Check router and satellite firmware versions/updates | 3: operation / apply behavior untested |
| Firmware management | Manual firmware file upload | 3: operation / apply behavior untested |
| Firmware management | Router and satellite update orchestration | 3: operation / apply behavior untested |
| Firmware management | Automatic firmware update setting template | 3: operation / apply behavior untested |
| NETGEAR Armor | Armor dashboard state | 3: operation / apply behavior untested |
| NETGEAR Armor | Network threat blocking and malicious-web protection | 3: operation / apply behavior untested |
| NETGEAR Armor | Device/network vulnerability scans | 3: operation / apply behavior untested |
| NETGEAR Armor | Companion-device protection and Armor VPN (plan dependent) | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | SPC supported product, app management (no exact native SPC HTML page established) | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | Legacy Circle/OpenDNS switching form | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | Pause Internet across a child's devices | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | Child profiles and assigned devices | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | Internet/app usage and website history | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | Age-based content filtering | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | Daily time limits and bedtimes | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | Internet breaks and extra-time rewards | 3: operation / apply behavior untested |
| Smart Parental Controls and legacy parental templates | My Time companion mobile-device management | 3: operation / apply behavior untested |
| NETGEAR Router Protection | Router Protection support in model release lineage | 3: operation / apply behavior untested |
| Diagnostics/debug artifact | Diagnostic recording and debug-file download controls | 3: operation / apply behavior untested |
| Diagnostics/debug artifact | LAN/WAN packet capture and roaming debug template | 3: operation / apply behavior untested |
| Diagnostics/debug artifact | Telnet/RSTP/beta controls in debug template | 3: operation / apply behavior untested |
| Other shared UI artifacts | ReadySHARE/USB storage placeholder | 3: operation / apply behavior untested |
| Other shared UI artifacts | USB advanced tab placeholder | 3: operation / apply behavior untested |
| Other shared UI artifacts | DLNA control artifact | 3: operation / apply behavior untested |
| Other shared UI artifacts | Wireless WDS template | 3: operation / apply behavior untested |
| Other shared UI artifacts | Legacy wireless-only MAC ACL template | 3: operation / apply behavior untested |

Source detail: [UI inventory with template locations and conditional controls](../../firmware-rbr850-7.2.8.8/evidence/ui-feature-inventory.json)
and [live page/control evidence by family](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/ui-family-validation-table.md).
Hidden daisy-chain/beamforming/MU-MIMO/fast-roaming and legacy QoS markup is not
a validated current UI toggle. The current WAN web-admin editor is absent;
app Anywhere Access is a separate untested capability. The VPN UI describes
remote access into home, not a verified provider-VPN client.

## Interface diagnostics, separate from feature categories

These are verified observations about particular interfaces, not additional
hardware limitations or declarations that a feature cannot be controlled over
SSH. A rejected SOAP action can have a working native/vendor alternative; an
alternative write procedure still needs its own validation.

| Requested interface/feature | Validated limitation | Alternative or boundary |
| --- | --- | --- |
| SOAP `GetDNSLookUpStatus` | Authenticated response code 404. | WAN DNS configuration itself is readable. No active DNS diagnostic was run. |
| SOAP `GetBandwidthControlOptions` | Authenticated response code 404. | QoS enabled-state getter works. Policy editing remains untested. |
| SOAP `IsSmartConnectEnabled` | Authenticated response code 404. | Not evidence that shared-SSID behavior is absent. |
| SOAP `Get5G1ChannelInfo` | Authenticated response code 404. | `iw` provides the second 5 GHz radio's operating channel. |
| SOAP `GetAvailableChannel` with `5G1` | Authenticated response code 404. | `2.4G` and `5G` arguments work. |
| SOAP `Get5G1GuestAccessEnabled` | Authenticated response code 404. | The alternate action named `Get5GGuestAccessEnabled` successfully reads primary 5 GHz guest state. |
| SOAP `Get5GGuestAccessEnabled2` | Authenticated response code 404. | No second-5-GHz guest capability established by that endpoint. |
| SOAP `GetDeviceListAll` | HTTP 500, followed by service errors and loss of the session. | Exclude it from an MCP allowlist. Both attached-device getters work. Do not automatically retry this failure. |
| SOAP hardware capacity | `GetSystemInfo` reports physical-memory value 256, inconsistent with native `MemTotal=894960 kB` under the expected units. | Treat the SOAP hardware field as unsuitable for authoritative capacity reporting; native memory/procd sources agree. CPU percentage was not independently calibrated. |
| SOAP timezone | `GetTimeZoneInfo` returns a namespace URI as `NewTimeZone`. | It is not a usable timezone value. The NTP settings page exists, but a correct timezone read adapter still needs validation. |
| SOAP Internet-port information | `GetInternetPortInfo` returns a WAN-config-shaped payload, without the expected port-information field. | Read physical port telemetry with ethtool. |
| Vendor wireless/satellite RPC reads | `orbi_wlparam.get_channel` timed out; subsequent vendor object queries reported Not found. Objects appeared again later. | Exclude these paths until debugged. Native interface reads and SOAP satellite inventory work. |
| IPv4 management from this client during audit | Connections to router IPv4 management were refused. A controlled refusal coincided with Bitdefender/Armor TCP REJECT counters increasing. | IPv6 LAN management with the same pinned SSH/TLS identities worked. Trigger/expiry of the runtime block is unknown; no access rules were changed. |
| Classic WAN web-admin editor | Current `FW_remote.htm` exposes local HTTPS management; traditional WAN-management values are hidden fields, not an editable editor. | Orbi app Anywhere Access is a separate feature and was not tested. |
| Stock `wg`, `docker`, `python3`, `node`, `systemctl` commands | Each direct version invocation returned command-not-found, exit 127, on the router host. | This is five scoped host-CLI limitations, not proof that installation/custom implementations are impossible. LXC already runs containers. MCP can run on the Mac. |

The historical matrix stores **20 scoped observations** under
`confirmed_limitations`: the **one hardware boundary** in section 2 and
**19 interface/tool observations** summarized here (seven SOAP 404 actions,
seven other API/UI/access-path issues, and five missing commands). That legacy
field name does not classify 20 router features as impossible.

### Stability observations

The HTTP daemon PID changed from 7867 to 21272 during the getter/error sequence;
the TLS proxy and Dropbear PIDs stayed stable. The router uptime continued
increasing, so this was not a full reboot. A request named "Get" is not thereby
proven safe or reliable. Subsequent requests from the failed session are not
classified as independent unsupported features; a fresh session was used for
the successful second pass, with no retry of `GetDeviceListAll`.

The vendor RPC timeout/object disappearance was also recorded rather than
repaired. No service restart command was issued. A later read-only object list
showed the objects present again. Later Basic-auth UI snapshot attempts returned
401; those attempts did not supply validated configuration values and are not
counted as successful reads. The original 39 authenticated page observations
remain separately timestamped.

These are material limits for an unattended MCP implementation even though all
36 tracked configuration hashes stayed unchanged.

## Configuration-preservation evidence

During the live audit, no setters, Apply actions, configuration sessions,
reboot, service restart, key enrollment, startup changes or package installs
were sent. Before/after hashes matched for **36 tracked configuration
files/stores**: 29 files under `/etc/config`, five selected system/SSH files,
DHCP configuration and `/tmp/nvram`. This covers those tracked files, not all
router state: authentication, logs, counters and caches can change. The
separate `fnvram` shared-memory/committed-flash state was not independently
fingerprinted. Runtime instability is recorded in the interface notes above.

Evidence: [configuration comparison](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/configuration-hash-comparison.json).

## What this enables for the MCP

A first read-only tool set can cover device/satellite inventory, WAN/LAN and
Wi-Fi observations, native system health, route/firewall/connection inspection,
service/container inventory and configuration backup download. Keep explicit
allowlists and bounded requests, avoid the failed interfaces above, and prefer
native resource metrics over shared-template SOAP values.

Provisioning/enrollment and any future boot changes stay separate from ordinary
tool calls. A connection failure must not automatically trigger key enrollment,
security changes or a reboot. Do not change the installed configuration simply
to make validation pass.

## Evidence and reproduction

- [Full capability matrix](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/capability-matrix.json)
- [UI family validation table](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/ui-family-validation-table.md)
- [Authenticated page observations](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/http-ui-pages.json)
- [SOAP first pass](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-getter-results.json), [fresh-session second pass](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/soap-phase2-results.json)
- [Backup download metadata](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/backup-download.json)
- [Configuration hash comparison](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/configuration-hash-comparison.json)
- [IPv4 rejection observation](../../firmware-rbr850-7.2.8.8/evidence/capability-audit-2026-10-28/ipv4-rejection-counter-validation.json)
- [Official-source provenance](../../firmware-rbr850-7.2.8.8/evidence/official-ui-sources.json)
- [Offline SSH candidates](../../firmware-rbr850-7.2.8.8/evidence/ssh-capability-candidates.json), explicitly not all runtime-proven

Raw observations contain private device names, IPs and MACs. The audit directory
and live observation files are owner-only; do not publish them as sample data.
Credential values and the sensitive backup payload were not intentionally
retained. `build_matrix.py` in the audit directory regenerates the matrix/table
from saved observations without contacting the router. Re-running the raw live
probe sequences blindly is not recommended because of the observed failures.

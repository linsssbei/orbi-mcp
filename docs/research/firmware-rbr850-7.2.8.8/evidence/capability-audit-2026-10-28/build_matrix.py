"""Join saved read-only observations; never contacts the router."""
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
RESEARCH = OUT.parent.parent


def load(name):
    return json.loads((OUT / name).read_text())


def proof(name):
    p = OUT / name
    assert p.exists(), p
    return str(p.relative_to(RESEARCH))


def item(identifier, description, evidence, **details):
    return dict(id=identifier, description=description,
                evidence=[proof(x) for x in evidence], **details)


ui = load('http-ui-pages.json')['pages']
static = json.loads((RESEARCH / 'evidence/ui-feature-inventory.json').read_text())
families = []
for family in static['families']:
    live = [page for page in family['pages'] if ui.get(page, {}).get('http_status') == 200]
    features = []
    for index, feature in enumerate(family['features'], 1):
        pages = [p for p in feature['ui_pages'] if ui.get(p, {}).get('http_status') == 200]
        selectors = set()
        for evidence in feature['source_evidence']:
            selectors.update(re.findall(r'''\b(?:name|id)\s*=\s*["']([^"']+)''', evidence['text']))
        matched = []
        for page in pages:
            for control in ui[page]['controls']:
                if control.get('name') in selectors or control.get('id') in selectors:
                    matched.append({'page': page, 'name': control.get('name'),
                                    'id': control.get('id'), 'type': control.get('type')})
        features.append(dict(
            id=f'{family["id"]}/{index}', feature=feature['feature'],
            static_ui_status=feature['static_ui_status'],
            source_evidence=[{'file': x['file'], 'line': x['line']} for x in feature['source_evidence']],
            official_manual_pages=feature.get('official_manual_pages', []),
            live_http200_pages=pages, matching_live_html_controls=matched,
            ui_validation=('control_markup_observed' if matched else
                           'page_only_observed' if pages else 'not_live_tested'),
            javascript_visibility_evaluated=False,
            write_validation='not_attempted; configuration changes prohibited',
            ui_control_action_executed=False,
            notes=feature.get('notes', ''),
        ))
    families.append(dict(id=family['id'], label=family['label'],
                         menu=family['documented_menu_path'],
                         pages=family['pages'], live_http200_pages=live,
                         notes=family['notes'], features=features))

# Normalize wrapper aliases and prefer later, fresh-session observations.
soap = {}
for filename in ['soap-getter-results.json', 'soap-phase2-results.json']:
    for name, row in load(filename)['actions'].items():
        key = row.get('action', name)
        if name.startswith('getAvailableChannel('):
            key += '/' + name.partition('(')[2].rstrip(')')
        soap[key] = dict(row, observation_name=name, evidence=proof(filename))

reads = [
    item('identity', 'Read model, firmware and hardware identity.', ['soap-getter-results.json', 'system_board_ipv6.json']),
    item('devices', 'List attached clients, IP/MAC, connection type and access state.', ['soap-phase2-results.json'], attached_devices=18),
    item('satellites', 'Read satellite inventory, firmware, parent and backhaul metadata.', ['soap-phase2-results.json'], satellites=1, observed_satellite_model='RBS850', observed_satellite_firmware='V7.2.8.2'),
    item('dhcp', 'Read current DHCP leases and LAN/DHCP settings.', ['dhcp_leases_ipv6.json', 'soap-getter-results.json']),
    item('wan', 'Read WAN connection type, addresses, DNS and configured MTU.', ['soap-getter-results.json', 'wan_state_ipv6.json']),
    item('ethernet', 'Read physical WAN link speed, duplex and negotiation state.', ['ethernet_phy_ipv6.json'], observed_speed='2500Mb/s', observed_duplex='Full'),
    item('wifi_radios', 'Read active radio interfaces, channel/frequency, width and transmit power.', ['wireless_interfaces.json', 'driver_capabilities_ipv6.json']),
    item('wifi_configuration', 'Read configured primary channels and allowed 2.4/5 GHz channels.', ['soap-phase2-results.json'], note='Second 5 GHz SOAP getter is unsupported; its operating channel is readable through iw.'),
    item('guest_state', 'Read 2.4 GHz and primary 5 GHz guest enable state.', ['soap-phase2-results.json'], observed_enabled=False),
    item('access_control_state', 'Read access-control enable state and attached-device allow/block labels.', ['soap-phase2-results.json', 'http-ui-pages.json'], observed_enabled=False, note='Setting allow/block rules was not tested.'),
    item('traffic_meter', 'Read traffic-meter enable state, options and returned stored counters.', ['soap-phase2-results.json'], observed_enabled=False, note='Disabled meter returns zero counters; traffic collection accuracy not validated.'),
    item('qos_state', 'Read the QoS enabled flag.', ['soap-phase2-results.json'], observed_enabled=False, note='QoS rule configuration was not tested.'),
    item('port_mapping', 'Read the port-mapping table.', ['soap-getter-results.json'], observed_entries=0),
    item('backup_download', 'Download the current configuration backup.', ['backup-download.json'], bytes_received=131096, backup_payload_saved=False, restore_tested=False),
    item('logs', 'Read system/kernel logs and SOAP log details.', ['logs_readable_ipv6.json', 'kernel_logs_readable_ipv6.json', 'soap-phase2-results.json']),
    item('uptime', 'Read uptime and load/memory metrics through kernel/procd sources.', ['uptime.json', 'system_metrics_ipv6.json']),
    item('hardware_resources', 'Read CPU identity/counters and native memory information.', ['cpu.json', 'memory.json', 'cpu_counters_sample1_ipv6.json']),
    item('storage', 'Read filesystem capacity, mounts, MTD layout and persistent-overlay location.', ['filesystems.json', 'mounts.json', 'mtd_partitions_ipv6.json']),
    item('routes', 'Read IPv4/IPv6 routes and policy-routing rules.', ['routes_ipv4.json', 'routes_ipv6.json', 'routing_rules_final_ipv6.json']),
    item('network_topology', 'Read interfaces, neighbors and bridge membership.', ['interfaces.json', 'neighbors.json', 'bridge.json']),
    item('firewall', 'Read current IPv4/IPv6 firewall rules and counters.', ['firewall_rules.json', 'firewall_ipv6_rules.json', 'ipv4-rejection-counter-validation.json']),
    item('conntrack', 'Read connection-tracking counts and per-CPU statistics.', ['connection_count.json', 'conntrack_stats_ipv6.json']),
    item('services', 'Read listening sockets and process identities associated with them.', ['listeners.json', 'current_listeners_after_soap_ipv6.json']),
    item('lxc_inventory', 'List running LXC containers and inspect container state.', ['container_inventory_ipv6.json', 'container_state_ipv6.json', 'lxc_version_ipv6.json'], running_containers=['armor-bd', 'spc-circle'], note='Launching or modifying containers not tested.'),
    item('temperature_raw', 'Read thermal-sensor raw values.', ['kernel_temperature_ipv6.json'], note='Sensor-specific units/scaling not normalized; no Celsius interpretation claimed.'),
    item('software_inventory', 'Read installed packages, kernel modules and tool availability.', ['packages.json', 'kernel_modules.json', 'command_inventory.json']),
    item('capture_inventory', 'Enumerate packet-capture interfaces; identify tcpdump/libpcap versions.', ['capture_interfaces_ipv6.json'], note='Version output recorded in ssh-batch-stderr.txt. No live capture performed.'),
    item('read_config_value', 'Read a selected nonsecret configuration value with fnvram get.', ['config_getter_lan_ipv6.json', 'current_routing_mode_ipv6.json'], note='No set/commit/dump command used.'),
]

limitations = []
for key, row in soap.items():
    if row.get('response_code') == '404':
        limitations.append(dict(id='soap_' + row['observation_name'],
                                description='Action returned SOAP 404 in an authenticated session.',
                                action=row['action'], scope='This SOAP action/parameter only; not the whole feature.',
                                evidence=[row['evidence']]))
limitations += [
    item('no_6ghz_radio', 'No 6 GHz operating channels are exposed by any of the three live radios.', ['driver_capabilities_ipv6.json', 'wireless_interfaces.json'], scope='Installed RBR850 radio/driver capabilities; not a general Wi-Fi limitation.'),
    item('device_list_all_failure', 'GetDeviceListAll is not a usable validated reader here: HTTP 500, followed by service errors and lost authentication.', ['soap-getter-results.json', 'listeners.json', 'current_listeners_after_soap_ipv6.json'], scope='Do not use this endpoint in an MCP allowlist. GetAttachDevice/GetAttachDevice2 work.'),
    item('system_info_unreliable', 'GetSystemInfo returns physical-memory value 256, inconsistent with the native 894960 KiB memory view under the expected units.', ['soap-getter-results.json', 'memory.json'], scope='Do not use this SOAP field as authoritative hardware capacity.'),
    item('timezone_invalid', 'GetTimeZoneInfo returns a namespace URI as NewTimeZone, not a usable timezone value.', ['soap-getter-results.json'], scope='This SOAP response field; UI NTP/time settings page exists.'),
    item('internet_port_payload', 'GetInternetPortInfo returns a WAN-config-shaped payload, without the expected internet-port information field.', ['soap-getter-results.json'], scope='This SOAP action; ethtool provides working physical-port telemetry.'),
    item('wireless_rpc_unreliable', 'Vendor wireless RPC timed out; subsequent wireless/satellite object calls returned Not found. Objects appeared again later.', ['radio_channel_24_ipv6.json', 'radio_channel_5_ipv6.json', 'satellites_ipv6.json', 'final-state-and-hashes.json'], scope='These vendor RPC read paths are excluded until debugged; iw and SOAP alternatives exist.'),
    item('ipv4_management_block', 'This client could not connect to router IPv4 management ports during the audit; a controlled refusal correlated with Bitdefender TCP REJECT counter increments.', ['access-interruption.json', 'ipv4-rejection-counter-validation.json'], scope='Observed source/path/runtime security state; IPv6 with the same pinned host key worked. Trigger/expiry unknown.'),
    item('classic_wan_web_editor', 'The current Web Services Management page renders local-HTTPS management; conventional WAN remote-management fields are hidden state fields.', ['http-ui-pages.json'], scope='This current web page, not Orbi app Anywhere Access or custom SSH networking.'),
]
for identifier, name, filename in [
    ('no_wg_cli','WireGuard wg','wireguard_cli_ipv6.json'),
    ('no_docker_cli','Docker','docker_cli_ipv6.json'),
    ('no_python_cli','Python 3','python_cli_ipv6.json'),
    ('no_node_cli','Node.js','node_cli_ipv6.json'),
    ('no_systemd_cli','systemd systemctl','systemd_cli_ipv6.json'),
]:
    assert load(filename)['exit_code'] == 127
    limitations.append(item(identifier, name + ' command is not installed/available in the current router host environment.', [filename], scope='Stock host CLI; does not prove custom installation or another implementation impossible. MCP itself can run on the Mac.'))

installed = [
    item('openvpn_engine', 'OpenVPN 2.4.7 executable and /dev/net/tun exist; UI service/configuration controls are served.', ['vpn_version.json', 'vpn_device.json', 'http-ui-pages.json'], status='installed_and_ui_observed; tunnel operation not tested'),
    item('nft_tool', 'nft list ruleset succeeds with an empty ruleset.', ['nft_rules_ipv6.json'], status='reader_verified_empty; active firewall is represented by iptables'),
]

matrix = dict(
    schema_version=1,
    target=dict(model='RBR850', firmware='V7.2.8.8_5.1.24', inspected_date='2026-10-28', mode='router, enable_ap_mode=0'),
    scope='Validation only. No setters, Apply actions, config sessions, reboot, service restart, install, key enrollment or startup change sent.',
    configuration_verification=load('configuration-hash-comparison.json'),
    definitions=dict(read_verified='A bounded getter returned relevant data on the live router.',
                     ui_observed='An authenticated GET served a page/form/control; write behavior and JavaScript visibility are not validated.',
                     unavailable_interface='A specific existing interface returned unsupported/error/command-not-found; alternatives may exist.',
                     untested='No operational claim; modifying tests were prohibited.'),
    ui_family_count=len(families), ui_feature_entry_count=sum(len(f['features']) for f in families),
    live_ui_pages_http200=sum(x.get('http_status') == 200 for x in ui.values()),
    read_capabilities=reads, confirmed_limitations=limitations,
    installed_but_operation_untested=installed,
    soap_observations=soap, ui_families=families,
    untested_operations=[
        'Create/edit/delete DHCP reservations; apply LAN/DHCP changes',
        'Enable/configure OpenVPN server; export profiles that may generate credentials; restore backup',
        'Third-party outbound OpenVPN client; policy VPN routing; site-to-site VPN',
        'Change Wi-Fi/IoT/guest settings, channels/security, per-band SSIDs or mesh behavior',
        'Set access control, site/service blocks, QoS policies, schedules, traffic limits',
        'Create/change routes, NAT/port forwarding/triggering, UPnP, VLAN/IPTV, IPv6 or WAN modes',
        'Custom isolated LAN VLANs or IoT isolation beyond existing bridge/firewall observations',
        'Restart/reboot/update/reset, install packages or launch new containers',
        'Install/test Dropbear autostart or modify keys/passwords',
        'Verify app/cloud/subscription entitlements, Router Protection or Anywhere Access',
        'Run speed tests, active Wi-Fi scans, cable tests or packet captures',
        'WireGuard kernel/tunnel support or installing WireGuard/Docker/alternative firmware',
    ],
    privacy='Raw observations contain device names/MACs/IPs. Audit directory/files are owner-only. No credential values or backup contents intentionally retained.',
)

(OUT / 'capability-matrix.json').write_text(json.dumps(matrix, indent=2)+'\n')
(OUT / 'capability-matrix.json').chmod(0o600)
rows = ['| UI family | Settings/catalog scope | Live GET evidence | Writes |',
        '| --- | --- | --- | --- |']
for f in families:
    labels='; '.join(x['feature'] for x in f['features'])
    pages=', '.join('`'+p+'`' for p in f['live_http200_pages']) or 'Not exercised; documentation/template evidence only'
    rows.append('| '+f['label']+' | '+labels+' | '+pages+' | Not tested |')
(OUT / 'ui-family-validation-table.md').write_text('\n'.join(rows)+'\n')
print('Matrix:', len(reads), 'validated read capabilities;', len(limitations), 'scoped limitations;', len(families), 'UI families;', matrix['ui_feature_entry_count'], 'catalog entries')
print('Tracked configuration unchanged:',matrix['configuration_verification']['all_tracked_files_unchanged'])

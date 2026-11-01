"""Build an offline, source-line-addressable UI inventory; never contacts a router."""
from pathlib import Path
import re, json, hashlib

BASE = Path(__file__).resolve().parents[1]
WWW = BASE / 'rootfs/www'
MANUAL = 'https://www.downloads.netgear.com/files/GDC/RBK852/RBK852_UM_EN.pdf'
AP = 'https://kb.netgear.com/000061277/Disabled-Features-on-the-Orbi-when-set-to-AP-Mode'

def lines(page):
    return (WWW / page).read_text(errors='replace').splitlines()

def evidence(page, pattern, limit=3):
    rx = re.compile(pattern, re.I)
    return [{'file':'rootfs/www/'+page, 'line':n, 'text':line.strip()[:600]} for n,line in enumerate(lines(page),1) if rx.search(line)][:limit]

def attrs(tag):
    tag = re.sub(r'<%.*?%>', 'SERVER_TOKEN', tag, flags=re.S)
    return {m.group(1).lower():next(x for x in m.groups()[1:] if x is not None) for m in re.finditer(r'([\w-]+)\s*=\s*(?:"([^"]*)"|\x27([^\x27]*)\x27|([^\s>]+))', tag)}

def page_catalog(page):
    ll = lines(page)
    forms, controls, conditions, routes, requests = [], [], [], [], []
    comment = False
    for n,line in enumerate(ll,1):
        # A lexical catalog: comments remain identified, server includes are not rendered.
        if '<!--' in line and '-->' not in line: comment = True
        clean = re.sub(r'<%.*?%>', 'SERVER_TOKEN', line)
        for match in re.finditer(r'<(?:form|input|select|button)\b[^>]*>',clean,re.I):
            tag = match.group(); a = attrs(tag)
            if tag.lower().startswith('<form'):
                forms.append({'line':n,'method':a.get('method','GET').upper(),'action':a.get('action'), 'commented':comment})
            elif a.get('name'):
                controls.append({'line':n,'element':re.match(r'<(\w+)',tag).group(1).lower(),'name':a['name'],'type':a.get('type'), 'disabled_literal':bool(re.search(r'\bdisabled\b',tag,re.I)), 'hidden_input':a.get('type','').lower()=='hidden','commented':comment})
        if re.search(r'display\s*[:=]\s*["\x27]?\s*none|\.hide\(|\.disabled\s*=|\bhidden[ >]',line,re.I):
            conditions.append({'line':n,'text':line.strip()[:300],'commented':comment})
        for m in re.finditer(r'(?:\.action\s*=|\baction\s*=)\s*["\x27]([^"\x27]+)',line,re.I):
            routes.append({'line':n,'route':m.group(1),'commented':comment})
        for m in re.finditer(r'\burl\s*:\s*["\x27]([^"\x27]+)',line,re.I):
            requests.append({'line':n,'route':m.group(1),'commented':comment})
        if '-->' in line: comment = False
    return {'file':'rootfs/www/'+page,'sha256':hashlib.sha256((WWW/page).read_bytes()).hexdigest(),'forms':forms,'controls':controls,'visibility_evidence':conditions,'action_routes':routes,'ajax_request_routes':requests,'server_token_count':sum(len(re.findall(r'<%\d+%>',x)) for x in ll)}

families=[]
def family(id, label, menu, pages, manual, ap=False, notes=''):
    item={'id':id,'label':label,'documented_menu_path':menu,'pages':pages.split(), 'official_manual_pages':manual,'official_sources':[{'url':MANUAL,'pages':manual}] if manual else [],'ap_mode': 'officially_disabled_or_grayed_out' if ap else 'not_asserted_by_this_inventory','notes':notes,'features':[]}
    if ap: item['official_sources'].append({'url':AP,'section':'disabled-features list'})
    families.append(item)
    return item

def feature(f,label,page,pattern,manual=None,status='present_in_template_rendering_unverified',notes='',extra=None):
    ev=evidence(page,pattern)
    assert ev, (label,page,pattern)
    if page not in catalogs: catalogs[page]=page_catalog(page)
    item={'feature':label,'ui_pages':[page],'form_routes':list(dict.fromkeys(x['action'] for x in catalogs[page]['forms'] if x['action'])),'static_ui_status':status,'runtime_status':'not_tested','source_evidence':ev,'official_manual_pages':manual if manual is not None else f['official_manual_pages'],'notes':notes}
    if extra: item['source_evidence'] += extra
    f['features'].append(item)

PAGES = '''start.htm start_repeater.htm adv-wifi.htm MNU_menu.htm DashBoard.htm ADVANCED_home.htm ADVANCED_home1.htm ADVANCED_home2.htm ADVANCED_home2_Etherwan.htm BAS_basic.htm BAS_basictop.htm BAS_basictop2.htm BAS_ether.htm BAS_pppoe.htm BAS_pptp.htm BAS_l2tp.htm BAS_orange_dhcp.htm BAS_orange_pppoe.htm BAS_basic_ipv6_jp.htm WLG_wireless2.htm WLG_wireless2_2.htm WLG_wireless_dual_band_r10.htm WLG_adv_qca.htm WLG_adv_qca_no6G.htm WLG_wifi_sche_set.htm WLG_acl.htm WLG_wds.htm WLG_opmode_main.htm WLG_opmode_router_dual_band.htm WLG_opmode_ap_dual_band.htm WLG_ap_dual_band.htm Orbi_backhaul.htm DEV_redirect.htm DEV_device.htm DEV_device2.htm DEV_device_edit.htm DEV_device_DIL_Enhance.htm DEV_device_DIL_Enhance_edit.htm DEV_led_sche_set.htm DEV_name.htm DEV_control.htm DEV_control_add.htm DEV_control_edit.htm BKS_keyword.htm BKS_service.htm BKS_service_add.htm FW_schedule.htm FW_email.htm FW_log.htm FW_forward3.htm FW_forward_service3.htm FW_pt.htm FW_pt_service.htm FW_remote.htm LAN_lan.htm LAN_reserv_add.htm LAN_reserv_edit.htm WAN_wan.htm DNS_ddns.htm STR_routes.htm STR_add.htm OPENVPN.htm openvpn_crt_update.htm UPNP_upnp.htm VLAN_IPTV.htm VLAN_IPTV_add.htm VLAN_IPTV_edit.htm VLAN_IPTV_edit_2.htm IPV6_basic.htm IPV6_basictop.htm IPV6_disable_axorbi.htm IPV6_auto_axorbi.htm IPV6_autoconfig_axorbi.htm IPV6_tunnel_axorbi.htm IPV6_6rd_axorbi.htm IPV6_passthrough_axorbi.htm IPV6_fixed_axorbi.htm IPV6_dhcp_axorbi.htm IPV6_pppoe_axorbi.htm IPV6_dslite_axorbi.htm IPV6_plus_axorbi.htm IPV6_orange_axorbi.htm traffic_meter.htm traffic_status.htm traffic_stattbl.htm NTP_settings.htm BAK_backup.htm BAK_cfm.htm PWD_password.htm UPG_upgrade.htm UPG_upgradeall.htm UPG_upgradebase.htm UPG_fw_check.htm QOS_down_streaming.htm QOS_main.htm QOS_service.htm QOS_video_streaming.htm Parental_controls.htm Orbi_RA_OptinOptout.htm Orbi_add_new_satellite.htm Orbi_setup_satellite.htm Orbi_sync_satellite_start.htm WPS.htm WPS_PIN.htm Add_WPS_Client.htm WPS_Add_Client_PBC.htm WPS_Add_Client_PIN.htm RST_status.htm RST_statistics.htm RST_wanstat.htm RST_st_dhcp.htm RST_st_poe.htm RST_st_fix.htm INT_statistics.htm Reboot_confirm.htm debug.htm currentsetting.htm Readyshare_Storage.htm USB_adv_tab.htm dlna.htm'''.split()
catalogs={page:page_catalog(page) for page in PAGES}

f=family('internet','Internet connection','BASIC > Internet; ADVANCED > Setup > Internet Setup','BAS_basic.htm BAS_basictop.htm BAS_basictop2.htm BAS_ether.htm BAS_pppoe.htm BAS_pptp.htm BAS_l2tp.htm BAS_orange_dhcp.htm BAS_orange_pppoe.htm',[23,24,25,26],True,'Protocol, regional ISP, and route selection are server-dependent. PPTP/L2TP here are ISP/WAN logins, not a general third-party VPN client.')
for label,page,pat in [('Automatic IPv4/DHCP or fixed IPv4','BAS_ether.htm','name="?WANAssign'),('Manual DNS server addresses','BAS_ether.htm','name="?DNSAssign'),('WAN MAC default/clone/custom','BAS_ether.htm','name="?MACAssign'),('Host/system name and domain','BAS_ether.htm','name="?(?:system_name|domain_name)'),('DHCP vendor class and client identifier options 60/61','BAS_ether.htm','name="?option6[01]'),('PPPoE username/password/service','BAS_pppoe.htm','name="?pppoe_(?:username|servicename)'),('PPPoE connection policy and idle timeout','BAS_pppoe.htm','name="?pppoe_(?:dod|idletime)'),('PPTP WAN ISP login','BAS_pptp.htm','name="?pptp_username'),('L2TP WAN ISP login','BAS_l2tp.htm','name="?l2tp_username'),('Orange regional ISP templates','BAS_orange_pppoe.htm','<form')]: feature(f,label,page,pat)
f=family('wan_aggregation','WAN preference and Internet aggregation','BASIC > Internet','BAS_basictop2.htm',[70,71],True,'Manual explicitly covers RBR850 Internet port + Ethernet port 1 aggregation. This is WAN aggregation, not proof of LAN LACP or dual-WAN failover.')
feature(f,'Internet-only versus aggregated WAN preference','BAS_basictop2.htm','name="WANAggr"')
f=family('main_wifi','Main WiFi','BASIC > Wireless; ADVANCED > Setup > Wireless Setup','WLG_wireless2.htm',[53,54,55,56],False,'One main SSID security setting, shared 2.4/5 GHz front-haul. Shared templates also contain 6 GHz and other-model fields; their existence does not give RBR850 a 6 GHz radio.')
for label,pat in [('Main SSID','name="ssid"'),('2.4 GHz front-haul channel','name="w_channel"'),('5 GHz front-haul channel','name="h_channel"'),('802.11ax enable independently for 2.4/5 GHz','name="enable_[25]g_axmode"'),('WPA2-Personal security and passphrase','id="security_wpa2"|name="wpa2_passphrase"'),('Mixed WPA/WPA2 security option in template','id="security_auto"'),('WPA2/WPA3 transition and WPA3-Personal radio controls in template','id="security_wpa3')]: feature(f,label,'WLG_wireless2.htm',pat,notes='Security render branches and model logic must be respected; no runtime negotiation was tested.')
feature(f,'Open WiFi choice in RBR850-specific branch','WLG_wireless2.htm','id="security_disable"',status='model_branch_present_rendering_unverified',notes='setSecurity explicitly displays open_radio_2G for RBR850/RBR840/RBR750. This is a source finding, not a recommendation or current setting.',extra=evidence('WLG_wireless2.htm','open_radio_2G.*block',1))
feature(f,'Legacy WEP and WPA-PSK choices carried in shared template','WLG_wireless2.htm','id="security_(?:wep|wpapsk)"',status='hidden_or_rejected_legacy_choices',notes='setSecurity hides WEP/WPA-PSK rows and change validation rejects these choices. Do not infer their stock UI availability from raw input markup.',extra=evidence('WLG_wireless2.htm','wep_radio_2G.*none|wpa_radio_2G.*none',2))
feature(f,'6 GHz fields from shared template','WLG_wireless2.htm','name="enable_6g"|name="ssid_6g"',manual=[],status='shared_template_other_model_not_rbr850_capability',notes='RBR850 is dual-band client WiFi plus dedicated 5 GHz backhaul; 6 GHz controls are shared-template residue, gated by server tokens.')
f=family('iot_wifi','IoT WiFi','BASIC > Wireless > Wireless IoT Settings','WLG_wireless2.htm',[57,58,59,60],False,'Official 7.2.6.21 release notes explicitly add IoT network. IoT SSID presence is not proof of a separately firewalled LAN/VLAN.')
f['official_sources'].append({'url':'https://kb.netgear.com/000065816/RBR850-RBS850-Firmware-Version-7-2-6-21','section':'New Features'})
for label,pat in [('Enable IoT network','name="enable_iot"'),('IoT 2.4+5 GHz, 2.4 GHz-only, 5 GHz-only band selection','name="enable_iot_radio"'),('IoT SSID','name="ssid_iot"'),('IoT WPA2 or mixed WPA/WPA2 security and passphrase','name="security_type_iot"|name="wpa2_passphrase_iot"')]: feature(f,label,'WLG_wireless2.htm',pat,notes='IoT blocks wrapped in server tokens <%1971%>/<%1972%>; rendering not observed.')
f=family('guest_wifi','Guest WiFi','BASIC > Guest Network','WLG_wireless2_2.htm',[60,61],False,'Guest route appears via server token <%821%> in menu/dashboard; exact template route is a candidate supported by its explicit wireless_guest.cgi form.')
for label,pat in [('Enable guest network','name="enable_bssid"'),('Guest SSID','name="ssid"'),('Guest SSID broadcast','name="enable_broadcast"'),('Allow guests to see each other and access local network','name="allow_access"'),('Guest security options including WPA2/WPA3 template branches','name="security_type"'),('Guest passphrase','name="(?:wpa2_passphrase|passphrase)"')]: feature(f,label,'WLG_wireless2_2.htm',pat)
f=family('advanced_wifi','Advanced WiFi settings','ADVANCED > Advanced Setup > Wireless Settings','WLG_adv_qca.htm WLG_adv_qca_no6G.htm WLG_wifi_sche_set.htm',[62,63,64,86],False,'Advanced wireless menu target is server token <%769%>; do not assume every field in either variant is rendered for the exact board/region.')
for label,pat in [('Region selection (region/firmware dependent)','name="WRegion"'),('Enable 2.4 GHz radio template control','name="enable_radio_2g"'),('20/40 MHz coexistence','name="enable_coexist_2g"'),('RTS threshold','NAME="set_rts_'),('Preamble mode per band','name="set_preamble_[25]g"'),('Transmit power control per band','name="set_tpc_[25]g"'),('WiFi on/off schedule templates','name="wifi_off_[25]g"'),('Generate new backhaul password','name="gen_backhaul_pwd"')]: feature(f,label,'WLG_adv_qca.htm',pat)
for label,pat in [('SSID broadcast control hidden in main advanced variant','name="enable_bc_[25]g"'),('Daisy chain topology toggle','name="daisy_chain"'),('Implicit beamforming toggle','name="enable_bf"'),('MU-MIMO toggle','name="enable_mimo"'),('Fast roaming toggle','name="enable_fast_roaming"')]: feature(f,label,'WLG_adv_qca.htm',pat,manual=[],status='explicitly_hidden_in_template',notes='Containing rows use display:none; developer comments explicitly remove topology/beamforming/MU-MIMO/fast-roaming options. Hidden setting UI does not establish absent underlying wireless capability.',extra=evidence('WLG_adv_qca.htm','Following the Netgear',3))
feature(f,'WMM toggles in no6G shared variant','WLG_adv_qca_no6G.htm','name="wmm_enable_[25]g"',manual=[],status='shared_template_conditional_unverified')
f=family('wps','WPS onboarding','WPS wizard / Sync onboarding','WPS.htm WPS_PIN.htm Add_WPS_Client.htm WPS_Add_Client_PBC.htm WPS_Add_Client_PIN.htm',[17],False,'Physical WPS documented; software wizard templates exist, but menu exposure on exact model not established.')
feature(f,'Software WPS push-button wizard','WPS.htm','<form',status='template_present_menu_unverified')
feature(f,'Software WPS PIN wizard','WPS_PIN.htm','name="PIN"',status='template_present_menu_unverified')
f=family('attached_devices','Attached devices and satellite inventory','BASIC > Attached Devices; ADVANCED > Administration > Attached Devices','DEV_redirect.htm DEV_device.htm DEV_device2.htm DEV_device_edit.htm DEV_device_DIL_Enhance.htm DEV_device_DIL_Enhance_edit.htm',[101,103,104,105])
feature(f,'Attached devices display and refresh','DEV_device_DIL_Enhance.htm','<form|id="(?:ipColumn|macColumn|connTypeColumn|connOrbiColumn)"')
feature(f,'Device name/model/type editing','DEV_device_DIL_Enhance_edit.htm','name="(?:dev_model|dev_name|sel_dev_type_name)"')
feature(f,'Satellite connection inventory','DEV_device_DIL_Enhance.htm','<%1138%>|<%1139%>|<%1140%>|<%1141%>')
feature(f,'Satellite LED brightness/schedule/sync fields in shared editor','DEV_device_DIL_Enhance_edit.htm','name="(?:led_switch|lightbright|led_schedule|sync_switch)"',manual=[],status='shared_template_conditional_unverified',notes='Some device types include special LED capabilities; not a claim that RBS850 supports every editor field.')
f=family('mesh','Satellite onboarding and backhaul','BASIC > Add Orbi Satellite; ADVANCED > Advanced Setup > Wireless Settings','Orbi_add_new_satellite.htm Orbi_setup_satellite.htm Orbi_sync_satellite_start.htm Orbi_backhaul.htm',[14,15,86])
feature(f,'Add/sync satellite wizard','Orbi_add_new_satellite.htm','<form|[Ss]ync|satellite',notes='Wizard templates retained; no synchronization executed.')
feature(f,'Regenerate backhaul password confirmation','Orbi_backhaul.htm','<form|name="no_conn_ignore"')
f=family('access_control','Network access control','ADVANCED > Security > Access Control','DEV_control.htm DEV_control_add.htm DEV_control_edit.htm',[43,44,45],True,'Network allow/block lists govern network/Internet access; no live allow/block state inspected.')
for label,pat in [('Enable access control','name="enable_acl"'),('Default allow or block new devices','name="access_all"'),('Allow/block selected attached device','name="(?:allow|block)"'),('Known-device allowed/blocked lists','name="(?:add_white|add_black|delete_white|delete_black)"')]: feature(f,label,'DEV_control.htm',pat)
feature(f,'Add MAC/name to access-control list','DEV_control_add.htm','name="(?:mac_addr|dev_name)"')
f=family('site_service_blocking','Site and service blocking','ADVANCED > Security > Block Sites / Block Services / Schedule / E-mail','BKS_keyword.htm BKS_service.htm BKS_service_add.htm FW_schedule.htm FW_email.htm',[45,46,47,48,49,50],True)
for label,page,pat in [('Keyword/domain block list','BKS_keyword.htm','name="?cfKeyWord_Domain'),('Trusted computer exemption','BKS_keyword.htm','name="?trustipenble'),('Block-services schedules/modes','BKS_service.htm','name="?skeyword'),('Service TCP/UDP protocol and port ranges','BKS_service_add.htm','name="?(?:protocol|portstart|portend)'),('Block service by source computer or address range','BKS_service_add.htm','name="?iptype'),('Days and times schedule','FW_schedule.htm','name="?(?:checkboxNameMon|starthour|endhour)'),('SMTP server/port/authentication email alerts','FW_email.htm','name="?(?:email_smtp|smtp_port|smtp_auth)'),('Immediate and scheduled event email','FW_email.htm','name="?(?:block_site|cfAlert_Select)')]: feature(f,label,page,pat)
f=family('lan_dhcp','LAN and DHCP','ADVANCED > Setup > LAN Setup','LAN_lan.htm LAN_reserv_add.htm LAN_reserv_edit.htm DEV_name.htm',[76,77,78,79,80,81],True)
for label,pat in [('Router device name','name="?device_name'),('LAN IPv4 address and subnet mask','name="?sysLAN(?:IPAddr|SubnetMask)1'),('DHCP server enable','name="?dhcp_server'),('DHCP address pool start/end','name="?sysPool(?:Starting|Finish)Addr1'),('RIP direction/version shared-template controls','name="?(?:rip_direction|sysRIPVersion)')]: feature(f,label,'LAN_lan.htm',pat)
feature(f,'DHCP static address reservations (MAC/IP/name)','LAN_reserv_add.htm','name="?(?:rsv_mac|rsv_ip1|dv_name)"?')
f=family('wan','WAN security and MTU','ADVANCED > Setup > WAN Setup','WAN_wan.htm',[40,41,67,75],True)
for label,pat in [('SPI firewall disable control','name="disable_spi"'),('Default DMZ host','name="dmz_enable"'),('Respond to WAN ping','name="rspToPing"'),('IGMP proxy control','name="disable_gproxy"'),('MTU','name="wan_mtu"'),('NAT filtering secured/open','name="NatInboundFiltering"'),('SIP ALG disable control','name="disable_sip"')]: feature(f,label,'WAN_wan.htm',pat)
feature(f,'PPPoE/IPsec/PPTP/L2TP passthrough and IPTV fields in shared template','WAN_wan.htm','name="(?:pppoe_relay_enable|IPSecPassthrough|PPTPPassthrough|L2TPPassthrough)"',manual=[],status='shared_template_conditional_unverified')
f=family('ddns','Dynamic DNS','ADVANCED > Advanced Setup > Dynamic DNS','DNS_ddns.htm',[72,73,74],True)
for label,pat in [('Enable Dynamic DNS','name="sysDNSActive"'),('Provider and hostname/account credentials','name="(?:sysDNSProviderlist|sysDNSHost|sysDNSUser)"'),('NETGEAR mynetgear.com registration/account workflow','name="sysDNSHost_Netgear"|name="account"')]: feature(f,label,'DNS_ddns.htm',pat)
f=family('static_routes','IPv4 static routing','ADVANCED > Advanced Setup > Static Routes','STR_routes.htm STR_add.htm',[82,83,84])
for label,pat in [('Route name, private and active flags','name="?(?:route_name|SRoutePrivate|SRouteActive)'),('Destination/subnet/gateway/metric','name="?(?:SRouteDestAddr1|SRouteSubnetMask1|SRouteGatewayAddr1|route_metric)')]: feature(f,label,'STR_add.htm',pat)
f=family('operating_mode','Router / AP operating mode','ADVANCED > Advanced Setup > Router / AP Mode','WLG_opmode_main.htm WLG_ap_dual_band.htm WLG_opmode_ap_dual_band.htm WLG_opmode_router_dual_band.htm',[85,86],False,'AP mode changes feature availability; official disabled list linked in affected families.')
feature(f,'Router versus access-point operating mode','WLG_opmode_main.htm','name="operation_type"')
feature(f,'AP management IP automatic versus fixed','WLG_ap_dual_band.htm','name="enable_fixed_ip_setting"')
f=family('upnp','UPnP','ADVANCED > Advanced Setup > UPnP','UPNP_upnp.htm',[87,88],True)
for label,pat in [('UPnP enable','name="UPnP"'),('Advertisement period and TTL','name="(?:AdverTime|TimeToLive)"'),('UPnP port mapping table','<%188[6-9]%>|<%1891%>')]: feature(f,label,'UPNP_upnp.htm',pat)
f=family('vlan_iptv','VLAN/IPTV bridging','ADVANCED > Advanced Setup > VLAN / Bridge Settings','VLAN_IPTV.htm VLAN_IPTV_add.htm VLAN_IPTV_edit.htm',[88,89,90,91],True,'Port-group or VLAN-tag-group bridge to ISP. Not evidence of arbitrary LAN VLANs, independent L3 interfaces, inter-VLAN firewall policy, or managed-switch trunking.')
for label,pat in [('Enable VLAN/IPTV and bridge mode','name="vlan_iptv_(?:enable|select)"'),('Bridge port group membership','name="iptv_ports_'),('IPTV VLAN enable/id','name="iptv_vlan_id')]: feature(f,label,'VLAN_IPTV.htm',pat)
feature(f,'VLAN tag group name/id/priority/ports','VLAN_IPTV_add.htm','name="(?:vlan_name|vlan_id|vlan_prio|vlan_ports_)')
f=family('ipv6','IPv6 Internet','ADVANCED > Advanced Setup > IPv6','IPV6_basic.htm IPV6_basictop.htm IPV6_auto_axorbi.htm IPV6_autoconfig_axorbi.htm IPV6_tunnel_axorbi.htm IPV6_6rd_axorbi.htm IPV6_passthrough_axorbi.htm IPV6_fixed_axorbi.htm IPV6_dhcp_axorbi.htm IPV6_pppoe_axorbi.htm',[27,28,29,30,31,32,33,34,35,36,37,38,39],True,'Regional DS-Lite, IPv6 Plus and Orange templates also exist. Their presence is not unconditional applicability for every SKU/ISP.')
for label,page in [('Auto detect','IPV6_auto_axorbi.htm'),('Auto configuration','IPV6_autoconfig_axorbi.htm'),('6to4 tunnel','IPV6_tunnel_axorbi.htm'),('6rd tunnel','IPV6_6rd_axorbi.htm'),('IPv6 passthrough','IPV6_passthrough_axorbi.htm'),('Fixed IPv6','IPV6_fixed_axorbi.htm'),('DHCPv6 Internet','IPV6_dhcp_axorbi.htm'),('IPv6 PPPoE','IPV6_pppoe_axorbi.htm')]: feature(f,label,page,'<form')
for label,page in [('DS-Lite','IPV6_dslite_axorbi.htm'),('IPv6 Plus','IPV6_plus_axorbi.htm'),('Orange IPv6','IPV6_orange_axorbi.htm')]: feature(f,label,page,'<form',manual=[],status='regional_shared_template_conditional_unverified')
f=family('openvpn','OpenVPN remote access service','ADVANCED > Advanced Setup > VPN Service','OPENVPN.htm openvpn_crt_update.htm',[113,114,115,116,117,118,119,120,121],True,'Router operates as remote-access OpenVPN server for home network access; stock UI evidence does not establish arbitrary outbound commercial VPN client, WireGuard, or site-to-site service.')
f['official_sources'].append({'url':'https://kb.netgear.com/31489/How-do-I-use-VPN-on-my-Orbi-system-with-my-iOS-device','section':'VPN Service setup'})
for label,pat in [('Enable OpenVPN service','name="openvpnActive"'),('TUN/TAP UDP or TCP protocol and service ports','name="openvpn_(?:protocol|service_port)'),('VPN client Internet versus home-LAN access policy','name="openvpn_redirectGW"'),('Download client profiles for Windows/Mac/smartphone','name="(?:openvpn_download|openvpn_windows|openvpn_smart_phone)|[Ww]indows|[Ss]mart [Pp]hone')]: feature(f,label,'OPENVPN.htm',pat)
f=family('forwarding_triggering','Port forwarding and port triggering','ADVANCED > Advanced Setup > Port Forwarding / Port Triggering','FW_forward3.htm FW_forward_service3.htm FW_pt.htm FW_pt_service.htm',[124,125,126,127,128,129,130],True,'start.htm links FW_forward2.htm which is absent in extracted www; FW_forward3.htm and its forms are present. Runtime substitution to exact variant was not observed.')
feature(f,'Port forwarding predefined/custom services','FW_forward3.htm','<form|name="(?:svs_gm|serv_type)"')
feature(f,'Custom forwarding TCP/UDP/external/internal ports/LAN IP','FW_forward_service3.htm','name="(?:portname|srvtype|port_start|internal_port_start|server_ip1)"')
feature(f,'Port triggering enable/timeout/rule list','FW_pt.htm','name="(?:fwpt_enable|fwpt_timeout)"')
feature(f,'Triggering source/protocol/trigger/inbound port rules','FW_pt_service.htm','name="(?:src_ip_type|pt_type|pt_port|in_port_start|in_port_end)"')
f=family('traffic_meter','Internet traffic meter','ADVANCED > Advanced Setup > Traffic Meter','traffic_meter.htm traffic_status.htm traffic_stattbl.htm',[107,108],True)
for label,pat in [('Enable traffic meter','name="checkTraffic"'),('Volume or connection-time monthly limit','name="(?:tm_type|volume_monthly_limit|conntime_monthly_limit)"'),('Monthly counter reset schedule','name="(?:hour|day)"'),('Threshold warning and Internet block at limit','name="(?:waterMark|checkLed|checkBlock)"'),('Traffic statistics','traffic_stattbl|traffic_status')]: feature(f,label,'traffic_meter.htm',pat)
f=family('qos_speedtest','Speed test / QoS templates','ADVANCED > Setup > Speed Test or QoS menu label is server-rendered','QOS_down_streaming.htm QOS_main.htm',[106],True,'Manual documents bandwidth speed test; extensive manual/dynamic QoS markup is shared legacy code and hidden in the inspected current page. Do not advertise user-configurable QoS rules as validated.')
feature(f,'Built-in Internet bandwidth test','QOS_down_streaming.htm','speedtest_|speed_test',status='present_in_template_rendering_unverified')
feature(f,'Manual/dynamic QoS and device/service/LAN-port priority rule controls','QOS_down_streaming.htm','name="(?:qosEnable|qosTypeSelect|quick_qos_rule|fast_track_enable)"',manual=[],status='hidden_or_shared_template_not_validated_as_user_capability',extra=evidence('QOS_down_streaming.htm','upstream-table.*hidden|upstream-menu.*hidden|manual_upstream.*display.*none|dynamic_upstream.*display.*none',4))
f=family('logs_status','Status, logs and statistics','ADVANCED Home; ADVANCED > Administration > Logs','ADVANCED_home.htm ADVANCED_home1.htm ADVANCED_home2.htm RST_status.htm RST_statistics.htm RST_wanstat.htm FW_log.htm',[99,100,101,102])
feature(f,'Router Internet/WiFi/device status dashboard','ADVANCED_home.htm','ADVANCED_home[12]')
feature(f,'Internet interface statistics and connection status','RST_statistics.htm','<frame|[Ss]tatistics')
feature(f,'Refresh/clear/email logs','FW_log.htm','name="?(?:action_Refresh|action_Clear|action_Send)')
feature(f,'Event categories included in logs','FW_log.htm','name="?log_cat_')
feature(f,'Internet connection status release/renew/connect dialogs','RST_st_dhcp.htm','<form')
feature(f,'Router reboot confirmation','Reboot_confirm.htm','<form|name="yes"',manual=[99],notes='POST newgui_adv_home.cgi is an inventory entry only; never submitted.')
f=family('interface_setup','Setup and interface management','BASIC / ADVANCED; Setup Wizard; language menu','start.htm Orbi_config_wan.htm',[18,19,20,21],False,'Web UI and app setup are documented. Setup pages and language switching were not invoked.')
feature(f,'Web UI language selector','start.htm','name="choicelang"')
feature(f,'Automatic Internet setup versus manual setup or saved configuration','Orbi_config_wan.htm','name="WANConf"')
f=family('ntp','Time zone and NTP','ADVANCED > Administration > NTP Settings','NTP_settings.htm',[108,109])
feature(f,'Default versus preferred NTP server','NTP_settings.htm','name="(?:ntp_policy|ntp_primary_server)"')
feature(f,'Time zone and daylight-saving adjustment','NTP_settings.htm','name="(?:time_zone|adjust)"')
f=family('backup_reset','Configuration backup, restore and reset','ADVANCED > Administration > Backup Settings','BAK_backup.htm BAK_cfm.htm',[109,110,111],False,'Routes are inventory only; backup, restore, erase, reset were not executed.')
feature(f,'Download configuration backup','BAK_backup.htm','name="(?:backup|Backup)"|backup.cgi|[Bb]ackup')
feature(f,'Restore uploaded configuration file','BAK_backup.htm','type="?[Ff][Ii][Ll][Ee]|name="?upfile')
feature(f,'Erase configuration/factory reset confirmation','BAK_backup.htm','name="defaults"')
f=family('admin_password','Administrator password and recovery','ADVANCED > Administration > Set Password','PWD_password.htm',[96,97,98])
feature(f,'Change administrator password','PWD_password.htm','name="sysNewPasswd"')
feature(f,'Password recovery and two security questions','PWD_password.htm','name="(?:enable_recovery|answer1|answer2)"|question1')
f=family('management','Local HTTPS and remote management','ADVANCED > Advanced Setup > Web Services Management / Remote Management','FW_remote.htm Orbi_RA_OptinOptout.htm',[98,111],False,'Classic WAN web administration, app remote access, and local HTTPS are distinct. Exact current menu label and classic remote block rendering unresolved.')
feature(f,'Always use HTTPS for local management','FW_remote.htm','name="local_https_check"',manual=[98])
feature(f,'Classic WAN web remote management, source IP allowlist and port','FW_remote.htm','name="(?:remote_mg_enable|rm_access|http_rmport)"',manual=[],status='server_side_conditional_unresolved',notes='Entire block is wrapped in <%1441%> / <%1453%> and may be excluded for this firmware; not verified as exposed.',extra=evidence('FW_remote.htm','<%1441%>|<%1453%>',2))
feature(f,'Orbi app remote-access status/opt-in template','Orbi_RA_OptinOptout.htm','<%|[Rr]emote|[Rr][Aa]_',manual=[111],status='template_present_app_service_conditional')
f['features'][-1]['form_routes']=['ajax/gui_set_optInOut_option.cgi']
f['features'][-1]['source_evidence']=evidence('Orbi_RA_OptinOptout.htm','url:|RA_enable|type: "POST"',3)
f=family('firmware','Firmware management','ADVANCED > Administration > Firmware Update','UPG_upgrade.htm UPG_upgradeall.htm UPG_upgradebase.htm',[93,94,95],False,'No firmware check, download-to-router, upload, update, or reboot operation executed.')
for label,pat in [('Check router and satellite firmware versions/updates','upgrade_check.cgi|ver_check_upgrade.cgi'),('Manual firmware file upload','type="file"|name="upfile"'),('Router and satellite update orchestration','upgrade_allsat.cgi|satupdate'),('Automatic firmware update setting template','name="autoupdate"|upgrade_config.cgi')]: feature(f,label,'UPG_upgrade.htm',pat)
f=family('armor','NETGEAR Armor','Orbi app; BASIC dashboard status','DashBoard.htm',[43],True,'Subscription/account/region dependent. Dashboard Armor status is not evidence of enabled subscription or active protection on target.')
f['official_sources'].append({'url':'https://kb.netgear.com/000061281/Which-products-support-NETGEAR-Armor','section':'RBR850 in supported products'})
feature(f,'Armor dashboard state','DashBoard.htm','Armor_State|id="armor"',status='conditional_app_service',extra=evidence('DashBoard.htm','isEnableApMode == "1"|#armor.*display',3))
armor_url='https://kb.netgear.com/000066335/What-is-NETGEAR-Armor-Plus-and-how-is-it-different-from-Armor'
f['official_sources'].append({'url':armor_url,'section':'Armor / Armor Plus feature comparison; applies to RBR850'})
for label in ['Network threat blocking and malicious-web protection','Device/network vulnerability scans','Companion-device protection and Armor VPN (plan dependent)']:
    f['features'].append({'feature':label,'ui_pages':[],'form_routes':[],'static_ui_status':'official_app_service_documentation_only','runtime_status':'not_tested','source_evidence':[],'official_manual_pages':[],'official_sources':[{'url':armor_url,'section':'feature comparison'}],'notes':'Subscription/account/region/device dependent; companion VPN is not an outbound router VPN client.'})
f=family('parental','Smart Parental Controls and legacy parental templates','Orbi app; legacy BASIC/Security parental links','Parental_controls.htm DashBoard.htm',[],True,'RBR850 officially supports SPC, subject to country, registered SSO account, router registration and router mode. Legacy Circle/OpenDNS controls in www do not establish active support for those services.')
f['official_sources'] += [{'url':'https://kb.netgear.com/000064166/Which-products-support-NETGEAR-Smart-Parental-Controls','section':'RBR850 model support; country condition'},{'url':'https://kb.netgear.com/000062988/Why-can-t-I-see-the-NETGEAR-Smart-Parental-Controls-tile-in-the-Orbi-or-Nighthawk-app-after-upgrading-to-the-latest-firmware','section':'app tile conditions'}]
feature(f,'SPC supported product, app management (no exact native SPC HTML page established)','DashBoard.htm','id="parental"',status='app_documented_web_tile_hidden',notes='Parental dashboard tile has inline display:none; source does not establish exact SPC UI implementation.')
feature(f,'Legacy Circle/OpenDNS switching form','Parental_controls.htm','<form|name="(?:circleplc|standard_plc)"',status='legacy_shared_template_unverified')
spc_url='https://kb.netgear.com/000062103/What-are-the-features-of-NETGEAR-Smart-Parental-Controls-and-Smart-Parental-Controls-Premium'
f['official_sources'].append({'url':spc_url,'section':'free versus Premium comparison'})
for label,tier in [('Pause Internet across a child\'s devices','free'),('Child profiles and assigned devices','free'),('Internet/app usage and website history','Premium'),('Age-based content filtering','Premium'),('Daily time limits and bedtimes','Premium'),('Internet breaks and extra-time rewards','Premium'),('My Time companion mobile-device management','Premium')]:
    f['features'].append({'feature':label,'ui_pages':[],'form_routes':[],'static_ui_status':'official_app_service_documentation_only','runtime_status':'not_tested','subscription_tier':tier,'source_evidence':[],'official_manual_pages':[],'official_sources':[{'url':spc_url,'section':'feature comparison'},{'url':'https://kb.netgear.com/000064166/Which-products-support-NETGEAR-Smart-Parental-Controls','section':'RBR850 supported product'}],'notes':'App feature documentation plus RBR850 product-support list. Country, account, registration, mode and plan conditions apply; no account or subscription checked.'})
f=family('router_protection','NETGEAR Router Protection','Service support; no dedicated www HTML page identified','DashBoard.htm',[],False,'Official RBR850/RBS850 7.2.7.15 release note says Router Protection support added. Exact 7.2.8.8 www page/control was not identified; do not merge with Armor or claim target service is enabled.')
f['official_sources']=[{'url':'https://kb.netgear.com/000066592/RBR850-RBS850-Firmware-Version-7-2-7-15','section':'Enhancements'}]
f['features'].append({'feature':'Router Protection support in model release lineage','ui_pages':[],'form_routes':[],'static_ui_status':'official_release_note_only_no_dedicated_html_identified','runtime_status':'not_tested','source_evidence':[],'official_manual_pages':[],'notes':f['notes']})
f=family('diagnostics','Diagnostics/debug artifact','Direct debug.htm (not established as ordinary menu)','debug.htm currentsetting.htm',[],False,'Developer/diagnostic endpoints are present; no page or CGI was contacted, no capture/logging/telnet/debug setting was enabled, and runtime authorization/exposure was not tested.')
for label,pat in [('Diagnostic recording and debug-file download controls','name="(?:action_Start_Capture|Save_Debug_File)"'),('LAN/WAN packet capture and roaming debug template','name="(?:action_Enable_LANWAN_Packet_Capture|action_Enable_Roaming_Debug)"'),('Telnet/RSTP/beta controls in debug template','name="(?:action_telnet_enable|action_rstp_enable|action_beta_acceptance)"')]: feature(f,label,'debug.htm',pat,status='diagnostic_template_only_not_validated_or_invoked')
f=family('shared_residue','Other shared UI artifacts','No supported menu established for exact model','Readyshare_Storage.htm USB_adv_tab.htm dlna.htm WLG_wds.htm WLG_acl.htm',[],False,'Do not promote these firmware files to RBR850 runtime features. RBR850 hardware/manual does not establish USB storage/ReadySHARE, print serving, or arbitrary WDS repeater mode from their presence.')
for label,page in [('ReadySHARE/USB storage placeholder','Readyshare_Storage.htm'),('USB advanced tab placeholder','USB_adv_tab.htm'),('DLNA control artifact','dlna.htm'),('Wireless WDS template','WLG_wds.htm'),('Legacy wireless-only MAC ACL template','WLG_acl.htm')]: feature(f,label,page,'<form|<html|<HTML',status='shared_template_artifact_not_validated_as_model_capability')

menus=[]
for p in ['start.htm','start_repeater.htm','adv-wifi.htm','MNU_menu.htm']:
    for n,line in enumerate(lines(p),1):
        if re.search(r'<a\b.*href=',line,re.I) and (p=='MNU_menu.htm' or n>800):
            menus.append({'file':'rootfs/www/'+p,'line':n,'source':line.strip()[:650], 'note':'Raw template entry; server tokens, comments, CSS and model/mode conditions may hide, disable or rewrite it.'})

all_html=[]
for p in sorted(WWW.glob('*.htm')):
    if p.name not in catalogs:
        c=page_catalog(p.name)
        if c['forms']: all_html.append({'file':c['file'],'forms':c['forms'],'action_routes':c['action_routes'],'note':'Supplemental form catalog; not a claim that this setup/legacy/model-specific page is exposed.'})

data={'schema_version':1,'target':{'model':'RBR850','firmware':'V7.2.8.8_5.1.24','bundle_model':'RBK852'},'created_date':'2026-10-28','method':{'router_contact':False,'configuration_changes':False,'firmware_binaries_executed':False,'sources':['Offline extracted www templates from the exact supplied firmware','Official NETGEAR manual downloaded 2026-10-28','Official NETGEAR knowledge base and release notes read online'],'scope_note':'Source-evidenced capability/UI inventory. No endpoint execution, rendering with target state, reachability, daemon operation, successful feature behavior, current settings, licenses, account state or live availability was validated. A static form action is not proof that its CGI is registered or implemented.','conditional_tokens':'Numeric <%...%> server directives are unresolved. Markup includes multiple models, regions and obsolete features; UI visibility entries refer to source templates, never live target state.'},'official_reference':{'manual_url':MANUAL,'manual_local_file':'reference/RBK852_UM_EN_official_2026-10-28.pdf','manual_text_local_file':'reference/RBK852_UM_EN_official_2026-10-28.txt','manual_title':'Orbi Whole Home Tri-Band Mesh WiFi 6 System','manual_cover':'November 2022; 202-12600-02; includes RBR850/RBS850','manual_page_count':161,'page_number_note':'Manual printed page numbers; PDF page index is printed page minus 1.','firmware_release_url':'https://kb.netgear.com/000070916/','firmware_release_date':'2026-09-09'},'family_count':len(families),'feature_count':sum(len(f['features']) for f in families),'families':families,'page_catalog':catalogs,'raw_menu_entries':menus,'supplemental_forms':all_html,'not_established':{'absent_ui_not_absent_runtime':['No dedicated general outbound VPN-client or WireGuard UI identified','No general per-VLAN LAN routing/firewall or multiple independent LAN-subnet UI established','No dedicated Router Protection HTML settings page identified','No runtime capabilities inferred from USB/ReadySHARE/WDS/shared radio artifacts'],'explicit_hidden_controls':['Daisy chain topology','Beamforming toggle','MU-MIMO toggle','Fast roaming toggle','QoS manual/dynamic controls in current speed-test template'],'limitations':['No live per-board rendered menu captured by this inventory','Model/SKU/server token selection unresolved','App/cloud services require official model/account/region qualifications','No inference that IoT SSID is isolated from main LAN','No claim that 6 GHz template fields apply to RBR850']}}
out=BASE/'evidence/ui-feature-inventory.json'
out.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'output':str(out),'families':data['family_count'],'features':data['feature_count'],'page_catalog':len(catalogs),'supplemental_form_pages':len(all_html),'raw_menu_entries':len(menus),'bytes':out.stat().st_size}))

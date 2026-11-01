"""Disable the observed Orbi IoT SSID through its authenticated configuration form."""
import html.parser
import http.cookiejar
import json
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request

BASE = 'https://192.168.1.1'
PAGE = '/WLG_wireless2.htm'


class WirelessForm(html.parser.HTMLParser):
    def __init__(self, body):
        super().__init__()
        self.fields = {}
        self.inputs = {}
        self.action = None
        self.select = None
        self.option = None
        self.options = []
        self.feed(body)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            if self.action is not None:
                raise RuntimeError('Unexpected multiple forms; refusing to apply.')
            self.action = a['action']
        elif tag == 'input' and a.get('name'):
            name = a['name']
            self.inputs[name] = a
            kind = a.get('type', 'text').lower()
            if 'disabled' not in a and kind not in ('submit', 'button', 'reset'):
                if kind not in ('checkbox', 'radio') or 'checked' in a:
                    self.fields[name] = a.get('value', '')
        elif tag == 'select':
            self.select = a.get('name')
            self.options = []
        elif tag == 'option' and self.select:
            self.option = [a.get('value'), 'selected' in a, '']

    def handle_data(self, data):
        if self.option is not None:
            self.option[2] += data

    def handle_endtag(self, tag):
        if tag == 'option' and self.option is not None:
            self.options.append(self.option)
            self.option = None
        elif tag == 'select' and self.select:
            if self.options:
                selected = next((x for x in self.options if x[1]), self.options[0])
                self.fields[self.select] = selected[0] if selected[0] is not None else selected[2]
            self.select = None


def main():
    password = subprocess.run([
        '/usr/bin/security', 'find-generic-password', '-a', 'admin',
        '-s', 'local-orbi-tools:192.168.1.1', '-w',
    ], check=True, capture_output=True, text=True).stdout.removesuffix('\n')
    manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, BASE, 'admin', password)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl._create_unverified_context()),
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        urllib.request.HTTPBasicAuthHandler(manager),
    )

    def read():
        with opener.open(BASE + PAGE, timeout=8) as response:
            return WirelessForm(response.read().decode(errors='replace'))

    before = read()
    fields = dict(before.fields)
    if fields.get('ssid') != 'PangKunPewPew':
        raise RuntimeError('Main SSID does not match; refusing to apply.')
    if fields.get('ssid_iot') not in ('IOT', 'PangKunPewPew-IoT'):
        raise RuntimeError('IoT SSID does not match; refusing to apply.')
    print(json.dumps({
        'mainSSID': fields['ssid'], 'iotSSID': fields['ssid_iot'],
        'iotEnabled': fields.get('enable_iot_value') == '1',
        'iot24GHz': fields.get('enable_iot_2g_value'),
        'iot5GHz': fields.get('enable_iot_5g_value'),
    }), flush=True)
    if fields.get('enable_iot_value') == '0':
        print('IoT is already disabled.')
        return
    if fields.get('enable_iot_value') != '1':
        raise RuntimeError('Unexpected IoT state; refusing to apply.')
    if fields.get('security_type_2G') != 'WPA2-PSK' or fields.get('security_type_2G_IOT') != 'WPA2-PSK':
        raise RuntimeError('Wireless security changed; inspect the form before applying.')

    # Mirror initScrn/checkData on the live form while preserving its existing settings.
    fields['w_channel'] = fields['initChannel']
    fields['h_channel'] = fields['initHChannel']
    fields['security_type'] = fields['security_type_2G']
    fields['security_type_iot'] = fields['security_type_2G_IOT']
    for band, mode in [('2g', '11axg'), ('5g', '11axa')]:
        checkbox = f'enable_{band}_axmode'
        if fields[f'{checkbox}_value'] == mode:
            fields[checkbox] = '1'
        else:
            fields.pop(checkbox, None)
    for key in ('password_changed', 'password_changed_iot', 'password_changed_6g'):
        fields[key] = '0'
    fields['enable_iot_radio'] = '1'
    fields.pop('enable_iot', None)
    fields['enable_iot_value'] = 'disable'
    fields['Apply'] = 'Apply'

    target = urllib.parse.urljoin(BASE + PAGE, before.action)
    parts = urllib.parse.urlsplit(target)
    if parts.scheme != 'https' or parts.hostname != '192.168.1.1' or parts.path != '/wireless.cgi':
        raise RuntimeError('Unexpected form target; refusing to apply.')
    print('Prepared change: IoT enabled -> disabled; existing main SSID, security, password, channels and AX modes retained.', flush=True)
    if '--apply' not in sys.argv:
        print('Inspection only; no changes submitted.')
        return

    request = urllib.request.Request(target, data=urllib.parse.urlencode(fields).encode(), headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': BASE, 'Referer': BASE + PAGE,
    })
    try:
        with opener.open(request, timeout=12) as response:
            print(f'Apply response: HTTP {response.status}', flush=True)
    except (OSError, urllib.error.URLError) as error:
        print(f'Apply response interrupted ({type(error).__name__}); checking saved state without resubmitting.', flush=True)

    preserved = [
        'ssid', 'ssid_iot', 'security_type_2G', 'security_type_2G_IOT',
        'initChannel', 'initHChannel', 'WRegion',
        'enable_2g_axmode_value', 'enable_5g_axmode_value',
        'wpa2_passphrase', 'wpa2_passphrase_iot',
        'enable_iot_2g_value', 'enable_iot_5g_value',
    ]
    for attempt in range(12):
        try:
            after = read()
            if after.fields.get('enable_iot_value') == '0':
                changed = [key for key in preserved if before.fields.get(key) != after.fields.get(key)]
                if changed:
                    raise RuntimeError('Unexpected additional field changes: ' + ', '.join(changed))
                print(json.dumps({
                    'verified': True, 'iotEnabled': False,
                    'mainSSID': after.fields.get('ssid'),
                    'mainSettingsAndPasswordsUnchanged': True,
                }), flush=True)
                return
        except (OSError, urllib.error.URLError):
            pass
        if attempt < 11:
            time.sleep(3)
    raise RuntimeError('IoT disable was submitted but could not be verified; do not resubmit without checking.')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Orbi: {error}', file=sys.stderr)
        sys.exit(1)

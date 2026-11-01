"""Exercise original firmware Lua instructions with every OS operation mocked.

No sockets, subprocesses, real credentials, or router writes. Chunk conversion
changes host layout and numeric constant representation, not instructions.
"""
import hashlib
import json
from pathlib import Path

from lupa.lua51 import LuaRuntime
from inspect_lua51 import read, standard_chunk

BASE = Path(__file__).resolve().parent
PASSWORD = b'OfflineOnlyExample7'
PUBKEY = b'ssh-rsa AAAATEST offline-placeholder'


def probe(name, *, password=PASSWORD, username=b'admin', attempts=0,
          internal=True, debug=False, upper_digest=False, command_result=0,
          is_orbi=True, method=b'POST'):
    lua = LuaRuntime(encoding=None)
    table = lambda **d: lua.table_from({k.encode(): v for k, v in d.items()})
    output, commands, auth_commands, writes = [], [], [], []
    files = {b'/tmp/enable-ssh-attempt-counter': str(attempts).encode()} if attempts else {}
    digest = hashlib.sha256(PASSWORD).hexdigest().encode()
    if upper_digest:
        digest = digest.upper()
    payload = json.dumps({'username': username.decode(), 'password': password.decode(),
                          'pubkey': PUBKEY.decode()}).encode()
    cgi = {b'DOCUMENT_ROOT': b'/www-seal', b'REQUEST_METHOD': method,
           b'REQUEST_URI': b'/api/v1/enable_ssh', b'HTTP_CONTENT_LENGTH': str(len(payload)).encode()}
    if internal:
        cgi[b'HTTP_X_SEAL_INTERNAL'] = b'1'

    def execute(command):
        commands.append(command.decode())
        return command_result

    def write_file(path, value):
        files[path] = value
        writes.append({'path': path.decode(), 'value': value.decode()})

    def os_exec(command):
        assert command == b'/usr/bin/which seal 2>&1 >/dev/null'
        return 0 if is_orbi else 1

    def popen(command):
        auth_commands.append(command.decode())
        if command == b'seal plat get_admin_username':
            stdout = b'admin\n'
        elif command == b'seal plat get_admin_password_digest':
            stdout = digest + b'\n'
        elif command.startswith(b'echo -n ') and command.endswith(b" | sha256sum | cut -d ' ' -f0"):
            # BusyBox 1.30.1 treats field 0 as field 1. Only simple dummy
            # passwords are accepted by this mock; no shell is invoked.
            value = command[len(b'echo -n '):-len(b" | sha256sum | cut -d ' ' -f0")]
            assert value.isalnum()
            stdout = hashlib.sha256(value).hexdigest().encode() + b'\n'
        else:
            raise AssertionError(('Unexpected popen', command))
        return table(read=lambda *_: stdout, close=lambda *_: True)

    env = lua.table()
    for key in (b'assert', b'error', b'ipairs', b'pairs', b'next', b'pcall',
                b'tostring', b'tonumber', b'type', b'select', b'setmetatable',
                b'getmetatable', b'rawget', b'rawset', b'unpack', b'string',
                b'table', b'math'):
        env[key] = lua.globals()[key]
    env[b'os'] = table(execute=execute, getenv=lambda k: cgi.get(k))
    env[b'io'] = table(popen=popen, read=lambda n: payload[:int(n)])
    env[b'print'] = lambda *args: output.append('\t'.join(str(x, 'utf8') if isinstance(x, bytes) else str(x) for x in args))
    mods = {
        b'seal-io': table(file_exists=lambda p: p in files or (debug and p == b'/debugEnable'),
                          read_all_from_file=lambda p: files[p], write_to_file=write_file,
                          os_exec=os_exec,
                          os_exec_full=lambda cmd: table(stdout=b'y' if debug else b'')),
        b'dal': table(), b'seal-platform': table(), b'seal-services': table(),
        b'seal-log': table(LogLevel=table(Error=1), log=lambda *a: None),
    }
    loader = lua.eval(b'function(c,e) local f,x=loadstring(c);assert(f,x);setfenv(f,e);return f end')

    def require(modname):
        if modname not in mods:
            path = BASE / 'rootfs/usr/share/lua' / (modname.decode() + '.lua')
            mods[modname] = loader(standard_chunk(read(path)), env)()
        return mods[modname]

    env[b'require'] = require
    path = BASE / 'rootfs/www-seal/rest/rest.lua'
    loader(standard_chunk(read(path)), env)()
    return dict(name=name, output=output, commands=commands,
                auth_commands=auth_commands, writes=writes)


def main():
    cases = [
        (dict(name='valid-admin-through-normal-proxy'), 200, 4, 0),
        (dict(name='wrong-password', password=b'WrongOfflineExample'), 418, 0, 1),
        (dict(name='wrong-username', username=b'other'), 418, 0, 1),
        (dict(name='five-failed-attempts', attempts=5), 418, 0, 0),
        (dict(name='direct-root-without-debug-or-internal-header', internal=False), 200, 4, 0),
        (dict(name='debug-allows-direct-root', internal=False, debug=True), 200, 4, 0),
        (dict(name='uppercase-stored-digest-does-not-match-lowercase-output', upper_digest=True), 418, 0, 1),
        (dict(name='command-errors-still-return-success', command_result=256), 200, 4, 0),
        (dict(name='GET-does-not-enable'), 404, 0, 0),
        (dict(name='non-orbi-only-prints', is_orbi=False), 200, 0, 0),
    ]
    cases[8][0]['method'] = b'GET'
    results = []
    for params, status, command_count, write_count in cases:
        result = probe(**params)
        assert f'Status: {status}' in '\n'.join(result['output']), result
        assert len(result['commands']) == command_count, result
        assert len(result['writes']) == write_count, result
        if command_count:
            assert PUBKEY.decode() in result['commands'][1], result
        result['passed'] = True
        results.append(result)
    sources = ['usr/share/lua/seal-development.lua', 'www-seal/rest/rest.lua',
               'usr/share/lua/seal-environ.lua', 'usr/share/lua/utility.lua',
               'usr/share/lua/third_party/router.lua', 'usr/share/lua/third_party/rxi-json-lua.lua']
    manifest = {p: hashlib.sha256((BASE/'rootfs'/p).read_bytes()).hexdigest() for p in sources}
    report = {'mode': 'offline; original instructions; all OS operations mocked',
              'sources_sha256': manifest, 'cases': results}
    (BASE/'evidence/seal-offline-results.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'Passed {len(results)} offline SeAL REST cases')


if __name__ == '__main__':
    main()

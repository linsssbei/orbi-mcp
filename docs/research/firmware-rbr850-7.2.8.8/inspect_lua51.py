"""Parse OpenWrt Lua 5.1/LNUM chunks without executing them.

Also serialize standard Lua 5.1 bytecode for isolated tests in lupa.lua51.
The firmware's type 9 constants are signed 32-bit integers.
"""
import argparse
import json
import struct
from pathlib import Path

OPS = ('MOVE LOADK LOADBOOL LOADNIL GETUPVAL GETGLOBAL GETTABLE SETGLOBAL '
       'SETUPVAL SETTABLE NEWTABLE SELF ADD SUB MUL DIV MOD POW UNM NOT LEN '
       'CONCAT JMP EQ LT LE TEST TESTSET CALL TAILCALL RETURN FORLOOP FORPREP '
       'TFORLOOP SETLIST CLOSE CLOSURE VARARG').split()


class Reader:
    def __init__(self, data):
        self.data = data[data.index(b'\x1bLua'):]
        assert self.data[:12] == bytes.fromhex('1b4c75615100010404040804')
        self.pos = 12

    def get(self, n):
        v = self.data[self.pos:self.pos+n]
        assert len(v) == n
        self.pos += n
        return v

    def integer(self):
        return struct.unpack('<i', self.get(4))[0]

    def string(self):
        n = self.integer()
        return self.get(n)[:-1].decode('utf-8', errors='surrogateescape') if n else None

    def proto(self):
        p = dict(source=self.string(), line=self.integer(), endline=self.integer())
        p['nups'], p['params'], p['vararg'], p['stack'] = self.get(4)
        p['code'] = [struct.unpack('<I', self.get(4))[0] for _ in range(self.integer())]
        p['constants'] = []
        for _ in range(self.integer()):
            t = self.get(1)[0]
            if t == 0: v = None
            elif t == 1: v = bool(self.get(1)[0])
            elif t == 3: v = struct.unpack('<d', self.get(8))[0]
            elif t == 9: v = self.integer()
            elif t == 4: v = self.string()
            else: raise ValueError((t, self.pos))
            p['constants'].append(v)
        p['children'] = [self.proto() for _ in range(self.integer())]
        p['lines'] = [self.integer() for _ in range(self.integer())]
        p['locals'] = [(self.string(), self.integer(), self.integer()) for _ in range(self.integer())]
        p['upnames'] = [self.string() for _ in range(self.integer())]
        return p


def read(path):
    r = Reader(Path(path).read_bytes())
    p = r.proto()
    assert r.pos == len(r.data), (r.pos, len(r.data))
    return p


def listing(p, name='main'):
    rows = [f'{name}: lines {p["line"]}-{p["endline"]}, params={p["params"]}, upvalues={p["nups"]}']
    rows.extend(f' K{i}: {v!r}' for i, v in enumerate(p['constants']))
    for i, w in enumerate(p['code']):
        op, a, b, c = w & 63, (w >> 6) & 255, w >> 23, (w >> 14) & 511
        bx = w >> 14
        extra = ''
        if op in (1, 5, 7): extra = repr(p['constants'][bx])
        elif op in (22, 31, 32): extra = f'-> {i + 2 + bx - 131071}'
        elif op == 36: extra = f'{name}.{bx}'
        else:
            extra = ', '.join(f'{v}=K{v-256} {p["constants"][v-256]!r}' for v in (b, c) if v >= 256 and v-256 < len(p['constants']))
        rows.append(f' {i+1:03} {OPS[op]:10} {a:3} {b:3} {c:3} {extra}')
    for i, ch in enumerate(p['children']): rows.append(listing(ch, f'{name}.{i}'))
    return '\n'.join(rows)


def standard_chunk(p):
    """Transcode only chunk layout and integer constants, preserving instructions."""
    def integer(n): return struct.pack('<i', n)
    def string(s):
        b = s.encode('utf-8', errors='surrogateescape') + b'\0' if s is not None else b''
        return struct.pack('<Q', len(b)) + b
    def array(a, encode): return integer(len(a)) + b''.join(encode(v) for v in a)
    def constant(v):
        if v is None: return b'\0'
        if isinstance(v, bool): return b'\1' + bytes([int(v)])
        if isinstance(v, (float, int)): return b'\3' + struct.pack('<d', v)
        return b'\4' + string(v)
    def proto(x):
        return (string(x['source']) + integer(x['line']) + integer(x['endline'])
                + bytes(x[k] for k in ('nups','params','vararg','stack'))
                + array(x['code'], lambda w: struct.pack('<I',w))
                + array(x['constants'], constant) + array(x['children'], proto)
                + array(x['lines'], integer)
                + array(x['locals'], lambda v: string(v[0])+integer(v[1])+integer(v[2]))
                + array(x['upnames'], string))
    return bytes.fromhex('1b4c75615100010408040800') + proto(p)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--output', type=Path, default=Path('evidence/lua'))
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for filename in args.files:
        proto = read(filename)
        target = args.output / Path(filename).name
        target.with_suffix('.json').write_text(json.dumps(proto, indent=2))
        target.with_suffix('.txt').write_text(listing(proto)+'\n')
        print(filename, '->', target.with_suffix('.txt'))

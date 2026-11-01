"""Credential-authenticated SSH activation packet for the inspected RBR850 build.

Uses only the pure-Python Blowfish class from the locally saved MIT reference;
the original script's network code and main routine are never loaded.
"""
from pathlib import Path
import ast
import hashlib
from itertools import cycle
import re
import struct

REFERENCE = Path(__file__).resolve().parent / "reference/telnet-enable.py"
REFERENCE_SHA256 = "ec650fc11cd7d7a00b706aed044b5cc84e3227fc2117293d6338fbaca628839d"


def normalize_mac(mac):
    compact = re.sub(r"[:-]", "", mac).upper()
    if not re.fullmatch(r"[0-9A-F]{12}", compact):
        raise ValueError("MAC must contain exactly six hexadecimal octets")
    return compact


def build_packet_from_digest(mac, digest):
    mac = normalize_mac(mac)
    if not re.fullmatch(r"[0-9A-F]{64}", digest):
        raise ValueError("Expected an uppercase SHA-256 hexadecimal digest")
    source = REFERENCE.read_bytes()
    if hashlib.sha256(source).hexdigest() != REFERENCE_SHA256:
        raise ValueError("Saved reference changed; review it before updating its checksum")
    tree = ast.parse(source)
    selected = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Blowfish"]
    assert len(selected) == 1
    namespace = {"Struct": struct.Struct, "struct_error": struct.error, "iter_cycle": cycle}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "reference-Blowfish-only", "exec"), namespace)
    fields = (mac.encode().ljust(16, b"\0") + b"admin".ljust(16, b"\0")
              + digest.encode().ljust(80, b"\0"))
    clear = (hashlib.md5(fields).digest() + fields).ljust(248, b"\0")
    cipher = namespace["Blowfish"](b"AMBIT_TELNET_ENABLE+" + digest.encode(), byte_order="little")
    return b"".join(cipher.encrypt_ecb(clear))


def build_packet(mac, password):
    digest = hashlib.sha256(password.encode("utf-8")).hexdigest().upper()
    return build_packet_from_digest(mac, digest)

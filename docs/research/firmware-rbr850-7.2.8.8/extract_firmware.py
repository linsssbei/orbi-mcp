"""Extract the downloaded Orbi CHK image for offline inspection; never execute it.

Run with .venv/bin/python extract_firmware.py. Requires dissect.squashfs.
Symlinks and device files are recorded, not created. Files get no execute bits.
"""
from pathlib import Path
import hashlib
import json
import struct
import zipfile
from collections import defaultdict

from dissect.squashfs import SquashFS


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "downloads/RBR850-V7.2.8.8.zip"
IMAGE = ROOT / "firmware/RBR850-V7.2.8.8_5.1.24.chk"


def extract():
    with zipfile.ZipFile(ARCHIVE) as archive:
        for entry in archive.infolist():
            path = Path(entry.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe archive path: {path}")
            if entry.is_dir():
                continue
            destination = ROOT / "firmware" / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(entry))

    data = IMAGE.read_bytes()
    base = data.index(b"UBI#")
    # Determine physical erase-block size from consecutive erase-counter headers.
    block_size = data.index(b"UBI#", base + 4) - base
    volumes = defaultdict(dict)
    records = []
    for offset in range(base, len(data) - block_size + 1, block_size):
        block = data[offset : offset + block_size]
        if block[:4] != b"UBI#":
            continue
        vid_offset, payload_offset = struct.unpack_from(">II", block, 16)
        header = block[vid_offset : vid_offset + 64]
        if header[:4] != b"UBI!":
            continue
        volume_id, logical_block = struct.unpack_from(">II", header, 8)
        payload_size = struct.unpack_from(">I", header, 20)[0]
        payload = block[payload_offset:]
        if payload_size:
            payload = payload[:payload_size]
        if logical_block in volumes[volume_id]:
            raise ValueError("Duplicate logical block; requires sequence-number handling")
        volumes[volume_id][logical_block] = payload
        records.append({"offset": offset, "volume_id": volume_id,
                        "logical_block": logical_block, "data_size": payload_size})

    volume_dir = ROOT / "volumes"
    volume_dir.mkdir(exist_ok=True)
    rootfs = None
    for volume_id, blocks in sorted(volumes.items()):
        if sorted(blocks) != list(range(len(blocks))):
            raise ValueError(f"Missing logical block in volume {volume_id}")
        payload = b"".join(blocks[index] for index in sorted(blocks))
        (volume_dir / f"volume-{volume_id}.bin").write_bytes(payload)
        if payload.startswith(b"hsqs"):
            used_size = struct.unpack_from("<Q", payload, 40)[0]
            if used_size > len(payload):
                raise ValueError("Truncated SquashFS volume")
            rootfs = volume_dir / "rootfs.squashfs"
            rootfs.write_bytes(payload[:used_size])
    (ROOT / "ubi-blocks.json").write_text(json.dumps(records, indent=2) + "\n")
    if rootfs is None:
        raise ValueError("No SquashFS volume found")

    output = ROOT / "rootfs"
    output.mkdir(exist_ok=True)
    inventory = []
    with rootfs.open("rb") as handle:
        filesystem = SquashFS(handle)

        def walk(node, relative=Path(), extracted_relative=Path()):
            used_names = set()
            for name, child in node.listdir().items():
                if name in (".", "..") or "/" in name or "\\" in name:
                    raise ValueError(f"Unsafe filesystem name: {name}")
                path = relative / name
                host_name = name
                if host_name.casefold() in used_names:
                    host_name += "__case_" + hashlib.sha256(name.encode()).hexdigest()[:8]
                if host_name.casefold() in used_names:
                    raise ValueError(f"Host filename collision: {path}")
                used_names.add(host_name.casefold())
                host_path = extracted_relative / host_name
                destination = output / host_path
                entry = {"path": str(path), "extracted_path": str(host_path),
                         "mode": oct(child.mode), "size": child.size}
                if child.is_symlink():
                    entry.update(type="symlink", target=child.link)
                elif child.is_dir():
                    entry["type"] = "directory"
                    destination.mkdir(exist_ok=True)
                    walk(child, path, host_path)
                elif child.is_file():
                    entry["type"] = "file"
                    with child.open() as source:
                        contents = source.read()
                    destination.write_bytes(contents)
                    entry["sha256"] = hashlib.sha256(contents).hexdigest()
                else:
                    entry["type"] = "special-skipped"
                inventory.append(entry)

        walk(filesystem.root)
    (ROOT / "filesystem-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    print(json.dumps({"entries": len(inventory), "files": sum(x["type"] == "file" for x in inventory),
                      "rootfs": str(output)}, indent=2))


if __name__ == "__main__":
    extract()

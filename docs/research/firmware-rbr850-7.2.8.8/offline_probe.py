"""Offline, synthetic-input emulation of remoteshellenable from this exact image.

All imported functions and process launches are Python stubs. No host network,
router connection, native firmware execution, or process launch is possible in
the emulated code. This is an investigation harness, not a live unlock tool.
"""
from pathlib import Path
import hashlib
import json
import struct

from activation_packet import build_packet_from_digest

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent
BINARY = ROOT / "rootfs/usr/sbin/remoteshellenable"
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
FIXTURE_MAC = "020000123456"
FIXTURE_PASSWORD = "Synthetic-Orbi-Test-Only!"
FIXTURE_DIGEST = hashlib.sha256(FIXTURE_PASSWORD.encode()).hexdigest().upper()
STOP = 0x500000
OUTPUT = 0x300000


def reference_packet(mac, digest):
    """Independent Python implementation, compared to firmware ARM instructions."""
    return build_packet_from_digest(mac, digest)


class OfflineEmulator:
    def __init__(self, packets=(), binary=BINARY, image_size=0x20000, guard_address=0x18000):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        for address, size in [(0, image_size), (OUTPUT, 0x10000), (0x400000, 0x100000), (STOP, 0x1000)]:
            self.uc.mem_map(address, size)
        if guard_address >= image_size:
            self.uc.mem_map(guard_address & ~0xFFF, 0x1000)
        self.imports = {}
        self.events = []
        self.packets = list(packets)
        self.packet_index = 0
        self.stopped = False
        with binary.open("rb") as handle:
            elf = ELFFile(handle)
            for segment in elf.iter_segments():
                if segment.header.p_type == "PT_LOAD":
                    self.uc.mem_write(segment.header.p_vaddr, segment.data())
            symbols = elf.get_section_by_name(".dynsym")
            for relocation in elf.get_section_by_name(".rel.dyn").iter_relocations():
                symbol = symbols.get_symbol(relocation.entry.r_info_sym)
                if symbol.name == "__stack_chk_guard":
                    self.uc.mem_write(guard_address, struct.pack("<I", 0x12345678))
                    self.uc.mem_write(relocation.entry.r_offset, struct.pack("<I", guard_address))
            plt = elf.get_section_by_name(".plt").header.sh_addr + 20
            for index, relocation in enumerate(elf.get_section_by_name(".rel.plt").iter_relocations()):
                self.imports[plt + index * 12] = symbols.get_symbol(relocation.entry.r_info_sym).name
        if binary == BINARY:
            self.uc.mem_write(0x14220, b"br-lan\0\0")
        self.uc.hook_add(UC_HOOK_CODE, self.hook)

    def string(self, address):
        result = bytearray()
        for offset in range(1024):
            value = self.uc.mem_read(address + offset, 1)[0]
            if not value:
                return result.decode()
            result.append(value)
        raise AssertionError("Unterminated emulated string")

    def return_value(self, result=0):
        self.uc.reg_write(UC_ARM_REG_R0, result & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def hook(self, uc, address, size, _):
        args = [uc.reg_read(r) for r in REGS]
        r0, r1, r2, r3 = args
        if address == STOP:
            self.stopped = True
            uc.emu_stop()
            return
        if address == 0x20A8:  # Firmware's subprocess wrapper: never launch anything.
            stack = uc.reg_read(UC_ARM_REG_SP)
            extra = struct.unpack("<II", uc.mem_read(stack, 8))
            command = [self.string(r3)]
            for pointer in extra:
                if not pointer:
                    break
                command.append(self.string(pointer))
            self.events.append({"blocked_exec": command})
            self.return_value()
            return
        name = self.imports.get(address)
        if name is None:
            return
        result = 0
        if name == "memset":
            uc.mem_write(r0, bytes([r1 & 255]) * r2)
            result = r0
        elif name == "memmove":
            uc.mem_write(r0, bytes(uc.mem_read(r1, r2)))
            result = r0
        elif name in ("strlcpy", "strncpy"):
            data = self.string(r1).encode()
            if name == "strlcpy":
                if r2:
                    uc.mem_write(r0, data[:r2-1] + b"\0")
                result = len(data)
            else:
                uc.mem_write(r0, data[:r2].ljust(r2, b"\0"))
                result = r0
        elif name == "snprintf":
            assert self.string(r2) == "AMBIT_TELNET_ENABLE+%s"
            data = ("AMBIT_TELNET_ENABLE+" + self.string(r3)).encode()
            uc.mem_write(r0, data[:r1-1] + b"\0")
            result = len(data)
        elif name == "fopen":
            assert self.string(r0) == "/tmp/httpwd"
            result = 0x19000
        elif name == "fgets":
            uc.mem_write(r0, (FIXTURE_DIGEST + "\n").encode()[:r1-1] + b"\0")
            result = r0
        elif name in ("fclose", "close", "daemon", "setsockopt"):
            pass
        elif name == "socket":
            self.events.append({"stub_socket": args[:3]})
            result = 3
        elif name == "ioctl":
            if r1 == 0x8927:  # SIOCGIFHWADDR
                uc.mem_write(r2 + 16, struct.pack("<H", 1) + bytes.fromhex(FIXTURE_MAC))
            elif r1 == 0x8915:  # SIOCGIFADDR
                uc.mem_write(r2 + 16, struct.pack("<HH", 2, 0) + bytes([192, 168, 1, 1]))
            else:
                raise AssertionError(f"Unexpected ioctl {r1:#x}")
        elif name == "htons":
            result = int.from_bytes(r0.to_bytes(2, "little"), "big")
        elif name == "htonl":
            result = int.from_bytes(r0.to_bytes(4, "little"), "big")
        elif name == "bind":
            data = bytes(uc.mem_read(r1, 16))
            self.events.append({"stub_bind_port": int.from_bytes(data[2:4], "big")})
        elif name == "select":
            result = 1
        elif name == "recvfrom":
            if self.packet_index >= len(self.packets):
                self.stopped = True
                uc.emu_stop()
                return
            data = self.packets[self.packet_index]
            self.packet_index += 1
            assert len(data) <= r2
            uc.mem_write(r1, data)
            result = len(data)
        elif name == "memcmp":
            a, b = bytes(uc.mem_read(r0, r2)), bytes(uc.mem_read(r1, r2))
            result = 0 if a == b else 1
        elif name == "sendto":
            self.events.append({"stub_reply": bytes(uc.mem_read(r1, r2)).decode()})
            result = r2
        elif name == "puts":
            self.events.append({"stub_log": self.string(r0)})
        else:
            raise AssertionError(f"Unimplemented imported function: {name} at {address:#x}")
        self.return_value(result)

    def run(self, address, args=()):
        self.uc.reg_write(UC_ARM_REG_SP, 0x4FF000)
        self.uc.reg_write(UC_ARM_REG_LR, STOP)
        for register, value in zip(REGS, args):
            self.uc.reg_write(register, value)
        self.uc.emu_start(address, STOP + 4, timeout=20_000_000, count=10_000_000)
        assert self.stopped, "Emulation did not finish within resource limits"
        return self.uc.reg_read(UC_ARM_REG_R0)


class OfflineDebugFormEmulator(OfflineEmulator):
    def __init__(self, form):
        super().__init__(binary=ROOT / "rootfs/usr/sbin/httpd", image_size=0x300000,
                         guard_address=0x600000)
        self.form = form

    def hook(self, uc, address, size, userdata):
        r0, r1, r2, r3 = [uc.reg_read(r) for r in REGS]
        if address == 0x28BE4:  # HTTP form-value lookup
            key = self.string(r1)
            data = self.form.get(key, "").encode()
            uc.mem_write(r2, data[:r3-1] + b"\0")
            self.events.append({"form_lookup": key})
            self.return_value(len(data))
            return
        if address == 0x29C48:  # Diagnostic logger
            self.return_value()
            return
        if address == 0x2B110:  # Page renderer
            self.events.append({"render_page": self.string(r0)})
            self.return_value()
            return
        name = self.imports.get(address)
        if name == "strcmp":
            a, b = self.string(r0), self.string(r1)
            self.return_value((a > b) - (a < b))
            return
        if name == "acosNvramConfig_set":
            self.events.append({"stub_nvram_set": [self.string(r0), self.string(r1)]})
            self.return_value()
            return
        if name == "acosNvramConfig_save":
            self.events.append({"stub_nvram_save": True})
            self.return_value()
            return
        if name in ("system", "doSystem"):
            self.events.append({"blocked_system": self.string(r0)})
            self.return_value()
            return
        super().hook(uc, address, size, userdata)


def main():
    expected = reference_packet(FIXTURE_MAC, FIXTURE_DIGEST)
    generator = OfflineEmulator()
    size = generator.run(0x2484, [OUTPUT])
    generated = bytes(generator.uc.mem_read(OUTPUT, size))
    assert size == 248
    assert generated == expected, "Native generator and independent Python reference differ"
    cases = {
        "correct_credentials": expected,
        "wrong_mac": reference_packet("020000123457", FIXTURE_DIGEST),
        "wrong_password": reference_packet(FIXTURE_MAC, "0" * 64),
        "truncated_packet": expected[:-1],
        "corrupted_packet": bytes([expected[0] ^ 1]) + expected[1:],
    }
    results = {}
    for name, packet in cases.items():
        emulator = OfflineEmulator([packet])
        emulator.run(0xBEC)
        started = any(e.get("blocked_exec") == ["/etc/init.d/sshd", "start"] for e in emulator.events)
        acked = any(e.get("stub_reply") == "ACK" for e in emulator.events)
        assert started == acked == (name == "correct_credentials"), (name, emulator.events)
        results[name] = {"would_start_sshd": started, "would_reply_ack": acked,
                         "events": emulator.events}
    debug_cases = {
        "telnetEnableForm": {"form_name": "telnetEnableForm", "action_telnet_enable": "1", "telnet_enable": "1"},
        "debugLogForm": {"form_name": "debugLogForm", "action_Start_When_Boot_Up": "1"},
        "sentLogForm": {"form_name": "sentLogForm"},
    }
    debug_results = {}
    for name, form in debug_cases.items():
        emulator = OfflineDebugFormEmulator(form)
        emulator.run(0xDA2D0, [OUTPUT, OUTPUT + 0x100])
        writes = [e["stub_nvram_set"] for e in emulator.events if "stub_nvram_set" in e]
        commands = [e["blocked_system"] for e in emulator.events if "blocked_system" in e]
        if name == "telnetEnableForm":
            assert writes == [] and commands == [], emulator.events
            assert [e["form_lookup"] for e in emulator.events if "form_lookup" in e] == ["form_name"]
        elif name == "debugLogForm":
            assert ["action_Start_Capture_When_Boot_Up", "1"] in writes, emulator.events
        else:
            assert ["dbg_log_collect_send", "1"] in writes, emulator.events
        debug_results[name] = {"nvram_writes": writes, "would_run_commands": commands,
                               "events": emulator.events}
    report = {
        "firmware_binary_sha256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "method": "ARM instruction emulation with synthetic inputs and stubbed host interfaces",
        "network_packets_sent": 0,
        "host_processes_launched_by_firmware": 0,
        "native_generator_matches_python_reference": True,
        "packet_bytes": size,
        "synthetic_packet_sha256": hashlib.sha256(expected).hexdigest(),
        "cases": results,
        "debug_form_cases": debug_results,
    }
    (ROOT / "evidence/offline-probe-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("cases", "debug_form_cases")}, indent=2))
    for name, result in results.items():
        print(name, "PASS", "would_start_sshd=", result["would_start_sshd"])
    for name, result in debug_results.items():
        print(name, "PASS", "nvram_write_count=", len(result["nvram_writes"]))


if __name__ == "__main__":
    main()

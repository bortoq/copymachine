"""Bulk-synchronous RV32I generator (roadmap 8.10, variant A).

Same universal interpreter as rv32i.py (no guest instruction is examined),
but the emitted copy schedule is rewritten for the bulk-synchronous tick:
all instructions of a tick are fetched at the start, all copies commit
together, a field patched in a tick is visible only from the next tick.

The generator therefore splits every block into layers ("ticks"):

* a node (a copy) is placed at a dependency level: a read of a position
  written by another node follows it; a field patch follows its index bits;
* a patched instruction executes at least two layers after its patch, so
  the patch writes the target's home before the link of the previous layer
  reads that home (rule P1: patch at L writes H_M, the link at M-1 reads
  H_M, so M >= L+2);
* within a layer all writes are pairwise disjoint (read-after-write and
  write-after-write order are both preserved);
* the block terminator is the link of its last layer.

Arithmetic and reductions are rewritten to logarithmic depth: a
Kogge-Stone prefix adder and binary reduction trees, so a layer holds
many independent gate reads.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import dependencies
from copycode.vm2.machine import describe, space_bits_for_bytes

from rv32i import (Image, Copy, Field, Layout, SLOTS, SPACE_BYTES,
                   MEMORY_BYTES, REGS, PC, STATUS, EXIT_CODE, FRAME_BITS,
                   SCRATCH, TEMP, COND, REDUCE, IR, A, B, RHS, RESULT,
                   NEXT_PC, EA, IMM, JUMP, RD_ADDRESS, CARRY)

# scratch for the log-depth primitives, above the named rv32i scratch and
# below the constant region (SCRATCH .. SCRATCH+12288 bits)
PB_G0 = SCRATCH + 64*32
PB_P0 = SCRATCH + 65*32
PB_AG = SCRATCH + 66*32
PB_AP = SCRATCH + 67*32
PB_BG = SCRATCH + 68*32
PB_BP = SCRATCH + 69*32
PB_T = SCRATCH + 70*32
PB_CIN = SCRATCH + 71*32
TREE = SCRATCH + 72*32
VAL = SCRATCH + 80*32
# io adapter scratch: the SYS answer record and the status byte
IO_RSP = SCRATCH + 96*32
IO_ST = SCRATCH + 100*32
# Persistent cooperative monitor state, below constant_base.
MON_REMAIN = SCRATCH + 128*32
MON_RELOAD = MON_REMAIN + 32
MON_COMMITTED = MON_RELOAD + 32
MON_INPUT = MON_COMMITTED + 64
MON_OUTPUT = MON_INPUT + 64
MON_READS = MON_OUTPUT + 64
MON_WRITES = MON_READS + 64
MON_AMOUNT = MON_WRITES + 64
MON_CARRY = MON_AMOUNT + 32

# Wide-LUT gate functions, keyed by (name, arity): a k-input lookup computes a
# k-ary boolean function in one read, so gate trees collapse into fewer levels
# (the FPGA k-LUT trade; roadmap 8.10.4).
GATE_FUNCTIONS = {
    "and": lambda *a: all(a),
    "or": lambda *a: any(a),
    "xor": lambda *a: bool(sum(1 for x in a if x) & 1),
    "not": lambda a: not a,
    "mux": lambda a, b, select: b if select else a,
    "signed_lt": lambda sign_a, sign_b, unsigned: sign_a if sign_a != sign_b else unsigned,
    # fused wide-LUT primitives that pull a serial dependency into one lookup
    "or_and": lambda g, p, gs: g | (p & gs),      # prefix combine: G|(P&G')
    "xor_or": lambda a, g, p: a ^ (g | p),        # sum bit with carry-select
    "andn": lambda a, b: a & (1 - b),             # subtract: a & ~b
    "xnor": lambda a, b: 1 - (a ^ b),             # subtract: a ^ ~b
}
TREE_ARITY = 6


class BulkImage(Image):
    """Image that emits a bulk-synchronous (new emulator) schedule."""

    def __init__(self, *args, segment_budget=None, trace=None, phase_markers=False, final_snapshot=True, **kwargs):
        super().__init__(*args, **kwargs)
        if segment_budget is not None and (not isinstance(segment_budget, int) or
                                           not 1 <= segment_budget < 1 << 32):
            raise ValueError("segment budget must be within 1..2**32-1 commits")
        if trace not in (None, "full", "channels"):
            raise ValueError("trace must be full or channels")
        if phase_markers and trace is None:
            raise ValueError("legacy phase-only markers are unsupported; select an explicit trace mode or the direct target")
        self.final_snapshot = final_snapshot
        self.trace = trace
        self.phase_markers = phase_markers or trace is not None
        self.segment_budget = (2**32-1 if segment_budget is None and trace else segment_budget)

    def _monitor_next(self):
        self.serial += 1
        label = f"monitor_{self.serial}"
        self.jump(label)
        self.start(label)

    def _monitor_add64(self, dst, amount):
        # Explicit blocks isolate the shared adder scratch and carry lifetime.
        self._monitor_next()
        self.add(dst, dst, amount)
        self._monitor_next()
        self.emit(32, MON_CARRY, self.constant(0))
        self.emit(1, MON_CARRY, CARRY)
        self._monitor_next()
        self.add(dst+32, dst+32, MON_CARRY)
        self._monitor_next()

    def _monitor_io(self, reading, moved, width):
        if self.segment_budget is None:
            return
        self._monitor_next()
        self.emit(32, MON_AMOUNT, self.constant(0))
        self.emit(width, MON_AMOUNT, moved)
        self._monitor_add64(MON_INPUT if reading else MON_OUTPUT, MON_AMOUNT)
        self._monitor_add64(MON_READS if reading else MON_WRITES, self.constant(1))
        self.serial += 1
        name = f"io_result_{self.serial}"
        self.jump(name)
        self.start(name)

    def build(self):
        super().build()
        if self.segment_budget is None:
            return self
        self.data.extend([(MON_REMAIN, 32, self.segment_budget),
                          (MON_RELOAD, 32, self.segment_budget)])
        self.blocks["checkpoint"][1].src = "monitor_commit"
        self.start("monitor_commit")
        self._monitor_add64(MON_COMMITTED, self.constant(1))
        self.add(MON_REMAIN, MON_REMAIN, self.constant(1), subtract=True)
        self.reduce_or(COND, list(range(MON_REMAIN, MON_REMAIN+32)))
        self.branch(COND, "monitor_report", "fetch")
        self.start("monitor_report")
        # encode() redirects this known boundary to terminal copycode.
        self.jump("halt")
        return self

    # ------------------------------------------------------------------
    # log-depth primitives
    # ------------------------------------------------------------------
    def add(self, dst, a, b, subtract=False):
        """Kogge-Stone prefix adder: dst[0..31] = a +/- b, CARRY = carry out."""
        for i in range(32):
            if subtract:
                self.gate("andn", PB_G0 + i, [a + i, b + i])
                self.gate("xnor", PB_P0 + i, [a + i, b + i])
            else:
                self.gate("and", PB_G0 + i, [a + i, b + i])
                self.gate("xor", PB_P0 + i, [a + i, b + i])
        source_g, source_p = PB_G0, PB_P0
        buffers = [(PB_AG, PB_AP), (PB_BG, PB_BP)]
        selected = 0
        for shift in (1, 2, 4, 8, 16):
            dest_g, dest_p = buffers[selected]
            for i in range(32):
                if i < shift:
                    self.emit(1, dest_g + i, source_g + i)
                    self.emit(1, dest_p + i, source_p + i)
                else:
                    self.gate("or_and", dest_g + i,
                              [source_g + i, source_p + i, source_g + i - shift])
                    self.gate("and", dest_p + i, [source_p + i, source_p + i - shift])
            source_g, source_p = dest_g, dest_p
            selected ^= 1
        zero = self.constant(0)
        for i in range(32):
            if i == 0:
                carry = self.constant(1) if subtract else zero
                self.gate("xor", dst + 0, [PB_P0 + 0, carry])
            elif subtract:
                self.gate("xor_or", dst + i, [PB_P0 + i, source_g + i - 1, source_p + i - 1])
            else:
                self.gate("xor", dst + i, [PB_P0 + i, source_g + i - 1])
        if subtract:
            self.gate("or", CARRY, [source_g + 31, source_p + 31])
        else:
            self.emit(1, CARRY, source_g + 31)

    def gate(self, name, dst, inputs):
        """One lookup per k-ary function; the table is keyed by (name, arity)
        so reductions/validations can use wide lookups, not only 2-input ones."""
        key = (name, len(inputs))
        if key not in self.gates:
            function = GATE_FUNCTIONS[name]
            count = len(inputs)
            self.gates[key] = self.table(
                [int(function(*[(i >> j) & 1 for j in range(count)]))
                 for i in range(1 << count)], 0)
        self.lookup(dst, self.gates[key], inputs, 1)

    def _tree(self, name, dst, inputs):
        current = list(inputs)
        if not current:
            self.emit(1, dst, self.constant(0))
            return
        level = 0
        while len(current) > 1:
            following = []
            for j in range(0, len(current), TREE_ARITY):
                chunk = current[j:j + TREE_ARITY]
                if len(chunk) == 1:
                    following.append(chunk[0])
                else:
                    node = TREE + level * 32 + j // TREE_ARITY
                    self.gate(name, node, chunk)
                    following.append(node)
            current = following
            level += 1
        if current[0] != dst:
            self.emit(1, dst, current[0])

    def reduce_or(self, dst, inputs):
        self._tree("or", dst, inputs)

    def _check(self, bits, error):
        self._tree("and", COND, bits)
        self.guard(COND, error)

    def validate(self, mask, expected):
        bits = []
        for i in range(32):
            if mask & (1 << i):
                source = IR + i
                if not (expected & (1 << i)):
                    self.gate("not", VAL + i, [source])
                    source = VAL + i
                bits.append(source)
        self._check(bits, "illegal")

    def require_value(self, source, expected, error):
        bits = []
        for i in range(32):
            bit = source + i
            if not ((expected >> i) & 1):
                self.gate("not", VAL + i, [bit])
                bit = VAL + i
            bits.append(bit)
        self._check(bits, error)

    # ------------------------------------------------------------------
    # scheduling
    # ------------------------------------------------------------------
    @staticmethod
    def _span(value, n):
        if isinstance(value, int):
            return range(value, value + n)
        return ()

    def _level(self, ops, term):
        """Assign _level to every node; return the terminator layer index."""
        # Every operand participates, including two reads and symbolic fields.
        # Unknown runtime operands/channels get an isolated layer.
        used, levels, patch = {}, {}, {}
        dynamic={id(v.instruction) for node in ops for v in (node.dst,node.src)
                 if isinstance(v,Field) and v is node.dst}
        isolated=0
        top=0
        def spans(value,n):
            if isinstance(value,int):return [('memory',i) for i in range(value,value+n)]
            if isinstance(value,Field):
                return [(id(value.instruction),value.name,i) for i in range(value.offset,value.offset+n)]
            return []
        for node in ops:
            operands=spans(node.src,node.n)+spans(node.dst,node.n)
            level=max([isolated+1]+[used.get(p,0)+1 for p in operands])
            unknown=id(node) in dynamic or any(isinstance(v,int) and v>=self.sys_nbits for v in (node.dst,node.src))
            if unknown:level=max(level,top+1)
            if id(node) in patch:level=max(level,patch[id(node)]+2)
            if isinstance(node.dst,Field):
                patch[id(node.dst.instruction)]=max(level,patch.get(id(node.dst.instruction),0))
            levels[id(node)]=level
            for position in operands:used[position]=level
            if unknown:isolated=level
            top=max(top,level)
        top = max(levels.values()) if levels else 0
        last = top + 1 if term is not None else top
        if term is not None and id(term) in patch:
            last = max(last, patch[id(term)] + 2)
        for node in ops:
            node._level = levels[id(node)]
        if term is not None:
            term._level = last
        return last

    def _resolve_field(self, value, context):
        if isinstance(value, Field):
            target = value.instruction
            offset = {"n": 0, "dst": self.layout.n_bits,
                      "src": self.layout.n_bits + self.layout.address_bits}[value.name]
            return target.home + target.slot * self.layout.instruction_bits + offset + value.offset
        return value

    # ------------------------------------------------------------------
    # io adapter (roadmap 8.1): old IN/OUT through the new data channels
    # ------------------------------------------------------------------
    @property
    def sys_nbits(self):
        """Space size reserves the actual shared device table."""
        return space_bits_for_bytes(self.layout.space_bytes)

    @staticmethod
    def _offsets(widths):
        off, at = [], 0
        for width in widths:
            off.append(at)
            at += width
        return off

    @staticmethod
    def _record(widths, values):
        """Pack record fields low bit first into bytes the `literal` reads."""
        total, at, value = sum(widths), 0, 0
        for width, field in zip(widths, values):
            value |= (field & ((1 << width) - 1)) << at
            at += width
        raw = bytearray((total + 7)//8)
        for i in range(total):
            if (value >> i) & 1:
                raw[i//8] |= 1 << (7 - i % 8)
        return bytes(raw)

    def build_io(self):
        address_bits, n_bits = self.layout.address_bits, self.layout.n_bits
        sys_nbits = self.sys_nbits
        # SYS record fields (proto.def): req op/chan/flags/arg/off,
        # rsp op/status/flags/size/moved/eof; SYS controls any channel.
        boundary = describe(sys_nbits, SLOTS)
        assert boundary['instruction']['bits'] == self.layout.instruction_bits
        devices = {d['name']: d['position'] for d in boundary['channels']['devices']}
        req_w = [f['width_bits'] for f in boundary['records']['req']['fields']]
        rsp_w = [f['width_bits'] for f in boundary['records']['rsp']['fields']]
        req_bits, rsp_bits = sum(req_w), sum(rsp_w)
        rsp_off = self._offsets(rsp_w)          # [op, status, flags, size, moved, eof]
        a0, a1, a2, a7 = (REGS + 32*i for i in (10, 11, 12, 17))

        for name, descriptor, device, reading in [
                ("read", 0, devices["stdin"], True), ("write", 1, devices["stdout"], False)]:
            self.start("io_" + name)
            self.require_value(a0, descriptor, "io_ebadf")
            self.reduce_or(COND, list(range(a2, a2 + 32)))
            self.branch(COND, "io_zero", "io_" + name + "_range")
            self.start("io_" + name + "_range")
            self.require_zero(list(range(a1 + self.memory_bits, a1 + 32)), "io_efault")
            self.add(EA, a1, a2)
            self.gate("not", COND, [CARRY])
            self.guard(COND, "io_efault")
            self.add(IMM, EA, self.constant(self.memory_bytes + 1), subtract=True)
            self.gate("not", COND, [CARRY])
            self.guard(COND, "io_efault")
            # prepare a data copy; it is placed in its own block so the host
            # services it in its own tick, after the field patches commit
            if reading:
                channel, field = Copy(0, self.layout.memory_bit, device), "dst"
            else:
                channel, field = Copy(0, device, self.layout.memory_bit), "src"
            self.emit(self.memory_bits + 1, Field(channel, "n", 3), a2)
            self.emit(self.memory_bits, Field(channel, field, 3), a1)
            self.jump("io_" + name + "_transfer")
            self.start("io_" + name + "_transfer")
            self.blocks[self.current][0].append(channel)
            self.jump("io_" + name + "_status")
            # a later block asks SYS to fstat the channel and reads the answer
            self.start("io_" + name + "_status")
            self.blocks[self.current][0].append(Copy(
                req_bits, sys_nbits,
                self.literal(self._record(req_w, [boundary["contract"]["operations"]["FSTAT"], device, 0, 0, 0]))))
            self.blocks[self.current][0].append(Copy(rsp_bits, IO_RSP, sys_nbits))
            self._monitor_io(reading, IO_RSP + rsp_off[4], n_bits)
            self.emit(8, IO_ST, IO_RSP + rsp_off[1])
            self.reduce_or(REDUCE, list(range(IO_ST, IO_ST + 8)))
            self.gate("not", COND, [REDUCE])            # status == 0
            if reading:
                self.emit(32, RESULT, self.constant(0))
                self.emit(n_bits, RESULT, IO_RSP + rsp_off[4])
            else:
                self.emit(32, RESULT, a2)
            self.branch(COND, "io_eio", "io_return")

        a0, a1, a2, a7 = (REGS + 32*i for i in (10, 11, 12, 17))
        self.start("io_dispatch")
        self.require_zero(list(range(a7 + 7, a7 + 32)), "io_enosys")
        self.dispatch(list(range(a7, a7 + 7)),
                      {63: "io_read", 64: "io_write", 93: "io_exit"}, default="io_enosys")
        self.start("io_zero")
        self.emit(32, RESULT, self.constant(0))
        self.jump("io_return")
        for name, value in [("enosys", -38), ("ebadf", -9), ("efault", -14), ("eio", -5)]:
            self.start("io_" + name)
            self.emit(32, RESULT, self.constant(value & 0xffffffff))
            self.jump("io_return")
        self.start("io_return")
        self.emit(32, a0, RESULT)
        self.jump("commit")
        self.start("io_exit")
        self.emit(32, EXIT_CODE, a0)
        self.emit(32, STATUS, self.constant(10))
        if self.segment_budget is not None:
            self._monitor_add64(MON_COMMITTED, self.constant(1))
        self.jump("halt")

    def encode(self, program=b"", entry=0, registers=None, *, initial_label="fetch",
               image_bytes=None):
        if self.state_output or self.report_status:
            raise NotImplementedError("the bulk generator supports the base and io profiles")
        if len(program) > self.memory_bytes:
            raise ValueError("program exceeds guest memory")
        if not 0 <= entry < (1 << 32):
            raise ValueError("entry must be a 32-bit address")
        if registers is None:
            registers = {2: self.memory_bytes-16}
        if any(not 0 <= i < 32 or not 0 <= value < (1 << 32) for i, value in registers.items()):
            raise ValueError("invalid initial register")

        instruction_bits = self.layout.instruction_bits
        layer_bits = self.layout.layer_bits
        link_slot = SLOTS - 1
        labels, scheduled = {}, []
        end, tick = self.code_base, 0
        for name, (ops, term) in self.blocks.items():
            if term is None:
                raise ValueError("block without terminator: " + name)
            last = self._level(ops, term)
            labels[name] = end
            scheduled.append((name, end, ops, term, last))
            for node in ops:
                node._abs = tick + node._level
            term._abs = tick + last
            tick += last
            end += last * layer_bits
        if end > self.code_limit:
            raise ValueError(f"strict operand schedule needs {end} code bits before guest memory at {self.layout.memory_bit}; increase Layout or use the compact direct target")

        def bits(address, width, value):
            if isinstance(value, str):
                value = labels[value]
            if not 0 <= value < (1 << width):
                raise ValueError(f"field overflow: {value}, {width}")
            for i in range(width):
                mask = 1 << (7-(address+i) % 8)
                byte = (address+i) // 8
                if (value >> i) & 1:
                    image[byte] |= mask
                else:
                    image[byte] &= ~mask

        def resolve(value):
            value = self._resolve_field(value, None)
            return labels[value] if isinstance(value, str) else value

        def place(node, home):
            node.home = home
            at = node.home + node.slot * instruction_bits
            for width, value in [(self.layout.n_bits, node.n),
                                 (self.layout.address_bits, resolve(node.dst)),
                                 (self.layout.address_bits, resolve(node.src))]:
                bits(at, width, value)
                at += width

        # first assign every home and slot (labels and homes are needed
        # by resolve for field patches that point at later layers)
        layout = []
        for name, base, ops, term, last in scheduled:
            by_level = {}
            for node in ops:
                by_level.setdefault(node._level, []).append(node)
            for level, group in by_level.items():
                if len(group) > link_slot:
                    raise ValueError(
                        f"level {level} of {name} has {len(group)} nodes > {link_slot}")
            for level in range(1, last + 1):
                home = base + (level-1) * layer_bits
                for slot, node in enumerate(by_level.get(level, ())):
                    node.home, node.slot = home, slot
            term.home, term.slot = base + (last-1) * layer_bits, link_slot
            layout.append((base, by_level, term, last))

        # invariants of the bulk schedule: within one tick all copies are
        # pairwise disjoint (P2), no copy touches the processor region, and
        # a patched instruction runs at least two layers after its patch (P1).
        # An instruction whose "dst" field is patched has a data-dependent
        # destination (the writeback write goes to REGS or DISCARD); it is
        # skipped here, the generator guarantees the destination is outside
        # the processor region.
        dynamic = set()
        for base, by_level, term, last in layout:
            for group in by_level.values():
                for node in group:
                    if isinstance(node.dst, Field) and node.dst.name == "dst":
                        dynamic.add(id(node.dst.instruction))
        for base, by_level, term, last in layout:
            for level, group in by_level.items():
                ranges=[]
                for node in group:
                    if id(node) in dynamic or not node.n:
                        continue
                    for operand in (node.dst,node.src):
                        at=self._resolve_field(operand,None)
                        if isinstance(at,int) and at<self.sys_nbits:
                            ranges.append((at,at+node.n))
                ranges.sort()
                for (a0, a1), (b0, _) in zip(ranges, ranges[1:]):
                    if b0 < a1:
                        raise ValueError("overlapping memory operands, including src/src, in one tick")
                for node in group:
                    if id(node) in dynamic:
                        continue
                    if isinstance(node.dst, int) and node.dst < layer_bits:
                        raise ValueError("a copy writes the processor region")
                    if (isinstance(node.dst, Field)
                            and node.dst.instruction._abs - node._abs < 2):
                        raise ValueError("a patch is closer than two layers to its instruction")

        if self.trace:
            # Ordinary n fields must be static for exact channel-only counts.
            for _, (_, ops, _, _) in enumerate(layout):
                for group in ops.values():
                    for node in group:
                        if isinstance(node.dst, Field) and node.dst.name == "n":
                            target = node.dst.instruction
                            if not any(isinstance(v, int) and v >= self.sys_nbits for v in (target.dst,target.src)):
                                raise ValueError("PCS2 cannot count a dynamically sized ordinary copy")
        image = bytearray(image_bytes if image_bytes is not None else
                          self.layout.memory_bit//8 + self.memory_bytes)
        for address, width, value in self.data:
            bits(address, width, value)
        for base, by_level, term, last in layout:
            for level in range(1, last + 1):
                home = base + (level-1) * layer_bits
                for node in by_level.get(level, ()):
                    place(node, home)
                if level == last:
                    place(term, home)
                else:
                    link = Copy(layer_bits, 0, base + level * layer_bits)
                    link.slot = link_slot
                    place(link, home)
        for i, value in registers.items():
            if i:
                bits(REGS+i*32, 32, value)
        bits(PC, 32, entry)
        image[self.layout.memory_bit//8:self.layout.memory_bit//8+len(program)] = program
        first = labels[initial_label] // 8
        image[:layer_bits//8] = image[first:first+layer_bits//8]
        manifest = {
            "space_bytes": self.layout.space_bytes, "processor_n": SLOTS,
            "boundary": describe(self.sys_nbits, SLOTS), "exit_code_bit": EXIT_CODE,
            "n_bits": self.layout.n_bits, "address_bits": self.layout.address_bits,
            "instruction_bits": instruction_bits, "layer_bits": layer_bits,
            "code_base": self.code_base, "code_end_bit": end,
            "registers_bit": REGS, "pc_bit": PC, "status_bit": STATUS,
            "guest_memory_bit": self.layout.memory_bit, "guest_memory_bytes": self.memory_bytes,
            "initial_stack": registers.get(2, 0), "entry": entry,
            "layer_count": sum(last for _, _, _, _, last in scheduled),
            "schedule_blocks": [dict(name=name,home=base,layers=last) for name,base,_,_,last in scheduled],
            "labels": labels,
        }
        if self.segment_budget is not None:
            from copycode.vm2.boundary import Format
            from copycode.vm2.terminal import TerminalFragment
            fmt = Format(self.sys_nbits, SLOTS)
            # A compact input image may omit the guest's zero-filled BSS/heap.
            # Monitor code must still live beyond the ENTIRE writable guest region.
            guest_end = self.layout.memory_bit//8 + self.memory_bytes
            if len(image) < guest_end:
                image.extend(bytes(guest_end-len(image)))
            counters = dict(committed=MON_COMMITTED, read_ops=MON_READS, write_ops=MON_WRITES)
            shared = dict(exit_address=EXIT_CODE, guest_status_address=STATUS,
                          input_cursor_address=MON_INPUT, output_cursor_address=MON_OUTPUT,
                          counter_addresses=counters, phase_markers=self.phase_markers)
            continuation = [(32, MON_REMAIN, MON_RELOAD), (layer_bits, 0, labels["fetch"])]
            checkpoint = TerminalFragment(self.sys_nbits, SLOTS, len(image)*8,
                                          snapshot=True, continuation=continuation,
                                          reason="limit", **shared)
            image.extend(checkpoint.data)
            final = TerminalFragment(self.sys_nbits, SLOTS, len(image)*8,
                                     snapshot=self.final_snapshot, **shared)
            image.extend(final.data)
            for name, fragment in [("monitor_report", checkpoint), ("halt", final)]:
                # Both boundary blocks contain exactly a link and no body.
                at = labels[name]//8
                image[at:at+fmt.layer_bytes] = fmt.layer([(0,0,0)]*(SLOTS-1)+[(layer_bits, 0, fragment.entry)])
            manifest["monitor"] = dict(format="rv32i-commit-v1", segment_budget=self.segment_budget,
                remaining_bit=MON_REMAIN, reload_bit=MON_RELOAD, input_cursor_bit=MON_INPUT,
                output_cursor_bit=MON_OUTPUT, counters_bit=counters,
                continuation_hex=fmt.layer(continuation).hex(),
                checkpoint_entry=checkpoint.entry, final_entry=final.entry,
                checkpoint_snapshot_entry=checkpoint.snapshot_entry,
                checkpoint_report_ticks=len(checkpoint.chain)-1, final_report_ticks=len(final.chain)-1,
                final_snapshot=self.final_snapshot)
            if self.trace:
                from copycode.vm2.dynamic_trace import instrument
                phases = []
                for name,base,ops,term,last in scheduled:
                    phase = 1 if name.startswith("monitor_") else 0
                    for level in range(1,last+1):
                        home = base+(level-1)*layer_bits
                        nonempty = any(node._level == level for node in ops)
                        phases.append((home, phase if nonempty else (1 if phase else 2)))
                relocations = [(at,width,labels[value]) for at,width,value in self.data if isinstance(value,str)]
                instrument(image,manifest,phases,relocations,mode=self.trace,initial_label=initial_label)
        return bytes(image), manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--entry", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--stack", type=lambda value: int(value, 0))
    parser.add_argument("--memory-bytes", type=lambda value: int(value, 0), default=MEMORY_BYTES)
    parser.add_argument("--space-bytes", type=lambda value: int(value, 0), default=SPACE_BYTES)
    parser.add_argument("--trace-mode",choices=("full","channels"))
    parser.add_argument("--segment-budget",type=int)
    args = parser.parse_args()
    try:
        image, manifest = BulkImage(memory_bytes=args.memory_bytes,
                                    layout=Layout(args.space_bytes),trace=args.trace_mode,
                                    segment_budget=args.segment_budget).build().encode(
            args.program.read_bytes(), args.entry,
            None if args.stack is None else {2: args.stack})
    except (OSError, ValueError, NotImplementedError) as error:
        parser.error(str(error))
    args.output.write_bytes(image)
    if args.manifest:
        args.manifest.write_text(json.dumps(manifest, indent=2)+"\n")


if __name__ == "__main__":
    main()

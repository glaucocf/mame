#!/usr/bin/env python3
"""
disasm_audio.py — Recursive Z80 disassembler for 1943 audio ROM (05.4k)
Output: audio_05_4k.asm  (WLA-DX syntax, ready for SMS/GG port)

1943 AUDIO CPU MEMORY MAP
  0x0000-0x7FFF  ROM (05.4k, 32 KiB)
  0xC000-0xC7FF  RAM (work variables)
  0xC800         sound_latch  — command byte written by main Z80
  0xD800         mcu_comm     — MCU <-> audioCPU shared byte
  0xE000         ym1_addr     — YM2203 #1 register select
  0xE001         ym1_data     — YM2203 #1 data write
  0xE002         ym2_addr     — YM2203 #2 register select
  0xE003         ym2_data     — YM2203 #2 data write

SMS/GG TARGET EQUIVALENTS (for port)
  sound_latch -> I/O port $C0 / GG port $C0 (joystick latch trick) or custom RAM
  YM2203 #1  -> YM2413 / OPLL at I/O port $F0 (addr) / $F1 (data)
  YM2203 #2  -> map remaining channels to YM2413 channels 3-8

Usage:
  python disasm_audio.py [--zip PATH] [--rom PATH]
  Default: reads 05.4k from 1943.zip in the current directory.
"""

import sys
import zipfile
import argparse
from pathlib import Path
from collections import deque

# ─────────────────────────────────────────────────────────────────────────────
# Hardware constants
# ─────────────────────────────────────────────────────────────────────────────
ROM_SIZE  = 0x8000

NAMED_ADDRS: dict[int, str] = {
    0xC800: 'sound_latch',
    0xD800: 'mcu_comm',
    0xE000: 'ym1_addr',
    0xE001: 'ym1_data',
    0xE002: 'ym2_addr',
    0xE003: 'ym2_data',
}

# YM2203 register names (for annotation when preceding LD (ym1_addr), A patterns)
YM_REG: dict[int, str] = {
    0x00:'SSG_TONE_A_LO', 0x01:'SSG_TONE_A_HI',
    0x02:'SSG_TONE_B_LO', 0x03:'SSG_TONE_B_HI',
    0x04:'SSG_TONE_C_LO', 0x05:'SSG_TONE_C_HI',
    0x06:'SSG_NOISE_PER', 0x07:'SSG_MIXER',
    0x08:'SSG_VOL_A',     0x09:'SSG_VOL_B',  0x0A:'SSG_VOL_C',
    0x0B:'SSG_ENV_LO',    0x0C:'SSG_ENV_HI', 0x0D:'SSG_ENV_SHAPE',
    0x20:'FM_LFO',
    0x24:'FM_TIMERA_HI',  0x25:'FM_TIMERA_LO', 0x26:'FM_TIMERB',
    0x27:'FM_TIMER_CTRL',
    0x28:'FM_KEYON',
    0x2A:'FM_DAC_DATA',   0x2B:'FM_DAC_EN',
}
# FM operator register blocks: 0x30-0x8F
_OP_NAMES = {0x30:'DT1_MUL', 0x40:'TL', 0x50:'KS_AR',
             0x60:'AM_DR',   0x70:'SR', 0x80:'SL_RR'}
for _base, _nm in _OP_NAMES.items():
    for _op in range(4):
        for _ch in range(3):
            YM_REG[_base + _op*0x10 + _ch] = f'FM_{_nm}_OP{_op+1}_CH{_ch+1}'
# FM channel registers 0xA0-0xB6
for _ch in range(3):
    YM_REG[0xA0+_ch] = f'FM_FN_LO_CH{_ch+1}'
    YM_REG[0xA4+_ch] = f'FM_FN_HI_CH{_ch+1}'
    YM_REG[0xA8+_ch] = f'FM_CH3_FN_LO_CH{_ch+1}'
    YM_REG[0xAC+_ch] = f'FM_CH3_FN_HI_CH{_ch+1}'
    YM_REG[0xB0+_ch] = f'FM_FB_ALGO_CH{_ch+1}'
    YM_REG[0xB4+_ch] = f'FM_LR_AMS_PMS_CH{_ch+1}'

# SMS/GG target register names for port (YM2413 OPLL)
YM2413_REG: dict[int, str] = {
    0x00:'OPLL_CUSTOM_M_AMVIBEGTYPE', 0x01:'OPLL_CUSTOM_C_AMVIBEGTYPE',
    0x02:'OPLL_CUSTOM_M_KSL_TOTAL_LV', 0x03:'OPLL_CUSTOM_C_KSL_TOTAL_LV',
    0x04:'OPLL_CUSTOM_M_AR_DR',  0x05:'OPLL_CUSTOM_C_AR_DR',
    0x06:'OPLL_CUSTOM_M_SL_RR',  0x07:'OPLL_CUSTOM_C_SL_RR',
}
for _ch in range(9):
    YM2413_REG[0x10+_ch] = f'OPLL_FN_LO_CH{_ch+1}'
    YM2413_REG[0x20+_ch] = f'OPLL_FN_HI_BLK_SUS_KEY_CH{_ch+1}'
    YM2413_REG[0x30+_ch] = f'OPLL_VOL_INST_CH{_ch+1}'

# ─────────────────────────────────────────────────────────────────────────────
# Z80 mnemonics tables
# ─────────────────────────────────────────────────────────────────────────────
R8  = ['B','C','D','E','H','L','(HL)','A']
RP  = ['BC','DE','HL','SP']
RP2 = ['BC','DE','HL','AF']
CC  = ['NZ','Z','NC','C','PO','PE','P','M']
ALU_OP = ['ADD A,','ADC A,','SUB ','SBC A,','AND ','XOR ','OR ','CP ']
ROT_OP = ['RLC','RRC','RL','RR','SLA','SRA','SLL','SRL']


def _s8(v: int) -> int:
    return v - 256 if v >= 128 else v

def _rd16(rom: bytes, pc: int) -> int:
    return rom[pc] | (rom[pc+1] << 8)

def _fmtA(addr: int) -> str:
    """Format address: named label > $XXXX."""
    return NAMED_ADDRS.get(addr, f'${addr:04X}')


# ─────────────────────────────────────────────────────────────────────────────
# Instruction decoder
# Returns: (mnemonic, byte_length, unconditional_flow_stop, extra_jump_targets)
# ─────────────────────────────────────────────────────────────────────────────
def decode(rom: bytes, pc: int, ixy: str = '') -> tuple[str, int, bool, list[int]]:
    if pc >= len(rom):
        return ('DB $00', 1, False, [])

    op = rom[pc]

    # ── Prefix: CB ──────────────────────────────────────────────────────────
    if op == 0xCB and not ixy:
        if pc+1 >= len(rom): return (f'DB $CB', 1, False, [])
        op2 = rom[pc+1]
        row, col = op2 >> 3, op2 & 7
        r = R8[col]
        if   row <  8: mn = f'{ROT_OP[row]} {r}'
        elif row < 16: mn = f'BIT {row-8},{r}'
        elif row < 24: mn = f'RES {row-16},{r}'
        else:          mn = f'SET {row-24},{r}'
        return (mn, 2, False, [])

    # ── Prefix: DD / FD (IX / IY) ───────────────────────────────────────────
    if op in (0xDD, 0xFD) and not ixy:
        pfx = 'IX' if op == 0xDD else 'IY'
        if pc+1 >= len(rom): return (f'DB ${op:02X}', 1, False, [])
        nxt = rom[pc+1]
        if nxt == 0xCB:   # DDCB / FDCB  — 4-byte
            if pc+3 >= len(rom): return (f'DB ${op:02X}', 1, False, [])
            d   = _s8(rom[pc+2])
            op3 = rom[pc+3]
            row, col = op3 >> 3, op3 & 7
            disp = f'({pfx}{d:+d})'
            if   row <  8: mn = f'{ROT_OP[row]} {disp}'
            elif row < 16: mn = f'BIT {row-8},{disp}'
            elif row < 24: mn = f'RES {row-16},{disp}'
            else:          mn = f'SET {row-24},{disp}'
            return (mn, 4, False, [])
        # Recurse with ixy set — wraps the inner instruction
        inner_mn, inner_len, unc, tgt = decode(rom, pc+1, pfx)
        return (inner_mn, inner_len+1, unc, tgt)

    # ── Prefix: ED ───────────────────────────────────────────────────────────
    if op == 0xED and not ixy:
        if pc+1 >= len(rom): return ('DB $ED', 1, False, [])
        op2 = rom[pc+1]
        mn, unc, tgt, extra_bytes = _decode_ed(rom, pc+1, op2)
        return (mn, 2+extra_bytes, unc, tgt)

    # ── IX/IY r8 substitution helper ─────────────────────────────────────────
    def ixy_r8(col: int) -> tuple[str, int]:
        """Return (operand_string, extra_disp_bytes)."""
        if not ixy:
            return R8[col], 0
        if col == 4: return f'{ixy}H', 0
        if col == 5: return f'{ixy}L', 0
        if col == 6:
            off = pc + 2      # prefix byte already consumed
            d   = _s8(rom[off]) if off < len(rom) else 0
            return f'({ixy}{d:+d})', 1
        return R8[col], 0

    def HL() -> str:
        return ixy if ixy else 'HL'

    x = op >> 6
    y = (op >> 3) & 7
    z = op & 7

    # ── x=0 ─────────────────────────────────────────────────────────────────
    if x == 0:
        # Misc single-byte
        singles = {
            0x00:'NOP', 0x07:'RLCA', 0x08:"EX AF,AF'", 0x0F:'RRCA',
            0x17:'RLA',  0x1F:'RRA',  0x27:'DAA',  0x2F:'CPL',
            0x37:'SCF',  0x3F:'CCF',
            0x02:'LD (BC),A', 0x0A:'LD A,(BC)',
            0x12:'LD (DE),A', 0x1A:'LD A,(DE)',
            0xEB:'EX DE,HL',  0xD9:'EXX',
            0xF3:'DI',   0xFB:'EI',
        }
        if op in singles:
            return (singles[op], 1, False, [])

        # DJNZ (10)
        if op == 0x10:
            e = _s8(rom[pc+1]) if pc+1 < len(rom) else 0
            target = (pc + 2 + e) & 0xFFFF
            return (f'DJNZ ${target:04X}', 2, False, [target])

        # JR e (18)
        if op == 0x18:
            e = _s8(rom[pc+1]) if pc+1 < len(rom) else 0
            target = (pc + 2 + e) & 0xFFFF
            return (f'JR ${target:04X}', 2, True, [target])

        # JR cc, e  (20/28/30/38)
        if op in (0x20, 0x28, 0x30, 0x38):
            cc_idx = (op >> 3) & 3
            e = _s8(rom[pc+1]) if pc+1 < len(rom) else 0
            target = (pc + 2 + e) & 0xFFFF
            return (f'JR {CC[cc_idx]},${target:04X}', 2, False, [target])

        # LD rp, nn
        if z == 1 and y & 1 == 0:
            rp_idx = y >> 1
            rp_name = HL() if rp_idx == 2 else RP[rp_idx]
            nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
            return (f'LD {rp_name},${nn:04X}', 3, False, [])

        # ADD HL/IX/IY, rp
        if z == 9 and y & 1 == 0:
            rp_idx = y >> 1
            rp_name = HL() if rp_idx == 2 else RP[rp_idx]
            return (f'ADD {HL()},{rp_name}', 1, False, [])

        # INC rp / DEC rp
        if z == 3 and y & 1 == 0:
            rp_idx = y >> 1
            rp_name = HL() if rp_idx == 2 else RP[rp_idx]
            return (f'INC {rp_name}', 1, False, [])
        if z == 11 and y & 1 == 0:
            rp_idx = y >> 1
            rp_name = HL() if rp_idx == 2 else RP[rp_idx]
            return (f'DEC {rp_name}', 1, False, [])

        # INC r
        if z == 4:
            r, extra = ixy_r8(y)
            length = 1 + extra + (1 if (ixy and y == 6) else 0)
            return (f'INC {r}', length, False, [])

        # DEC r
        if z == 5:
            r, extra = ixy_r8(y)
            length = 1 + extra + (1 if (ixy and y == 6) else 0)
            return (f'DEC {r}', length, False, [])

        # LD r, n
        if z == 6:
            r, extra = ixy_r8(y)
            n_off = pc + 1 + extra
            n = rom[n_off] if n_off < len(rom) else 0
            return (f'LD {r},${n:02X}', 2+extra, False, [])

        # LD (nn), HL/IX/IY
        if op == 0x22:
            nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
            return (f'LD ({_fmtA(nn)}),{HL()}', 3, False, [])

        # LD HL/IX/IY, (nn)
        if op == 0x2A:
            nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
            return (f'LD {HL()},({_fmtA(nn)})', 3, False, [])

        # LD (nn), A
        if op == 0x32:
            nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
            return (f'LD ({_fmtA(nn)}),A', 3, False, [])

        # LD A, (nn)
        if op == 0x3A:
            nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
            return (f'LD A,({_fmtA(nn)})', 3, False, [])

    # ── x=1: LD r, r' ───────────────────────────────────────────────────────
    if x == 1:
        if op == 0x76: return ('HALT', 1, True, [])
        dst, d_ex = ixy_r8(y)
        src, s_ex = ixy_r8(z)
        extra = max(d_ex, s_ex)
        return (f'LD {dst},{src}', 1+extra, False, [])

    # ── x=2: ALU A, r ───────────────────────────────────────────────────────
    if x == 2:
        src, s_ex = ixy_r8(z)
        return (f'{ALU_OP[y]}{src}', 1+s_ex, False, [])

    # ── x=3 ─────────────────────────────────────────────────────────────────
    # RET cc
    if x == 3 and z == 0:
        return (f'RET {CC[y]}', 1, False, [])

    # POP rp2
    if x == 3 and z == 1 and y & 1 == 0:
        rp_name = HL() if (y >> 1) == 2 else RP2[y >> 1]
        return (f'POP {rp_name}', 1, False, [])

    # PUSH rp2
    if x == 3 and z == 5 and y & 1 == 0:
        rp_name = HL() if (y >> 1) == 2 else RP2[y >> 1]
        return (f'PUSH {rp_name}', 1, False, [])

    # JP cc, nn
    if x == 3 and z == 2:
        nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
        return (f'JP {CC[y]},${nn:04X}', 3, False, [nn])

    # JP nn
    if op == 0xC3:
        nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
        return (f'JP ${nn:04X}', 3, True, [nn])

    # JP (HL/IX/IY)
    if op == 0xE9:
        return (f'JP ({HL()})', 1, True, [])

    # CALL cc, nn
    if x == 3 and z == 4:
        nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
        return (f'CALL {CC[y]},${nn:04X}', 3, False, [nn])

    # CALL nn
    if op == 0xCD:
        nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
        return (f'CALL ${nn:04X}', 3, False, [nn])

    # RET
    if op == 0xC9: return ('RET', 1, True, [])

    # RST n
    if x == 3 and z == 7:
        vec = y * 8
        return (f'RST ${vec:02X}H', 1, False, [vec])

    # ALU A, n
    if x == 3 and z == 6:
        n = rom[pc+1] if pc+1 < len(rom) else 0
        return (f'{ALU_OP[y]}${n:02X}', 2, False, [])

    # OUT (n), A
    if op == 0xD3:
        n = rom[pc+1] if pc+1 < len(rom) else 0
        return (f'OUT (${n:02X}),A', 2, False, [])

    # IN A, (n)
    if op == 0xDB:
        n = rom[pc+1] if pc+1 < len(rom) else 0
        return (f'IN A,(${n:02X})', 2, False, [])

    # EX (SP), HL/IX/IY
    if op == 0xE3:
        return (f'EX (SP),{HL()}', 1, False, [])

    # EX DE, HL
    if op == 0xEB: return ('EX DE,HL', 1, False, [])

    # EXX
    if op == 0xD9: return ('EXX', 1, False, [])

    # DI / EI
    if op == 0xF3: return ('DI', 1, False, [])
    if op == 0xFB: return ('EI', 1, False, [])

    # LD SP, HL/IX/IY
    if op == 0xF9: return (f'LD SP,{HL()}', 1, False, [])

    # Fallthrough: unknown / data
    return (f'DB ${op:02X}', 1, False, [])


def _decode_ed(rom: bytes, pc: int, op: int) -> tuple[str, bool, list[int], int]:
    """Decode ED-prefixed instruction. Returns (mn, unc, targets, extra_bytes_beyond_2)."""
    y = (op >> 3) & 7
    z = op & 7

    # IN r, (C)
    if z == 0 and 0x40 <= op <= 0x7F:
        r = R8[y]
        return (f'IN {r},(C)', False, [], 0)

    # OUT (C), r
    if z == 1 and 0x40 <= op <= 0x7F:
        r = R8[y]
        return (f'OUT (C),{r}', False, [], 0)

    # SBC HL, rp
    if z == 2 and y & 1 == 0:
        return (f'SBC HL,{RP[y>>1]}', False, [], 0)

    # ADC HL, rp
    if z == 10 and y & 1 == 0:
        return (f'ADC HL,{RP[y>>1]}', False, [], 0)

    # LD (nn), rp  (43/53/63/73)
    if z == 3 and y & 1 == 0:
        rp_idx = y >> 1
        nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
        return (f'LD (${nn:04X}),{RP[rp_idx]}', False, [], 2)

    # LD rp, (nn)  (4B/5B/6B/7B)
    if z == 11 and y & 1 == 0:
        rp_idx = y >> 1
        nn = _rd16(rom, pc+1) if pc+2 < len(rom) else 0
        return (f'LD {RP[rp_idx]},(${nn:04X})', False, [], 2)

    specials = {
        0x44: ('NEG',  False, [], 0),
        0x45: ('RETN', True,  [], 0),
        0x4D: ('RETI', True,  [], 0),
        0x46: ('IM 0', False, [], 0),
        0x56: ('IM 1', False, [], 0),
        0x5E: ('IM 2', False, [], 0),
        0x47: ('LD I,A', False, [], 0),
        0x4F: ('LD R,A', False, [], 0),
        0x57: ('LD A,I', False, [], 0),
        0x5F: ('LD A,R', False, [], 0),
        0x67: ('RLD',  False, [], 0),
        0x6F: ('RRD',  False, [], 0),
        0xA0: ('LDI',  False, [], 0),
        0xA1: ('CPI',  False, [], 0),
        0xA2: ('INI',  False, [], 0),
        0xA3: ('OUTI', False, [], 0),
        0xA8: ('LDD',  False, [], 0),
        0xA9: ('CPD',  False, [], 0),
        0xAA: ('IND',  False, [], 0),
        0xAB: ('OUTD', False, [], 0),
        0xB0: ('LDIR', False, [], 0),
        0xB1: ('CPIR', False, [], 0),
        0xB2: ('INIR', False, [], 0),
        0xB3: ('OTIR', False, [], 0),
        0xB8: ('LDDR', False, [], 0),
        0xB9: ('CPDR', False, [], 0),
        0xBA: ('INDR', False, [], 0),
        0xBB: ('OTDR', False, [], 0),
    }
    if op in specials:
        return specials[op]

    return (f'DB $ED,${op:02X}', False, [], 0)


# ─────────────────────────────────────────────────────────────────────────────
# Recursive disassembler
# ─────────────────────────────────────────────────────────────────────────────
def disassemble(rom: bytes) -> dict[int, tuple[str, int, str]]:
    """
    Recursively disassemble rom starting from all known entry points.
    Returns: addr -> (mnemonic, byte_length, annotation)
    """
    # Entry points: reset, NMI, all RST vectors, INT handler
    entry_points = [0x0000, 0x0008, 0x0010, 0x0018, 0x0020, 0x0028, 0x0030, 0x0038, 0x0066]

    visited: set[int]     = set()
    result:  dict[int, tuple[str, int, str]] = {}
    worklist: deque[int]  = deque(entry_points)

    # Track last YM2203 register selected (for annotation)
    # We'll do a second pass for annotations
    while worklist:
        pc = worklist.popleft()
        if pc < 0 or pc >= ROM_SIZE or pc in visited:
            continue
        visited.add(pc)

        mn, length, is_unc, targets = decode(rom, pc)
        result[pc] = (mn, length, '')   # annotation filled below

        for t in targets:
            if 0 <= t < ROM_SIZE and t not in visited:
                worklist.append(t)

        if not is_unc:
            nxt = pc + length
            if 0 <= nxt < ROM_SIZE and nxt not in visited:
                worklist.append(nxt)

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Annotation pass: detect YM2203 write patterns
# ─────────────────────────────────────────────────────────────────────────────
def annotate(rom: bytes, insns: dict[int, tuple[str, int, str]]) -> dict[int, tuple[str, int, str]]:
    """
    Second pass: add comments to instructions.
    Detects the pattern:
        LD A, $XX          ; select YM register XX
        LD (ym1_addr), A   ; write to YM addr port
        LD A, $YY
        LD (ym1_data), A   ; write data YY
    and annotates accordingly.
    """
    annotated = dict(insns)
    addrs = sorted(insns.keys())
    addr_set = set(addrs)

    def next_addr(a: int) -> int:
        idx = addrs.index(a) + 1
        return addrs[idx] if idx < len(addrs) else -1

    # Track A value for annotation (simple constant propagation)
    a_val: dict[int, int | None] = {}
    for addr in addrs:
        mn, length, _ = insns[addr]
        # LD A, $nn
        if mn.startswith('LD A,$') and len(mn) == 8:
            try:
                a_val[addr] = int(mn[6:], 16)
            except ValueError:
                a_val[addr] = None
        else:
            a_val[addr] = None

    for addr in addrs:
        mn, length, _ = insns[addr]
        ann = ''

        # Detect: CALL ym2203_write pattern — look back for LD BC, $E000/$E002 and LD A, reg
        if mn == 'CALL $00EE' or (mn.startswith('CALL') and 'ym2203_write' in mn):
            # Find preceding LD BC, $E0xx and LD A, $xx
            chip = '?'
            reg_name = '?'
            data_hint = ''
            for prev in reversed([a for a in addrs if a < addr]):
                pm, _, _ = insns[prev]
                if pm == 'LD BC,$E000': chip = '1'; break
                if pm == 'LD BC,$E002': chip = '2'; break
                if '(' in pm or pm.startswith('CALL'): break
            for prev in reversed([a for a in addrs if a < addr]):
                pm, _, _ = insns[prev]
                if pm.startswith('LD A,$') and len(pm) == 8:
                    try:
                        reg = int(pm[6:], 16)
                        reg_name = YM_REG.get(reg, f'REG_${reg:02X}')
                        # SMS/GG OPLL mapping hint
                        if 0x00 <= reg <= 0x0D:
                            data_hint = f' [OPLL: SSG->SN76489 or map to OPLL rhythm]'
                        elif reg == 0x28:
                            data_hint = f' [OPLL: key on/off -> OUT($20+ch),data]'
                        elif 0xA0 <= reg <= 0xB6:
                            data_hint = f' [OPLL: freq/key -> OUT($10+ch)/$20+ch)]'
                        elif 0x30 <= reg <= 0xB6:
                            data_hint = f' [OPLL: instrument params (2-op simplification)]'
                    except ValueError:
                        pass
                    break
            ann = f'; YM2203 #{chip} write: reg={reg_name}{data_hint}'

        # Detect: LD (ym1_addr), A  or  LD (ym2_addr), A
        elif mn in ('LD (ym1_addr),A', 'LD (ym2_addr),A'):
            chip = '1' if 'ym1' in mn else '2'
            # Look backwards for LD A, $nn
            prev = addr
            for _ in range(4):
                prev_addrs = [a for a in addrs if a < prev]
                if not prev_addrs: break
                prev = prev_addrs[-1]
                prev_mn, _, _ = insns[prev]
                if prev_mn.startswith('LD A,$') and len(prev_mn) == 8:
                    try:
                        reg = int(prev_mn[6:], 16)
                        reg_name = YM_REG.get(reg, f'REG_${reg:02X}')
                        opll_note = ''
                        # Suggest OPLL mapping
                        if reg <= 0x0D:
                            opll_note = ' [SMS: OPLL FM ch or SN76489 PSG]'
                        elif reg == 0x28:
                            opll_note = ' [SMS: OPLL key on/off reg $20-$28]'
                        elif 0xA0 <= reg <= 0xB6:
                            opll_note = ' [SMS: map -> OPLL $10-$38]'
                        ann = f'; YM2203 #{chip} addr = {reg_name} (${reg:02X}){opll_note}'
                    except ValueError:
                        pass
                    break
                # Stop if we hit another store instruction
                if '(' in prev_mn:
                    break

        # Detect: LD (ym1_data), A  or  LD (ym2_data), A
        elif mn in ('LD (ym1_data),A', 'LD (ym2_data),A'):
            chip = '1' if 'ym1' in mn else '2'
            ann = f'; YM2203 #{chip} data write'

        # Detect: LD A, (sound_latch)
        elif mn == 'LD A,(sound_latch)':
            ann = '; read audio command from main Z80'

        # Detect: LD A, (mcu_comm)
        elif mn == 'LD A,(mcu_comm)':
            ann = '; read MCU<->audio shared byte'

        # Detect: LD (mcu_comm), A
        elif mn == 'LD (mcu_comm),A':
            ann = '; write MCU<->audio shared byte'

        # Detect interrupt mode settings
        elif mn in ('IM 0', 'IM 1', 'IM 2'):
            ann = '; set interrupt mode'

        # Detect LDIR (often used for data copy / instrument load)
        elif mn == 'LDIR':
            ann = '; block copy: HL->DE, BC bytes'

        annotated[addr] = (mn, length, ann)

    return annotated


# ─────────────────────────────────────────────────────────────────────────────
# Label generation
# ─────────────────────────────────────────────────────────────────────────────
# Per-ROM configuration: dispatch table address and output filename
ROM_CONFIG: dict[str, dict] = {
    'ee2bd2d7': {
        'name':         '1943 / 1943J / 1943U',
        'dispatch_addr': 0x009F,
        'out_file':     'audio_1943_new.asm',
    },
    '25f37957': {
        'name':         '1943kai / 1943mii',
        'dispatch_addr': 0x0DD2,
        'out_file':     'audio_kai_new.asm',
    },
}


def _scan_dispatch_table(rom: bytes, dispatch_addr: int) -> dict[int, str]:
    """Return labels for all valid track data pointers in the dispatch table."""
    track_labels: dict[int, str] = {}
    for cmd in range(0x40):
        addr = dispatch_addr + cmd * 2
        if addr + 1 >= len(rom):
            break
        ptr = rom[addr] | (rom[addr + 1] << 8)
        if ptr >= 0x8000:
            continue  # $FFxx sentinel — no data pointer
        if ptr >= ROM_SIZE:
            continue
        b = rom[ptr]
        if b >> 7:
            track_labels[ptr] = f'sfx_{cmd:02X}_data'
        else:
            track_labels[ptr] = f'bgm_{cmd:02X}_track'
    return track_labels


def _discover_irq_routines(insns: dict[int, tuple[str, int, str]]) -> dict[int, str]:
    """Walk the IRQ handler at $0038 and label the first 3 CALLs as audio routines.

    The IRQ handler structure is consistent across 1943 ROMs:
      CALL cmd_dispatcher   ; reads sound latch, dispatches command
      CALL music_update     ; advances active BGM channels
      CALL sfx_update       ; advances active SFX channels
    """
    role_names = ['cmd_dispatcher', 'music_update', 'sfx_update']
    found: dict[int, str] = {}
    pc = 0x0038
    seen: set[int] = set()

    while len(found) < 3:
        if pc not in insns or pc in seen:
            break
        seen.add(pc)
        mn, length, _ = insns[pc]

        if mn.startswith('CALL $'):
            try:
                target = int(mn[6:], 16)
                found[target] = role_names[len(found)]
            except ValueError:
                pass

        # Stop at unconditional flow break
        if mn in ('RET', 'RETI', 'RETN') or (mn.startswith('JP $') and ',' not in mn):
            break

        pc += length

    return found


def build_labels(rom: bytes, insns: dict[int, tuple[str, int, str]],
                 dispatch_addr: int) -> dict[int, str]:
    """Build a label for every address that is a jump/call target."""
    labels: dict[int, str] = {}

    # Hardware-fixed Z80 entry points — identical across all 1943 ROMs
    fixed = {
        0x0000: 'reset',
        0x0008: 'rst_08',
        0x0010: 'rst_10',
        0x0018: 'rst18_add_a_to_hl',
        0x0020: 'rst20_read_byte_hl_a',
        0x0028: 'rst28_read_word_hl_a2',
        0x0030: 'rst30_dispatch_table_jp',
        0x0038: 'irq_handler',
        0x0066: 'nmi_handler',
        dispatch_addr: 'music_cmd_table',
    }

    # Discover cmd_dispatcher / music_update / sfx_update from the IRQ handler
    labels.update(_discover_irq_routines(insns))

    # Add track data labels from the dispatch table
    labels.update(_scan_dispatch_table(rom, dispatch_addr))

    call_count: dict[int, int]   = {}
    jump_count: dict[int, int]   = {}
    branch_count: dict[int, int] = {}

    for addr in sorted(insns.keys()):
        mn, length, _ = insns[addr]

        target: int | None = None
        for token in mn.split(','):
            token = token.strip()
            if token.startswith('$') and len(token) in (5, 6):
                try:
                    target = int(token[1:], 16)
                except ValueError:
                    pass
        if target is None:
            continue

        if mn.startswith('CALL'):
            call_count[target] = call_count.get(target, 0) + 1
        elif mn.startswith('JP') and not mn.startswith('JP ('):
            jump_count[target] = jump_count.get(target, 0) + 1
        elif mn.startswith('JR') or mn.startswith('DJNZ'):
            branch_count[target] = branch_count.get(target, 0) + 1

    for tgt in sorted(set(list(call_count) + list(jump_count) + list(branch_count))):
        if tgt in labels:
            continue
        if tgt in call_count:
            labels[tgt] = f'sub_{tgt:04X}'
        elif tgt in jump_count:
            labels[tgt] = f'loc_{tgt:04X}'
        else:
            labels[tgt] = f'branch_{tgt:04X}'

    # Fixed names override auto-generated ones
    labels.update(fixed)

    return labels


# ─────────────────────────────────────────────────────────────────────────────
# Output formatter
# ─────────────────────────────────────────────────────────────────────────────
def _build_cmd_map(rom: bytes, dispatch_addr: int) -> list[str]:
    """Build a human-readable command map from the dispatch table."""
    lines = [
        f'; --- Sound Command Map (music_cmd_table @ ${dispatch_addr:04X}) ---',
        '; cmd  type   ptr    label',
    ]
    for cmd in range(0x40):
        addr = dispatch_addr + cmd * 2
        if addr + 1 >= len(rom):
            break
        ptr = rom[addr] | (rom[addr + 1] << 8)
        if ptr >= 0x8000:
            sub = ptr & 0xFF
            desc = {0x00: 'stop BGM ch1', 0x01: 'stop BGM ch2', 0x04: 'NOP'}.get(sub, f'special ${sub:02X}')
            lines.append(f';  ${cmd:02X}  SPEC   $FF{sub:02X}  ({desc})')
        else:
            b = rom[ptr]
            if b >> 7:
                lines.append(f';  ${cmd:02X}  SFX    ${ptr:04X}  sfx_{cmd:02X}_data')
            else:
                lines.append(f';  ${cmd:02X}  BGM    ${ptr:04X}  bgm_{cmd:02X}_track')
    return lines


def emit(rom: bytes, insns: dict[int, tuple[str, int, str]], labels: dict[int, str],
         dispatch_addr: int, rom_crc: str = '', rom_name: str = '') -> list[str]:
    lines: list[str] = []

    lines += [
        '; ============================================================',
        '; 1943 Audio ROM  05.4k  — disassembled by disasm_audio.py',
        '; WLA-DX Z80 syntax',
        ';',
        f'; Source ROM CRC32 : {rom_crc}',
        f'; Used by          : {rom_name}',
        f'; Dispatch table   : ${dispatch_addr:04X}',
        ';',
        '; Original hardware: 2× YM2203 (OPN) + Z80 @ 3.58 MHz',
        '; SMS/GG target:     YM2413 (OPLL) at I/O $F0/$F1',
        ';   Map YM2203 FM ch 1-3  -> OPLL ch 1-3  (4-op -> 2-op, quality loss)',
        ';   Map YM2203 FM ch 4-6  -> OPLL ch 4-6',
        ';   Map YM2203 SSG ch 1-6 -> OPLL ch 7-9 (rhythm) or SN76489',
        '; ============================================================',
        '',
    ]

    lines += _build_cmd_map(rom, dispatch_addr)
    lines.append('')

    lines += [
        '.include "smsgg_defs.inc"   ; define OPLL_ADDR=$F0, OPLL_DATA=$F1, etc.',
        '',
        '.bank 0 slot 0',
        '.org $0000',
        '',
    ]

    # Emit header equ for known RAM variables
    lines += [
        '; --- RAM variables (0xC000-0xC7FF) ---',
        '; (populated as they appear in the disassembly)',
        '; sound_latch   EQU $C800   ; read-only, command from main Z80',
        '; ym1_addr      EQU $E000',
        '; ym1_data      EQU $E001',
        '; ym2_addr      EQU $E002',
        '; ym2_data      EQU $E003',
        '',
    ]

    # Data blocks: addresses NOT in insns
    code_addrs = set(insns.keys())
    all_addrs  = sorted(insns.keys())

    # Build coverage map
    covered: set[int] = set()
    for addr, (mn, length, _) in insns.items():
        for i in range(length):
            covered.add(addr + i)

    pc = 0
    while pc < ROM_SIZE:
        # Emit label if present
        if pc in labels:
            lines.append('')
            lines.append(f'{labels[pc]}:')

        if pc in insns:
            mn, length, ann = insns[pc]
            # Build hex dump comment (up to 4 bytes)
            hex_bytes = ' '.join(f'{rom[pc+i]:02X}' for i in range(min(length, 4)))
            if length > 4:
                hex_bytes += '..'
            ann_str = f'  {ann}' if ann else ''
            # Format: <addr>  <hex>  <mnemonic>  <annotation>
            hex_col  = f'{hex_bytes:<12}'
            mn_col   = f'{mn:<28}'
            addr_col = f'${pc:04X}'
            lines.append(f'    {mn_col} ; {addr_col}  {hex_col}{ann_str}')
            pc += length
        elif pc not in covered:
            # Data byte: collect a run of unvisited bytes
            start = pc
            data_bytes = []
            while pc < ROM_SIZE and pc not in covered and pc not in insns:
                if pc in labels and pc != start:
                    break
                data_bytes.append(rom[pc])
                pc += 1
                if len(data_bytes) >= 16 or (pc in labels and pc != start):
                    break
            # Emit as .db
            hex_str = ','.join(f'${b:02X}' for b in data_bytes)
            lines.append(f'    .db {hex_str:<47} ; ${start:04X}  (data)')
        else:
            pc += 1

    lines.append('')
    lines.append('; === END OF DISASSEMBLY ===')
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# Statistics
# ─────────────────────────────────────────────────────────────────────────────
def print_stats(rom: bytes, insns: dict, labels: dict) -> None:
    covered: set[int] = set()
    for addr, (mn, length, _) in insns.items():
        for i in range(length):
            covered.add(addr + i)

    code_bytes = len(covered)
    data_bytes = ROM_SIZE - code_bytes
    calls  = sum(1 for addr, (mn, *_) in insns.items() if mn.startswith('CALL'))
    jumps  = sum(1 for addr, (mn, *_) in insns.items() if mn.startswith('JP') or mn.startswith('JR'))
    ym_ops = sum(1 for addr, (mn, *_) in insns.items()
                 if any(n in mn for n in ('ym1_addr', 'ym1_data', 'ym2_addr', 'ym2_data'))
                 or ('CALL' in mn and ('$00EE' in mn or 'ym2203_write' in mn)))
    subs   = sum(1 for lbl in labels.values() if lbl.startswith('sub_'))

    print(f'  ROM size:      {ROM_SIZE} bytes ({ROM_SIZE//1024} KiB)')
    print(f'  Code coverage: {code_bytes} bytes ({100*code_bytes//ROM_SIZE}%)')
    print(f'  Data/unknown:  {data_bytes} bytes ({100*data_bytes//ROM_SIZE}%)')
    print(f'  Instructions:  {len(insns)}')
    print(f'  Subroutines:   {subs}')
    print(f'  Jumps/branches:{jumps}')
    print(f'  CALL sites:    {calls}')
    print(f'  YM2203 writes: {ym_ops}')
    print(f'  Labels:        {len(labels)}')


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def load_rom(args) -> tuple[bytes, str]:
    """Load ROM and return (data, crc32_hex). Searches source ZIPs by CRC."""
    import zlib as _zlib

    known_crcs = set(ROM_CONFIG.keys())

    if args.rom:
        data = Path(args.rom).read_bytes()
        crc  = f'{_zlib.crc32(data) & 0xFFFFFFFF:08x}'
        cfg  = ROM_CONFIG.get(crc, {})
        print(f'  Loaded ROM: {args.rom}  CRC={crc}  ({cfg.get("name", "unknown")})')
        return data, crc

    source_zips = [
        Path(args.zip),
        Path('1943.zip'), Path('1943j.zip'), Path('1943u.zip'),
        Path('1943kai.zip'), Path('1943mii.zip'),
    ]
    target_crc = args.crc.lower() if args.crc else None

    for zp in source_zips:
        if not zp.exists():
            continue
        try:
            with zipfile.ZipFile(zp) as zf:
                for info in zf.infolist():
                    data = zf.read(info.filename)
                    crc  = f'{_zlib.crc32(data) & 0xFFFFFFFF:08x}'
                    if target_crc:
                        if crc == target_crc:
                            cfg = ROM_CONFIG.get(crc, {})
                            print(f'  Loaded: {info.filename} from {zp}  CRC={crc}  ({cfg.get("name","unknown")})')
                            return data, crc
                    elif crc in known_crcs:
                        cfg = ROM_CONFIG[crc]
                        print(f'  Loaded: {info.filename} from {zp}  CRC={crc}  ({cfg["name"]})')
                        return data, crc
        except Exception:
            continue

    sys.exit(
        f'ERROR: audio ROM not found in any source ZIP.\n'
        f'  Known CRCs: {list(ROM_CONFIG.keys())}\n'
        f'  Use --crc CRC32 to specify or --rom PATH for raw binary.'
    )


def main():
    parser = argparse.ArgumentParser(description='Z80 disassembler for 1943 audio ROM')
    parser.add_argument('--zip', default='1943.zip',
                        help='Source ZIP file (default: 1943.zip)')
    parser.add_argument('--rom', default='',
                        help='Direct path to raw binary ROM file')
    parser.add_argument('--out', default='',
                        help='Output .asm file (default: auto from ROM CRC)')
    parser.add_argument('--crc', default='',
                        help='CRC32 of the ROM to load (ee2bd2d7=1943, 25f37957=KAI)')
    args = parser.parse_args()

    print('=== disasm_audio.py — 1943 audio ROM Z80 disassembler ===')
    rom, rom_crc = load_rom(args)

    if len(rom) < ROM_SIZE:
        print(f'  WARNING: ROM is {len(rom)} bytes, expected {ROM_SIZE}. Padding with $FF.')
        rom = rom + b'\xff' * (ROM_SIZE - len(rom))

    cfg          = ROM_CONFIG.get(rom_crc, {})
    dispatch_addr = cfg.get('dispatch_addr', 0x0DD2)
    rom_name     = cfg.get('name', 'unknown')
    out_file     = args.out or cfg.get('out_file', f'audio_{rom_crc}.asm')

    print(f'  ROM: {rom_name}  dispatch_table=${dispatch_addr:04X}  -> {out_file}')

    print('  Disassembling...')
    insns = disassemble(rom)

    print('  Annotating YM2203 write patterns...')
    insns = annotate(rom, insns)

    print('  Building labels...')
    labels = build_labels(rom, insns, dispatch_addr)

    print('  Emitting output...')
    lines = emit(rom, insns, labels, dispatch_addr, rom_crc, rom_name)

    out_path = Path(out_file)
    out_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f'  Written: {out_path}  ({len(lines)} lines)')
    print()
    print_stats(rom, insns, labels)
    print()
    print('Next steps:')
    print('  1. Review the .asm — identify driver init, command dispatcher, update loop')
    print('  2. Find instrument tables (sequences of LD (ym1_addr)/LD (ym1_data) pairs)')
    print('  3. Adapt YM2203 register writes to YM2413 OPLL (port $F0/$F1 on SMS/GG)')
    print('  4. Replace sound_latch read with SMS/GG equivalent')


if __name__ == '__main__':
    main()

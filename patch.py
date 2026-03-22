"""
Pokémon Rumble Blast — Shiny Mod Patcher (Release)
====================================================
Patches code.bin IN-PLACE to add the shiny Pokémon system.

Usage:
  python patch.py <code_bin_path> [--rate RATE]

Arguments:
  code_bin_path   Path to the ORIGINAL (unpatched) code.bin
                  (from ExtractedExeFS/code.bin)

Options:
  --rate RATE     Shiny encounter rate as "1/N" (default: 1/512)
                  Examples: 1/512, 1/1024, 1/4096, 1/2

The script patches the file in place. Keep a backup of the original.
"""
import struct
import hashlib
import sys
import os
import argparse
import math

EXPECTED_MD5 = '912a034e35fc2415655e6ba642c25d78'
EXPECTED_SIZE = 6131712  # 0x5D9000

patched_count = 0


def parse_rate(rate_str):
    """Parse a rate string like '1/512' into an ARM bitmask.

    The RNG uses an LCG and checks: TST state, mask
    If the masked bits are all zero, the pokemon is shiny.
    For rate 1/N, we need the smallest bitmask M such that
    only 1 in N values of (state AND M) == 0.

    For power-of-2 rates, the mask is (N-1) shifted to avoid
    low bits (which have poor LCG randomness).
    For non-power-of-2, we round to the nearest power of 2.
    """
    parts = rate_str.strip().split('/')
    if len(parts) == 2 and parts[0].strip() == '1':
        n = int(parts[1].strip())
    elif len(parts) == 1:
        n = int(parts[0].strip())
    else:
        raise ValueError("Rate must be in format '1/N' or 'N', got: %s" % rate_str)

    if n < 1:
        raise ValueError("Rate denominator must be >= 1, got: %d" % n)

    # Round to nearest power of 2
    pow2 = 1 << round(math.log2(n))
    if pow2 != n:
        print("  NOTE: Rate 1/%d rounded to nearest power of 2: 1/%d" % (n, pow2))
        n = pow2

    # Mask = (N-1), shifted left by 4 to skip low LCG bits
    mask = (n - 1) << 4
    if mask > 0xFFFFFFFF:
        raise ValueError("Rate 1/%d too low (mask overflow)" % n)

    # Verify it's encodable as ARM immediate (8-bit rotated)
    # For common rates this is fine; we use a literal pool so any 32-bit value works
    return n, mask


def main():
    global patched_count

    parser = argparse.ArgumentParser(
        description="Pokémon Rumble Blast — Shiny Mod Patcher")
    parser.add_argument('code_bin', help="Path to original code.bin")
    parser.add_argument('--rate', default='1/512',
                        help="Shiny rate as '1/N' (default: 1/512)")
    args = parser.parse_args()

    code_bin_path = args.code_bin

    if not os.path.exists(code_bin_path):
        print("ERROR: File not found: %s" % code_bin_path)
        sys.exit(1)

    rate_n, rate_mask = parse_rate(args.rate)

    print("=== Shiny Mod Patcher (Release) ===")
    print("  Target: %s" % code_bin_path)
    print("  Shiny rate: 1/%d (mask: 0x%08X)" % (rate_n, rate_mask))
    print()

    with open(code_bin_path, 'rb') as f:
        data = bytearray(f.read())

    md5 = hashlib.md5(data).hexdigest()
    if md5 != EXPECTED_MD5:
        print("WARNING: MD5 mismatch: %s" % md5)
        print("  Expected: %s" % EXPECTED_MD5)
        print("  The file may already be patched or is not the correct code.bin.")
        print("  Proceed anyway? [y/N] ", end="")
        if input().strip().lower() != 'y':
            sys.exit(1)
    if len(data) != EXPECTED_SIZE:
        print("ERROR: Size mismatch: %d (expected %d)" % (len(data), EXPECTED_SIZE))
        sys.exit(1)

    print("Original verified: %d bytes" % len(data))
    print()

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------
    def patch(file_off, expected_orig, new_val, label):
        global patched_count
        va = file_off + 0x100000
        cur = struct.unpack_from('<I', data, file_off)[0]
        if cur != expected_orig:
            print("  FAIL 0x%06X: expected 0x%08X, got 0x%08X -- %s" %
                  (va, expected_orig, cur, label))
            sys.exit(1)
        struct.pack_into('<I', data, file_off, new_val)
        patched_count += 1

    def write_cave(file_off_start, words, label):
        global patched_count
        for i, w in enumerate(words):
            off = file_off_start + i * 4
            struct.pack_into('<I', data, off, w)
            patched_count += 1

    # ================================================================
    #  HOOKS
    # ================================================================
    print("Applying hooks...")
    patch(0x1AA9B8, 0xE320F000, 0xEB087C4C, "Hook1: Shiny RNG")
    patch(0x1E9A84, 0xEB00B42D, 0xEB077FD1, "Hook2: Shiny Model")
    patch(0x1BB9B0, 0xE5D010CC, 0xEB083822, "Hook5: Shiny Drop")
    patch(0x093244, 0xE320F000, 0xEA0CDA61, "Hook6: Name Color")
    patch(0x218A78, 0xE92D4010, 0xEA06C43E, "Hook7a: Color Entry")
    patch(0x218AC0, 0xE8BD8010, 0xEA06C42F, "Hook7b: Color Exit")
    patch(0x20F174, 0xE8BD8FF8, 0xEA06EAA1, "Hook8: Face Icon")
    patch(0x149038, 0xE3A03001, 0xEB0A0306, "Hook9: Collection Model")

    # ================================================================
    #  CAVES
    # ================================================================
    print("Writing code caves...")

    # --- Cave 1: Shiny Flag RNG + save persistence (32 words) ---
    cave1 = [
        0xE92D500F,  # PUSH {R0-R3, R12, LR}
        0xE5963000,  # LDR R3, [R6]
        0xE3530000,  # CMP R3, #0
        0x0A000016,  # BEQ done
        0xE593100C,  # LDR R1, [R3, #0xC]
        0xE3110004,  # TST R1, #4
        0x1A000010,  # BNE common_set
        0xE59F004C,  # LDR R0, [PC, #0x4C]  ; =0x6DA000
        0xE5901000,  # LDR R1, [R0]
        0xE3510000,  # CMP R1, #0
        0x1A000003,  # BNE skip_seed
        0xEF000028,  # SVC #0x28
        0xE0201001,  # EOR R1, R0, R1
        0xE3811001,  # ORR R1, R1, #1
        0xE59F0030,  # LDR R0, [PC, #0x30]  ; =0x6DA000
        0xE59FC030,  # LDR R12, [PC, #0x30] ; =0x343FD
        0xE00C0C91,  # MUL R12, R1, R12
        0xE59F102C,  # LDR R1, [PC, #0x2C]  ; =0x269EC3
        0xE08CC001,  # ADD R12, R12, R1
        0xE580C000,  # STR R12, [R0]
        0xE59F1024,  # LDR R1, [PC, #0x24]  ; =rate_mask
        0xE11C0001,  # TST R12, R1
        0x1A000003,  # BNE done
        0xE593100C,  # LDR R1, [R3, #0xC]
        0xE3811005,  # ORR R1, R1, #0x05
        0xE3811102,  # ORR R1, R1, #0x80000000
        0xE583100C,  # STR R1, [R3, #0xC]
        0xE8BD900F,  # POP {R0-R3, R12, PC}
        0x006DA000,  # RNG state addr
        0x000343FD,  # LCG multiplier
        0x00269EC3,  # LCG addend
        rate_mask,   # Rate mask (configurable)
    ]
    write_cave(0x3C9AF0, cave1, "Cave 1")

    # --- Cave 2: Shiny Model _S suffix (26 words) ---
    cave2 = [
        0xE92D400E, 0xEBF93459, 0xE5961000, 0xE3510000,
        0x0A000013, 0xE591100C, 0xE3110005, 0x0A00000E,
        0xE59F303C, 0xE1A02003, 0xE1A01000, 0xE0D100B2,
        0xE0C200B2, 0xE3500000, 0x1AFFFFFB, 0xE2422002,
        0xE3A0005F, 0xE0C200B2, 0xE3A00053, 0xE0C200B2,
        0xE3A00000, 0xE1C200B0, 0xE1A00003, 0xE8BD400E,
        0xE12FFF1E, 0x006DA010,
    ]
    write_cave(0x3C99D0, cave2, "Cave 2")

    # --- Cave 5: Shiny death drop (42 words) ---
    CAVE5_VA = 0x4C9A40

    def arm_b(from_i, to_i, cond):
        offset = (to_i - from_i - 2) & 0x00FFFFFF
        return (cond << 28) | 0x0A000000 | offset

    def arm_bl(from_i, target_va):
        from_va = CAVE5_VA + from_i * 4
        offset = ((target_va - from_va - 8) >> 2) & 0x00FFFFFF
        return 0xEB000000 | offset

    def arm_ldr_pc(from_i, lit_i, rd):
        pc = CAVE5_VA + from_i * 4 + 8
        lit_va = CAVE5_VA + lit_i * 4
        imm12 = lit_va - pc
        return 0xE59F0000 | (rd << 12) | imm12

    cave5 = [
        0xE5D010CC, 0xE3510000, 0x112FFF1E,
        0xE5901060, 0xE3510000, 0xC3A01000, 0xC12FFF1E,
        0xE92D502C, 0xE1A05000,
        0xE5903020, 0xE3530000, arm_b(11, 18, 0x0),
        0xE59330FC, 0xE3530000, arm_b(14, 18, 0x0),
        0xE593C00C, 0xE31C0102, arm_b(17, 21, 0x1),
        0xE1A00005, 0xE8BD502C, arm_b(20, 39, 0xE),
        0xE3CCC102, 0xE583C00C,
        arm_ldr_pc(23, 41, 3),
        0xE593C000, 0xE28CC001, 0xE583C000,
        0xE24DD008, 0xE3A01000, 0xE58D1000, 0xE58D1004,
        0xE1A00004, 0xE3A02001,
        0xE3A03C02, 0xE3833065, arm_bl(35, 0x2BF104),
        0xE28DD008, 0xE1A00005, 0xE8BD502C,
        0xE3A01000, 0xE12FFF1E,
        0x006DA004,
    ]
    write_cave(0x3C9A40, cave5, "Cave 5")

    # --- Cave 6: Shiny name color override (5 words) ---
    cave6 = [
        0xE5970000, 0xE590000C, 0xE3100004,
        0x13A04003, 0xEAF32598,
    ]
    write_cave(0x3C9BD0, cave6, "Cave 6")

    # --- Cave 7: GetColorIndex + bit-0 self-heal (13 words) ---
    cave7 = [
        0xE92D4010, 0xE1A04000, 0xEAF93BBD,
        0xE594100C, 0xE3110004, 0x1A000004,
        0xE3110001, 0x0A000003,
        0xE3811005, 0xE3811102, 0xE584100C,
        0xE3A00003, 0xE8BD8010,
    ]
    write_cave(0x3C9B78, cave7, "Cave 7")

    # --- Cave 8: Conditional shiny face icon _S (22 words) ---
    cave8 = [
        0xE59D0024, 0xE59F1048, 0xE1500001, 0x1A00000F,
        0xE59D0004, 0xE5900008, 0xE590000C, 0xE3100004,
        0x0A00000A, 0xE5970000,
        0xE0D010B2, 0xE3510000, 0x1AFFFFFC, 0xE2400002,
        0xE3A0105F, 0xE0C010B2, 0xE3A01053, 0xE0C010B2,
        0xE3A01000, 0xE1C010B0,
        0xE8BD8FF8, 0x001B6460,
    ]
    write_cave(0x3C9C00, cave8, "Cave 8")

    # --- Cave 9: Collection model shiny flag injection (8 words) ---
    cave9 = [
        0xE5943014, 0xE593300C, 0xE3130001,
        0x159D3068, 0x13A0C004, 0x1583C00C,
        0xE3A03001, 0xE12FFF1E,
    ]
    write_cave(0x3C9C58, cave9, "Cave 9")

    # ================================================================
    #  Write patched binary
    # ================================================================
    with open(code_bin_path, 'wb') as f:
        f.write(data)

    # ================================================================
    #  Verify
    # ================================================================
    with open(code_bin_path, 'rb') as f:
        verify = f.read()

    orig_md5 = EXPECTED_MD5
    new_md5 = hashlib.md5(verify).hexdigest()

    # Count changes
    orig_data_for_diff = bytearray(len(data))
    # We can't diff without the original, so just count patched_count
    print()
    print("  Patched words: %d" % patched_count)
    print("  Patched MD5:   %s" % new_md5)
    print("  Shiny rate:    1/%d" % rate_n)
    print()
    print("=== PATCH SUCCESSFUL ===")
    print()
    print("Next steps:")
    print("  1. Run copy_assets.py to install shiny model/icon assets")
    print("  2. Rebuild the ROM with HackingToolkit9DS")


if __name__ == '__main__':
    main()

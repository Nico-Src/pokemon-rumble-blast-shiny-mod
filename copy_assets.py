"""
Pokémon Rumble Blast — Shiny Mod Asset Installer (Release)
===========================================================
Copies shiny variant assets into the extracted RomFS directory.

Usage:
  python copy_assets.py <romfs_dir>

Arguments:
  romfs_dir   Path to the ExtractedRomFS directory
              (e.g., rom/ExtractedRomFS)

Assets copied:
  - title2d.arc.cx, title2d.US_English.arc.cx  →  <romfs>/
  - pii/*_S.bcres.cx (shiny 3D models)         →  <romfs>/pii/
  - pokeicon/face/*_S.arc (shiny face icons)    →  <romfs>/pokeicon/face/
"""
import os
import sys
import shutil
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets')


def copy_files(src_dir, dst_dir, pattern_desc):
    """Copy all files from src_dir to dst_dir. Returns count of files copied."""
    if not os.path.isdir(src_dir):
        print("  SKIP: Source not found: %s" % src_dir)
        return 0

    if not os.path.isdir(dst_dir):
        print("  ERROR: Destination not found: %s" % dst_dir)
        print("         Ensure the RomFS is fully extracted.")
        return 0

    count = 0
    for name in sorted(os.listdir(src_dir)):
        src = os.path.join(src_dir, name)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dst_dir, name)
        shutil.copy2(src, dst)
        print("    %s" % name)
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Pokémon Rumble Blast — Shiny Mod Asset Installer")
    parser.add_argument('romfs_dir', help="Path to ExtractedRomFS directory")
    args = parser.parse_args()

    romfs = args.romfs_dir

    if not os.path.isdir(romfs):
        print("ERROR: Directory not found: %s" % romfs)
        sys.exit(1)

    print("=== Shiny Mod Asset Installer ===")
    print("  RomFS: %s" % os.path.abspath(romfs))
    print()

    total = 0

    # --- title2d files (root of RomFS) ---
    print("[title2d]")
    for name in ['title2d.arc.cx', 'title2d.US_English.arc.cx']:
        src = os.path.join(ASSETS_DIR, name)
        if os.path.isfile(src):
            dst = os.path.join(romfs, name)
            shutil.copy2(src, dst)
            print("    %s" % name)
            total += 1
        else:
            print("  SKIP: %s not found in assets" % name)
    print()

    # --- pii models ---
    print("[pii] Shiny 3D models")
    pii_src = os.path.join(ASSETS_DIR, 'pii')
    pii_dst = os.path.join(romfs, 'pii')
    total += copy_files(pii_src, pii_dst, "pii models")
    print()

    # --- pokeicon face icons ---
    print("[pokeicon/face] Shiny face icons")
    icon_src = os.path.join(ASSETS_DIR, 'pokeicon', 'face')
    icon_dst = os.path.join(romfs, 'pokeicon', 'face')
    total += copy_files(icon_src, icon_dst, "face icons")
    print()

    print("=== %d files copied ===" % total)
    print()
    print("Next steps:")
    print("  1. Rebuild the ROM with HackingToolkit9DS")


if __name__ == '__main__':
    main()

# Important Addresses & Memory Map

Key addresses and memory regions in Pokémon Rumble Blast's `code.bin`.

## Binary Layout

| Property | Value |
|----------|-------|
| File size | 6,131,712 bytes (`0x5D9000`) |
| Original MD5 | `912a034e35fc2415655e6ba642c25d78` |
| VA mapping | `VA = file_offset + 0x100000` |
| Architecture | ARM11 (ARMv6, little-endian) |

## Code Cave Region

Unused region in the binary repurposed for mod code.

| Range (file) | Range (VA) | Size | Usage |
|--------------|------------|------|-------|
| `0x3C9960 – 0x3CA000` | `0x4C9960 – 0x4CA000` | 1696 bytes | All 7 code caves |

### Cave Addresses

| Cave | File Offset | VA | Size |
|------|-------------|-----|------|
| Cave 1 | `0x3C9AF0` | `0x4C9AF0` | 128 bytes (32 words) |
| Cave 2 | `0x3C99D0` | `0x4C99D0` | 104 bytes (26 words) |
| Cave 5 | `0x3C9A40` | `0x4C9A40` | 168 bytes (42 words) |
| Cave 6 | `0x3C9BD0` | `0x4C9BD0` | 20 bytes (5 words) |
| Cave 7 | `0x3C9B78` | `0x4C9B78` | 52 bytes (13 words) |
| Cave 8 | `0x3C9C00` | `0x4C9C00` | 88 bytes (22 words) |
| Cave 9 | `0x3C9C58` | `0x4C9C58` | 32 bytes (8 words) |

## BSS Variables (Mod)

Variables stored in the BSS section used by the mod at runtime.

| VA | Size | Purpose | Used By |
|----|------|---------|---------|
| `0x6DA000` | 4 bytes | RNG state (LCG) | Cave 1 |
| `0x6DA004` | 4 bytes | Shiny drop counter | Cave 5 |
| `0x6DA010` | 64 bytes | Shiny name buffer (UTF-16LE) | Cave 2 |

## BSS Variables (Game)

Known game-owned BSS addresses discovered during reverse engineering.

| VA | Purpose | Notes |
|----|---------|-------|
| `0x7CB458` | Entity container root pointer | Used by CTRPF scan to navigate entity list |

## Entity Container Navigation

Pointer chain to reach the entity linked list at runtime:

```
*(0x7CB458) → sub_context
  [+0x20]   → sub2
    [+0x14] → entity_container
      [+0x8C] → first record pointer (linked list head)
      [+0x40] → record array base
```

Each record is 16 bytes:

| Offset | Type | Description |
|--------|------|-------------|
| `+0x00` | u32 | Flags |
| `+0x04` | u16 | Next index (1-based, low 16 bits; 0 = end) |
| `+0x08` | ptr | Entity raw pointer |
| `+0x0C` | u32 | Unknown |

Next record: `array_base + (next_index - 1) * 16`

## Data Tables

| VA | File Offset | Description |
|----|-------------|-------------|
| `0x609988` | `0x509988` | Species name table (700 entries, UTF-16LE pointers) |
| `0x4F68AC` | `0x3F68AC` | Species data structs (0x3C bytes each). Name ptrs at `+0x2C` (male) and `+0x30` (female). |
| `0x29A850` | — | `CreatePokemonFromTable` entries (0x18 bytes each) |
| `0x2C871C` | — | Scripted encounter definitions (0x2C bytes each) |

## Key String Addresses

Format strings used by the model/asset loading system:

| VA (approx) | String | Used By |
|--------------|--------|---------|
| `0x2E9CF8` | `rom:/pii/` | `LoadPokemonModel` path prefix |
| `0x2E9D0C` | `_v1` | Alternate model suffix (bit 0 flag) |
| `0x2E9D14` | `_v%d` | Variant format string |
| `0x2E9D1E` | `.bcres` | Model file extension |
| `0x2E9D32` | `_P` | Unknown suffix (possibly player?) |

## Hook Points

Original instructions at each hook location:

| VA | File Offset | Original Bytes | Original Instruction | Function |
|----|-------------|----------------|---------------------|----------|
| `0x2AA9B8` | `0x1AA9B8` | `E320F000` | `NOP` | `CreatePokemonEntity` wrapper |
| `0x2E9A84` | `0x1E9A84` | `EB00B42D` | `BL 0x316B40` | `LoadPokemonModel` |
| `0x2BB9B0` | `0x1BB9B0` | `E5D010CC` | `LDRB R1,[R0,#0xCC]` | Death handler |
| `0x193244` | `0x093244` | `E320F000` | `NOP` | Field name display |
| `0x318A78` | `0x218A78` | `E92D4010` | `PUSH {R4,LR}` | `GetColorIndex` entry |
| `0x318AC0` | `0x218AC0` | `E8BD8010` | `POP {R4,PC}` | `GetColorIndex` exit |
| `0x30F174` | `0x20F174` | `E8BD8FF8` | `POP {R3-R11,PC}` | `GetIconFilename_Wide` return |
| `0x249038` | `0x149038` | `E3A03001` | `MOV R3,#1` | Collection detail function |

## Entity Structure Sizes

| Structure | Size | Allocator |
|-----------|------|-----------|
| Inner Pokémon struct | 0x70 (112 bytes) | `AllocateObject(0x70)` in `PokemonFactory` |
| Entity wrapper | 0x1A4 (420 bytes) | `CreateGameEntity` |
| HpBar struct | 0x1F8 (504 bytes) | `CreatePlayerHpBar` |
| Secondary data (sd) | ≥0x360 bytes | Field layout confirmed via offset analysis |
| Ref-count block | 0x10 (16 bytes) | `CreateRefCountBlock` |
| Animation controller | 0x7C (124 bytes) | `CreateAnimController` |
| Species data struct | 0x3C (60 bytes) | ROM data table |
| Spawn table entry | 0x48 (72 bytes) | Per-area, 5 species/form slots each |

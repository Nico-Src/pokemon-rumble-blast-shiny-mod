# Hooks & Code Caves

Technical documentation for all code patches applied to `code.bin` by the shiny mod.

All addresses use the format: **VA** (Virtual Address) = file offset + `0x100000`.

## Hooks

Hooks replace a single instruction at a known address with a branch (B or BL) to a code cave.

| Hook | VA | Original Instruction | Replacement | Target |
|------|----|----------------------|-------------|--------|
| Hook 1 | `0x2AA9B8` | `NOP` | `BL 0x4C9AF0` | Cave 1: Shiny RNG |
| Hook 2 | `0x2E9A84` | `BL 0x316B40` | `BL 0x4C99D0` | Cave 2: Shiny Model |
| Hook 5 | `0x2BB9B0` | `LDRB R1,[R0,#0xCC]` | `BL 0x4C9A40` | Cave 5: Shiny Drop |
| Hook 6 | `0x193244` | `NOP` | `B 0x4C9BD0` | Cave 6: Name Color |
| Hook 7a | `0x318A78` | `PUSH {R4,LR}` | `B 0x4C9B78` | Cave 7: Color Entry |
| Hook 7b | `0x318AC0` | `POP {R4,PC}` | `B 0x4C9B84` | Cave 7: Color Exit |
| Hook 8 | `0x30F174` | `POP {R3-R11,PC}` | `B 0x4C9C00` | Cave 8: Face Icon |
| Hook 9 | `0x249038` | `MOV R3,#1` | `BL 0x4C9C58` | Cave 9: Collection Model |

## Code Caves

Code caves are written into unused space in the binary at file offsets `0x3C9960`–`0x3CA000` (1696 bytes).

### Cave 1 — Shiny Flag RNG + Save Persistence

| Field | Value |
|-------|-------|
| Address | `0x4C9AF0` (file `0x3C9AF0`) |
| Size | 32 words (128 bytes) |
| Hook | Hook 1 at `0x2AA9B8` inside `CreatePokemonEntity` wrapper (`0x2AA8B0`) |
| Registers | R6 = SmartPtr output, R3 = inner_pokemon pointer |

**Purpose:** Assigns shiny status to newly spawned Pokémon using an LCG random number generator. Also preserves shiny status for Pokémon loaded from save data.

**Flow:**
1. Dereference SmartPtr R6 to get inner_pokemon pointer
2. Check if `+0xC` bit 2 is already set (saved shiny) — if so, skip RNG
3. On first call, seed RNG from `svcGetSystemTick` (SVC 0x28)
4. Run LCG step: `state = state * 0x343FD + 0x269EC3`
5. Check `state & rate_mask` — if zero, mark as shiny
6. Set flags: `+0xC |= 0x80000005` (bit 0 sparkle + bit 2 shiny + bit 31 one-shot)

**Rate mask** (word 31): Controls shiny probability. `0x00001FF0` = 1/512 default.

### Cave 2 — Shiny Model `_S` Suffix

| Field | Value |
|-------|-------|
| Address | `0x4C99D0` (file `0x3C99D0`) |
| Size | 26 words (104 bytes) |
| Hook | Hook 2 at `0x2E9A84` inside `LoadPokemonModel` (`0x2E9960`) |
| Registers | R6 = pokemonSP, R0 = species name string (from original `GetPokemonModelName`) |

**Purpose:** Appends `_S` to the model name for shiny Pokémon so the game loads alternate texture files (e.g. `MINEZUMI_S.bcres` instead of `MINEZUMI.bcres`).

**Flow:**
1. Call original `GetPokemonModelName` (`0x316B40`)
2. Dereference R6 to get inner_pokemon, read `+0xC` flags
3. Test bits 0 or 2 (`TST R1, #5`) — either indicates shiny
4. Copy name to BSS buffer at `0x6DA010`, append `_S\0`
5. Return pointer to modified name

### Cave 5 — Shiny Death Drop

| Field | Value |
|-------|-------|
| Address | `0x4C9A40` (file `0x3C9A40`) |
| Size | 42 words (168 bytes) |
| Hook | Hook 5 at `0x2BB9B0` inside death handler (`0x2BB928`) |
| Registers | R0 = sd (secondary data), R4 = entity wrapper |

**Purpose:** When a shiny Pokémon dies, forces a guaranteed toy drop by calling `CreateDrop` directly, bypassing the game's normal CC gate system.

**Flow:**
1. Execute displaced `LDRB R1, [R0, #0xCC]` — if CC != 0, return (game handles)
2. Check `sd[+0x60]` (HP) — if alive, return CC=0
3. Follow 3-hop pointer chain: `sd[+0x20]` → `container_entity[+0xFC]` → `inner_pokemon[+0xC]`
4. Test bit 31 (one-shot flag) — if not set, not shiny
5. Clear bit 31 (prevents repeat drops), keep bit 2 (model stays shiny)
6. Call `CreateDrop(entity, 0, 1, 0x265, 0, 0)` at `0x2BF104`
7. Return CC=0 to skip game's normal drop path

### Cave 6 — Shiny Name Color (Field)

| Field | Value |
|-------|-------|
| Address | `0x4C9BD0` (file `0x3C9BD0`) |
| Size | 5 words (20 bytes) |
| Hook | Hook 6 at `0x193244` (NOP convergence point in field name display `0x192F44`) |
| Registers | R7 = pokemon data context, R4 = color index |

**Purpose:** Overrides the field HUD name color for shiny Pokémon to the RARE (gold) color.

**Flow:**
1. Load inner_pokemon via `[R7]`, read flags at `+0xC`
2. Test bit 2 — if set, override R4 to 3 (PIINAME_RARE)
3. Branch to `0x193248` (color application)

**Color indices:** 0 = Normal, 2 = Prefixed, 3 = Rare (gold), 4 = Mine

### Cave 7 — GetColorIndex Wrapper + Self-Heal

| Field | Value |
|-------|-------|
| Address | `0x4C9B78` (file `0x3C9B78`) |
| Size | 13 words (52 bytes) |
| Hooks | Hook 7a at `0x318A78` (entry), Hook 7b at `0x318AC0` (exit) |
| Registers | R0 = pokemon data pointer, R4 = saved pokemon pointer |

**Purpose:** Wraps the `GetColorIndex` utility function to override the color for shiny Pokémon on all UI screens. Also performs self-healing of shiny flags that may be partially lost during save/load.

**Flow (entry):**
1. Execute displaced `PUSH {R4, LR}`
2. Save pokemon pointer to R4
3. Jump to original function body at `0x318A7C`

**Flow (exit):**
1. Read `[R4, +0xC]` flags
2. If bit 2 set → return color index 3 (Rare)
3. If bit 0 set but bit 2 not → self-heal: set bits 0+2+31, return 3
4. Otherwise return original result

**Self-heal:** After save/load, bit 2 may be lost but bit 0 survives (only our mod sets bit 0 in inner_pokemon). This restores the full shiny flag set.

**Callers:** `0x18B17C`, `0x18BE80`, `0x1B63F4` (collection screen, party display, info panels)

### Cave 8 — Shiny Face Icon `_S` Suffix

| Field | Value |
|-------|-------|
| Address | `0x4C9C00` (file `0x3C9C00`) |
| Size | 22 words (88 bytes) |
| Hook | Hook 8 at `0x30F174` (`GetIconFilename_Wide` return) |
| Registers | R7 = C++ string object, SP+0x24 = saved LR, SP+0x04 = caller's R4 |

**Purpose:** Conditionally appends `_S` to face icon filenames for shiny Pokémon, allowing shiny-specific icons to load from `rom:/pokeicon/face/`.

**Flow:**
1. Check saved LR against known caller address (`0x1B6460`)
2. If not the instance-level caller → execute displaced return (skip)
3. Read `caller_R4[+8]` → inner_pokemon → `[+0xC]` flags
4. Test bit 2 — if not shiny, skip
5. Find null terminator in wide string, append `_S\0`
6. Execute displaced `POP {R3-R11, PC}`

### Cave 9 — Collection Model Shiny Flag Injection

| Field | Value |
|-------|-------|
| Address | `0x4C9C58` (file `0x3C9C58`) |
| Size | 8 words (32 bytes) |
| Hook | Hook 9 at `0x249038` in collection detail function (`0x248978`) |
| Registers | R4 = iterator node, SP+0x68 = pokemonSP data pointer |

**Purpose:** Injects the shiny flag from the collection entry into the temporary 0x70 pokemonSP struct before `LoadPokemonModel` runs.

**Flow:**
1. Load collection data via `[R4, +0x14]`, read collection flags at `+0xC`
2. Test bit 0 (sparkle indicator for saved shinies)
3. If set, load pokemonSP data from `[SP, +0x68]` and write bit 2 to `+0xC`
4. Execute displaced `MOV R3, #1`
5. Return

**Note:** This cave addresses the collection screen's 3D model not showing as shiny. The 0x70 temporary struct always has `+0xC` zeroed at construction, so the shiny flag must be injected before model loading.

## Memory Layout

### Code cave region

```
File 0x3C9960 – 0x3CA000 (VA 0x4C9960 – 0x4CA000)
Total: 1696 bytes

0x4C99D0  Cave 2  (104 bytes)
0x4C9A40  Cave 5  (168 bytes)
0x4C9AF0  Cave 1  (128 bytes)
0x4C9B78  Cave 7  (52 bytes)
0x4C9BD0  Cave 6  (20 bytes)
0x4C9C00  Cave 8  (88 bytes)
0x4C9C58  Cave 9  (32 bytes)
```

### BSS variables

| VA | Size | Purpose |
|----|------|---------|
| `0x6DA000` | 4 bytes | RNG state (LCG, used by Cave 1) |
| `0x6DA004` | 4 bytes | Shiny drop counter (Cave 5 increments on each shiny drop) |
| `0x6DA010` | 64 bytes | Shiny name buffer (UTF-16LE, used by Cave 2 for `_S` suffix) |

# Pokémon Instance Structure

The inner Pokémon data struct used by Pokémon Rumble Blast. Total size: **0x70 (112 bytes)**.

Allocated by `PokemonFactory` (`0x1EC920`) via `AllocateObject(0x70)`.  
Initialized by `PokemonBaseConstructor` (`0x0C0D0C`) → `PokemonInitializer` (`0x0C0AF0`).

## Access Pattern

Pokémon data is accessed through a **smart pointer passed by stack reference**:

```
&stack_var → raw_pokemon_ptr → Inner Pokémon Struct (0x70 bytes)
             control_block_ptr
```

The caller copies the smart pointer from `entity[+0xFC/+0x100]` into stack locals, then passes `&stack_var` as the parameter. Dereference: `*param = raw pointer`, `*(param+1) = ref-count block`.

## Struct Layout

| Offset | Size | Init | Type | Description |
|--------|------|------|------|-------------|
| `+0x00` | 4 | vtable | ptr | Vtable pointer |
| `+0x04` | 4 | 0 | ptr | Sub-object pointer (self-referencing in some cases) |
| `+0x08` | 4 | 0 | — | Unknown |
| **`+0x0C`** | **4** | **0** | **uint** | **Flags bitfield** (see below) |
| `+0x10` | 4 | SP.data | ptr | Template species smart pointer — data |
| `+0x14` | 4 | SP.ctrl | ptr | Template species smart pointer — control block |
| `+0x18` | 4 | param | ptr | Factory-provided vtable/template object |
| `+0x1C` | 4 | param | uint | Species template flags (from `speciesData+0x0C`). Read-only metadata. |
| `+0x20` | 4 | 0 | — | Unknown |
| **`+0x24`** | **4** | **param** | **uint** | **Species/Identity ID** — primary key. Max `0x11C` (284). |
| `+0x28` | 2 | 0 | ushort | Move slot 0 |
| `+0x2A` | 2 | 0 | ushort | Move slot 1 |
| `+0x2C` | 2 | 0 | ushort | Move slot 2 |
| `+0x2E` | 2 | 0 | ushort | Move slot 3 |
| **`+0x30`** | **1** | **classify** | **char** | **Type classification** (0/1/2). Derived from `+0x24` via 3 species check functions. |
| **`+0x31`** | **1** | **0** | **byte** | **Prefix/trait byte**. 0=none, non-zero=trait ID. Read by `GetColorIndex` and field name display. |
| **`+0x32`** | **1** | **0** | **byte** | **Variant index**. Model variant suffix (`_v%d` in `LoadPokemonModel`). |
| `+0x33` | 1 | 0 | byte | Second variant field. Dirty-tracked like `+0x32`. |
| `+0x34` | 1 | 0 | byte | Unknown |
| `+0x35` | 1 | 0 | byte | Unknown |
| `+0x36` | 1 | 0 | byte | Unknown |
| `+0x37` | 1 | 0xFF | byte | Marker byte (unassigned team/slot?) |
| `+0x38` | 4 | 0 | — | Unknown |
| `+0x3C` | 4 | 0 | — | Unknown |
| `+0x40` | 4 | 1 | int | Unknown (initialized to 1) |
| `+0x44` | 4 | 1 | int | Unknown (initialized to 1) |
| `+0x48` | 4 | 1 | int | Unknown (initialized to 1) |
| `+0x4C` | 4 | 0 | — | Unknown |
| `+0x50` | 4 | 0 | — | Unknown |
| `+0x54` | 4 | — | — | Gap (not written by constructor) |
| `+0x58` | 4 | 0 | — | Unknown |
| `+0x5C` | 4 | 0 | — | Unknown |
| `+0x60` | 4 | 0 | — | Unknown |
| `+0x64` | 4 | 0 | — | Unknown |
| `+0x68` | 4 | 0 | — | Unknown |
| `+0x6C` | 4 | — | — | Gap (not written by constructor) |

## Flags Bitfield (`+0x0C`)

Constructor sets `+0xC = 0`. All bits are set post-construction via ORR operations.

### Bit Map

| Bit | Mask | Name | Origin | Description |
|-----|------|------|--------|-------------|
| 0 | `0x00000001` | sparkle | **Mod (Cave 1)** | Shiny sparkle effect marker. Only our mod sets this in inner_pokemon — the game tracks sparkle in sd fields. Used for save persistence self-heal. |
| 2 | `0x00000004` | isShiny | **Mod (Cave 1)** | Primary shiny flag. Checked by Cave 2 (model), Cave 5 (drop), Cave 6/7 (name color), Cave 8 (icon). |
| 17 | `0x00020000` | unknown | Game | Checked by `GetColorIndex` as part of MINE color detection. |
| 20 | `0x00100000` | unknown | Game | Checked alongside bit 17 for MINE color (index 4). |
| 26 | `0x04000000` | isBoss | Game | Distinguishes bosses from regular enemies. Read by `CreateEnemyOrBossHpBar`. |
| 27 | `0x08000000` | variantDirty | Game | Set when variant at `+0x32` changes. Likely triggers model reload. |
| 31 | `0x80000000` | shinyOneShot | **Mod (Cave 1)** | One-shot flag for Cave 5 drop. Cleared after use. Also used by CTRPF for reliable shiny detection. |

### Mod flag usage

Cave 1 sets: `+0xC |= 0x80000005` (bits 0 + 2 + 31)

- **Bit 2** must be checked by Cave 2 (not bit 31). Bit 2 persists through memory reuse in the game's pool allocator, so dropped toys also load shiny models.
- **Bit 31** must NOT be used for Cave 2. It does not survive memory reuse, causing toys to lose shiny models.
- **Bit 0** serves as a self-heal indicator after save/load. Only our mod sets bit 0 in inner_pokemon, so its presence reliably indicates a shiny pokemon even if bit 2 was lost.

## Species ID (`+0x24`)

The primary key identifying which Pokémon this is. Passed to:

| Function | Purpose |
|----------|---------|
| `GetSpeciesName` (`0x221270`) | Display name |
| `GetSpeciesType` (`0x22E154`) | Type/category |
| `GetPokemonModelName` (`0x216B40`) | Base model filename |
| `GetPortraitResourceId` (`0x3523B0`) | Boss portrait texture |
| `GetSpeciesBaseScale` (`0x35241C`) | Entity rendering scale |
| `IsBossLongVariant` (`0x1DC790`) | HP bar layout selection |

## Secondary Data (sd) Structure

The secondary data struct (`sd`) is a larger companion to the inner_pokemon struct, pointed to by `entity[+0x04]`. It survives entity death and contains gameplay state.

### Key Offsets

| Offset | Type | Description |
|--------|------|-------------|
| `+0x20` | ptr | Container entity pointer (used by Cave 5's 3-hop chain) |
| `+0x60` | int | HP value |
| `+0x79` | byte | Entity removal flag (set to 1 by 31 locations) |
| `+0xCC` | byte | CC gate value (0=skip, 1=trigger drop path) |
| `+0x268` | byte | Befriendable byte (read at `0x2ADDF8`) |
| `+0x2B8` | byte | Entity type (0xA = sparkle) |
| `+0x2D4–0x348` | — | Fields copied from inner_pokemon by `sd_init` |
| `+0x320` | byte | Befriend gate state |
| `+0x322` | byte | Befriend sub-state (may be copied to `+0x268`) |
| `+0x325` | byte | Trait value |

## Collection Structure

The collection entry struct is 0x4C bytes. Used by the collection/Pokédex screen.

| Offset | Type | Description |
|--------|------|-------------|
| `+0x0C` | uint | Flags (bit 0 = sparkle indicator, used by Cave 9) |
| `+0x31` | byte | Pass/rare byte |
| `+0x48` | uint | Validity marker |

# Identified Functions

Functions discovered through reverse engineering of Pokémon Rumble Blast's `code.bin`.

Addresses are listed as **VA** (Virtual Address) = file offset + `0x100000`.  
Confidence: **High** = confirmed by string refs or clear behavior, **Medium** = inferred from context, **Low** = speculative.

## Pokémon Data Access

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x216B40` | `GetPokemonModelName` | High | `(speciesId, form)` → UTF-16LE species name pointer from name table. Table: 700 entries at file `0x509988`. |
| `0x2186CC` | `GetPokemonHP` | Medium | Takes inner_pokemon data, returns HP value. |
| `0x221270` | `GetSpeciesName` | Medium | Takes species ID (`+0x24`), returns display name string. |
| `0x22E154` | `GetSpeciesType` | Medium | Takes species ID, returns type/category value. |
| `0x1DC790` | `IsBossLongVariant` | Medium | Takes species ID, checks if boss uses long HP bar layout. |
| `0x3522F0` | `HasSpecialVisualTrait` | Low | Takes species ID, returns bool for scale/flag changes. |
| `0x3523B0` | `GetPortraitResourceId` | Medium | Takes species ID, returns portrait texture resource ID. |
| `0x35241C` | `GetSpeciesBaseScale` | Medium | Takes species ID, returns float base scale for rendering. |
| `0x2E4CCC` | `GetPokemonSizeFactor` | Medium | Takes pokemon data ptr, returns float size multiplier. |
| `0x0C0778` | `StorePokemonVariant` | High | `(Pokemon*, variantIndex)` — writes variant to `+0x32`, ORs bit 27 into `+0xC`. |
| `0x0C076C` | `SetVariantViaSP` | High | `(PokemonSP*, variant)` — dereferences SP, falls through to `StorePokemonVariant`. |

## Model & Asset Loading

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x2E9960` | `LoadPokemonModel` | High | Builds path `rom:/pii/<name>[suffix].bcres`, loads 3D model with fallback. Reads `+0xC` bit 0, `+0x24` species, `+0x30` form, `+0x32` variant. |
| `0x319EFC` | `LoadModelResource` | Medium | Loads `.bcres` file into model object. Returns nonzero on success. |
| `0x31A4D4` | `InitModelObject` | Medium | Initializes 200-byte model object after allocation. |
| `0x318F7C` | `InitEntityModel` | High | Loads model via `LoadPokemonModel`, sets up animation, calculates scale. Reads entity `+0xF8` bit 0, `+0xFC` for pokemon SP. |
| `0x30F0E4` | `GetIconFilename_Wide` | High | Produces UTF-16LE icon filenames (`N%03d_%c_%02d`) via swprintf. 7 callers. |
| `0x30EF38` | `GetIconFilename` | High | Narrow string version for collection full icons (`rom:/pokeicon/full/%ls.arc`). |
| `0x255154` | `StringFormat` | High | `swprintf`-style formatting. Used with `rom:/pii/%ls.bcres`. |

## Pokémon Creation

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x2AA8B0` | `CreatePokemonEntity` (wrapper) | High | Main creation function. Resolves forms, creates instance, configures power/moves. Contains Hook 1 NOP. 13 parameters. |
| `0x2AA620` | `CreatePokemonEntity` (core) | High | Core CPE. 15 BL callers across 9 functions. Only fires at level init (6 times). Field enemies use recycling. |
| `0x1CC078` | `GetPokemonBySpeciesForm` | Medium | Thin wrapper around species lookup. `(speciesId, form, unused, ?)`. |
| `0x1EC920` | `PokemonFactory` | High | Allocates 0x70 bytes for inner struct via `AllocateObject`. Retry loop with validation. |
| `0x0C0D0C` | `PokemonBaseConstructor` | High | Sets vtable, zeros key fields, calls `PokemonInitializer`. |
| `0x0C0AF0` | `PokemonInitializer` | High | Real struct initializer. Zeroes `+0xC`, copies template SP, stores species ID at `+0x24`, classifies via 3 functions → `+0x30`. |
| `0x2BF104` | `CreateDrop` | High | Entity initialization function used by Cave 5 for guaranteed shiny drops. `(entity, init_value, 1, 0x265, 0, 0)`. |
| `0x29A424` | `CreatePokemonFromTable` | Medium | Secondary creation path via static table. Used for shop/rewards/scripted. |
| `0x2C815C` | `HandleScriptedEncounter` | Medium | Third creation path for scripted encounters. |

## Entity System

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x2A6398` | `CreateGameEntity` | High | General entity factory. Allocates 0x1A4-byte entity, constructs, wraps in SP, registers with managers. |
| `0x2B550C` | `EntityConstructor` | Medium | Constructs 0x1A4-byte entity object. |
| `0x2BB928` | Death Handler | High | Per-frame handler for ALL entities. Timer management → CC gate → drop path. **Hook 5 location.** |
| `0x30AB60` | `sd_init` | High | 17 callers. Copies fields from inner_pokemon to sd at `+0x2D4` through `+0x348`. R5=sd, R7=inner_pokemon. |
| `0x30A27C` | `entity_init` | High | 30 callers. Writes sd fields including `sd[+0x268]`. Called after `sd_init` in recycler path. |
| `0x309804` | `sd_bulk_copy` | High | ~0x7E8 byte function copying many sd fields (R5=src, R4=dest). Copies both `+0xCC` and `+0x268`. |
| `0x3B197C` | Confusion Handler | Medium | Sets CC=1 for confused/sparkle entity subtypes (0x13, 0x38). |

## UI / HP Bar

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x189944` | `CreatePlayerHpBar` | High | Allocates 0x1F8-byte HpBar, entityType=0. |
| `0x29A934` | `CreateBossHpBar` | High | Same structure, entityType=3. |
| `0x2A301C` | `CreateEnemyOrBossHpBar` | High | Reads `+0xC` bit 26 to choose entityType (2=enemy, 3=boss). |
| `0x246294` | `LoadUILayout` | High | Loads named UI layout (e.g. `"hp_player"`). |
| `0x2429B0` | `FindUIElement` | High | Searches for named sub-element in UI layout. |
| `0x318A78` | `GetColorIndex` | High | `(pokemon_data*)` → color index (0=Normal, 1=Dead, 2=Prefixed, 3=Rare, 4=Mine). **Wrapped by Cave 7.** |
| `0x192F44` | Field Name Display | High | Sets text widget color for field HUD names. Contains Hook 6 NOP. |

## Spawn / Recycling

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x34FA90` | `PreloadStageModelVariants` | Medium | Collects all Pokémon for a stage from spawn tables (15 areas × 0x48-byte entries), preloads models. |
| `0x248B70` | `PreloadStageEntities` | Medium | Parses entity list (type 0x19=Pokémon, 0x1B=flag, 0x1C=Mii), deduplicates, preloads models. |
| `0x3D17F0` | Recycler 1 | Medium | Entity recycling function. Calls `0x2AA8B0` + `0x30AB60` + `0x30A27C` (not CPE). |
| `0x3DACC8` | Recycler 2 | Medium | Same pattern as Recycler 1. |
| `0x3DB9FC` | Recycler 3 | Medium | Same pattern. |
| `0x3EBF68` | Recycler 4 | Medium | Same pattern. |

## Befriend / Drop Pipeline

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x2ADB58` | Befriend Function | High | Real befriend handler. 6 callers — all boss/special encounters, NOT field combat. 5-phase decision tree, no RNG. |
| `0x3BCBE4` | Dead Code | High | **NEVER CALLED.** ~12KB vestigial function with unused parallel befriend/sparkle implementation. Zero callers in entire binary. |
| `0x40049C` | Force Befriend Caller | Medium | One of 6 callers of `0x2ADB58`. Force-writes `+0x268=1` (guaranteed drop — bosses). |
| `0x443198` | Parallel CC Consumer | Low | Reads/processes CC value using same vtable[12] pattern as death handler. |

## Memory Management

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x3550B4` | `AllocateObject` | Medium | `(size, context)` — general allocator. 0x70 for pokemon, 0x1A8 for portrait, 0x10 for ref-count. |
| `0x351C24` | `DecrementRefCount` | Medium | Smart pointer cleanup. Called 4× in DropWrapper to clean temporaries. |
| `0x317C84` | `SmartPtrCopy` | Medium | Smart pointer copy with refcount increment. |

## Stage / Coroutine

| VA | Name | Confidence | Description |
|----|------|------------|-------------|
| `0x3DE9E8` | `StageGameplayCoroutine` | High | Main stage flow: setup → battle → collection → transition. Contains inline pokemon creation calls. |
| `0x308008` | `YieldCoroutine` | High | Yields execution in coroutine wait loops. |
| `0x248978` | Collection Detail Function | High | Shows collection screen 3D model. Contains Hook 9 between pokemonSP creation and `LoadPokemonModel`. |

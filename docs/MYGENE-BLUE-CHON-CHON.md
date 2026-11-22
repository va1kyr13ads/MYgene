# MYgene Slayer Series #3 — Blue Chon Chon

**Feature branch:** `feature/blue-chon-chon-slayer-20261123`  
**Preserved known-good rollback:** `milestone/slayer-working-2026-11-23` (server `58a8bf1179adbdea43dce4e3e1d42b56d3432f89`; client `feb78501668de69b0883c9cd7e7a3e25ffeef594`).

This third family follows the already-accepted Yellow Fabre / Red Thief Bug encounter pattern. **Mini-bosses, elites, bosses and MVPs do not qualify.**

## Hunting family (exact IDs)

| Mob | ID | Ordinary family | Credits 30-kill counter | Subject to Slayer bow execution |
|---|---:|---|---|---|
| Chonchon | 1011 | Yes | Yes | Yes |
| Steel Chonchon | 1042 | Yes | Yes | Yes |
| Hunter Fly | 1035 | Yes | Yes | Yes |
| **Blue Chon Chon (special)** | **31052** | Special non-boss | Its labeled death credits the next cycle once | Yes |
| Dragon Fly | 1091 | **No: mini-boss** | No | No |
| Any summoned/elite/boss variant | Any other ID | No | No | No |

Thirty qualifying kills **on the same map**, aggregated across players on that map, summon Blue Chon Chon at the 30th kill or killer's location. An active encounter blocks spawning another on that map. The normal labeled encounter death resets the active flag and starts the next cycle at 1, mirroring Yellow Fabre and Red Thief Bug. Each map tracks its own progress. The in-memory count resets when NPC scripts reload.

The custom special mob `31052` has its own name, Wind/Insect stats, and normal Chonchon drop table. A `db/import/mob_avail.yml` entry aliases its **sprite appearance only** to the vanilla `CHONCHON` sprite so a stock authorized GRF can render it; **blue recolored artwork is not included yet.** This does not change its server ID or name.

## Drops (per special monster kill)

Exactly independent of global 4x/normal multipliers:

| Reward | ID | Chance |
|---|---:|---:|
| Chonchon Slayer Bow [1] | 60010 | **0.05%** |
| Blue Chon Chon Card | 60011 | **0.01%** |
| One of Red / Blue / Yellow Gemstone | 715 / 716 / 717 | 70.00% |
| Gold item | 969 | 11.00% |
| Existing Attraction Potion | 31003 | 0.50% |

The Bow is awarded to the killer's inventory when carry weight allows and otherwise placed on the ground with a message. Card and auxiliary rewards spawn on the ground at the killer's tile. On a killing player's **15-second Legendary Bubble Gum** window (item `31009`), each eligible special roll succeeds. Drops from labeled NPC encounter mobs and unlabeled `@monster 31052` mobs both call exactly one shared reward routine; no double rolls.

### Weapon and Blue card effects

- **Chonchon Slayer Bow [1]** (`60010`): two-handed Bow; ATK 17, Weight 40, range 5, Weapon Lv. 1, equip Lv. 4, unrefinable. Uses standard RO bow jobs. Requires arrows for ordinary ranged attacks as normal.
- On a **successful basic weapon attack** against mob IDs `1011`, `1042`, `1035` or `31052`: a **50%** chance of lethal execution. No skill attacks, no unrelated monsters, and unconditional rAthena `BOSSTYPE_NONE` protection.
- **Blue Chon Chon Card** (`60011`): compounded in the Bow's first slot, raises that bow's execution chance to **90%**. No general card-only effect on other weapons.
- **Perfect Chonchon Slayer Bow (P.C.S.B)** (`60012`): ATK 25, Weapon Lv. 4, equip Lv. 40, Weight 100, range 5, 1 slot, indestructible, unrefinable, same jobs; 90% execution **only when Blue Chon Chon Card remains compounded**. This is **never** a monster drop.
- **Perfect upgrade access is GM test only (group 99)** at World Relic Keeper in Prontera. It reuses the established equipment-instance revalidation and conversion safety checks. Public crafting, leasing and world supply registry remain disabled.

## Client support

The parallel `rustnarok-client` branch `feature/blue-chon-chon-slayer-20261123` adds tooltip, name, one-slot and card metadata for item IDs `60010`, `60011` and `60012`. It deliberately borrows standard Bow and Chonchon Card **inventory assets** until the dedicated art is ready. No copyrighted GRF is added to GitHub.

## Install on development / live Codespace

**Before deploy:** make a verified live database backup (separate from GitHub source; see `ops/milestone-live-backup-20261123`) and back up local configuration. Do not switch the running checkout while live servers are in use.

1. Update the MYgene Codespace checkout from a merged or explicitly selected feature commit, protecting any uncommitted edits.
2. **Compile the server** after the battle.cpp change (e.g. your server's existing `make map` build target).
3. Stop the old map-server safely and restart it with the same private configuration, after backing up active characters. `@reloadscript` alone **cannot** load the new compiled ranged execution logic; for new YAML mob, equipment and sprite alias, full map-server startup is strongly preferred.
4. Update and launch a tested Windows client build based on the matching client branch/merged SHA. Preserve existing authorized GRFs and `data/clientinfo.xml`.
5. Read map-server startup output for YAML or NPC script-load warnings.

## Live GM verification checklist

- `@item 60010 1`, `@item 60011 1`, `@item 60012 1`, `@item 31009 2` (GM test items), confirm correct name, one slot and bow rendering.
- `@monster 1011 30` on the **same map**; kill 30 normals and check one Blue Chon Chon spawn. Repeat with a mixture of Steel Chonchon `1042` and Hunter Fly `1035`.
- Verify Dragon Fly `1091` never advances the counter; no boss, elite or MVP is affected by execution. An ordinary 30-kill spawn must be solo on each map.
- Spawn `@monster 31052 1`, activate `Legendary Bubble Gum`, kill within 15 seconds. Expect Bow and Blue card and auxiliaries; weapon inventory or ground fallback. Repeat without gum to observe ordinary independent probabilities (absence of rare drops is normal).
- Equip Bow `60010` with arrows; test regular basic attacks versus Chonchon, Steel Chonchon, Hunter Fly and Blue Chon Chon; check approximately 50% execution for attacks that hit. Compound Blue card `60011` and expect approximately 90% over many hits. Test other families, skills, Dragon Fly and elites as negatives.
- At group 99, verify Perfect Bow conversion on a **backed-up development character** with the carded normal bow equipped, at Level 40+. Negative-test non-GM, uncarded/refined/bound/graded items.
- Recheck Fabre and Thief Bug weapons, items, drops and card execution; the prior saved milestone remains the rollback point.

## Automated test coverage and limits

`python3 -m unittest discover -s tools -p 'verify_mygene_slayer_drops.py' -v` validates event dispatch, key IDs, Bow equipment type, card logic, and drop percentages. The Windows workflow runs `cargo test --locked` and a Windows release build. These tests are **not a substitute** for compilation and direct testing on the live MYgene Codespace.


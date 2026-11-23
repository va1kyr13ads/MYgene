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

Thirty qualifying kills **on the same map**, aggregated across players on that map, summon Blue Chon Chon at the 30th kill or killer's location. An active encounter blocks spawning another on that map. The normal labeled encounter death resets the active flag and starts the next cycle at 1, mirroring Yellow Fabre and Red Thief Bug. Each map tracks its own progress. The in-memory count resets when NPC scripts reload. If a GM or another script
removes the special monster without its death callback, the next normal family
kill detects that the map has no labeled Blue Chon Chon and recovers the stale
active flag. A failed summon does not issue a false appearance announcement;
the encounter remains at 29/30 so the next eligible kill can retry.

The custom special mob `31052` has its own name, Wind/Insect stats, and normal Chonchon drop table. A `db/import/mob_avail.yml` entry aliases its **sprite appearance only** to the vanilla `CHONCHON` sprite so a stock authorized GRF can render it; **blue recolored artwork is not included yet.** This does not change its server ID or name.

## Blue Chon Chon combat profile (2026-11-23)

Blue Chon Chon is a **stronger normal Chonchon**, not a copy of Hunter Fly's attacks, drops or movement. Its AI has been switched from passive `01` to **aggressive `04` (the same AI as Hunter Fly)**, so it actively acquires and attacks nearby players. It remains **non-boss** and killable by the Slayer Bow.

| Stat | Blue Chon Chon (31052) |
|---|---:|
| Level | 30 |
| HP | 3,000 (unchanged) |
| Base / Job EXP | 450 / 300 |
| ATK | 110–145 |
| DEF / MDEF | 25 / 10 |
| STR / AGI / VIT | 24 / 55 / 25 |
| INT / DEX / LUK | 8 / 45 / 12 |
| AI | 04 (aggressive) |

Normal Chonchon characteristics are deliberately retained: **Small, Insect, Wind Lv. 1; 1-cell attack range, 10 skill range, 12 chase range, 200 walk speed, 1076 attack delay, 576 attack motion, 288 client attack motion, and 480 damage motion**. Detector mode and normal Chonchon drops remain unchanged. The custom `db/import/mob_skill_db.txt` copies normal Chonchon's level-1 **NPC_WINDATTACK** row and uses the same attack in `angry` state for proactive aggression. Do **not** add Hunter Fly teleport, HP drain, combo, extra drops or boss classification.

**Development playtest:** Spawn `@monster 31052 1` on a disposable map and approach without attacking; it must aggro and chase like a Hunter Fly, then perform normal attacks and occasionally level-1 Wind Attack. Check its Level 30 and 3,000 HP, compare its pace/attack animations with Chonchon `1011`, and verify it does not teleport or use Hunter Fly-only skills. Confirm the 30-kill-per-map summon and reward logic still operate unchanged. Full map-server startup is required for updated monster and mob-skill databases.

## Drops (per special monster kill)

Exactly independent of global 4x/normal multipliers:

| Reward | ID | Chance |
|---|---:|---:|
| Chonchon Slayer Bow [1] | 60010 | **0.05%** |
| Blue Chon Chon Card | 60011 | **0.01%** |
| One of Red / Blue / Yellow Gemstone | 715 / 716 / 717 | 70.00% |
| Gold item | 969 | 11.00% |
| Existing Attraction Potion | 60003 | 0.50% |

All five MYgene-exclusive reward rolls (Bow, Blue Card, one random Gemstone, Gold item, Attraction Potion) are delivered directly to the killing player's inventory. Any successful reward that cannot fit is dropped at the killer's tile with an on-screen notice. The same inventory-first/floor-fallback rule applies to Yellow Fabre and Red Thief Bug; their fixed roll probabilities and normal monster drops are unchanged. On a killing player's **15-second Legendary Bubble Gum** window (item `60009`), each eligible special roll succeeds. Drops from labeled NPC encounter mobs and unlabeled `@monster 31052` mobs both call exactly one shared reward routine; no double rolls.

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

- `@item 60010 1`, `@item 60011 1`, `@item 60012 1`, `@item 60009 2` (GM test items), confirm correct name, one slot and bow rendering.
- `@monster 1011 30` on the **same map**; kill 30 normals and check one Blue Chon Chon spawn. Repeat with a mixture of Steel Chonchon `1042` and Hunter Fly `1035`.
- Verify Dragon Fly `1091` never advances the counter; no boss, elite or MVP is affected by execution. An ordinary 30-kill spawn must be solo on each map.
- On a disposable test map, force-remove the labeled Blue Chon Chon with GM/script cleanup and kill another normal Chonchon. Verify the event recovers from the stale active flag without announcing an imaginary spawn or affecting another map's counter. Simulate or test a failed summon, verifying the retry stays at 29/30.
- Spawn `@monster 31052 1`, activate `Legendary Bubble Gum`, kill within 15 seconds. Expect Bow, Blue Card and auxiliaries to enter the killer's inventory, except any items that cannot fit (ground fallback with notification). Repeat without gum to observe ordinary independent probabilities (absence of rare drops is normal).
- Equip Bow `60010` with arrows; test regular basic attacks versus Chonchon, Steel Chonchon, Hunter Fly and Blue Chon Chon; check approximately 50% execution for attacks that hit. Compound Blue card `60011` and expect approximately 90% over many hits. Test other families, skills, Dragon Fly and elites as negatives.
- At group 99, verify Perfect Bow conversion on a **backed-up development character** with the carded normal bow equipped, at Level 40+. Negative-test non-GM, uncarded/refined/bound/graded items.
- Recheck Fabre and Thief Bug weapons, items, drops and card execution; the prior saved milestone remains the rollback point.

## Automated test coverage and limits

`python3 -m unittest discover -s tools -p 'verify_mygene_slayer_drops.py' -v` validates event dispatch, key IDs, Bow equipment type, card logic, and drop percentages. The Windows workflow runs `cargo test --locked` and a Windows release build. These tests are **not a substitute** for compilation and direct testing on the live MYgene Codespace.

## ID collision fix and migration caution

The three **new, unreleased** Blue-series item IDs are now **60010 / 60011 / 60012**. Those numbers are below 65,536 for legacy packet compatibility and have been checked against the tracked official pre-renewal and Renewal item equipment, usable and miscellaneous YAML databases. Do not reuse the original tentative `31010 / 31011 / 31012`: those are official Renewal LoVA cards.

**Legacy ID source refactor, deployment still blocked:** Old Fabre/Thief Bug custom item IDs \`31001–31009\` are reassigned in this **feature branch's source** to \`60001–60009\` (\`60005\` reserved), alongside Blue items \`60010–60012\`. All \`60001–60012\` were found free against official item DBs in both modes. Monster IDs \`31050–31052\` are unchanged and do not conflict with official monsters. This does **not** migrate any persisted player items. The legacy IDs overlap official Renewal cards; deployment to a populated server is unsafe without an audited, unambiguous, backup-verified per-instance SQL migration and matching client update. Follow \`docs/MYGENE-SLAYER-ID-MIGRATION.md\`. Recheck Renewal startup CI.

Build CI note: legacy workflows were pinned to Ubuntu 22.04/24.04 as appropriate.


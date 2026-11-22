# MYgene — Yellow Fabre Field Encounter (experimental)

Implemented on server branch `feature/yellow-fabre`. This has **not** been deployed to a running MYgene server and must be compiled and playtested before merging to `mygene-rustnarok-compat`.

The matching client visual/UI changes are on `va1kyr13ads/rustnarok-client`, branch `feature/yellow-fabre`. They also need a successful Windows CI build and real game playtest.

## Encounter

- **Monster:** Yellow Fabre (ID `31050`, `MYGENE_YELLOW_FABRE`), inspired by the standard Fabre (1007).
- **Appearance:** Yellow-tinted base Fabre animation rendered by the MYgene client at runtime (no new game GRF).
- **Combat:** Level 8, 650 HP, ATK 22–30, Small Insect, Earth 1, slightly faster than regular Fabre.
- **Map:** `prt_fild01` (Prontera field). The NPC event script watches ordinary Fabre (1007) deaths on this field.
- **Trigger:** After the 30th ordinary Fabre death, one Yellow Fabre spawns at a random walkable location on that map. A field-wide announcement appears. While it is alive, additional Fabre kills are not counted. After its death, the count restarts at zero.
- **Server restart:** The temporary counter and encounter state reset on server/script restart. Do not reload scripts while the special monster is alive; clean up its spawn before development reloads.

If the target field lacks Fabre in your live spawn configuration, adapt the event's `.Field$` to an actual Fabre-populated field after checking it, or add an ordinary Fabre spawn to that field. Do not edit stable map spawns without testing.

## Reward rolls

The special rewards are each **independent** per Yellow Fabre death. They are scripted as 1,000,000-sided rolls at the killer's current position, not ordinary database rates; the live 4× normal-drop multiplier does **not** multiply these five percentages.

| Reward | Item ID | Exact chance per kill |
|---|---:|---:|
| Fabre Slayer Knife [1] | 31001 | 0.05% |
| One random Red/Blue/Yellow Gemstone | 716/717/715 | 70% |
| Yellow Fabre Card | 31002 | 0.01% |
| Gold (item, not zeny) | 969 | 55% |
| Attraction Potion | 31003 | 0.5% |

Standard Fabre drops are **also** defined on Yellow Fabre: Fluff, Feather, Club [3], Azure Jewel, Green Herb, Clover, Club and Fabre Card, with their original Fabre base rates and normal MYgene multiplier.

Successful special weapon rolls are granted directly to the killer when carry capacity allows, otherwise they become ground drops near the killer. The other scripted rewards are ground drops near the killer, not necessarily on the monster corpse. Gold means the normal Gold loot item (969), not zeny.

## New items

**Fabre Slayer Knife [1] (31001):** novice-friendly dagger, 17 attack and one socket. Upon a **successful normal melee weapon hit** against standard Fabre (1007), Pupa (1008), Creamy (1018) or Yellow Fabre (31050), has a 50% chance to deal enough damage to defeat the target. Does not work on unrelated insects, players or skill damage. One Yellow Fabre Card compounded into its socket raises that proc to **90%**, *not* 50% plus 90%.

**Yellow Fabre Card (31002):** right-hand weapon card. The 90% proc applies only when compounded into item ID 31001. Its effect is implemented in `src/map/battle.cpp`, rather than an item script, and should be tested with actual socketing.

**Attraction Potion (31003):** on use starts a 5-minute character-local effect. For this first prototype, the 70% bonus is implemented as a **70% chance on each passive-monster AI scan** to acquire the buffed player as a target. Applies only to ordinary passive monsters on `*_fild` fields. Does not change boss AI, dungeons, towns or PvP. This is a functional interpretation of "70% increased aggro"; it is **not** an exact 1.7× aggression radius or a guaranteed one-time 70% proc. For balance review, remember that repeated scans can make aggro more likely over time.

All three new items currently use existing client icons, not proprietary new artwork. The MYgene client supplies readable item names and tooltips even if the player's original GRF lacks custom iteminfo entries.

## Code changes

- `db/import/mob_db.yml`: Yellow Fabre stats and inherited vanilla drops.
- `db/import/item_db.yml`: Knife, card, potion.
- `npc/custom/mygene/yellow_fabre.txt`: Field kill trigger, Yellow Fabre kill handler, custom reward rolls.
- `npc/scripts_custom.conf`: registers the event script.
- `src/map/battle.cpp`: Fabre Slayer normal-attack proc and card upgrade.
- `src/map/mob.cpp`: Attraction Potion field aggro.

These changes are server-side and do not require altering the MYgene public game rates. Do not mix with the stable branch until tests pass.

## Safe deployment (GitHub Codespaces terminal, **not Windows PowerShell**)

Stop the map/login/char servers before changing the branch, or use a second Codespace for compilation. Keep any unstaged edits safe. From the **MYgene repository root**:

```bash
git status --short
git fetch origin
git switch feature/yellow-fabre
git pull --ff-only origin feature/yellow-fabre
make server -j2
```

If `git switch` would overwrite local work, **do not force it**; save/stash/commit the changes first. The custom C++ files require rebuilding the `map-server` executable. After a clean build, start the server using your existing known-working startup procedure, which previously used:

```powershell
pwsh -NoProfile -File ./mygene-start.ps1
```

Observe map-server startup logs for YAML, NPC and C++ errors. Confirm the new item IDs and monster ID load without warnings.

## Player tests

1. Keep the original Windows executable in place. Use a separate `MYgeneClient.exe` from a **successful** GitHub Actions build on the matching client branch.
2. In the field, defeat 29 Fabres: no Yellow Fabre. On the 30th: **one** Yellow Fabre should appear and broadcast.
3. Kill the Yellow Fabre: confirm it resets the counter; no second special mob appears until 30 more regular Fabre kills.
4. With appropriate GM permissions, inspect IDs via `@monster 31050 1` and `@item 31001 1`, `@item 31002 1`, `@item 31003 1` for debugging. Manually spawned Yellow Fabres **do not** have the NPC kill event label, so use the actual 30-kill encounter for scripted custom reward rolls.
5. Test the Fabre Slayer Knife against the four specified family monster types with and without the Yellow Fabre Card. Verify proc is restricted to actual equipped knife and normal attacks.
6. Use Attraction Potion near passive field mobs, verify duration and ensure unrelated monsters/maps remain unaffected.
7. For drop probabilities, use many automated/scripted trials or isolated roll tests. The 0.01% card is expected only once per **10,000 kills on average**; it is not guaranteed after 10,000 kills.
8. Check that the existing 7× Base/Job EXP and 4× ordinary drops are unchanged, and that the custom rolls remain exact.

## Known limitations / pending verification

- **Not compiled or deployed yet**; inspect server build and game logs before claiming success.
- The yellow tint applies to green-dominant Fabre sprite pixels; its visual appearance depends on the source game's sprite palette.
- Unique new icon/weapon/card illustrations are not part of this prototype.
- The event keeps the counter in temporary NPC memory and resets it on script/server restart.
- The encounter currently targets only `prt_fild01`, not all fields or the entire server.
- Current potion behavior uses a repeated AI scan chance and should be balanced with real-player testing.
- Default item IDs are in a custom range (31001–31003). Inspect database conflicts before merging in later custom items.

## Custom weapon reward delivery (23 Nov 2026)

For the current `feature/yellow-fabre` implementation, the **actual** Fabre Slayer Knife (31001) and Thief Bug Slayer Sword (31006) rates are **0.05% per special encounter kill**, or 1 in 2,000 on average. A 0.05% rate does not guarantee a drop after 2,000 kills.

Both special-monster kill handlers now deliver a successful weapon roll directly to the attached killer's inventory when carry capacity allows it. If it cannot be carried, the weapon falls on the ground at the killer's position. Legendary Bubble Gum still guarantees the special weapon roll while active, and all other independently rolled rewards keep their existing chances. The normal 30-family-kill encounter keeps its existing labeled death callback. Unlabeled Yellow Fabres (31050) and Red Thief Bugs (31051), including GM-spawned copies, now receive the **same** fixed exclusive rolls through `OnNPCKillEvent`. The two paths are mutually exclusive in rAthena's death dispatch, so an encounter kill does not roll rewards twice.

**Verification:** rebuild/restart is not necessary for changes limited to these NPC scripts, but the running map-server must load them by restart or deliberate `@reloadscript` (which resets encounter counters). Kill 30 family monsters on one map, activate Legendary Bubble Gum immediately before killing the spawned special monster, then verify the appropriate weapon appears in inventory or as a floor drop if overweight. Repeat for both families. Also test a GM-only `@monster 31050 1` and `@monster 31051 1` with Gum before the killing blow: each should now yield its own Slayer weapon, while the encounter counters remain unchanged. Verify client-displayed item names against ID 31001 and 31006, not their art fallbacks. Review map-server logs for script errors. Do not claim an in-game fix until this succeeds on the running server.

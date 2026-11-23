# MYgene Novice Tower — Floor 4 solo trial

Status: **prototype only**, isolated from the existing development server and
the MYgene rare-loot announcement PR. This version does **not** select a
permanent progression route, award a new title, or change first job.

## Approved progression design (future work)

1. **Awakening** — introduction and Novice movement.
2. **Survival** — combat, preparation and recovery.
3. **Wisdom** — discovery of first-job roles.
4. **Conquest** — fight the Guardian alone, with scripted first-job support
   joining at boss HP milestones.
5. **Destiny** — complete the Tower and choose a first job.

At onboarding, a player will choose **Vanilla** or **Novice Tower**. Once
Novice Tower is chosen, the full route must be finished before leaving that
progression. This permanent selection is intentionally **not yet enabled**
because floors 1–3 and 5 are not implemented or validated.

### Floor 4 progression

- Guardian begins **solo**.
- 80% HP: **Swordman** — courage, Endure.
- 65% HP: **Mage** — knowledge, scripted support damage.
- 50% HP: **Archer** — precision, increased movement and support damage.
- 35% HP: **Acolyte** — faith, healing and Blessing.
- 20% HP: **Thief** — shadows, extra support damage.
- 10% HP: **Merchant** — ambition, final support.
- Helpers never reduce Guardian below **1 HP**. The Novice must finish it.

Current support uses **scripted autonomous effects**, not individual
character-shaped NPC sprites or a full mobile party AI. Those visuals and
behavior are still to be developed.

## Isolation and safeguards

- A private character-owned `IM_CHAR` instance uses a copied `1@tower`
  map with `NoNpc: true`, so existing Endless Tower NPCs are not cloned.
- Entrance is the temporary **Novice Tower Trial** herald in Prontera at
  `158,176`. It only accepts Novices **not in a party**.
- The controlling script is attached to each player's RID and tracks their
  own boss unique GID, instance ID, stage and time-based support effects.
- A successful boss kill is only recorded when the character's tracked
  Guardian was defeated and that character is in the associated map and
  unpartied. It sets `MYGENE_NT_TRIAL_FINISHED` as a **trial-only** flag.
- No titles, permanent graduation, job change, rare reward, or world
  announcement are granted by the trial.
- The test uses the stock Wolf sprite as a **placeholder** for the Guardian.
  Boss health and basic attacks are set in `guardian_boss.txt`, for balancing
  after real player testing.

## Contents

| File | Purpose |
|---|---|
| `entry.txt` | Temporary solo trial entrance in Prontera |
| `guardian_boss.txt` | Spawn and stats of placeholder Guardian |
| `tower_core.txt` | Poll HP, trigger job stages, verify final player kill |
| `adventurers.txt` | Job dialogues, support buffs and damage |
| `tower_floors.txt` | Five-floor design scaffold, not live |
| `graduation.txt` | Graduation safeguard and future notes, not live |
| `db/pre-re/instance_db.yml` | Character-owned private instance registration |
| `npc/scripts_custom.conf` | Trial NPC script registration |

## Validation and test plan

1. Confirm `python3 -m unittest discover -s tools -p
   'verify_mygene_novice_tower.py' -v` passes.
2. Verify `make map` and `./map-server --run-once` with **Pre-Renewal**
   enabled, and check NPC loading for script warnings.
3. On a **separate test Codespace** (not the running server), log in as a
   Novice without a party and talk to the trial herald in Prontera.
4. Check that the instance is private and another character cannot enter the
   same map even if it knows the test NPC or map name.
5. Fight the boss and verify six messages at 80/65/50/35/20/10% HP, once
   each and in order. Observe supportive buffs and boss HP never falling
   below 1 from automatic helpers.
6. Verify a player-delivered final hit marks only that character's trial.
7. Disconnect, die, leave the map, or re-enter and verify no duplicated
   guardians, cross-player events, or stuck re-entry.
8. Verify the unchanged **Vanilla** starting route and all MYgene Slayer
   features remain functional. Do not enable permanent Tower selection
   before floors 1–3 and 5 are ready.

**Important:** This test prototype is deliberately *not* automatically
deployed. Do not merge or copy its NPC registration into a public server
until the Pre-Renewal compile/NPC parser and in-game tests pass.

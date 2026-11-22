# MYgene — World Relic Keeper NPC and Perfect Fabre upgrade (stage 1)

## Standalone Perfect knife implementation — added 22 Nov 2026

The standalone upgraded weapon is defined on `feature/yellow-fabre`, before
the world-limit lease/renewal backend exists. It uses a different internal item
ID because Ragnarok's intrinsic attack, weight, range, weapon level, and required
level are attributes of an **item definition**, not a compoundable card.

| Property | Base ID 31001 | Perfect ID 31004 |
| --- | --- | --- |
| Display name | Fabre Slayer Knife [1] | Perfect Fabre Slayer Knife [1] |
| Weapon type | Dagger | Dagger |
| Weapon level | 1 | 4 |
| Required base level | 1 | 40 |
| ATK | 17 | 25 |
| Weight (game UI) | 40 | 100 |
| Range | 1 | 2 |
| Refinement | Disabled | Disabled |
| Unbreakable | No | Yes, via `bonus bUnbreakableWeapon;` |
| Card socket | 1 empty or occupied | 1 occupied by Yellow Fabre Card 31002 |
| Fabre-family proc | 50% or 90% if carded | 90% if carded |

`db/import/item_db.yml` specifies `Weight: 1000` for the Perfect variant,
because rAthena stores one displayed weight as ten database units.

### Upgrade current carded knives without needing another rare card

The World Relic Keeper NPC now exposes an extra **Perfect Knife Upgrade [GM]**
menu. It is intentionally **limited to Group 99**, until world slot issuance is
made atomic and safe for all players. It requires:
- Character base level 40 or higher; otherwise keep the working legacy knife.
- Original ID 31001 **equipped in right hand**, with card ID 31002 in slot 0.
- The weapon must be +0, identified, unbound, undamaged, non-rental,
  non-graded, and without random options / extra cards.
- Sufficient free carry weight for a newly created Perfect knife.

After confirmation, the NPC unequips that **specific inventory entry** and
exchanges it for ID 31004 with the same Yellow Fabre Card 31002 in slot 0.
No fresh Yellow Fabre Card is required. If prechecks fail, nothing is changed.

**Test-only safety note:** The script uses ordinary rAthena
`delitemidx`/`getitem2` commands, **not an SQL transaction**. Inventory
addition failure after deletion is not automatically reversible. The NPC
prechecks weight and data and is accessible to admins only; back up the SQL
database before test conversion. Do **not** remove the admin restriction
or release this to general players until there is a transaction-safe
conversion/registration flow.

### Existing carded knives continue working

Server `src/map/battle.cpp` retains the already-proven 90% execution proc
on old 31001+31002 and adds the same proc on 31004+31002. The 50% base
knife without the card stays unchanged. A malformed 31004 without the
special card gets no instant-defeat proc.

The paired `rustnarok-client` branch adds client item 31004, provides
readable tooltip lines (26-character limit), and removes the duplicate
`Yellow Fabre Fabre Slayer Knife` name. A legacy carded knife shows a
transitional "Yellow Fabre Slayer Knife" description with its genuine 90% proc.
Only ID 31004 shows the "Perfect" name and Level 4 traits.

### Safe Codespaces testing (NOT Windows PowerShell)

Your local `npc/custom/mygene/yellow_fabre.txt` may have important
uncommitted encounter settings, and `npc/scripts_custom.conf` may contain
a staged conflict resolution. **Do not reset, restore, checkout, or discard
either file, and do not drop your stash.** This release does not touch them.

```bash
cd /workspaces/MYgene
git status --short
git fetch origin
git pull --ff-only origin feature/yellow-fabre
```

If Git reports local changes would be overwritten, STOP and inspect rather
than force. Never use `git reset --hard` here.

Before testing an irreversible inventory exchange, back up the test DB and
save the backup OUTSIDE the repo:

```bash
sudo mariadb-dump mygene > "$HOME/mygene-before-perfect-$(date +%Y%m%d-%H%M%S).sql"
```

With all test players logged out, stop the services, rebuild the server
because `battle.cpp` changed, then start:

```bash
bash ./athena-start stop
make server -j2
```

Only after a successful rebuild:

```bash
pwsh -NoProfile -File ./mygene-start.ps1
bash ./athena-start status
```

Update the Windows `MYgeneClient.exe` to the latest successful
`MYgene-Windows-Client` artifact on `feature/yellow-fabre` *before*
claiming that the Perfect item will show its correct item name/icons.
Keep the existing loose Yellow Fabre Card BMP in place. The server controls
the gameplay stats, and the new Windows binary supplies the correct text.
An earlier Build #12 client knows ID 31001 but not ID 31004.

**Test:** at Base Level 40 or higher on an admin account, equip the
already-carded legacy 31001+31002, visit World Relic Keeper in Prontera
(167,187), select "Perfect Knife Upgrade [GM]", confirm, then equip the new
31004. Verify (a) true ATK25/Lv4/range2/weight100, (b) 90% on
Fabre-family monsters using successful normal attacks, (c) cannot refine,
(d) break effects don't destroy the Perfect weapon, and (e) Yellow Fabre
encounter remains unchanged. Test all checks and inventory exchange on a
throwaway character/backup before risking a treasured real item.

**Not yet live:** worldwide supply cap, lease/expiry, Soul ETC material,
non-GM upgrade requests, automatic conversion on card compounding, renewal,
registry and enforcement against deletion or dupes. This is intentionally
a standalone early test phase.

---

# MYgene — World Relic Keeper NPC (stage 1)

**Status:** NPC script added and registered on the server's `feature/yellow-fabre` branch.
The live relic lease / soul collection backend is **not yet implemented**. All
menus which would otherwise move items or change a lease are intentionally
read-only, so no player can accidentally surrender their scarce materials.

## Where to find the NPC

- **Name:** World Relic Keeper
- **Map:** `prontera`
- **Coordinates:** `167,187`
- **Facing:** `4`
- **Sprite:** `4_M_MINISTER`, an existing official NPC appearance
- **Script:** `npc/custom/mygene/world_relic_keeper.txt`
- **Registration:** `npc/scripts_custom.conf`

## Appearance and dialogue customization

Change the NPC's map, coordinates, direction, sprite or displayed name on the
single line near the beginning of the script:

```text
prontera,167,187,4\tscript\tWorld Relic Keeper#MYgene\t4_M_MINISTER,{
```

Use an NPC sprite constant available in the selected client's GRF and rAthena
`src/map/script_constants.hpp`. A new **unique NPC look** requires its own
custom sprite asset in the MYgene client; this first version reuses a standard
minister sprite and **does not** modify any GRF or player item artwork.

The menu currently has:

1. About World Relics (weapon concept and renewal rules).
2. Check My Materials (counts base knives and Yellow Fabre Cards in inventory).
3. Renew a World Relic (**disabled until backend is complete**).
4. World Relic Registry (**disabled until global registry exists**).
5. Soul Hunting Rules (planned Fabre, Pupa, Creamy and Yellow Fabre yields).
6. Leave.

Dialogue color uses Ragnarok formatting such as `^C9A13C...` and `^000000`.
You can change the text freely without altering any server combat logic.

## Previously discussed rules

- 300 Fabre Family Souls per successful renewal
- Ownership 60 days, renewable for 60 days, **unlimited renewals**
- Renewal opens 14 days before expiration; 7-day grace period
- Soul rewards planned: Fabre 1, Pupa 1, Creamy 1, Yellow Fabre 5
- Player must own an active registered relic; does not need to wield it to earn
  souls; GM and test spawns must not earn soul rewards
- Souls are an account-bound, stackable ETC material
- Perfect Fabre Slayer Knife: 25 ATK, weapon level 4, required level 40,
  range 2, weight 100, 90% Fabre-family instant-defeat, indestructible,
  non-refinable
- Base knife stays 17 ATK, level 1, required level 1, range 1, weight 40,
  50% Fabre-family instant-defeat; both knives non-refinable
- Suggested future item IDs: `31004` (Perfect knife) and `31005` (Souls),
  **not currently added to the item database**.
- The global supply cap has **not** been agreed yet. Do not assume 10 copies;
  that earlier number was only an example.

## Deployment in a GitHub Codespaces terminal

Before pulling from GitHub, inspect the current working tree and branch:

```bash
cd /workspaces/MYgene
git status --short
git branch --show-current
git fetch origin
git switch feature/yellow-fabre
git pull --ff-only origin feature/yellow-fabre
```

**Do not force-checkout over local work.** The script is interpreted by
rAthena: no C++ compilation or Windows client update is necessary for this
**stage-1 NPC**. On a development server, a GM can use `@reloadscript` or
restart the map server to load it. **Important:** `@reloadscript` also reloads
`yellow_fabre.txt` and resets its temporary 30-kill/active-monster counters;
do not use this casually in a public server or while Yellow Fabre is alive.
Review map-server logs for script parse errors.

The first visual test is to go to Prontera `167,187` and talk to the World
Relic Keeper. In this stage, it **does not consume souls, grant relic items,
reserve a world slot, change ownership, or mutate the database**.

## Backend required before turning on renewal

1. Confirm a global maximum circulation cap for Perfect knives.
2. Implement the Perfect knife and ETC Soul item in server DB + client UI.
3. Ensure card compounding/upgrade is transaction-safe and preserves the
   agreed rarity, one-socket configuration, and weapon restrictions.
4. Issue durable globally unique relic records backed by SQL transactions.
5. Tie relic validity and lease enforcement to the **actual item instance**
   (not a character variable alone), including trading/storage handling and
   expiration; enforce worldwide cap atomically.
6. Implement eligible-kill soul earning with spawn-source validation;
   account-bound storage and anti-exploit checks.
7. Make renewal consume 300 souls only after acquiring a transaction lock and
   verifying the live relic's serial, ownership, and time window. Roll back
   if any check fails. Handle interruption and duplicate requests safely.
8. Handle inactive/expired relics, free the limited slot exactly once, and
   preserve a commemorative keepsake if desired.
9. Test restart recovery, transfer restrictions, double renewal, concurrent
   claims, expirations during login, and invalid/manually spawned mobs.

Do not advertise renewal as live until the above checks have been implemented
and verified on a staging server.

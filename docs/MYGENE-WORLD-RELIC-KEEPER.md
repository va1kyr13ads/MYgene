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

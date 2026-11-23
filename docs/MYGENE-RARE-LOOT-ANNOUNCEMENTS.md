# MYgene rare loot announcements (development branch)

## Player-facing rule

World announcements start with the monster name. A **successful** inventory
receipt for a monster item is eligible when the MYgene server-adjusted chance
**before Bubble Gum** is strictly lower than 0.10% (1 through 9 in rAthena's
1/100-of-a-percent drop units). Exactly 0.10% does not qualify.

- One eligible item: `Red Thief Bug dropped Thief Bug Card [0.04%] to MYgeneNovice01`
- Multiple from a kill, one receiver:
  `Red Thief Bug dropped: Thief Bug Card [0.04%] + Red Thief Bug Card [0.01%] to MYgeneNovice01`
- Legendary Bubble Gum:
  `Red Thief Bug dropped Thief Bug Card [0.04%] to MYgeneNovice01 [Legendary Bubble Gum: 100.00%]`
- Bubble Gum and HE Bubble Gum:
  `[Bubble Gum: <effective rate>%]` or `[HE Bubble Gum: <effective rate>%]`.
  If effective rates differ between items, the modifier bracket is placed by
  the affected item instead of falsely advertising a shared rate.

The first bracket contains the **MYgene server-adjusted chance**, including
the applicable 4x / 3x / 2x item drop server rates, but excluding the active
Bubble Gum status. The Gum bracket appears only when Gum changes that drop
calculation. MYgene's fixed exclusive Slayer weapon/card chances are not
multiplied by the global server item rate; Legendary Gum makes their successful
roll certain for the item's own script, but ordinary/HE Gum do not modify their
scripted chance.

## Implementation

- A monster's unique GID and drop metadata travel from `mob.cpp` into a
  delayed drop and a `flooritem_data`, then through `party_share_loot`.
- `party_share_loot` notifies the announcer after `pc_additem` succeeds,
  using the real party-loot receiver; it never announces a failed pickup.
- MVP rewards notify immediately on successful inventory grant, otherwise
  carry the same metadata onto their floor fallback.
- `mygene_rare_reward` is the script bridge used only for Yellow Fabre and
  Red Thief Bug special weapons/cards. Weapons continue to grant to inventory
  first with a floor fallback; their custom cards stay on the floor until picked
  up. Uncollected ground items produce no announcement.
- A 1,500 ms window collects received rare items with the same monster GID
  and recipient into a single world broadcast. Delayed floor pickups outside
  that window can produce a separate announcement; we intentionally do **not**
  announce possible floor rewards before they are actually collected.
- Each receiver has their own batch; never attribute party-shared items
  automatically to the killer.
- Existing generic pre-pickup regular/MVP rare broadcasts are removed for this
  branch to avoid early and duplicate announcements.
- `rare_drop_announce: 9` enables this threshold. An override in
  `conf/import/battle_conf.txt` may replace the checked-in default.

## Before playtesting

Do not switch branches on a running public server. Save the current
Codespaces configuration, back up the database, verify no active players,
and build on a separate test server with the approved Windows client.
Run `make map` and `./map-server --run-once` in the build environment;
use the repository NPC validation workflow on the draft PR for both
Pre-Renewal and Renewal parser/build checks.

### Test cases

1. Confirm no world message for 0.10% or higher MYgene server rate.
2. Under Legendary Bubble Gum, kill a Red Thief Bug with inventory space:
   obtain Thief Bug Card (normal database item) and the 0.05% exclusive sword
   directly; the script card remains on the ground and should **not** appear
   until picked up. Each line shows the correct per-item percentage.
3. Pick up the Red Thief Bug Card quickly after kill: it should join the
   same batch if within 1.5 seconds.
4. Leave the custom card on the floor until it despawns: it should never
   be announced.
5. Test full inventory: the special weapon becomes a floor drop and is
   announced on receipt, not when rolled.
6. With regular Bubble Gum (SC_ITEMBOOST +100) and HE Bubble Gum (+200),
   check the reported effective chance matches `mob_getdroprate`.
7. Have a party distribute rare loot to a different member: the broadcast
   must show the actual recipient.
8. Test MVP reward in inventory and floor fallback separately.
9. Check that ordinary non-monster `makeitem` calls never trigger a rare
   announcement.
10. Under a high quantity of rare drops, verify the combined message fits
    the approved Windows client's global chat display.

This feature branch is not deployed. A passing build alone does not prove
live Windows client behavior; playtest against the intended running setup.

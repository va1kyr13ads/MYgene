# MYgene Slayer custom IDs and live-data migration gate

Source-only update on 2026-11-23. The protected milestone **milestone/slayer-working-2026-11-23** has not been changed.

## Item ID allocation

| Old ID | New ID | Custom Slayer item |
|---:|---:|---|
| 31001 | 60001 | Fabre Slayer Knife |
| 31002 | 60002 | Yellow Fabre Card |
| 31003 | 60003 | Shared Attraction Potion |
| 31004 | 60004 | Perfect Fabre Slayer Knife |
| 31005 | 60005 | Soul item, **reserved but not yet defined** |
| 31006 | 60006 | Thief Bug Slayer Sword |
| 31007 | 60007 | Red Thief Bug Card |
| 31008 | 60008 | Perfect Thief Bug Slayer Sword |
| 31009 | 60009 | Legendary Bubble Gum |
| — | 60010 | Chonchon Slayer Bow |
| — | 60011 | Blue Chon Chon Card |
| — | 60012 | Perfect Chonchon Slayer Bow |

All IDs 60001–60012 are free in the tracked official Pre-Renewal and Renewal equip/usable/etc item databases. A new CI regression checks these IDs so later official DB upgrades cannot silently collide.

## Monster IDs (unchanged)

| ID | Custom monster |
|---:|---|
| 31050 | Yellow Fabre |
| 31051 | Red Thief Bug |
| 31052 | Blue Chon Chon |

The three monster IDs are free in both official `db/pre-re/mob_db.yml` and `db/re/mob_db.yml`. Custom monster IDs are separate from item IDs. Do not change IDs unnecessarily: the monster and encounter logic already use 31050–31052.

## Critical production release blocker

**Source renumbering is not a live-player-item migration.** Earlier MYgene item IDs 31001–31009 collide with legitimate Renewal cards. Blind numerical SQL replacement can convert real Renewal cards into MYgene weapons or vice versa, including cards compounded in equipment. Do NOT merge or deploy this source change onto a populated server until migration is planned and verified.

1. Stop writes in a coordinated maintenance window. Back up the complete live SQL database and local Windows client/config, then **verify a restore** in an isolated test environment. Preserve the known-good milestone.
2. Inventory all installed schema tables and columns that store item IDs, equipped items, card socket IDs, cart, character storage, guild storage, mail/auction if present, and relevant logs or delayed deliveries. Inspect the actual schema rather than assuming table names.
3. Determine **provenance** of each legacy numeric ID instance (creation history/rollout date/logs/previous snapshots/instance attributes). A raw ID cannot distinguish a custom item from a legitimate official Renewal card. **Abort if any instance is ambiguous.**
4. On the restored isolated copy, prepare an explicit *per-item-instance* migration manifest limited to proven MYgene items. Use reviewed transactions, before/after item-instance totals and checksums, correct card-slot rewrites, and verified rollback. Do not rewrite any official item combos.
5. Deploy matching source, compiled server, and Windows client together only after passing both Renewal/Pre-Renewal `map-server --run-once`, Slayer drop/proc/encounter/GM upgrade tests, Rust Windows tests and release build, and migration data-integrity tests.
6. Obtain explicit approval before production SQL migration. If an invariant fails, restore the backup and previous server/client build. No automatic player-item remapping or live deployment is included in this change.

Read-only schema discovery aid:

```sql
SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND COLUMN_NAME IN ('nameid', 'item_id', 'card0', 'card1', 'card2', 'card3')
ORDER BY TABLE_NAME, ORDINAL_POSITION;
```

**No live SQL backup, per-instance migration, or deployment has been executed by this source-only update.**

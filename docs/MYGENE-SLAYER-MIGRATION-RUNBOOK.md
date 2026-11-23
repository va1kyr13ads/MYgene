# Audited Slayer ID Migration — operator runbook

**Status:** Prepared migration tooling, **NOT** a completed live migration. Do not deploy the new Slayer item ID mapping to a populated world until these steps succeed. The protected milestone remains unchanged.

The migration program is \`tools/migrate_mygene_slayer_ids.py\`; the offline unit tests are \`tools/test_migrate_mygene_slayer_ids.py\`. It handles **all nine** old IDs \`31001–31009\` → \`60001–60009\` (ID 60005 is reserved). New Blue item IDs \`60010–60012\` and custom monster IDs \`31050–31052\` are unchanged.

## Why migration cannot be automatic

Every old MYgene item ID is *also an official Renewal card ID*. \`31001\` may describe either a Fabre Slayer Knife or an official card, and an old card can appear in equipment \`card0\`–\`card3\` sockets. Neither its ID nor its current container alone proves its origin. The tool **refuses to guess** and requires explicit per-cell decisions with independent evidence. \`keep_official\` leaves genuine official cards untouched; \`migrate\` converts only positively identified MYgene instances. The audit records full-row SHA256 fingerprints to detect changed equipment, stack sizes, card sockets, etc.

The stock rAthena schema also defines \`inventory\`, \`cart_inventory\`, \`storage\`, \`guild_storage\`, \`auction\`, \`picklog\`, etc. with **MyISAM** storage engines. MyISAM does **not** support rollback; even \`START TRANSACTION\` does not make writes safe. The tool categorically refuses writes to affected non-InnoDB tables. Converting engines must be done separately in a documented offline rehearsal and maintenance window (never automatically by this tool).

The schema audit dynamically discovers all SQL tables with \`nameid\`, \`item_id\`, \`itemid\`, or \`card0\`–\`card3\`. It includes character inventory, cart, personal/guild/VIP storage, auction, mail attachments, picklog, guild-storage log, market, sales, roulette, buying-store items, feedinglog and any other installed tables with those columns. The audit is read-only, uses the installed table schema and primary keys, and emits local *sensitive* records for review. Genuine historical-log entries should normally be marked \`keep_official\` only when proven official; historical entries representing MYgene items can be explicitly migrated after reviewing whether log rewriting is desirable. Never hide or omit unresolved candidates.

## Prerequisites

1. Stop all game server processes and all background SQL writers. Confirm no active writes. Record the exact server/client commits and preserve config files and the protected Slayer milestone.
2. Take a full, point-in-time SQL dump of the **actual live** character/login/log schemas and a backup of Windows client/config files. Restore the dump into an isolated test environment and *verify inventories, equipment, storage and counts*. Record a restore receipt as a local text file. The script can check that the backup exists and hash it, but **cannot independently prove a successful restore**.
3. Assess installed SQL engines. Rehearse transactional InnoDB conversion on a **restored isolated database**, preserving data and indexes. If any table with approved changes remains MyISAM, \`apply\` will **block**. Explicitly plan and approve any eventual production engine migration.
4. Obtain independent evidence for each legacy item instance: item-origin logs, previous backups, rollout dates, and instance properties. If provenance is ambiguous, keep the manifest unreviewed and **do not apply**.
5. Prepare a separate local credentials file outside the Git checkout; \`pymysql\` is required for database operations.

Example local config (do **not** commit secrets):

\`\`\`json
{"host":"127.0.0.1","port":3306,"user":"migration_operator","password":"REPLACE_LOCALLY","database":"ragnarok"}
\`\`\`

## Procedure

Run from the server repository checkout against the *restored isolated* database first:

\`\`\`bash
python3 -m pip install pymysql
python3 -m unittest discover -s tools -p 'test_migrate_mygene_slayer_ids.py' -v
python3 tools/migrate_mygene_slayer_ids.py audit \
  --config /secure/db-credentials.json \
  --output /secure/slayer-review-manifest.json
\`\`\`

Open the generated manifest in a secure editor. For every \`candidates[].cells[]\`, change \`"decision": "unreviewed"\` to either \`"migrate"\` or \`"keep_official"\` and add a specific \`"evidence"\` statement (at least 12 characters). A multi-carded weapon is reviewed **per cell**, not per row. No bulk selection by ID is supported.

\`\`\`bash
python3 tools/migrate_mygene_slayer_ids.py validate \
  --manifest /secure/slayer-review-manifest.json
python3 tools/migrate_mygene_slayer_ids.py apply \
  --config /secure/db-credentials.json \
  --manifest /secure/slayer-review-manifest.json \
  --journal /secure/slayer-migration-journal.json
\`\`\`

The first apply invocation is **dry run** and does not write. Resolve every error before proceeding. Actual conversion is gated on explicit approval, stopped server, backup and restore receipt:

\`\`\`bash
python3 tools/migrate_mygene_slayer_ids.py apply \
  --config /secure/db-credentials.json \
  --manifest /secure/slayer-review-manifest.json \
  --journal /secure/slayer-migration-journal.json \
  --backup-file /secure/complete-db-backup.sql \
  --restore-receipt /secure/test-restore-verified.txt \
  --server-offline --operator-approval --execute
\`\`\`

The tool checks every candidate row's original fingerprint, uses \`SELECT ... FOR UPDATE\`, updates only explicitly approved cells (including compounded card slots), checks every post-update row, and creates a private durable write-ahead rollback journal before committing. All affected tables **must use InnoDB**.

To inspect or execute a rollback **while servers are stopped**, use the same safety gates with \`rollback\` instead of \`apply\` and \`--journal\` instead of \`--manifest\`. It refuses rows modified since migration and restores only journaled cells, checking the original row fingerprints after each reversal. If database state is uncertain or a nontransactional table was involved outside the tool, restore the full verified backup instead.

## Final release gate

Use the matching unmerged Windows client PR alongside the server PR; check \`cargo test --locked\`, Windows release build, server Slayer regression tests, full Pre-Renewal/Renewal startup, and in-game checks for three encounter families, original cards, storage/equipped items, drops, Gum timer, boss immunity and GM Perfect upgrades.

**No live DB connectivity, live SQL dump, restore receipt, offline maintenance window or provenance review was available during authoring; no live migration has been executed.**

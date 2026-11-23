#!/usr/bin/env python3
"""Audited, fail-closed MYgene Slayer item ID migration.

Requires PyMySQL only for MySQL commands: python3 -m pip install pymysql.
No secrets or player records are written to GitHub; local audit, manifest and
journal are sensitive. This program NEVER selects which legacy rows are truly
MYgene items. A human must classify every ambiguous cell from independent
provenance before any write. MyISAM/nontransactional tables are rejected.
"""
import argparse
import copy
import datetime as dt
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys

OLD_TO_NEW = {n: n + 29000 for n in range(31001, 31010)}
ITEM_COLUMNS = ("nameid", "item_id", "itemid", "card0", "card1", "card2", "card3")
MIGRATE = "migrate"
KEEP = "keep_official"
VERSION = 1


class MigrationError(RuntimeError):
    pass


def identifier(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise MigrationError("Unsafe SQL identifier")
    return chr(96) + name + chr(96)


def canonical(value):
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [canonical(x) for x in value]
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return {"date": value.isoformat()}
    if isinstance(value, Decimal):
        return {"decimal": str(value)}
    if isinstance(value, bytes):
        return {"hex": value.hex()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise MigrationError("Unsupported SQL value type: " + str(type(value)))


def fingerprint(row):
    content = json.dumps(canonical(row), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def write_private(path, data, replace=False):
    path = Path(path)
    if path.exists() and not replace:
        raise MigrationError("Refusing to overwrite existing file: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def connect(config_path):
    try:
        import pymysql
    except ImportError as e:
        raise MigrationError("Install PyMySQL locally: pip install pymysql") from e
    config = load_json(config_path)
    allowed = {"host", "port", "user", "password", "database", "unix_socket",
               "ssl_ca", "ssl_cert", "ssl_key"}
    if not isinstance(config, dict) or set(config) - allowed:
        raise MigrationError("Unexpected DB config keys")
    if not config.get("database") or not config.get("user"):
        raise MigrationError("Config requires database and user")
    return pymysql.connect(cursorclass=pymysql.cursors.DictCursor,
                           autocommit=False, connect_timeout=15,
                           read_timeout=120, write_timeout=120, **config)


def rows(conn, sql, params=()):
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def one(conn, sql, params=()):
    matches = rows(conn, sql, params)
    if len(matches) != 1:
        raise MigrationError("Expected one SQL row; got " + str(len(matches)))
    return matches[0]


def catalog(conn):
    meta = rows(conn, """SELECT TABLE_NAME, ENGINE FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'""")
    cols = rows(conn, """SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()""")
    keys = rows(conn, """SELECT TABLE_NAME, COLUMN_NAME, ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE() AND CONSTRAINT_NAME = 'PRIMARY'
        ORDER BY TABLE_NAME, ORDINAL_POSITION""")
    fields = {}
    for c in cols:
        fields.setdefault(c["TABLE_NAME"], set()).add(c["COLUMN_NAME"])
    primary = {}
    for k in keys:
        primary.setdefault(k["TABLE_NAME"], []).append(k["COLUMN_NAME"])
    result = {}
    for table in meta:
        name = table["TABLE_NAME"]
        found = sorted(set(ITEM_COLUMNS) & fields.get(name, set()))
        if found:
            result[name] = {"engine": table["ENGINE"], "columns": found,
                            "pk": primary.get(name, [])}
    return result


def sql_candidates(table, columns):
    where = " OR ".join(
        identifier(col) + " IN (" + ",".join(["%s"] * len(OLD_TO_NEW)) + ")"
        for col in columns
    )
    values = tuple(x for _ in columns for x in OLD_TO_NEW)
    return "SELECT * FROM " + identifier(table) + " WHERE " + where, values


def candidate_rows(conn, metadata):
    candidates = []
    for table in sorted(metadata):
        desc = metadata[table]
        sql, args = sql_candidates(table, desc["columns"])
        for row in rows(conn, sql, args):
            if not desc["pk"]:
                raise MigrationError("Legacy ID found in table lacking PRIMARY KEY: " + table)
            record = {
                "table": table,
                "pk": {k: row[k] for k in desc["pk"]},
                "before_sha256": fingerprint(row),
                "cells": [],
            }
            for col in desc["columns"]:
                value = row[col]
                if value in OLD_TO_NEW:
                    record["cells"].append({
                        "column": col, "old_id": value,
                        "new_id": OLD_TO_NEW[value],
                        "decision": "unreviewed", "evidence": "",
                    })
            if record["cells"]:
                candidates.append(record)
    return candidates


def identity(record):
    return (record["table"],
            json.dumps(canonical(record["pk"]), sort_keys=True))


def assert_valid_manifest(manifest):
    if manifest.get("format") != "mygene-slayer-migration" or manifest.get("version") != VERSION:
        raise MigrationError("Wrong migration manifest format/version")
    if not isinstance(manifest.get("catalog"), dict):
        raise MigrationError("Manifest missing table catalog")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list):
        raise MigrationError("Manifest missing candidates")
    seen = set()
    changes = 0
    for record in candidates:
        key = identity(record)
        if key in seen:
            raise MigrationError("Duplicate record in manifest: " + str(key))
        seen.add(key)
        if not record.get("before_sha256") or not record.get("cells"):
            raise MigrationError("Incomplete candidate record")
        metadata = manifest["catalog"].get(record["table"])
        if not metadata or sorted(record["pk"]) != sorted(metadata["pk"]):
            raise MigrationError("Candidate primary-key metadata mismatch")
        columns = set()
        for cell in record["cells"]:
            col, old, new = cell["column"], cell["old_id"], cell["new_id"]
            if col in columns or col not in metadata["columns"]:
                raise MigrationError("Duplicate or unknown item cell")
            columns.add(col)
            if OLD_TO_NEW.get(old) != new:
                raise MigrationError("Invalid legacy ID mapping")
            if cell["decision"] not in (MIGRATE, KEEP):
                raise MigrationError("Unreviewed/invalid decision: " + str(key) + " " + col)
            if len(str(cell.get("evidence", "")).strip()) < 12:
                raise MigrationError("Missing specific per-cell provenance evidence: " + str(key))
            changes += cell["decision"] == MIGRATE
    return changes


def assert_same_catalog(a, b):
    if set(a) != set(b):
        raise MigrationError("Item-bearing table catalog changed after audit")
    for name in a:
        if a[name]["columns"] != b[name]["columns"] or a[name]["pk"] != b[name]["pk"]:
            raise MigrationError("Schema columns/primary key changed: " + name)


def assert_live_candidates(conn, manifest, metadata):
    current = candidate_rows(conn, metadata)
    baseline = manifest["candidates"]
    if len(current) != len(baseline):
        raise MigrationError("Legacy-item row count changed since audit")
    found = {identity(x): x for x in current}
    if len(found) != len(current):
        raise MigrationError("Duplicate database row identity")
    for expected in baseline:
        fresh = found.get(identity(expected))
        if fresh is None or fresh["before_sha256"] != expected["before_sha256"]:
            raise MigrationError("Legacy-item row changed since audit: " + str(identity(expected)))
        expected_cells = {(x["column"], x["old_id"]) for x in expected["cells"]}
        fresh_cells = {(x["column"], x["old_id"]) for x in fresh["cells"]}
        if expected_cells != fresh_cells:
            raise MigrationError("Legacy ID cell changed since audit")


def affected_tables(manifest):
    return {r["table"] for r in manifest["candidates"]
            if any(c["decision"] == MIGRATE for c in r["cells"])}


def assert_transactional(metadata, tables):
    for table in sorted(tables):
        engine = (metadata[table]["engine"] or "").upper()
        if engine != "INNODB":
            raise MigrationError(
                "Unsafe write blocked: " + table + " uses " + engine +
                ", not InnoDB. rAthena often uses MyISAM. Migrate the tables "
                "to InnoDB in a rehearsed maintenance operation first."
            )


def select_pk(conn, record, lock=False):
    keys = record["pk"]
    criteria = " AND ".join(identifier(k) + " = %s" for k in keys)
    sql = "SELECT * FROM " + identifier(record["table"]) + " WHERE " + criteria
    if lock:
        sql += " FOR UPDATE"
    return one(conn, sql, tuple(keys.values()))


def execute_update(conn, record, cells, reverse=False):
    updates = [(c["column"], c["old_id"] if reverse else c["new_id"]) for c in cells]
    if not updates:
        return
    stmt = ("UPDATE " + identifier(record["table"]) + " SET " +
            ", ".join(identifier(c) + " = %s" for c, _ in updates) +
            " WHERE " +
            " AND ".join(identifier(k) + " = %s" for k in record["pk"]))
    args = [v for _, v in updates] + list(record["pk"].values())
    with conn.cursor() as cur:
        count = cur.execute(stmt, args)
        if count != 1:
            raise MigrationError("Expected one updated row; got " + str(count))


def verify_backup(args):
    if not args.execute:
        return "DRY-RUN"
    if not args.server_offline or not args.operator_approval:
        raise MigrationError("Writes require --server-offline and --operator-approval")
    if not args.backup_file or not args.restore_receipt:
        raise MigrationError("Writes require backup file and independent restore receipt")
    backup = Path(args.backup_file)
    receipt = Path(args.restore_receipt)
    if not backup.is_file() or backup.stat().st_size < 1024:
        raise MigrationError("Missing/empty SQL backup")
    if not receipt.is_file() or not receipt.read_text(encoding="utf-8").strip():
        raise MigrationError("Missing operator-supplied test-restore receipt")
    digest = hashlib.sha256()
    with backup.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    print("Backup SHA256:", digest.hexdigest(),
          "(restore evidence is operator-supplied, not automatically verified)")
    return digest.hexdigest()


def do_audit(args):
    with connect(args.config) as conn:
        metadata = catalog(conn)
        found = candidate_rows(conn, metadata)
        manifest = {"format": "mygene-slayer-migration", "version": VERSION,
                    "database": load_json(args.config)["database"],
                    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "catalog": metadata, "candidates": found}
        write_private(args.output, manifest)
        print("Read-only audit saved:", args.output,
              "records:", len(found),
              "cells:", sum(len(r["cells"]) for r in found),
              "review ALL cells as migrate or keep_official with evidence.")


def do_validate(args):
    manifest = load_json(args.manifest)
    n = assert_valid_manifest(manifest)
    print("Manifest reviewed:", len(manifest["candidates"]),
          "records;", n, "cells approved for migration.")
    if not n:
        print("No IDs are selected for conversion.")


def do_apply(args):
    manifest = load_json(args.manifest)
    num = assert_valid_manifest(manifest)
    proof = verify_backup(args)
    with connect(args.config) as conn:
        actual = catalog(conn)
        assert_same_catalog(manifest["catalog"], actual)
        affected = affected_tables(manifest)
        assert_transactional(actual, affected)
        if manifest.get("database") != load_json(args.config)["database"]:
            raise MigrationError("Audit was generated from a different database")
        assert_live_candidates(conn, manifest, actual)
        print("Preflight OK; affected tables:", sorted(affected),
              "; approved cells:", num)
        if not args.execute:
            print("DRY RUN: no SQL updates. --execute requires verified backup, "
                  "offline server, and approval.")
            return
        if not num:
            raise MigrationError("No selected item changes")
        if Path(args.journal).exists():
            raise MigrationError("Journal path already exists")
        journal = {"format": "mygene-slayer-journal", "version": VERSION,
                   "database": manifest["database"],
                   "backup_sha256": proof, "status": "prepared",
                   "records": []}
        try:
            conn.begin()
            # Lock AND fingerprint every audited candidate, including official
            # instances left unchanged, to catch any race before modification.
            for rec in manifest["candidates"]:
                original = select_pk(conn, rec, lock=True)
                if fingerprint(original) != rec["before_sha256"]:
                    raise MigrationError("Row changed during transaction: " + str(identity(rec)))
                cells = [c for c in rec["cells"] if c["decision"] == MIGRATE]
                if not cells:
                    continue
                changed = copy.deepcopy(original)
                for c in cells:
                    if changed[c["column"]] != c["old_id"]:
                        raise MigrationError("Old-ID mismatch during transaction")
                    changed[c["column"]] = c["new_id"]
                expected_after = fingerprint(changed)
                execute_update(conn, rec, cells)
                if fingerprint(select_pk(conn, rec, lock=True)) != expected_after:
                    raise MigrationError("Post-update checksum mismatch")
                journal["records"].append({
                    "table": rec["table"], "pk": rec["pk"], "cells": cells,
                    "before_sha256": rec["before_sha256"],
                    "after_sha256": expected_after,
                })
            # Durable write-ahead journal before the database COMMIT. If the
            # process crashes during COMMIT, rollback checks the actual state.
            write_private(args.journal, journal)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        journal["status"] = "committed"
        write_private(args.journal, journal, replace=True)
        print("COMMITTED:", len(journal["records"]), "rows; journal:", args.journal)


def do_rollback(args):
    journal = load_json(args.journal)
    if journal.get("format") != "mygene-slayer-journal" or journal.get("version") != VERSION:
        raise MigrationError("Invalid rollback journal")
    verify_backup(args)
    with connect(args.config) as conn:
        if journal["database"] != load_json(args.config)["database"]:
            raise MigrationError("Wrong database for rollback")
        metadata = catalog(conn)
        assert_transactional(metadata, {r["table"] for r in journal["records"]})
        for rec in journal["records"]:
            if rec["table"] not in metadata or sorted(rec["pk"]) != sorted(metadata[rec["table"]]["pk"]):
                raise MigrationError("Rollback schema mismatch")
            current = select_pk(conn, rec)
            if fingerprint(current) not in (rec["before_sha256"], rec["after_sha256"]):
                raise MigrationError("Cannot safely roll back modified row: " + str(identity(rec)))
        if not args.execute:
            print("ROLLBACK DRY RUN:", len(journal["records"]),
                  "rows eligible; no SQL updates.")
            return
        try:
            conn.begin()
            for rec in journal["records"]:
                current = select_pk(conn, rec, lock=True)
                digest = fingerprint(current)
                if digest == rec["before_sha256"]:
                    continue  # Already rolled back or transaction never committed.
                if digest != rec["after_sha256"]:
                    raise MigrationError("Rollback row changed during transaction")
                execute_update(conn, rec, rec["cells"], reverse=True)
                if fingerprint(select_pk(conn, rec, lock=True)) != rec["before_sha256"]:
                    raise MigrationError("Rollback checksum mismatch")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        journal["status"] = "rolled_back"
        write_private(args.journal, journal, replace=True)
        print("ROLLBACK COMPLETE:", len(journal["records"]), "rows.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    audit = sub.add_parser("audit", help="Read-only inventory of legacy-ID candidates")
    audit.add_argument("--config", required=True, help="Local untracked MySQL JSON config")
    audit.add_argument("--output", required=True)
    validate = sub.add_parser("validate", help="Require an explicit decision for every old-ID cell")
    validate.add_argument("--manifest", required=True)
    apply = sub.add_parser("apply", help="Dry-run or transactional conversion, fail closed")
    apply.add_argument("--config", required=True)
    apply.add_argument("--manifest", required=True)
    apply.add_argument("--journal", required=True)
    rollback = sub.add_parser("rollback", help="Reverse precisely journaled item conversions")
    rollback.add_argument("--config", required=True)
    rollback.add_argument("--journal", required=True)
    for subparser in (apply, rollback):
        subparser.add_argument("--execute", action="store_true")
        subparser.add_argument("--server-offline", action="store_true")
        subparser.add_argument("--operator-approval", action="store_true")
        subparser.add_argument("--backup-file")
        subparser.add_argument("--restore-receipt")
    args = parser.parse_args(argv)
    try:
        {"audit": do_audit, "validate": do_validate,
         "apply": do_apply, "rollback": do_rollback}[args.command](args)
    except (MigrationError, OSError, ValueError, KeyError) as err:
        print("BLOCKED:", err, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

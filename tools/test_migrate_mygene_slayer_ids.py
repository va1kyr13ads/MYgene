"""Fail-closed unit tests for Slayer ID migration, no DB required."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate_mygene_slayer_ids as m


class MigrationSafety(unittest.TestCase):
    def sample(self):
        row = {"id": 17, "nameid": 31001, "card0": 31002,
               "card1": 0, "amount": 1, "unique_id": 99}
        cells = [{"column": k, "old_id": row[k], "new_id": m.OLD_TO_NEW[row[k]],
                  "decision": "migrate", "evidence": "Verified legacy Slayer creation log"}
                 for k in ("nameid", "card0")]
        rec = {"table": "inventory", "pk": {"id": 17},
               "before_sha256": m.fingerprint(row), "cells": cells}
        metadata = {"inventory": {"pk": ["id"], "columns": ["nameid", "card0"], "engine": "InnoDB"}}
        return {"format": "mygene-slayer-migration", "version": 1,
                "database": "test", "catalog": metadata, "candidates": [rec]}

    def test_all_ids_covered(self):
        self.assertEqual(set(m.OLD_TO_NEW), set(range(31001, 31010)))
        self.assertEqual(set(m.OLD_TO_NEW.values()), set(range(60001, 60010)))
        self.assertEqual(m.OLD_TO_NEW[31002], 60002)
        self.assertEqual(m.OLD_TO_NEW[31007], 60007)

    def test_compounded_card_and_weapon_are_separate_choices(self):
        doc = self.sample()
        self.assertEqual(m.assert_valid_manifest(doc), 2)
        doc["candidates"][0]["cells"][1]["decision"] = m.KEEP
        self.assertEqual(m.assert_valid_manifest(doc), 1)

    def test_unreviewed_refused(self):
        doc = self.sample()
        doc["candidates"][0]["cells"][1]["decision"] = "unreviewed"
        with self.assertRaises(m.MigrationError):
            m.assert_valid_manifest(doc)

    def test_no_evidence_refused(self):
        doc = self.sample()
        doc["candidates"][0]["cells"][0]["evidence"] = "ok"
        with self.assertRaises(m.MigrationError):
            m.assert_valid_manifest(doc)

    def test_wrong_mapping_refused(self):
        doc = self.sample()
        doc["candidates"][0]["cells"][1]["new_id"] = 60010
        with self.assertRaises(m.MigrationError):
            m.assert_valid_manifest(doc)

    def test_duplicate_row_refused(self):
        doc = self.sample()
        doc["candidates"].append(copy.deepcopy(doc["candidates"][0]))
        with self.assertRaises(m.MigrationError):
            m.assert_valid_manifest(doc)

    def test_migration_of_item_id_in_primary_key(self):
        record = {"table": "market", "pk": {"name": "Item Shop", "nameid": 31008}}
        cells = [{"column": "nameid", "old_id": 31008, "new_id": 60008}]
        self.assertEqual(m.migrated_pk(record, cells),
                         {"name": "Item Shop", "nameid": 60008})

    def test_historical_log_exemption_restricted(self):
        doc = self.sample()
        doc["candidates"][0]["cells"][1]["decision"] = m.KEEP_HISTORICAL
        with self.assertRaises(m.MigrationError):
            m.assert_valid_manifest(doc)
        doc["candidates"][0]["table"] = "picklog"
        doc["catalog"] = {"picklog": doc["catalog"]["inventory"]}
        self.assertEqual(m.assert_valid_manifest(doc), 1)

    def test_nontransactional_tables_refused(self):
        md = self.sample()["catalog"]
        md["inventory"]["engine"] = "MyISAM"
        with self.assertRaises(m.MigrationError):
            m.assert_transactional(md, {"inventory"})

    def test_schema_drift_refused(self):
        metadata = self.sample()["catalog"]
        drifted = copy.deepcopy(metadata)
        drifted["inventory"]["columns"] = ["nameid"]
        with self.assertRaises(m.MigrationError):
            m.assert_same_catalog(metadata, drifted)

    def test_sql_identifiers_sanitized(self):
        self.assertEqual(m.identifier("guild_storage"), "\x60guild_storage\x60")
        for unsafe in ("inventory;DROP", "inventory.nameid", "a b", "", "x\x60"):
            with self.assertRaises(m.MigrationError):
                m.identifier(unsafe)

    def test_mysql_candidate_scan_includes_card_slots(self):
        stmt, args = m.sql_candidates("inventory", ["nameid", "card0", "card1"])
        self.assertIn("card0", stmt)
        self.assertIn("card1", stmt)
        self.assertEqual(len(args), 27)
        self.assertEqual(args.count(31002), 3)

    def test_checksum_not_only_item_id(self):
        row = {"id": 3, "nameid": 31001, "card0": 31002, "amount": 1}
        newer = dict(row, amount=2)
        self.assertNotEqual(m.fingerprint(row), m.fingerprint(newer))

    def test_private_manifest_permissions(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "audit.json"
            m.write_private(p, self.sample())
            self.assertEqual(m.load_json(p)["database"], "test")
            with self.assertRaises(m.MigrationError):
                m.write_private(p, self.sample())
            if sys.platform != "win32":
                self.assertEqual(p.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()

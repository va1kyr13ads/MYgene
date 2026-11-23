"""End-to-end transaction rehearsal on an EPHEMERAL MariaDB CI database.

Do NOT point this test at a live or populated database. Requires
MYGENE_MIGRATION_MYSQL_TEST=1, and a fresh local CI MariaDB root connection.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migrate_mygene_slayer_ids as m


@unittest.skipUnless(os.environ.get("MYGENE_MIGRATION_MYSQL_TEST") == "1",
                     "Only runs against explicit disposable MariaDB CI service")
class MigrationMariaDBIntegration(unittest.TestCase):
    def test_apply_and_rollback(self):
        import pymysql
        root = pymysql.connect(
            host=os.environ.get("MYSQL_TEST_HOST", "127.0.0.1"),
            port=int(os.environ.get("MYSQL_TEST_PORT", "3306")),
            user=os.environ.get("MYSQL_TEST_USER", "root"),
            password=os.environ.get("MYSQL_TEST_PASSWORD", ""),
            autocommit=True, cursorclass=pymysql.cursors.DictCursor)
        # Random database name: do not reuse or overwrite any existing schema.
        database = "mygene_slayer_ci_" + uuid.uuid4().hex[:16]
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            config_path = directory / "config.json"
            manifest_path = directory / "manifest.json"
            journal_path = directory / "journal.json"
            backup_path = directory / "test-backup.sql"
            receipt_path = directory / "restore-receipt.txt"
            config = {
                "host": os.environ.get("MYSQL_TEST_HOST", "127.0.0.1"),
                "port": int(os.environ.get("MYSQL_TEST_PORT", "3306")),
                "user": os.environ.get("MYSQL_TEST_USER", "root"),
                "password": os.environ.get("MYSQL_TEST_PASSWORD", ""),
                "database": database,
            }
            try:
                with root.cursor() as cur:
                    cur.execute("CREATE DATABASE " + m.identifier(database))
                config_path.write_text(json.dumps(config), encoding="utf-8")
                with m.connect(config_path) as conn:
                    with conn.cursor() as cur:
                        cur.execute("""CREATE TABLE inventory (
                            id INT PRIMARY KEY, nameid INT, card0 INT,
                            card1 INT, card2 INT, card3 INT, amount INT,
                            unique_id BIGINT) ENGINE=InnoDB""")
                        cur.execute("""CREATE TABLE storage (
                            id INT PRIMARY KEY, nameid INT, card0 INT,
                            card1 INT, card2 INT, card3 INT, amount INT)
                            ENGINE=InnoDB""")
                        cur.execute("""CREATE TABLE guild_storage (
                            id INT PRIMARY KEY, nameid INT, card0 INT,
                            card1 INT, card2 INT, card3 INT, amount INT)
                            ENGINE=MyISAM""")
                        cur.execute("""CREATE TABLE picklog (
                            id INT PRIMARY KEY, nameid INT, card0 INT)
                            ENGINE=MyISAM""")
                        cur.execute("""INSERT INTO inventory VALUES
                            (1,31001,31002,0,0,0,1,111),
                            (2,31001,0,0,0,0,1,222)""")
                        cur.execute("""INSERT INTO storage VALUES
                            (3,31003,0,0,0,0,5)""")
                        cur.execute("""INSERT INTO guild_storage VALUES
                            (4,31006,31007,0,0,0,1)""")
                        cur.execute("""INSERT INTO picklog VALUES
                            (5,31002,0)""")
                    conn.commit()

                m.do_audit(argparse.Namespace(config=str(config_path),
                                              output=str(manifest_path)))
                manifest = m.load_json(manifest_path)
                self.assertEqual(len(manifest["candidates"]), 5)
                for rec in manifest["candidates"]:
                    for cell in rec["cells"]:
                        # Inventory id=2 and historical official-card log id=5
                        # are truly official card instances, so preserve IDs.
                        keep = ((rec["table"] == "inventory" and rec["pk"]["id"] == 2)
                                or rec["table"] == "picklog")
                        cell["decision"] = m.KEEP if keep else m.MIGRATE
                        cell["evidence"] = (
                            "Verified official card fixture, keep the exact ID"
                            if keep else
                            "Verified preexisting MYgene item and card fixture")
                m.write_private(manifest_path, manifest, replace=True)
                self.assertEqual(m.assert_valid_manifest(manifest), 5)

                def apply_args(execute):
                    return argparse.Namespace(
                        config=str(config_path), manifest=str(manifest_path),
                        journal=str(journal_path), execute=execute,
                        server_offline=True, operator_approval=True,
                        backup_file=str(backup_path),
                        restore_receipt=str(receipt_path))
                with self.assertRaises(m.MigrationError):
                    m.do_apply(apply_args(False))  # MyISAM guild_storage blocked
                with m.connect(config_path) as conn:
                    with conn.cursor() as cur:
                        cur.execute("ALTER TABLE guild_storage ENGINE=InnoDB")
                    conn.commit()
                # Engine switch is a schema/storage event: repeat audit and approval.
                manifest_path.unlink()
                m.do_audit(argparse.Namespace(config=str(config_path),
                                              output=str(manifest_path)))
                newer = m.load_json(manifest_path)
                for rec in newer["candidates"]:
                    for cell in rec["cells"]:
                        keep = ((rec["table"] == "inventory" and rec["pk"]["id"] == 2)
                                or rec["table"] == "picklog")
                        cell["decision"] = m.KEEP if keep else m.MIGRATE
                        cell["evidence"] = (
                            "Official item verified in isolated database fixture"
                            if keep else "Custom Slayer source verified in isolated fixture")
                m.write_private(manifest_path, newer, replace=True)
                self.assertEqual(m.assert_valid_manifest(newer), 5)
                m.do_apply(apply_args(False))
                self.assertFalse(journal_path.exists())
                # Read/write drift between audit and apply is caught:
                with m.connect(config_path) as conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE inventory SET amount=2 WHERE id=1")
                    conn.commit()
                with self.assertRaises(m.MigrationError):
                    m.do_apply(apply_args(False))
                with m.connect(config_path) as conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE inventory SET amount=1 WHERE id=1")
                    conn.commit()

                # Test fixture backup/restore receipt only, never a live backup.
                backup_path.write_text("CREATE TABLE fixture (x INT);\n" * 60, encoding="utf-8")
                receipt_path.write_text("CI ephemeral DB fixture restoration verified",
                                        encoding="utf-8")
                m.do_apply(apply_args(True))
                journal = m.load_json(journal_path)
                self.assertEqual(journal["status"], "committed")
                with m.connect(config_path) as conn:
                    def item(table, id_):
                        return m.one(conn, "SELECT * FROM " + m.identifier(table)
                                     + " WHERE id=%s", (id_,))
                    self.assertEqual((item("inventory", 1)["nameid"],
                                      item("inventory", 1)["card0"]), (60001, 60002))
                    self.assertEqual(item("inventory", 2)["nameid"], 31001)
                    self.assertEqual(item("storage", 3)["nameid"], 60003)
                    self.assertEqual((item("guild_storage", 4)["nameid"],
                                      item("guild_storage", 4)["card0"]), (60006, 60007))
                    self.assertEqual(item("picklog", 5)["nameid"], 31002)

                rollback_args = argparse.Namespace(
                    config=str(config_path), journal=str(journal_path),
                    execute=False, server_offline=True, operator_approval=True,
                    backup_file=str(backup_path), restore_receipt=str(receipt_path))
                m.do_rollback(rollback_args)
                self.assertEqual(m.load_json(journal_path)["status"], "committed")
                rollback_args.execute = True
                m.do_rollback(rollback_args)
                self.assertEqual(m.load_json(journal_path)["status"], "rolled_back")
                with m.connect(config_path) as conn:
                    restored = m.one(conn, "SELECT * FROM inventory WHERE id=1")
                    self.assertEqual((restored["nameid"], restored["card0"]),
                                     (31001, 31002))
                    restored = m.one(conn, "SELECT * FROM guild_storage WHERE id=4")
                    self.assertEqual((restored["nameid"], restored["card0"]),
                                     (31006, 31007))
            finally:
                with root.cursor() as cur:
                    cur.execute("DROP DATABASE IF EXISTS " + m.identifier(database))
                root.close()


if __name__ == "__main__":
    unittest.main()

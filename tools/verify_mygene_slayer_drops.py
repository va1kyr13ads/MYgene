"""Static cross-check of MYgene Slayer IDs, event wiring, and reward rates.

Does not replace a running map-server test; keeps accidental name/ID and
death-event regressions from silently breaking custom Slayer loot.
"""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ITEM_DB = (ROOT / "db/import/item_db.yml").read_text(encoding="utf-8")
MOB_DB = (ROOT / "db/import/mob_db.yml").read_text(encoding="utf-8")


def item_block(item_id: int) -> str:
    match = re.search(
        rf"(?ms)^  - Id: {item_id}\s*\n(.*?)(?=^  - Id: |\Z)", ITEM_DB
    )
    if not match:
        raise AssertionError(f"Missing item {item_id}")
    return match.group(1)


class SlayerDropWiring(unittest.TestCase):
    def check_family(self, script_name, item_id, aegis, display_name, mob_id, handler, sub):
        script = (ROOT / "npc/custom/mygene" / script_name).read_text(encoding="utf-8")
        item = item_block(item_id)
        self.assertIn(f"AegisName: {aegis}", item)
        self.assertIn(f"Name: {display_name}", item)
        self.assertRegex(MOB_DB, rf"(?m)^  - Id: {mob_id}$")

        # Labeled encounter spawns and unlabeled/GM spawns are distinct
        # rAthena event paths. Each must call ONE shared reward function.
        self.assertIn(f'::{handler}"', script)
        self.assertRegex(
            script,
            rf"(?s)OnNPCKillEvent:.*?if \(killedrid == {mob_id}\) \{{\s*callsub {sub};",
        )
        self.assertRegex(script, rf"(?s){handler}:.*?callsub {sub};")
        self.assertEqual(script.count(f"callsub {sub};"), 2)
        self.assertEqual(script.count(f"\n{sub}:"), 1)

        reward_body = script.split(f"\n{sub}:")[1]
        self.assertIn("rand(1000000) < 500", reward_body)  # 0.05%
        self.assertEqual(reward_body.count(f"getitem {item_id},1;"), 1)
        self.assertEqual(reward_body.count(f"makeitem {item_id},1,"), 1)
        self.assertIn(f"checkweight({item_id},1)", reward_body)
        self.assertTrue(reward_body.rstrip().endswith("return;\n}"))

    def test_fabre_slayer(self):
        self.check_family(
            "yellow_fabre.txt", 31001, "MYGENE_FABRE_SLAYER",
            "Fabre Slayer Knife", 31050, "OnYellowFabreDead", "S_YellowRewards"
        )

    def test_thief_bug_slayer(self):
        self.check_family(
            "red_thief_bug.txt", 31006, "MYGENE_THIEF_BUG_SLAYER",
            "Thief Bug Slayer Sword", 31051, "OnRedThiefBugDead", "S_RedRewards"
        )


if __name__ == "__main__":
    unittest.main()

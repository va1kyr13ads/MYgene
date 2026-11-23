"""Static guardrails for the isolated MYgene Novice Tower Floor 4 trial.

These checks cannot prove client NPC visuals, combat balance or map geometry.
A pre-Renewal map-server --run-once and an actual in-game test are mandatory.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOWER = ROOT / "npc/custom/mygene/novice_tower"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class NoviceTowerTrial(unittest.TestCase):
    def test_separate_from_live_slayer_work(self):
        config = read("npc/scripts_custom.conf")
        paths = (
            "adventurers.txt",
            "guardian_boss.txt",
            "tower_core.txt",
            "entry.txt",
        )
        for part in paths:
            script = f"npc/custom/mygene/novice_tower/{part}"
            self.assertEqual(config.count(f"npc: {script}"), 1)

    def test_character_owned_and_no_real_party(self):
        entry = read("npc/custom/mygene/novice_tower/entry.txt")
        self.assertIn('instance_create("MYgene Novice Tower Trial", IM_CHAR)', entry)
        self.assertIn("instance_id(IM_CHAR)", entry)
        self.assertIn("if (getcharid(1) != 0)", entry)
        self.assertIn("if (Class != Job_Novice)", entry)
        self.assertIn("instance_enter(", entry)
        self.assertNotIn("MYGENE_TOWER_ROUTE =", entry)

    def test_instance_excludes_existing_npcs(self):
        for which in ["pre-re", "re"]:
            data = read(f"db/{which}/instance_db.yml")
            block = data.split("Name: MYgene Novice Tower Trial")
            self.assertEqual(len(block), 2)
            self.assertIn("NoNpc: true", block[1])
            self.assertIn("Map: 1@tower", block[1])

    def test_guardian_is_private_and_drops_no_permanent_reward(self):
        boss = read("npc/custom/mygene/novice_tower/guardian_boss.txt")
        core = read("npc/custom/mygene/novice_tower/tower_core.txt")
        self.assertIn('"MYgene_Tower_Core::OnBossDead"', boss)
        self.assertIn("unitexists(.@gid)", boss)
        self.assertIn("OnBossDead:", core)
        self.assertIn("killedgid != @MYGENE_NT_BOSS", core)
        self.assertIn("strcharinfo(3) != .@map$", core)
        self.assertIn("MYGENE_NT_TRIAL_FINISHED = 1", core)
        self.assertNotIn("jobchange", core)
        self.assertNotIn("getitem", core)

    def test_all_job_thresholds_in_fixed_order(self):
        core = read("npc/custom/mygene/novice_tower/tower_core.txt")
        allies = read("npc/custom/mygene/novice_tower/adventurers.txt")
        self.assertIn("setarray .@threshold[0],80,65,50,35,20,10;", core)
        for threshold, job in [
            (80, "Swordman"), (65, "Mage"), (50, "Archer"),
            (35, "Acolyte"), (20, "Thief"), (10, "Merchant"),
        ]:
            self.assertIn(f'[{threshold}%] {job}', allies)

        # Helpers cannot reduce the boss below 1 HP; a real player finishes.
        self.assertIn("if (.@newhp < 1) .@newhp = 1;", allies)
        self.assertIn('callfunc("MYgene_Tower_Ally_Pulse"', core)


if __name__ == "__main__":
    unittest.main()

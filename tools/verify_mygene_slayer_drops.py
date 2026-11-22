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


    def test_blue_chon_chon_bow(self):
        self.check_family(
            "blue_chon_chon.txt", 31010, "MYGENE_CHONCHON_SLAYER_BOW",
            "Chonchon Slayer Bow", 31052, "OnBlueChonChonDead", "S_BlueRewards"
        )
        script = (ROOT / "npc/custom/mygene/blue_chon_chon.txt").read_text(encoding="utf-8")
        self.assertIn(
            "killedrid != 1011 && killedrid != 1042 && killedrid != 1035", script
        )
        self.assertIn("if (.BlueActive[.@slot])", script)
        self.assertIn("if (.KillCount[.@slot] < 30)", script)
        self.assertIn(".KillCount[.@i] = 1;", script)
        self.assertNotIn("killedrid == 1091", script)  # Dragon Fly is a mini-boss.
        self.assertIn("MYGENE_LEGENDARY_GUM_UNTIL > gettimetick(2)", script)
        self.assertIn("rand(1000000) < 100", script)  # Card: 0.01%.
        self.assertIn("makeitem 31011,1,", script)
        self.assertNotIn("makeitem 31012,1,", script)  # Perfect bow never drops.
        self.assertIn("getmapxy(.@map$,.@x,.@y,BL_PC)", script)

    def test_blue_chon_chon_bow_is_ranged_and_perfect_is_not_a_drop(self):
        bow = item_block(31010)
        card = item_block(31011)
        perfect = item_block(31012)
        for token in (
            "SubType: Bow", "Range: 5", "Slots: 1", "Refineable: false",
            "Both_Hand: true",
        ):
            self.assertIn(token, bow)
        self.assertIn("Name: Blue Chon Chon Card", card)
        self.assertIn("Right_Hand: true", card)
        self.assertIn("SubType: Bow", perfect)
        self.assertIn("Name: P.C.S.B", perfect)
        self.assertIn("WeaponLevel: 4", perfect)
        self.assertIn("bonus bUnbreakableWeapon;", perfect)
        battle = (ROOT / "src/map/battle.cpp").read_text(encoding="utf-8")
        self.assertIn(
            "mob_class == 1011 || mob_class == 1042 ||", battle
        )
        self.assertIn(
            "mob_class == 1035 || mob_class == 31052;", battle
        )
        self.assertIn(
            "fabre_family || thief_bug_family || chonchon_family", battle
        )
        self.assertIn("hunted->get_bosstype() == BOSSTYPE_NONE", battle)
        self.assertIn("weapon_id == 31010 || weapon_id == 31012", battle)
        self.assertIn("weapon.card[0] == 31011 ? 90", battle)
        self.assertIn("weapon_id == 31010 ? 50 : 0", battle)

    def test_blue_chon_chon_db_and_npc_loader(self):
        npc = (ROOT / "npc/scripts_custom.conf").read_text(encoding="utf-8")
        self.assertIn("npc: npc/custom/mygene/blue_chon_chon.txt", npc)
        assert "AegisName: MYGENE_BLUE_CHON_CHON" in MOB_DB
        alias = (ROOT / "db/import/mob_avail.yml").read_text(encoding="utf-8")
        self.assertIn("Mob: MYGENE_BLUE_CHON_CHON", alias)
        self.assertIn("Sprite: CHONCHON", alias)
        from re import search
        blue_mob = search(r"(?ms)^  - Id: 31052\s*\n(.*?)(?=^  - Id: |\Z)", MOB_DB)
        self.assertIsNotNone(blue_mob)
        self.assertNotIn("Class: Boss", blue_mob.group(1))
        relic = (ROOT / "npc/custom/mygene/world_relic_keeper.txt").read_text(encoding="utf-8")
        self.assertIn("Perfect Bow Upgrade [GM]", relic)
        self.assertIn("getequipid(EQI_HAND_R) != 31010", relic)
        self.assertIn("getequipcardid(EQI_HAND_R,0) != 31011", relic)
        self.assertIn("getitem2 31012,1,1,0,0,31011,0,0,0;", relic)


if __name__ == "__main__":
    unittest.main()

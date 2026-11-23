// Copyright (c) MYgene contributors - Licensed under GNU GPL
// MYgene rare-loot metadata travels with a monster drop until inventory receipt.
// Chances use rAthena's unit: 1 = 0.01%, 10000 = 100%.
#ifndef MYGENE_RARE_LOOT_HPP
#define MYGENE_RARE_LOOT_HPP

#include <common/cbasetypes.hpp>
#include <common/mmo.hpp>

struct map_session_data;

struct mygene_rare_info {
	uint32 source_gid = 0;    // Individual monster death (not mob class).
	uint16 mob_id = 0;        // Monster database ID for the announcement.
	uint32 base_rate = 0;     // MYgene server chance before personal/Gum bonuses.
	uint32 modified_rate = 0; // Chance with the active Bubble Gum, if any.
	uint8 gum_type = 0;      // 0: none, 1: Bubble Gum, 2: HE, 3: Legendary.
};

// Queues a world broadcast only after a real successful inventory add.
// Multiple drops from one monster to one recipient share a short collection window.
void mygene_rare_obtained(map_session_data* receiver, t_itemid item_id, const mygene_rare_info& info);

#endif // MYGENE_RARE_LOOT_HPP

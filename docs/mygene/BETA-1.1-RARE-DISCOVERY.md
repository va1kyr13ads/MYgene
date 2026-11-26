# MYgene Beta 1.1 — Item transparency and rare discovery

Development candidate; compile and validate on an isolated server before deploying.

## Rules
- Shared Rustnarok description shows a blue item ID for identified items; unidentified equipment is not exposed.
- Normal monster and MVP reward eligibility is the original YAML base rate > 0 and <= 0.10%, not the rate after server scaling. Map bonus drops use their native 1/100000 units.
- Native announcements report the actual per-entry roll and effective multiplier (rounded for display). Bubble Gum and HE Bubble Gum use SC_ITEMBOOST +100% and +200% respectively. The text identifies the status effect, not necessarily the exact consumable source. Other rate modifiers, caps and rounding are reflected in the actual roll. Separate MVP reward rolls do not apply ordinary Gum in the existing implementation.
- Legendary Bubble Gum displays 100% for qualifying rolls; it remains unavailable by known ordinary acquisition methods. No change to drop rates or Gum effects.
- Slayer rewards remain fixed (weapon 0.05%, card 0.01%); guaranteed rolls record a separate persistent pending count so retries can distinguish natural from Legendary Gum rewards. Normal reservations drain before guaranteed reservations when mixed. Existing pending rewards from Beta 1.0 have no stored Gum provenance.
- Native announcements are discoveries at successful drop generation, attributed to the loot-priority character, not proof of eventual pickup or actual party recipient. Slayer announcements occur on successful delivery. Native item-specific special broadcasts are separate, and Steal uses the existing configuration. Script-added bonus drops and Ore Discovery are not covered by this candidate.
- Do not enable the legacy rare_drop_announce configuration solely for this feature; it can produce independent Steal notices.

## Acceptance checklist (not yet executed)
- [ ] Build Windows x64 server and Rustnarok release; run iteminfo unit tests.
- [ ] ID row appears once on ordinary items, cards, Slayer weapons, and all description windows; unidentified equipment does not expose its ID.
- [ ] Base rates 0.01%, 0.05%, 0.10% qualify; 0.11% and 0% do not.
- [ ] At 4x with no other modifiers: 0.01% -> 0.04%; standard Gum -> 0.08%; HE Gum -> 0.12%. Verify actual modifiers, rounding, cap and replacement of Gum status, and no change in drop mechanics.
- [ ] Boss/MVP category rates and separate MVP prize rolls report their real chance, rather than assuming standard Gum affects every path.
- [ ] Map bonus entries include correct 0.001% precision.
- [ ] Verify worldwide announcement colors and length on two connected clients.
- [ ] Validate native autoloot, floor drops, party even-share, and any item-specific announcements; check duplicate notices and recipient attribution before production.
- [ ] Verify Slayer fixed weapon/card drops with standard and HE Gum, Legendary Gum-assisted rewards, full inventory, retry after buff expires, relog, and mixed pending counts.
- [ ] No notices on shop, storage, trading, GM grants, or ordinary non-qualifying drops.
- [ ] Check the actual local server import configuration and runtime logs before deployment.

This branch is not a release, and does not modify the live server or Beta 1.0 tag.

# Novice Tower route and checkpoint staging

This is the first server-side slice of the five-floor design, not a release.
The original character-owned Floor 4 trial remains unchanged. The new menu
is accessible only to GM Novices via the existing Prontera herald (158,176).

## Manual staging checklist

- Choose Back from initial menu or Tower confirmation: no route saved.
- Choose Vanilla: saved route remains Vanilla after logout/restart; no warp,
  EXP, item, or normal trainer changes.
- Reset staging data, choose Tower, confirm: resume Awakening (1F).
- Simulate each current floor clear: resume Survival, Wisdom, Conquest,
  Destiny, then staged completion. No actual floor objective is satisfied
  by this tool and no character advancement or title is granted.
- Close and relog after each simulation; return to the herald and inspect the
  same checkpoint. Repeat with a second character; progress must be isolated.
- Reset on one character; the other character remains unchanged.
- Normal players and non-Novices must not see or use the staging menu.
- Existing Floor 4 trial still enters and operates for a solo Novice.

## Not yet enabled

Actual first-login client path screen, private entry landing, Awakening markers,
weapon/dummy checks, safe exact EXP grants, remaining floors, recovery/resume
warps, Guardian early-lethal protection, real graduation/title, final map and
client data. No permanent character route is written by this development menu.

Next implement actual Awakening objectives on an approved private test map;
connect checkpoint writes only after validating those objectives and safe
one-time EXP settlement. Test runtime parsing and relog/server restart before
integrating with the current local development branch.

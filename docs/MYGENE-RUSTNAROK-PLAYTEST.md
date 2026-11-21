# MYgene Rustnarok Windows playtest (experimental)

Branch: `mygene-rustnarok-compat` (separate from stable `mygene-custom-v1.1`).

## Why this branch exists
- Rustnarok Windows client supports PACKETVER 20220406 and later.
- This test branch sets `PACKETVER 20220406` in `src/custom/defines_pre.hpp`.
- It disables packet obfuscation in `src/config/packets.hpp`, matching the Rustnarok client.
- This is development-only, **not suitable for publicly exposed game ports** without a separate security review.
- The stable branch, production/test database, test PIN, and private config files must be preserved.
- Existing MYgene game rates remain in `mygene-config/battle_conf.txt`; they still need an active import/battle configuration in Codespaces.

## Tested so far
- MYgene stable branch: Login Server, Character Server, PIN registration, Novice creation and local Windows-to-Codespaces TCP forwarding were tested.
- This Rustnarok branch: source changes committed, **not yet compiled or tested against a Windows graphical client**.

## In Codespaces: rebuild this branch safely
Only do these steps in an existing MYgene Codespace after confirming database backup and no players connected.

```powershell
Set-Location /workspaces/MYgene
git status --short
# STOP if you see unexpected edits or untracked secrets.
bash ./athena-start stop
git fetch origin
git switch mygene-rustnarok-compat
git branch --show-current
git show HEAD:src/custom/defines_pre.hpp | Select-String PACKETVER
# Verify source:
Get-Content src/custom/defines_pre.hpp | Select-String PACKETVER
# A full rebuild matters: packet layout is compiled into the servers.
make clean
if ($LASTEXITCODE -ne 0) { throw "make clean failed" }
make server -j2
if ($LASTEXITCODE -ne 0) { throw "Server build failed" }
```

Do **not** run `./configure` with a conflicting `--enable-packetver` value. Check any previous configure flags with `./config.status --config` and remove a mismatched override before the build.

Check `conf/import/char_conf.txt` for `pincode_enabled`: Rustnarok v0.4.0 documents a PIN window; **keep existing PIN enabled** for the original MYgene test account. Do not overwrite your private config. Verify `mygene` and `mygene_logs` remain present. Start with:

```powershell
pwsh -NoProfile -File ./mygene-start.ps1
```

Do not assume startup success proves protocol compatibility. Check actual login/character logs and collect client errors.

## On Windows: install the open-source client
1. Official upstream: https://github.com/kindraywind/rustnarok-client/releases
2. Choose an official project release with a `rustnarok-client-<version>-windows-x86_64.zip` asset. Avoid third-party mirrors. The client is beta and published Windows builds are unsigned; **do not bypass Defender** if a download is flagged. If necessary, build from audited source.
3. Create `C:\Games\MYgene-Rustnarok-Test\`. Extract the client executable there.
4. Supply your **authorized** `data.grf` and optional `BGM` and translation files; the project does not distribute copyrighted game data. Prefer an official kRO data.grf compatible with the client's documentation.
5. Under `data\clientinfo.xml` add a connection such as:

```xml
<?xml version="1.0" encoding="utf-8"?>
<clientinfo>
  <servicetype>korea</servicetype>
  <connection>
    <display>MYgene</display>
    <address>127.0.0.1</address>
    <port>6900</port>
    <packetver>20220406</packetver>
  </connection>
</clientinfo>
```

6. Keep a private forwarding PowerShell window open:

```powershell
gh codespace ports forward 6900:6900 6121:6121 5121:5121 -R va1kyr13ads/MYgene
```

7. In another PowerShell window check ports 6900, 6121, 5121 with `Test-NetConnection`. Launch `rustnarok-client.exe` from its test directory, if your security software permits it.
8. Login with your existing test account; **do not paste passwords or PINs into chat**.

## Known constraints / rollback
- No claims of graphical gameplay success until tested.
- Existing login & char server address advertisements may require adjustments for the localhost tunnel; do not change public firewall settings to troubleshoot.
- Old 2021 client executables do not work against this 2022 branch.
- Do not disable your antivirus, manipulate EOS/Gepard, or merge this branch into stable.
- Roll back in Codespaces when servers are stopped: `git switch mygene-custom-v1.1`, then `make clean; make server -j2`, then start and verify. This rebuild is needed to restore the old packet protocol.
- Privacy: no database dump, access token, internal server password or PIN should be committed.

See upstream Rustnarok README and the rAthena fork's `RUSTNAROK.md` for current installation notes.

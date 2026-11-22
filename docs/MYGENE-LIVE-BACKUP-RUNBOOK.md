# MYgene live recovery data — read-only backup procedure

Milestone: **Slayer Working, 2026-11-23**.

This file is operational tooling, **not** a completed backup. The companion shell script needs to run INSIDE the actual MYgene Codespace. The connected ChatGPT GitHub app cannot see live MariaDB contents or your Windows filesystem. The existing source snapshot is immutable at server commit `58a8bf1179adbdea43dce4e3e1d42b56d3432f89` and Windows-client commit `feb78501668de69b0883c9cd7e7a3e25ffeef594`.

## Codespace live databases and configurations

1. Open a terminal in the Codespace where MYgene is actually running. **Do not change branches, restart servers, or run database imports.**
2. In the server checkout, install the `age` password-based encryption command if necessary:

   ```bash
   cd /workspaces/MYgene
   sudo apt-get update && sudo apt-get install -y age
   ```

3. Download the reviewed backup helper from the source snapshot of this ops branch, verify shell syntax and execute:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/va1kyr13ads/MYgene/b3c594b85f60b434bb0cd697092caace09ebce24/tools/backup-mygene-live.sh -o /tmp/backup-mygene-live.sh
   bash -n /tmp/backup-mygene-live.sh
   bash /tmp/backup-mygene-live.sh /workspaces/_mygene-secure-backups
   ```

4. Follow the **local** passphrase prompts. The tool checks both databases (`mygene`, `mygene_logs`), exports SQL transactionally, collects local server configuration and tracked uncommitted patches, encrypts them with `age`, decrypts to verify, checks archive and SQL stream integrity, and writes a SHA-256 checksum. No output is uploaded to GitHub automatically; only a successfully verified encrypted archive is published.
5. Inspect the final `ENCRYPTED LIVE BACKUP VERIFIED` line. Download the `.age` file **and matching `.sha256`** from the Codespace to secure off-Codespace storage, and keep the passphrase offline and separately. A file left only in Codespaces is **not** disaster recovery. Avoid putting either plaintext SQL or your passphrase into chats or repositories.

Because `--single-transaction` is designed for InnoDB, check the engine types if the server uses nontransactional tables and consider a brief maintenance-window snapshot for exact consistency. **Do not** import the exported SQL over your running production database to test; restore into a disposable MariaDB instance.

## Windows machine assets and client setup (separate, must be done on the PC)

The GitHub source and executable artifact do **not** include proprietary game files or your live Windows settings. On your own PC:

1. Find the actual MYgene client installation (the directory that contains `MYgeneClient.exe`, `data.grf`, `data/clientinfo.xml`, and/or `DATA.INI`, depending on your installation).
2. Copy the entire working client folder **with its overlays, authorized GRFs, game data, clientinfo.xml, and relevant player configuration** to private temporary storage, excluding unrelated downloads and secrets that do not need to be copied.
3. Use **7-Zip's 7z format with AES-256 and Encrypt file names** to encrypt that folder using a strong unique password. Do **not** upload unencrypted licensed assets or credentials into public GitHub.
4. Make a SHA-256 manifest for the final encrypted archive from PowerShell: `Get-FileHash -Algorithm SHA256 'C:\Path\MYgene-Client-Assets.7z'`.
5. Save the encrypted 7z and checksum offline/off-machine, separately from the passphrase. Keep the previous working executable untouched.

The compiled `MYgeneClient.exe` is already in the Slayer milestone recovery ZIP, but it does not replace a backup of the authorized assets or account/character database.

## Complete only after BOTH parts have been captured

- [ ] Live SQL export has passed encryption/decryption verification
- [ ] Config archive and uncommitted source patch are inside encrypted Codespace backup
- [ ] `.age` and `.sha256` have been copied outside Codespaces
- [ ] Windows client assets and settings have been archived and encrypted on the Windows PC
- [ ] Windows encrypted archive checksum saved off-machine
- [ ] Passphrases stored independently and can decrypt test copies
- [ ] Disposable test restores (MariaDB, files, Windows client) succeeded

**Never mark these as complete based solely on GitHub branch creation or CI.**

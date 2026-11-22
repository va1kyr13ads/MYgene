#!/usr/bin/env bash
# MYgene read-only encrypted live backup; never imports SQL, restarts services, or uploads data.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
if [[ $# -ne 1 ]]; then
  printf 'Usage: bash tools/backup-mygene-live.sh /workspaces/_mygene-secure-backups\n' >&2
  exit 2
fi
for bin in age gzip tar sudo sha256sum realpath mariadb; do
  command -v "$bin" >/dev/null 2>&1 || fail "Missing $bin. Install age with: sudo apt-get update && sudo apt-get install -y age"
done
dump_tool=$(command -v mariadb-dump || command -v mysqldump || true)
[[ -n "$dump_tool" ]] || fail "mariadb-dump or mysqldump is required"
repo=$(git rev-parse --show-toplevel 2>/dev/null) || fail "Run in the MYgene rAthena server checkout"
[[ -f "$repo/mygene-start.ps1" && -f "$repo/npc/custom/mygene/yellow_fabre.txt" ]] || fail "Wrong repository"
out_dir=$(realpath -m -- "$1")
[[ "$out_dir" != "$repo" && "$out_dir" != "$repo/"* ]] || fail "Backup must be OUTSIDE the public repository"
mkdir -p -m 700 -- "$out_dir"
chmod 700 -- "$out_dir" || fail "Unable to secure backup folder"

printf 'Checking local MariaDB databases without changing them...\n'
num_db=$(sudo -n mariadb -N -B -e "SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME IN ('mygene','mygene_logs');") ||
  fail "Cannot access MariaDB with passwordless sudo"
[[ "$num_db" == "2" ]] || fail "Expected BOTH live databases: mygene and mygene_logs"

stage=""
part=""
cleanup() {
  if [[ -n "$stage" && -d "$stage" ]]; then rm -rf -- "$stage"; fi
  if [[ -n "$part" && -e "$part" ]]; then rm -f -- "$part"; fi
}
trap cleanup EXIT
stage=$(mktemp -d "$out_dir/.mygene-staging.XXXXXXXX")
mkdir -p "$stage/payload/server-files"

printf 'Exporting mygene and mygene_logs (consistent InnoDB snapshot)...\n'
sudo -n "$dump_tool" --single-transaction --quick --routines --events --triggers --hex-blob --databases mygene mygene_logs |
  gzip -6 > "$stage/payload/database-mygene-and-logs.sql.gz" ||
  fail "Database dump failed; no complete backup was published"
[[ -s "$stage/payload/database-mygene-and-logs.sql.gz" ]] || fail "Database dump is empty"
gzip -t "$stage/payload/database-mygene-and-logs.sql.gz" || fail "Database gzip check failed"

printf 'Collecting the local configuration and script overrides...\n'
for rel in conf db/import npc/custom src/custom mygene-config mygene-start.ps1 .env .env.local; do
  if [[ -e "$repo/$rel" ]]; then
    mkdir -p "$stage/payload/server-files/$(dirname "$rel")"
    cp -a -- "$repo/$rel" "$stage/payload/server-files/$rel"
  fi
done

{
  printf 'MYgene Slayer-working confidential backup\nCaptured UTC: '
  date -u +%Y-%m-%dT%H:%M:%SZ
  printf 'Server source branch: '
  git -C "$repo" branch --show-current
  printf 'Codespace source SHA: '
  git -C "$repo" rev-parse HEAD
  printf 'Pinned working milestone SHA: 58a8bf1179adbdea43dce4e3e1d42b56d3432f89\n'
  printf 'Databases: mygene, mygene_logs\n'
  printf 'Configuration and scripts: conf, db/import, npc/custom, src/custom, mygene-config (where present)\n'
  printf 'Excluded: Windows assets, Windows client folder, external systems, secret process environment variables\n'
  printf 'Uncommitted local source file status:\n'
  git -C "$repo" status --porcelain || true
} > "$stage/payload/CAPTURE-DETAILS.txt"
git -C "$repo" diff --binary HEAD > "$stage/payload/uncommitted-tracked-source.patch" ||
  fail "Unable to record local tracked source edits"

tar -C "$stage" -czf "$stage/payload.tar.gz" payload || fail "Archive packaging failed"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
name="MYgene-Live-$stamp-$$.tar.gz.age"
final="$out_dir/$name"
part="$final.part"
[[ ! -e "$final" && ! -e "$part" ]] || fail "Backup name collision"

printf 'Encrypting with age; enter a strong passphrase LOCALLY. Do not share it in chat.\n'
age -p -o "$part" "$stage/payload.tar.gz" || fail "Encryption failed"
[[ -s "$part" ]] || fail "Encrypted file is empty"
printf 'Verify decryption with your passphrase...\n'
age -d -o "$stage/verify.tar.gz" "$part" || fail "Decryption verification failed"
tar -tzf "$stage/verify.tar.gz" >/dev/null || fail "Archive verification failed"
tar -xOzf "$stage/verify.tar.gz" payload/database-mygene-and-logs.sql.gz |
  gzip -t || fail "Database export verification failed"

mv -- "$part" "$final"
part=""
(cd "$out_dir" && sha256sum "$name" > "$name.sha256" && sha256sum -c "$name.sha256" >/dev/null) ||
  fail "Checksum validation failed"
printf '\nENCRYPTED LIVE BACKUP VERIFIED: %s\n' "$final"
printf 'CHECKSUM: %s.sha256\n' "$final"
printf 'Transfer BOTH files to private storage OFF this Codespace. Keep the passphrase separately.\n'
printf 'Windows game assets still require a separate encrypted local backup.\n'

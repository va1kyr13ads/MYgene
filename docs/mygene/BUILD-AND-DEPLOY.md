# MYgene Beta - Build and Deployment

## Release versions

- Server: rAthena Pre-Renewal, Episode 11 restrictions
- Slayer Series: V10.11.1
- Novice Tower: Beta 1.0 RC1.1
- Guardian of Time: V1.3.5
- Rustnarok Client: Tower V61

## Build verification

Windows server Release x64: Passed.
Rustnarok release build: Passed.
Known client warning: unused storage tabs field.

## Server requirements

- Visual Studio C++ and MSBuild
- SQL database configured locally
- Compatible Pre-Renewal map cache
- Compatible client and authorized game assets

## Client compilation

From client/rustnarok:

    cargo build --release

## Deployment notes

Configure SQL credentials locally.
Do not publish private configuration or player records.
Ensure the custom Tower map is available before starting.
Use the separate Novice Tower distribution installer
when porting the feature to another server.

Independent runtime acceptance testing is required.

Map cache differences detected during release audit:
db\pre-re\map_cache.dat

## Custom database definitions

MYgene gameplay definitions are included in db/import.
These files are intentionally tracked despite upstream
Git ignore rules.

The custom binary Pre-Renewal map cache is not included.
Generate or supply a compatible map cache before deployment.

Packet obfuscation is disabled for Rustnarok compatibility.
Review network security before exposing a live server.

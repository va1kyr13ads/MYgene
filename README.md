# MYgene Ragnarok Online

**Pre-Renewal • Episode 11 content restrictions • Beta 1.0 source release**

<img src="client/rustnarok/src/ui/mygene_tower_emblem.png" alt="MYgene Novice Tower emblem" width="112" />

MYgene is a customized rAthena server with a companion Rustnarok client, focused on classic Ragnarok Online progression, rare equipment and a guided introduction for new players.

> **Release status:** The Windows x64 server and Rustnarok release builds passed in local staging. A fresh-install runtime test is still required. This is a source release, not a ready-to-play distribution.

## Features

| System | Version / scope |
| --- | --- |
| Server | Pre-Renewal, Episode 11 restrictions |
| Rates | 7× base and job EXP; 4× ordinary item drops; 3× boss and 2× MVP-category rates |
| Slayer Series | V10.11.1 — six weapon families, matching cards and Perfect awakening |
| Novice Tower | Beta 1.0 RC1.1 — private character-owned five-floor tutorial |
| Guardian of Time | V1.3.5 — inactivity warnings and safe exit with completed checkpoints preserved |
| Rustnarok client | Tower V61, based on v0.4.0 |
| Achievements | Novice Tower Conqueror and hidden achievement support |
| Quality of life | Player autoloot, item-specific autoloot, autotrade and Space Box |

### Novice Tower

Players choose the Vanilla Path or Tower Path. The optional Tower guides novices through five floors:

1. **Awakening** — movement, stats, targeting and weapon choice.
2. **Survival** — recovery, combat and inventory basics.
3. **Wisdom** — six first-job mentors, skills and elemental training.
4. **Conquest** — guardian encounter with AI companions.
5. **Destiny** — first-job selection, graduation and optional recommended stats.

### Slayer Series

Yellow Fabre (knife), Red Thief Bug (sword), Blue Chon Chon (bow), Purple Willow (rod), Orange Rideword (book) and Dark Orc (axe). All twelve base and Perfect weapons are available to all jobs, subject to their equipment-level requirements.

## Build and deploy

- [Build and deployment guide](docs/mygene/BUILD-AND-DEPLOY.md)
- [MYgene release overview](docs/mygene/MYgene-Beta.md)
- [Custom database imports](db/import/)
- [Novice Tower scripts](npc/custom/mygene/novice_tower/)
- [Rustnarok client source](client/rustnarok/)
- [Releases](https://github.com/va1kyr13ads/MYgene/releases)

Use Visual Studio C++ / MSBuild to build the Windows server in Release x64 and Cargo to build the client. Configure an independent SQL database locally. Supply or generate a compatible Pre-Renewal map cache, including the Tower map, and obtain authorized game assets separately.

Do not use production credentials or player data in a public repository. Packet obfuscation is disabled for client compatibility; review security before Internet-facing deployment. No production runtime validation is claimed for a fresh clone.

## Credits and licenses

MYgene is based on [rAthena](https://github.com/rathena/rathena) (GNU GPL v3; see the upstream license notices). The Rustnarok client retains its [MIT](client/rustnarok/LICENSE-MIT) and [Apache-2.0](client/rustnarok/LICENSE-APACHE) licenses. Ragnarok Online and its proprietary game assets belong to their respective rights holders; this source repository does not grant rights to distribute them.

---

## Upstream rAthena documentation

<img src="doc/logo.png" align="right" height="90" />

# rAthena
![clang](https://img.shields.io/github/actions/workflow/status/rathena/rathena/build_servers_clang.yml?label=clang%20build&logo=llvm) 
![cmake](https://img.shields.io/github/actions/workflow/status/rathena/rathena/build_servers_cmake.yml?label=cmake%20build&logo=cmake)
![gcc](https://img.shields.io/github/actions/workflow/status/rathena/rathena/build_servers_gcc.yml?label=gcc%20build&logo=gnu) 
![ms](https://img.shields.io/github/actions/workflow/status/rathena/rathena/build_servers_msbuild.yml?label=ms%20build&logo=visualstudio) 
![GitHub](https://img.shields.io/github/license/rathena/rathena.svg) 
![commit activity](https://img.shields.io/github/commit-activity/w/rathena/rathena) 
![GitHub repo size](https://img.shields.io/github/repo-size/rathena/rathena.svg)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/rathena/rathena)


> rAthena is a collaborative software development project revolving around the creation of a robust massively multiplayer online role playing game (MMORPG) server package. Written in C++, the program is very versatile and provides NPCs, warps and modifications. The project is jointly managed by a group of volunteers located around the world as well as a tremendous community providing QA and support. rAthena is a continuation of the eAthena project.

[Forum](https://rathena.org/board)|[Discord](https://rathena.org/discord)|[Wiki](https://github.com/rathena/rathena/wiki)|[FluxCP](https://github.com/rathena/FluxCP)|[Crowdfunding](https://rathena.org/board/crowdfunding/)|[Fork and Pull Request Q&A](https://rathena.org/board/topic/86913-pull-request-qa/)
--------|--------|--------|--------|--------|--------

### Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Troubleshooting](#3-troubleshooting)
4. [More Documentation](#4-more-documentation)
5. [How to Contribute](#5-how-to-contribute)
6. [License](#6-license)

## 1. Prerequisites
Before installing rAthena there are certain tools and applications you will need which
differs between the varying operating systems available.

### Hardware
Hardware Type | Minimum | Recommended
------|------|------
CPU | 1 Core | 2 Cores
RAM | 1 GB | 2 GB
Disk Space | 300 MB | 500 MB

### Operating System & Preferred Compiler
Operating System | Compiler
------|------
Linux  | [gcc-6 or newer](https://www.gnu.org/software/gcc/gcc-6/) / [Make](https://www.gnu.org/software/make/)
Windows | [MS Visual Studio 2017 or newer](https://www.visualstudio.com/downloads/)

### Required Applications
Application | Name
------|------
Database | [MySQL 5 or newer](https://www.mysql.com/downloads/) / [MariaDB 5 or newer](https://downloads.mariadb.org/)
Git | [Windows](https://gitforwindows.org/) / [Linux](https://git-scm.com/download/linux)

### Optional Applications
Application | Name
------|------
Database | [MySQL Workbench 5 or newer](http://www.mysql.com/downloads/workbench/)

## 2. Installation 

### Full Installation Instructions
  * [Windows](https://github.com/rathena/rathena/wiki/Install-on-Windows)
  * [CentOS](https://github.com/rathena/rathena/wiki/Install-on-Centos)
  * [Debian](https://github.com/rathena/rathena/wiki/Install-on-Debian)
  * [FreeBSD](https://github.com/rathena/rathena/wiki/Install-on-FreeBSD)

## 3. Troubleshooting

If you're having problems with starting your server, the first thing you should
do is check what's happening on your consoles. More often that not, all support issues
can be solved simply by looking at the error messages given. Check out the [wiki](https://github.com/rathena/rathena/wiki)
or [forums](https://rathena.org/board) if you need more support on troubleshooting.

## 4. More Documentation
rAthena has a large collection of help files and sample NPC scripts located in the /doc/
directory. These include detailed explanations of NPC script commands, atcommands (@),
group permissions, item bonuses, and packet structures, among many other topics. We
recommend that all users take the time to look over this directory before asking for
assistance elsewhere.

## 5. How to Contribute
Details on how to contribute to rAthena can be found in [CONTRIBUTING.md](https://github.com/rathena/rathena/blob/master/.github/CONTRIBUTING.md)!

## 6. License
Copyright (c) rAthena Development Team - Licensed under [GNU General Public License v3.0](https://github.com/rathena/rathena/blob/master/LICENSE)

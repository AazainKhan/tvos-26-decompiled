# tvos-26-re

A machine-readable map of **tvOS 26.6** (Apple TV HD, `AppleTV5,3`, build `23L773`): which apps and frameworks exist, their Objective-C/Swift interfaces at name level, and the timing of every CoreAnimation package on the system.

> **Legal:** independent interoperability research, not affiliated with or endorsed by Apple. No Apple code, binaries, assets or keys are included. Not legal advice. See [Legal](#legal).

Built for coding agents (Claude Code, Codex, Cursor…) and people building Apple TV–style UIs on other platforms, such as [Glass](https://github.com/AazainKhan/glass-tv-launcher). Query it instead of re-extracting a 5 GB firmware.

**This repo contains no Apple code, binaries, headers or artwork.** It holds names, numbers and paths derived from the firmware, plus scripts that regenerate everything from your own copy of the IPSW. See [NOTICE.md](NOTICE.md).

## What's inside

| Path | What it is | Rows |
|---|---|---|
| `index/apps.tsv` | Every app: bundle id, executable, min OS, URL schemes, size | 62 |
| `index/frameworks.tsv` | Every framework: bundle id, whether it ships `Assets.car` / `.ca` motion packages, whether its binary is on disk or in the dyld cache | 1,832 |
| `index/objc/<image>.classes.tsv` | ObjC classes, protocols, categories with superclass and protocols | 2,663 types |
| `index/objc/<image>.members.tsv` | ObjC method and property declarations (signatures only) | 28,712 |
| `index/swift/PineBoard.types.tsv` | Swift types in the home-screen app and their fields | 106 types |
| `index/animations.tsv` | Every animation in every `.ca` package: keyPath, duration, beginTime, spring mass/stiffness/damping, timing functions, keyframes | 3,655 (1,674 springs) |
| `index/ca-packages.txt` | Every `.ca` / `.caar` package path | 145 |

Images indexed in `objc/`: `PineBoard` (home screen), `TVSystemUIService` (overlays, banners), `TVSystemUI`, `TVSystemMenuUI` (Control Center), `TVSettings`, `TVSettingsFoundation`, `FocusEngine`, `TVUIKit`, `PineBoardServices`, `PineBoardUIServices`, `CoreMaterial`.

## Where things live in tvOS 26

| Surface | Image | Notes |
|---|---|---|
| Home screen | `Applications/PineBoard.app` (`com.apple.PineBoard`) | Executable on disk; ObjC + Swift |
| Overlays, banners, now-playing | `Applications/TVSystemUIService.app`, `TVSystemUI.framework` | Most `.ca` motion packages live here |
| Control Center / system menu | `TVSystemMenuUI.framework` | Pure ObjC; binary in dyld cache |
| Focus | `FocusEngine.framework`, `TVUIKit.framework` | Pure ObjC |
| Materials (blur/glass) | `CoreMaterial.framework` | |
| Settings | `Applications/TVSettings.app` | |
| Idle / screensaver | `IdleScreen.app`, `TVScreenSaver.app`, `PosterBoard.app` | |

Framework binaries are not on disk in tvOS 26; they live in the dyld shared cache (`System/Library/Caches/com.apple.dyld/`, 3.4 GB). `frameworks.tsv` marks which is which.

## Use cases

For agents building an Apple TV–style launcher or app:

1. **Match tvOS motion.** Look up the real spring and keyframe parameters before tuning an animation.
   `grep CASpringAnimation index/animations.tsv | cut -f4,9-11 | sort | uniq -c | sort -rn | head`
2. **Find how a surface is built.** Which classes make up Control Center, and what do they expose?
   `cut -f2,3 index/objc/TVSystemMenuUI.classes.tsv`
3. **Reproduce focus behaviour.** Read FocusEngine's interface (focus movement, scroll groups, parallax) to design an equivalent on Android TV / Compose.
   `grep -i -E "parallax|scroll|velocity" index/objc/FocusEngine.members.tsv`
4. **Name things the way Apple does.** Map a feature ("sleep timer", "profile picker", "top shelf") to its owning app and classes before designing your own.
   `grep -i -h "profilepicker" index/objc/*.classes.tsv`
5. **Plan deep links and integrations.** Which apps declare URL schemes, and which services exist for a given feature.
   `awk -F'\t' '$5!=""' index/apps.tsv`
6. **Diff tvOS releases.** Re-run the scripts on a newer IPSW and `git diff index/` to see added or removed classes, members and animations.
7. **Skip the 5 GB download.** An agent can answer "does tvOS have X?" from these TSVs in seconds.

## Regenerate from your own IPSW

Needs macOS (`aea`, `hdiutil`), Python 3 and [`ipsw`](https://github.com/blacktop/ipsw).

```bash
scripts/reproduce.sh "/path/to/AppleTV5,3_26.6_23L773_Restore.ipsw"
```

It extracts the OS image, unwraps its key through Apple's public key service (`ipsw fw aea --key`), decrypts with `aea`, mounts read-only, dumps the interfaces into `.work/` (git-ignored) and rewrites `index/`. Roughly 10 minutes and 15 GB of scratch space.

| Script | Does |
|---|---|
| `scripts/index_bundles.py` | apps, frameworks, `.ca` package list |
| `scripts/index_headers.py` | class-dump headers → name-level TSV |
| `scripts/index_swift.py` | swift-dump → type and field names |
| `scripts/index_caml.py` | `.ca` packages → animation timing TSV |

## Related

- [fireos-karat-re](https://github.com/AazainKhan/fireos-karat-re): the same kind of map for Fire OS 8 on the Fire TV Stick 4K (2nd gen).
- [glass-tv-launcher](https://github.com/AazainKhan/glass-tv-launcher): the Apple TV–style launcher this research feeds.

## Legal

**Not legal advice.** This section describes how the project is intended to be used. It is not legal advice; if you need certainty for your situation or jurisdiction, ask a lawyer.

**No affiliation.** This project is not affiliated with, authorised, sponsored or endorsed by Apple Inc.

**What this repository is.** Independent research for interoperability: the indexes describe how tvOS is structured so that third-party software (launchers, companion apps, accessibility tools, custom builds for devices you own) can work with it. The repository contains only facts derived from the firmware (names, paths, declared signatures, configuration values and numbers) and original scripts written for this project.

**What it is not.** It does not contain, and pull requests must not add:
- Apple binaries, firmware, disk images, packages or installers;
- decompiled or disassembled code, method bodies, generated header files or source reconstructions;
- images, icons, sounds, fonts, `Assets.car`/resource files or other artwork;
- encryption keys, certificates, signing material, credentials or tokens, including any found embedded in the firmware;
- anything that removes, disables or works around copy protection or DRM.

**Get the firmware yourself.** The reproduce scripts expect a firmware file that you obtained lawfully. They do not download it for you, and everything they extract stays in a git-ignored local directory. Do not commit or share that directory.

**About decryption.** Apple distributes the IPSW's file-system images as encrypted archives and publishes the matching keys through its own public key service, which `ipsw fw aea --key` queries. The scripts use that service only to read the firmware you supplied; no keys are stored in this repository. This is not DRM on content: no media, app or account protection is touched.

**Your responsibility.** You are responsible for making sure your use complies with the laws of your jurisdiction and with any agreements you have accepted (for example the device's terms of use or the software licence agreement). Reverse engineering for interoperability is permitted in many jurisdictions under specific conditions, but not everywhere and not for every purpose.

**No warranty, use at your own risk.** The scripts and data are provided "as is", without warranty of any kind (see [LICENSE](LICENSE)). Modifying a device's software can void its warranty, break features or make the device unusable. The authors are not liable for any damage or loss.

**Trademarks.** Apple, Apple TV, tvOS, Siri and AirPlay are trademarks of Apple Inc., registered in the U.S. and other countries. All other trademarks are the property of their respective owners. Names are used only to identify the software described.

**Licence.** The original scripts and documentation are MIT-licensed. The MIT licence does not grant any rights in Apple's software; the derived facts are provided for reference.

**Takedown and contact.** If you are a rights holder and believe something here should not be published, open an issue (or contact the repository owner through GitHub) and it will be reviewed and removed promptly. Security-sensitive reports should not be filed as public issues; use GitHub's private vulnerability reporting on this repository instead.

See also [NOTICE.md](NOTICE.md).

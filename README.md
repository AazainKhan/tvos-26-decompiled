# tvos-26-decompiled

A machine-readable map of **tvOS 26.6** (Apple TV HD, `AppleTV5,3`, build `23L773`): which apps and frameworks exist, their Objective-C/Swift interfaces at name level, and the timing of every CoreAnimation package on the system.

> **Legal:** independent interoperability research, not affiliated with or endorsed by Apple. No Apple code, binaries, assets or keys are included. Not legal advice. See [Legal](#legal).

> **About the name:** "decompiled" describes how these indexes were made. The firmware was decompiled locally, and only derived facts (names, signatures, numbers) are published here, never the decompiled code itself.

Built for coding agents (Claude Code, Codex, Cursor…) and people building Apple TV–style UIs on other platforms, such as [Glass](https://github.com/AazainKhan/glass-tv-launcher). Query it instead of re-extracting a 5 GB firmware.

**This repo contains no Apple code, binaries, headers or artwork.** It holds names, numbers and paths derived from the firmware, plus scripts that regenerate everything from your own copy of the IPSW. See [NOTICE.md](NOTICE.md).

## What's inside

| Path | What it is | Rows |
|---|---|---|
| `index/apps.tsv` | Every app: bundle id, executable, min OS, URL schemes, size | 62 |
| `index/frameworks.tsv` | Every framework: bundle id, whether it ships `Assets.car` / `.ca` motion packages, whether its binary is on disk or in the dyld cache | 1,832 |
| `index/objc/{dsc,apps,disk}/<image>.classes.tsv` | ObjC classes, protocols, categories with superclass and protocols, for every dyld-cache image (`dsc`), app (`apps`) and other on-disk executable (`disk`) | 198,577 types |
| `index/objc/{dsc,apps,disk}/<image>.members.tsv` | ObjC method and property declarations (signatures only) | 2,228,265 |
| `index/swift/{dsc,apps,disk}/<image>.types.tsv` | Swift types and their fields | 661,287 types |
| `index/disk-images.tsv` | Maps each `disk/` name (`<binary>~<hash>`) to its full path | 1,224 |
| `index/animations.tsv` | Every animation in every `.ca` and `.caar` package: keyPath, duration, beginTime, spring mass/stiffness/damping, timing functions, keyframes | 7,713 (3,027 springs) |
| `index/constants/<image>.tsv` | Numbers that constant-returning methods produce, decoded from machine code: sizes, radii, spacing, spring mass/stiffness/damping, timing curves; `a if ne else b` marks a two-way choice such as `isScaledUI` | 1,093 methods, 12 images |
| `index/ca-packages.txt` | Every `.ca` / `.caar` package path | 145 |

Every dyld-cache image is in `objc/dsc/` and `swift/dsc/`, every app in `objc/apps/` and `swift/apps/`, and every other executable in `objc/disk/` and `swift/disk/` (names resolve through `index/disk-images.tsv`). Images with the same name in two places carry their parent folder, for example `AVKit~AVKit.framework` and `AVKit~AVKit.axbundle`.

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

## Coverage

What has been decompiled and indexed, measured against tvOS 26.6.

| Area | Done | Coverage |
|---|---|---|
| App inventory (bundle ids, executables, URL schemes) | 62 of 62 apps | **100%** |
| Framework inventory (bundle ids, assets, binary location) | 1,832 of 1,832 frameworks | **100%** |
| dyld shared cache images dumped (ObjC + Swift) | 2,392 of 2,392 | **100%** |
| App executables dumped | 61 of 61 (one app, `ShortcutsActions`, has no executable) | **100%** |
| Other on-disk executables dumped (daemons, plugins, extensions, XPC services) | 1,224 of 1,224 Mach-O files | **100%** |
| CoreAnimation packages parsed (`.ca` XML and `.caar` binary) | 145 of 145 (113 contain animations) | **100%** |
| Numeric constants decoded from machine code (key UI images: Control Center, system UI, home screen, focus, materials, settings) | 12 images, 1,093 methods | 12 key images |
| Function bodies (pseudo-code from machine code) | not attempted | 0% |
| Kernel, iBoot, SEP firmware | not attempted | 0% |

"Dumped" means the Objective-C runtime metadata and Swift type metadata were read from every binary. That gives every class, protocol, method, property and Swift type with its fields. It does not turn machine code back into source.

### Interfaces

| Scope | Images | With ObjC types | ObjC types | ObjC members | With Swift | Swift types | Swift fields |
|---|---|---|---|---|---|---|---|
| dyld shared cache | 2,392 | 1,870 | 165,185 | 1,872,870 | 969 | 598,050 | 448,291 |
| Apps | 61 | 58 | 5,822 | 67,846 | 33 | 6,551 | 6,976 |
| Other executables | 1,224 | 815 | 27,570 | 287,549 | 336 | 56,686 | 58,332 |
| **Total** | **3,677** | **2,743** | **198,577** | **2,228,265** | **1,338** | **661,287** | **513,599** |

Key UI images: `apps/PineBoard` (home screen, 967 types), `apps/TVSystemUIService` (513), `apps/TVSettings` (407), `dsc/PineBoardServices` (227), `dsc/TVSystemUI` (180), `dsc/TVUIKit` (96), `dsc/FocusEngine` (90), `dsc/TVSystemMenuUI` (Control Center, 48), `dsc/CoreMaterial` (35).

Headers and Swift dumps were generated locally and are not published; only type and member names with signatures are.

### Animations

| Type | Count |
|---|---|
| `CAKeyframeAnimation` | 3,547 |
| `CASpringAnimation` | 3,027 |
| `CABasicAnimation` | 887 |
| `CAAnimationGroup` | 180 |
| `LKStateAddAnimation` | 72 |
| **Total** | **7,713** |

From 84 XML packages and 29 binary packages. Most common springs (mass / stiffness / damping): 2 / 300 / 50 (1,719 uses), 1 / 435 / 25 (378), 3 / 500 / 1000 (128), 2 / 300 / 30 (85). Colors and vector paths inside the packages are artwork and are left out on purpose.

## Use cases

For agents building an Apple TV–style launcher or app:

1. **Match tvOS motion.** Look up the real spring and keyframe parameters before tuning an animation.
   `grep CASpringAnimation index/animations.tsv | cut -f4,9-11 | sort | uniq -c | sort -rn | head`
2. **Find how a surface is built.** Which classes make up Control Center, and what do they expose?
   `cut -f2,3 index/objc/dsc/TVSystemMenuUI.classes.tsv`
3. **Reproduce focus behaviour.** Read FocusEngine's interface (focus movement, scroll groups, parallax) to design an equivalent on Android TV / Compose.
   `grep -i -E "parallax|scroll|velocity" index/objc/dsc/FocusEngine.members.tsv`
4. **Name things the way Apple does.** Map a feature ("sleep timer", "profile picker", "top shelf") to its owning app and classes before designing your own.
   `grep -ril "profilepicker" index/objc/ | head`
5. **Plan deep links and integrations.** Which apps declare URL schemes, and which services exist for a given feature.
   `awk -F'\t' '$5!=""' index/apps.tsv`
6. **Diff tvOS releases.** Re-run the scripts on a newer IPSW and `git diff index/` to see added or removed classes, members and animations.
7. **Get exact sizes and springs.** Control Center panel width, row heights, corner radii and its push/pop springs, decoded from the binary.
   `grep -E "PlatterDesiredWidth|RowHeight|CornerRadius" index/constants/TVSystemPanelUI.tsv`
8. **Skip the 5 GB download.** An agent can answer "does tvOS have X?" from these TSVs in seconds.

## Regenerate from your own IPSW

Needs macOS (`aea`, `hdiutil`), Python 3 and [`ipsw`](https://github.com/blacktop/ipsw).

```bash
scripts/reproduce.sh "/path/to/AppleTV5,3_26.6_23L773_Restore.ipsw"
```

It extracts the OS image, unwraps its key through Apple's public key service (`ipsw fw aea --key`), decrypts with `aea`, mounts read-only, dumps the interfaces into `.work/` (git-ignored) and rewrites `index/`. Roughly 1-2 hours and 15 GB of scratch space. Note: the published indexes were produced step by step from the same IPSW; the script collects those steps but has not yet been run end to end in one pass.

| Script | Does |
|---|---|
| `scripts/index_bundles.py` | apps, frameworks, `.ca` package list |
| `scripts/index_headers.py` | class-dump headers → name-level TSV |
| `scripts/index_swift.py` | swift-dump → type and field names |
| `scripts/decode_constants.py` | `ipsw dyld disass` output → returned numbers per method |
| `scripts/relabel_stripped.py` | puts ObjC method names back on a stripped app's disassembly |
| `scripts/index_caml.py` | `.ca` packages → animation timing TSV |

## Related

- [fireos-karat-decompiled](https://github.com/AazainKhan/fireos-karat-decompiled): the same kind of map for Fire OS 8 on the Fire TV Stick 4K (2nd gen).
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

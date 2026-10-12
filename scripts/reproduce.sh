#!/bin/bash
# Rebuild everything in index/ from your own copy of the tvOS 26.6 IPSW.
# Decrypted images, headers and assets stay in $WORK and are never committed.
#
# Usage: scripts/reproduce.sh /path/to/AppleTV5,3_26.6_23L773_Restore.ipsw [work_dir]
# Needs: macOS (aea, hdiutil), python3, ipsw (github.com/blacktop/ipsw).
set -euo pipefail

IPSW="${1:?path to the .ipsw}"
WORK="${2:-$PWD/.work}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OS_AEA="094-98312-085.dmg.aea"   # OS root filesystem (from BuildManifest: Manifest.OS)
MNT="$WORK/mnt"

IMAGES_DSC=(
  PrivateFrameworks/TVSystemMenuUI PrivateFrameworks/TVSystemUI PrivateFrameworks/FocusEngine
  Frameworks/TVUIKit PrivateFrameworks/PineBoardServices PrivateFrameworks/PineBoardUIServices
  PrivateFrameworks/CoreMaterial PrivateFrameworks/TVSettingsFoundation
)
IMAGES_APP=(PineBoard TVSystemUIService TVSettings)

mkdir -p "$WORK"
echo "[1/6] extract OS image"
[ -f "$WORK/$OS_AEA" ] || unzip -o -q "$IPSW" "$OS_AEA" -d "$WORK"

echo "[2/6] unwrap archive key (Apple public key service) and decrypt"
if [ ! -f "$WORK/os.dmg" ]; then
  KEY=$(ipsw fw aea "$WORK/$OS_AEA" --key | grep '^base64:' | tail -1)
  aea decrypt -i "$WORK/$OS_AEA" -o "$WORK/os.dmg" -key-value "$KEY"
fi

echo "[3/6] mount read-only"
mkdir -p "$MNT"
mount | grep -q "$MNT" || hdiutil attach -readonly -nobrowse -noverify -mountpoint "$MNT" "$WORK/os.dmg" >/dev/null
DSC="$MNT/System/Library/Caches/com.apple.dyld/dyld_shared_cache_arm64"

echo "[4/6] class-dump / swift-dump (local headers in $WORK/headers)"
for fw in "${IMAGES_DSC[@]}"; do
  n=$(basename "$fw")
  ipsw class-dump "$DSC" "/System/Library/$fw.framework/$n" --headers --output "$WORK/headers/$n" >/dev/null
done
for app in "${IMAGES_APP[@]}"; do
  ipsw class-dump "$MNT/Applications/$app.app/$app" --headers --output "$WORK/headers/$app" >/dev/null
done
mkdir -p "$WORK/swift"
ipsw swift-dump "$MNT/Applications/PineBoard.app/PineBoard" --demangle > "$WORK/swift/PineBoard.swift"

echo "[5/6] build indexes"
python3 "$REPO/scripts/index_bundles.py" "$MNT" "$REPO/index"
python3 "$REPO/scripts/index_headers.py" "$WORK/headers" "$REPO/index/objc"
python3 "$REPO/scripts/index_swift.py" "$WORK/swift/PineBoard.swift" "$REPO/index/swift/PineBoard.types.tsv"
python3 "$REPO/scripts/index_caml.py" "$MNT" "$REPO/index/animations.tsv"

echo "[6/6] unmount"
hdiutil detach "$MNT" >/dev/null
echo "done: indexes in $REPO/index"

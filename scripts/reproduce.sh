#!/bin/bash
# Rebuild everything in index/ from your own copy of the tvOS 26.6 IPSW.
# Decrypted images, headers, Swift dumps and assets stay in $WORK and are never committed.
#
# Usage: scripts/reproduce.sh /path/to/AppleTV5,3_26.6_23L773_Restore.ipsw [work_dir]
# Needs: macOS (aea, hdiutil), python3, ipsw (github.com/blacktop/ipsw).
set -euo pipefail

IPSW="${1:?path to the .ipsw}"
WORK="${2:-$PWD/.work}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OS_AEA="094-98312-085.dmg.aea"   # OS root filesystem (from BuildManifest: Manifest.OS)
MNT="$WORK/mnt"
JOBS="${JOBS:-4}"

mkdir -p "$WORK"
echo "[1/7] extract OS image"
[ -f "$WORK/$OS_AEA" ] || unzip -o -q "$IPSW" "$OS_AEA" -d "$WORK"

echo "[2/7] unwrap archive key (Apple public key service) and decrypt"
if [ ! -f "$WORK/os.dmg" ]; then
  KEY=$(ipsw fw aea "$WORK/$OS_AEA" --key | grep '^base64:' | tail -1)
  aea decrypt -i "$WORK/$OS_AEA" -o "$WORK/os.dmg" -key-value "$KEY"
fi

echo "[3/7] mount read-only"
mkdir -p "$MNT"
mount | grep -q "$MNT" || hdiutil attach -readonly -nobrowse -noverify -mountpoint "$MNT" "$WORK/os.dmg" >/dev/null
DSC="$MNT/System/Library/Caches/com.apple.dyld/dyld_shared_cache_arm64"
export MNT DSC WORK

echo "[4/7] list every binary"
ipsw dyld info "$DSC" --dylibs | sed -n -E 's/^ *[0-9]+: \([^)]*\) +(\/.*)$/\1/p' > "$WORK/dsc-images.txt"
( cd "$MNT" && find . -path ./System/Library/Caches -prune -o -path ./Applications -prune -o -type f -perm +111 -size +1k -print \
  | while IFS= read -r f; do head -c 4 "$f" | xxd -p | grep -q -E '^(cffaedfe|cafebabe|feedfacf)' && echo "${f#./}"; done ) > "$WORK/disk-machos.txt" || true

echo "[5/7] dump ObjC and Swift metadata for every image (local)"
# Unique output names: basename, plus parent folder when the basename repeats in the cache.
python3 - "$WORK" <<'PY'
import collections, hashlib, os, sys
w = sys.argv[1]
imgs = open(f"{w}/dsc-images.txt").read().splitlines()
count = collections.Counter(os.path.basename(p) for p in imgs)
with open(f"{w}/dsc-jobs.tsv", "w") as f:
    for p in imgs:
        b = os.path.basename(p)
        f.write(f"{p}\t{b if count[b] == 1 else b + '~' + os.path.basename(os.path.dirname(p))}\n")
with open(f"{w}/disk-jobs.tsv", "w") as f:
    for rel in open(f"{w}/disk-machos.txt").read().splitlines():
        f.write(f"{rel}\t{os.path.basename(rel)}~{hashlib.sha1(rel.encode()).hexdigest()[:8]}\n")
PY
dump_dsc() {
  ipsw class-dump "$DSC" "$1" --headers --output "$WORK/headers/dsc/$2" >/dev/null 2>&1 || true
  ipsw swift-dump "$DSC" "$1" --demangle > "$WORK/swift/dsc/$2.swift" 2>/dev/null || true
  [ -s "$WORK/swift/dsc/$2.swift" ] || rm -f "$WORK/swift/dsc/$2.swift"
}
dump_file() {  # $1 = path under the mount, $2 = output name, $3 = scope (apps|disk)
  ipsw class-dump "$MNT/$1" --headers --output "$WORK/headers/$3/$2" >/dev/null 2>&1 || true
  ipsw swift-dump "$MNT/$1" --demangle > "$WORK/swift/$3/$2.swift" 2>/dev/null || true
  [ -s "$WORK/swift/$3/$2.swift" ] || rm -f "$WORK/swift/$3/$2.swift"
}
export -f dump_dsc dump_file
mkdir -p "$WORK"/headers/{dsc,apps,disk} "$WORK"/swift/{dsc,apps,disk}
tr '\t' '\0' < "$WORK/dsc-jobs.tsv" | xargs -0 -n 2 -P "$JOBS" bash -c 'dump_dsc "$0" "$1"'
for app in "$MNT"/Applications/*.app "$MNT"/System/Library/CoreServices/*.app; do
  exe=$(/usr/libexec/PlistBuddy -c "Print :CFBundleExecutable" "$app/Info.plist" 2>/dev/null || basename "$app" .app)
  [ -f "$app/$exe" ] && dump_file "${app#$MNT/}/$exe" "$(basename "$app" .app)" apps
done
tr '\t' '\0' < "$WORK/disk-jobs.tsv" | xargs -0 -n 2 -P "$JOBS" bash -c 'dump_file "$0" "$1" disk'

echo "[6/7] build indexes"
python3 "$REPO/scripts/index_bundles.py" "$MNT" "$REPO/index"
for scope in dsc apps disk; do
  rm -rf "$REPO/index/objc/$scope" "$REPO/index/swift/$scope"
  python3 "$REPO/scripts/index_headers.py" "$WORK/headers/$scope" "$REPO/index/objc/$scope" >/dev/null
  mkdir -p "$REPO/index/swift/$scope"
  for f in "$WORK/swift/$scope"/*.swift; do
    [ -e "$f" ] && python3 "$REPO/scripts/index_swift.py" "$f" "$REPO/index/swift/$scope/$(basename "$f" .swift).types.tsv" >/dev/null
  done
done
{ printf 'name\tpath\n'; awk -F'\t' '{print $2"\t"$1}' "$WORK/disk-jobs.tsv" | sort; } > "$REPO/index/disk-images.tsv"
python3 "$REPO/scripts/index_caml.py" "$MNT" "$REPO/index/animations.tsv"

echo "[7/7] unmount"
hdiutil detach "$MNT" >/dev/null
echo "done: indexes in $REPO/index"

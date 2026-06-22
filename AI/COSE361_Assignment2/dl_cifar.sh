#!/usr/bin/env bash
# Parallel chunked downloader for cifar-10-python.tar.gz (server throttles per-connection).
set -u
URL="https://cave.cs.toronto.edu/kriz/cifar-10-python.tar.gz"
TOTAL=170498071
MD5_EXPECTED="c58f30108f718f92721af3b95e74349a"
N=32
OUT="/tmp/cifar-10-python.tar.gz"
PARTDIR="/tmp/cifar_parts"
rm -rf "$PARTDIR" "$OUT"; mkdir -p "$PARTDIR"

chunk=$(( (TOTAL + N - 1) / N ))

fetch() {
  local i=$1 start end expected got tries
  start=$(( i * chunk ))
  end=$(( start + chunk - 1 ))
  if [ "$end" -ge "$TOTAL" ]; then end=$(( TOTAL - 1 )); fi
  expected=$(( end - start + 1 ))
  local part="$PARTDIR/part_$i"
  for tries in 1 2 3 4 5 6 7 8; do
    curl -s --max-time 120 -r ${start}-${end} -o "$part" "$URL"
    got=$(stat -c%s "$part" 2>/dev/null || echo 0)
    if [ "$got" -eq "$expected" ]; then return 0; fi
    rm -f "$part"
  done
  echo "CHUNK_$i FAILED (expected $expected got ${got:-0})" >&2
  return 1
}

echo "Downloading $N chunks of ~$chunk bytes..."
pids=""
for i in $(seq 0 $((N-1))); do fetch "$i" & pids="$pids $!"; done
fail=0
for p in $pids; do wait "$p" || fail=1; done
if [ "$fail" -ne 0 ]; then echo "DOWNLOAD_FAILED"; exit 1; fi

# Concatenate parts in order
for i in $(seq 0 $((N-1))); do cat "$PARTDIR/part_$i"; done > "$OUT"
sz=$(stat -c%s "$OUT")
echo "Assembled size: $sz (expected $TOTAL)"
if [ "$sz" -ne "$TOTAL" ]; then echo "SIZE_MISMATCH"; exit 1; fi

md5=$(md5sum "$OUT" | awk '{print $1}')
echo "MD5: $md5 (expected $MD5_EXPECTED)"
if [ "$md5" != "$MD5_EXPECTED" ]; then echo "MD5_MISMATCH"; exit 1; fi
echo "OK: $OUT"
rm -rf "$PARTDIR"

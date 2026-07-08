#!/usr/bin/env python3
"""Extract the MAP block of a ladder log into testing-tool -i input format."""
import sys

src, dst = sys.argv[1], sys.argv[2]
lines = [ln.rstrip("\r\n") for ln in open(src, encoding="utf-8", errors="replace")]
i = next(k for k, ln in enumerate(lines) if ln.strip() == "MAP")
N = int(lines[i + 1].split()[0])
out = [lines[i + 1], lines[i + 2], lines[i + 3],
       " ".join(lines[i + 4].split()[1:])]          # strip "STRONGHOLDS"
out += lines[i + 5:i + 5 + N]
open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"wrote {dst} (N={N})")

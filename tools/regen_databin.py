#!/usr/bin/env python3
"""Regenerate data.bin: default = main.py built-ins for ALL _TUNABLES,
PRESERVING existing map_buckets and profiles (regen gotcha from 0703)."""
import json, sys, os, importlib.util

HERE = r"C:\Users\Infocar\NYPC\nation-providing"
sys.argv = ["main.py"]                      # keep main.py's loader from seeing our argv
spec = importlib.util.spec_from_file_location("bot_main", os.path.join(HERE, "main.py"))
bm = importlib.util.module_from_spec(spec)
sys.modules["bot_main"] = bm
os.chdir(HERE)                              # so its data.bin load sees the current file
spec.loader.exec_module(bm)

old = json.load(open(os.path.join(HERE, "data.bin"), encoding="utf-8"))
assert old.get("schema") == 2

# rebuild defaults from the module's CURRENT values -- but the module just
# loaded data.bin over its built-ins, so re-derive built-ins by re-reading the
# source constants is wrong too. Instead: start from the old defaults, then
# add/overwrite ONLY keys whose built-in differs or is new, taken from a fresh
# parse of main.py source WITHOUT param loading.
import ast
src = open(os.path.join(HERE, "main.py"), encoding="utf-8").read()
tree = ast.parse(src)
builtins = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name):
        name = node.targets[0].id
        if name in bm._TUNABLES:
            try:
                builtins[name] = ast.literal_eval(node.value)
            except Exception:
                pass

missing = [k for k in bm._TUNABLES if k not in builtins]
assert not missing, f"tunables without top-level literal assignment: {missing}"

PROFILES = {
    # hand-calibrated from the 0704-0706 log-verified archetypes; the router
    # in main.py classifies and applies these via apply_style_profile
    "rusher":     {"MIN_GARRISON": 4, "RUSH_PREP_HOPS": 7, "RUSH_MASS_ARMY": 4,
                   "OPENING_MAX_TURN": 45},
    "strangler":  {"CLEAR_SQUAD": 10, "CLEAR_MAX_SQUADS": 3, "STRIKE_FORCE": 10,
                   "COUNTER_EXPAND_MARGIN": 3, "REBUILD_GUARD_HOPS": 3},
    # mirror-A/B swept (6 games each vs base, 2026-07-06): FLOOD_DOM_EARLY 35,
    # RAID_MAX_SQUADS 4, BLOCK_SQUAD 6 each net-positive (2W4D0L); RAID_SQUAD 7
    # was NET NEGATIVE (1W1D4L — over-commit) and is deliberately absent.
    "megaboomer": {"RAID_MAX_SQUADS": 4, "FLOOD_DOM_EARLY": 35,
                   "TECH_RACE_MARGIN": 6, "BLOCK_SQUAD": 6, "GOLD_DUMP_TURN": 140},
}
new = {
    "schema": 2,
    "default": {k: builtins[k] for k in bm._TUNABLES},
    "map_buckets": old.get("map_buckets", []),
    "profiles": PROFILES,
}
with open(os.path.join(HERE, "data.bin"), "w", encoding="utf-8") as f:
    json.dump(new, f, separators=(",", ":"))
sz = os.path.getsize(os.path.join(HERE, "data.bin"))
print(f"data.bin: {len(new['default'])} defaults, buckets={new['map_buckets']}, {sz} bytes")
changed = {k: (old['default'].get(k), v) for k, v in new['default'].items()
           if old['default'].get(k) != v}
print("changed/new keys:", json.dumps(changed, indent=1))

#!/usr/bin/env python3
"""Check the 'wounded expander' signature in weekend logs: for every enemy
BASE BUILD event, record the HP of the enemy warriors standing in that region
at build time, and whether the region was neutral-side (border/mid) territory.
Also count how many enemy claims happened while their main force was in OUR half.
"""
import sys, os, json, importlib.util
from collections import deque

HERE = r"C:\Users\Infocar\NYPC\nation-providing"
LOGDIR = os.environ.get("NYPC_LOGDIR", os.path.join(HERE, "ladder_logs", "0704 ~ 0706"))

spec = importlib.util.spec_from_file_location("testing_tool", os.path.join(HERE, "testing-tool.py"))
tt = importlib.util.module_from_spec(spec)
sys.modules["testing_tool"] = tt
spec.loader.exec_module(tt)
spec2 = importlib.util.spec_from_file_location("replay_log", os.path.join(HERE, "replay_log.py"))
rl = importlib.util.module_from_spec(spec2)
sys.modules["replay_log"] = rl
spec2.loader.exec_module(rl)

Side, BKind = tt.Side, tt.BKind


def bfs(adj, src, N):
    d = [-1] * N
    d[src] = 0
    q = deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if d[v] < 0:
                d[v] = d[u] + 1
                q.append(v)
    return d


def analyze(path, opp_is_left):
    tt._dijkstra_cache.clear()
    m, turns, final = rl.parse_log_file(path)
    N = m.N
    st = tt.init_state(m)
    hopsL, hopsR = bfs(m.adj, 0, N), bfs(m.adj, N - 1, N)
    opp = Side.LEFT if opp_is_left else Side.RIGHT
    my_hops = hopsR if opp_is_left else hopsL   # OUR side's hops
    op_hops = hopsL if opp_is_left else hopsR
    builds = []          # (day, region, builder_hps, territory, opp_inhalf_count)
    for T in turns:
        st.day = T["day"]
        pre_regions = set(st.buildings.keys())
        rb_l, rb_r = tt.ResultBlock(), tt.ResultBlock()
        tr = {}
        try:
            for side, key in ((Side.LEFT, "L"), (Side.RIGHT, "R")):
                sub = tt.parse_block(side, T["cmd"][key])
                rb = rb_l if key == "L" else rb_r
                # snapshot warriors BEFORE this side's upgrades resolve
                if side is opp:
                    for r in sub.upgrades:
                        if r not in pre_regions and r != (0 if opp_is_left else N - 1):
                            whps = [w.hp for w in st.warriors.values()
                                    if w.side is opp and w.region == r]
                            if my_hops[r] < 0 or op_hops[r] < 0:
                                terr = "?"
                            elif my_hops[r] < op_hops[r]:
                                terr = "OURS"
                            elif my_hops[r] == op_hops[r]:
                                terr = "MID"
                            else:
                                terr = "theirs"
                            inhalf = sum(1 for w in st.warriors.values()
                                         if w.side is opp and 0 <= my_hops[w.region] < op_hops[w.region])
                            builds.append((st.day, r, whps, terr, inhalf))
                tt.apply_upgrades(st, m, side, sub, rb)
                tt.apply_moves(st, m, side, sub)
                tr[key] = tt.apply_train_charge(st, side, sub)
        except tt.WaError:
            break
        siege = {}
        tt.apply_day_movement(st, m, rb_l, rb_r)
        tt.spawn_trained(st, Side.LEFT, tr["L"], rb_l)
        tt.spawn_trained(st, Side.RIGHT, tr["R"], rb_r)
        tt.apply_day_combat(st, rb_l, rb_r, siege)
        tt.apply_day_siege(st, rb_l, rb_r, siege)
        tt.apply_evening_work(st)
        tt.apply_evening_upkeep(st, rb_l, rb_r)
    return builds


def main():
    sides = json.load(open("sides.json", encoding="utf-8"))
    picks = sys.argv[1:] or ["1 (3).txt", "1 (100).txt", "1 (18).txt", "1 (95).txt", "1 (71).txt"]
    tot = {"full": 0, "wounded": 0, "mid_ours": 0, "during_invasion": 0}
    for name in picks:
        info = sides[name]
        opp_left = info["side"] == "RIGHT"
        builds = analyze(os.path.join(LOGDIR, name), opp_left)
        print(f"\n=== {name} (opp={'LEFT' if opp_left else 'RIGHT'}, {len(builds)} enemy builds) ===")
        for day, r, whps, terr, inhalf in builds:
            tag = "WOUNDED" if whps and min(whps) <= 2 else ""
            tot["full" if not tag else "wounded"] += 1
            if terr in ("MID", "OURS"):
                tot["mid_ours"] += 1
            if inhalf >= 3:
                tot["during_invasion"] += 1
            print(f"  d{day:>3} r{r:>3} builderHP={whps} {terr:6s} their_bodies_in_OUR_half={inhalf} {tag}")
    print("\nTOTALS:", tot)


if __name__ == "__main__":
    main()

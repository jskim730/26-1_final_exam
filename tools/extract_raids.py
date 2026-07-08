#!/usr/bin/env python3
"""extract_raids.py — build the raid-backtest dataset from real ladder logs.

Re-simulates each game with the referee's own functions (exact state), detects
RAID LAUNCH events (our MOVE orders whose destination holds a LIVE enemy BASE),
snapshots everything a launch-time model could use, then labels the outcome.

Event JSON row:
  log, side, turn, target, tgt_level, tgt_hp, tgt_turret,
  squad: [{id, hp, md}]                    (md = BFS-hops march-day proxy)
  defs: [{hp, md, approaching, on_own_bld}](every enemy warrior, md to target)
  opp_gold, opp_hq_level, opp_train_cap, opp_hq_md (their HQ -> target)
  outcome: {base_died_turn|None, squad_dead, squad_n, horizon}

Usage: python tools/extract_raids.py <logdir> <sides.json> <out.jsonl>
Sequential only (dijkstra cache gotcha).
"""
import sys, os, json, importlib.util
from collections import deque

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

tt = _load("testing_tool", "testing-tool.py")
rl = _load("replay_log", "replay_log.py")
Side, BKind = tt.Side, tt.BKind
HORIZON = 20

def bfs_all(adj, src, N):
    d = [-1] * N; d[src] = 0; q = deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if d[v] < 0:
                d[v] = d[u] + 1; q.append(v)
    return d

def extract(logdir, fn, myside):
    tt._dijkstra_cache.clear()
    m, turns, final = rl.parse_log_file(os.path.join(logdir, fn))
    st = tt.init_state(m)
    N = m.N
    adj = [list(m.adj[r]) for r in range(N)]
    my = Side.LEFT if myside == "LEFT" else Side.RIGHT
    op = Side.RIGHT if myside == "LEFT" else Side.LEFT
    my_k = "L" if myside == "LEFT" else "R"
    op_hq_r = N - 1 if myside == "LEFT" else 0
    dist = {}                                    # region -> bfs dists (cache)
    def D(src):
        if src not in dist:
            dist[src] = bfs_all(adj, src, N)
        return dist[src]

    events = []          # open + closed
    prev_pos = {}        # enemy id -> region (last turn)
    for T in turns:
        st.day = T["day"]
        rb_l, rb_r = tt.ResultBlock(), tt.ResultBlock()
        tr = {}
        subs = {}
        try:
            for side, k in ((Side.LEFT, "L"), (Side.RIGHT, "R")):
                subs[k] = tt.parse_block(side, T["cmd"][k])
                tt.apply_upgrades(st, m, side, subs[k], rb_l if k == "L" else rb_r)
        except tt.WaError:
            break
        # ---- detect OUR new raid orders BEFORE movement applies -------------
        # (state = this morning's positions; sub.moves = (unit_key, dest))
        my_moves = getattr(subs[my_k], "moves", [])
        for wk, dest in my_moves:
            b = st.buildings.get(dest)
            if b is None or b.side is not op or b.kind is not BKind.BASE:
                continue
            w = st.warriors.get(wk)
            if w is None or w.hp <= 0:
                continue
            ev = next((e for e in events if e["target"] == dest
                       and e["_open"]), None)
            if ev is None:
                dd = D(dest)
                opp_hq_b = st.buildings.get(op_hq_r)
                defs = []
                for ok, ow in st.warriors.items():
                    if ow.side is not op or ow.hp <= 0:
                        continue
                    md = dd[ow.region] if dd[ow.region] >= 0 else 99
                    pp = prev_pos.get(ok)
                    appr = (pp is not None and dd[pp] >= 0
                            and dd[ow.region] < dd[pp])
                    ob = st.buildings.get(ow.region)
                    defs.append(dict(hp=ow.hp, md=md, approaching=bool(appr),
                                     on_own_bld=bool(ob is not None
                                                     and ob.side is op)))
                ev = dict(log=fn, side=myside, turn=T["day"], target=dest,
                          tgt_level=b.level, tgt_hp=b.hp,
                          tgt_turret=b.turret(),
                          squad=[], defs=defs,
                          opp_gold=st.gold[1 if my is Side.LEFT else 0],
                          opp_hq_level=(opp_hq_b.level if opp_hq_b else 0),
                          opp_train_cap=(tt.HQ_LEVELS[opp_hq_b.level].train_cap
                                         if opp_hq_b else 0),
                          opp_hq_md=dd[op_hq_r] if dd[op_hq_r] >= 0 else 99,
                          _ids=set(), _open=True, _end=T["day"] + HORIZON,
                          outcome=dict(base_died_turn=None, squad_dead=0,
                                       squad_n=0, horizon=HORIZON))
                events.append(ev)
            if wk not in ev["_ids"]:
                dd = D(ev["target"])
                md = dd[w.region] if dd[w.region] >= 0 else 99
                ev["_ids"].add(wk)
                ev["squad"].append(dict(id=str(wk), hp=w.hp, md=md))
        # ---- advance the day (referee-exact) --------------------------------
        try:
            for side, k in ((Side.LEFT, "L"), (Side.RIGHT, "R")):
                tt.apply_moves(st, m, side, subs[k])
                tr[k] = tt.apply_train_charge(st, side, subs[k])
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
        prev_pos = {k: w.region for k, w in st.warriors.items()
                    if w.side is op and w.hp > 0}
        # ---- update open events ---------------------------------------------
        for ev in events:
            if not ev["_open"]:
                continue
            b = st.buildings.get(ev["target"])
            if (b is None or b.side is not op) \
                    and ev["outcome"]["base_died_turn"] is None:
                ev["outcome"]["base_died_turn"] = T["day"]
            dead = sum(1 for wk in ev["_ids"]
                       if wk not in st.warriors or st.warriors[wk].hp <= 0)
            ev["outcome"]["squad_dead"] = dead
            ev["outcome"]["squad_n"] = len(ev["_ids"])
            if T["day"] >= ev["_end"] or ev["outcome"]["base_died_turn"]:
                ev["_open"] = False
    for ev in events:
        ev.pop("_ids", None); ev.pop("_open", None); ev.pop("_end", None)
    return events


def main():
    logdir, sides_p, out_p = sys.argv[1], sys.argv[2], sys.argv[3]
    sides = json.load(open(sides_p, encoding="utf-8"))
    n_ev = 0
    with open(out_p, "w", encoding="utf-8") as f:
        for fn, meta in sorted(sides.items()):
            side = meta["side"] if isinstance(meta, dict) else meta
            try:
                evs = extract(logdir, fn, side)
            except Exception as e:
                print(f"!! {fn}: {e}")
                continue
            for ev in evs:
                f.write(json.dumps(ev) + "\n")
            n_ev += len(evs)
            print(f"{fn:18s} {side:5s} events={len(evs)}")
    print(f"TOTAL events: {n_ev} -> {out_p}")


if __name__ == "__main__":
    main()

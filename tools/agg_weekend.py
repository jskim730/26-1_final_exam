#!/usr/bin/env python3
"""
agg_weekend.py — authoritative per-game stats for the 0704~0706 ladder pool.
Re-simulates every log with the referee's own functions (replay_log machinery),
orients each game to OUR side (sides.json from identify_side.py), and prints
a per-game table + aggregate report + loss/draw taxonomy inputs.
"""
import sys, os, json, glob, importlib.util
from collections import deque, defaultdict, Counter

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


def bfs_hops(adj, src, N):
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


def analyze(path):
    tt._dijkstra_cache.clear()
    m, turns, final = rl.parse_log_file(path)
    N = m.N
    hq = {"L": 0, "R": N - 1}
    hops = {"L": bfs_hops(m.adj, 0, N), "R": bfs_hops(m.adj, N - 1, N)}
    diam = hops["L"][N - 1]
    st = tt.init_state(m)

    g = dict(N=N, K=m.K, diam=diam, n_sh=len(m.strongholds), days=len(turns))
    tech = {"L": {}, "R": {}}
    heals = {"L": 0, "R": 0}
    income = {"L": 0, "R": 0}
    trains = {"L": 0, "R": 0}
    deaths = {"L": 0, "R": 0}
    hq_siege_taken = {"L": 0, "R": 0}
    base_siege_taken = {"L": 0, "R": 0}
    first_hq_siege = {"L": None, "R": None}
    bases_lost = {"L": 0, "R": 0}      # razed (destroyed) bases
    bases_built = {"L": 0, "R": 0}
    first_inc = {"L": None, "R": None}  # first enemy strictly in my half
    max_army = {"L": 0, "R": 0}
    hq_hp_t150 = {"L": None, "R": None}
    wa = None

    for T in turns:
        day = T["day"]
        st.day = day
        pre_w = set(st.warriors.keys())
        pre_bases = {r for r, b in st.buildings.items() if b.kind is BKind.BASE}
        rb_l, rb_r = tt.ResultBlock(), tt.ResultBlock()
        tr = {}
        try:
            for side, key in ((Side.LEFT, "L"), (Side.RIGHT, "R")):
                sub = tt.parse_block(side, T["cmd"][key])
                rb = rb_l if key == "L" else rb_r
                tt.apply_upgrades(st, m, side, sub, rb)
                tt.apply_moves(st, m, side, sub)
                tr[key] = tt.apply_train_charge(st, side, sub)
                trains[key] += tr[key]
        except tt.WaError as e:
            wa = (day, "L" if e.side is Side.LEFT else "R", e.msg)
            break
        siege = {}
        tt.apply_day_movement(st, m, rb_l, rb_r)
        tt.spawn_trained(st, Side.LEFT, tr["L"], rb_l)
        tt.spawn_trained(st, Side.RIGHT, tr["R"], rb_r)
        tt.apply_day_combat(st, rb_l, rb_r, siege)
        tt.apply_day_siege(st, rb_l, rb_r, siege)
        gpre = list(st.gold)
        tt.apply_evening_work(st)
        for key, u in (("L", 0), ("R", 1)):
            income[key] += st.gold[u] - gpre[u]
        tt.apply_evening_upkeep(st, rb_l, rb_r)

        # records
        for rb in (rb_l, rb_r):
            for (reg, ups) in rb.upgrades:
                k = "L" if ups is Side.LEFT else "R"
                b = st.buildings.get(reg)
                if reg in (hq["L"], hq["R"]):
                    if b and b.level >= tt.HQ_MAX_LEVEL and b.level in tech[k]:
                        heals[k] += 1
                    elif b:
                        tech[k][b.level] = day
                else:
                    if reg not in pre_bases and b is not None:
                        bases_built[k] += 1
            for (sgs, reg, dmg) in rb.sieges:
                vk = "L" if sgs is Side.LEFT else "R"   # victim side
                if reg in (hq["L"], hq["R"]):
                    hq_siege_taken[vk] += dmg
                    if first_hq_siege[vk] is None:
                        first_hq_siege[vk] = day
                else:
                    base_siege_taken[vk] += dmg
        # razed bases
        for r in pre_bases:
            if r not in st.buildings:
                # owner was?  pre snapshot didn't save side; recompute via hops half
                pass
        # deaths + army sizes + incursion
        cnt = {"L": 0, "R": 0}
        for k2 in pre_w - set(st.warriors.keys()):
            deaths["L" if tt.id_str(k2)[0] == "A" else "R"] += 1
        for w in st.warriors.values():
            k = "L" if w.side is Side.LEFT else "R"
            cnt[k] += 1
            ek = "R" if k == "L" else "L"
            if hops[ek][w.region] < hops[k][w.region] and first_inc[ek] is None:
                first_inc[ek] = day
        for k in ("L", "R"):
            max_army[k] = max(max_army[k], cnt[k])
        if day == 150:
            for k in ("L", "R"):
                b = st.buildings.get(hq[k])
                hq_hp_t150[k] = b.hp if b else 0

    # base razes: count via built minus final
    final_bases = {"L": 0, "R": 0}
    for r, b in st.buildings.items():
        if b.kind is BKind.BASE:
            final_bases["L" if b.side is Side.LEFT else "R"] += 1
    for k in ("L", "R"):
        bases_lost[k] = bases_built[k] - final_bases[k]

    bL = st.buildings.get(hq["L"]); bR = st.buildings.get(hq["R"])
    g.update(dict(
        outcome=final[0] if final else "?", reason=final[1] if final else "?",
        wa=wa,
        hq_lvl={"L": bL.level if bL else 0, "R": bR.level if bR else 0},
        hq_hp={"L": bL.hp if bL else 0, "R": bR.hp if bR else 0},
        hq_hp_t150=hq_hp_t150,
        gold={"L": st.gold[0], "R": st.gold[1]},
        income=income, trains=trains, deaths=deaths,
        tech=tech, heals=heals,
        hq_siege_taken=hq_siege_taken, first_hq_siege=first_hq_siege,
        base_siege_taken=base_siege_taken,
        bases_built=bases_built, bases_final=final_bases, bases_lost=bases_lost,
        first_inc=first_inc, max_army=max_army,
    ))
    return g


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sides = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "sides.json", encoding="utf-8"))
    rows = []
    for name, info in sorted(sides.items()):
        if info.get("side") not in ("LEFT", "RIGHT"):
            print(f"!! skip {name}: side={info.get('side')}")
            continue
        path = os.path.join(LOGDIR, name)
        try:
            g = analyze(path)
        except Exception as e:
            print(f"!! {name}: {e}")
            continue
        me = "L" if info["side"] == "LEFT" else "R"
        op = "R" if me == "L" else "L"
        res = "draw"
        if g["outcome"] == ("LEFT_WIN" if me == "L" else "RIGHT_WIN"):
            res = "win"
        elif g["outcome"] == ("RIGHT_WIN" if me == "L" else "LEFT_WIN"):
            res = "loss"
        row = dict(log=name, me=info["side"], res=res, reason=g["reason"],
                   N=g["N"], diam=g["diam"], days=g["days"], wa=g["wa"],
                   my_hq=f"L{g['hq_lvl'][me]}/{g['hq_hp'][me]}",
                   op_hq=f"L{g['hq_lvl'][op]}/{g['hq_hp'][op]}",
                   my_hq_lvl=g["hq_lvl"][me], my_hq_hp=g["hq_hp"][me],
                   op_hq_lvl=g["hq_lvl"][op], op_hq_hp=g["hq_hp"][op],
                   my_income=g["income"][me], op_income=g["income"][op],
                   my_trains=g["trains"][me], op_trains=g["trains"][op],
                   my_deaths=g["deaths"][me], op_deaths=g["deaths"][op],
                   my_gold=g["gold"][me], op_gold=g["gold"][op],
                   my_bases=g["bases_final"][me], op_bases=g["bases_final"][op],
                   my_bases_built=g["bases_built"][me], op_bases_built=g["bases_built"][op],
                   my_bases_lost=g["bases_lost"][me], op_bases_lost=g["bases_lost"][op],
                   my_hqsiege_taken=g["hq_siege_taken"][me], op_hqsiege_taken=g["hq_siege_taken"][op],
                   my_first_hq_siege=g["first_hq_siege"][me], op_first_hq_siege=g["first_hq_siege"][op],
                   my_basesiege_taken=g["base_siege_taken"][me], op_basesiege_taken=g["base_siege_taken"][op],
                   my_tech=g["tech"][me], op_tech=g["tech"][op],
                   my_heals=g["heals"][me], op_heals=g["heals"][op],
                   my_first_inc=g["first_inc"][me], op_first_inc=g["first_inc"][op],
                   my_max_army=g["max_army"][me], op_max_army=g["max_army"][op])
        rows.append(row)

    json.dump(rows, open("weekend_rows.json", "w", encoding="utf-8"), indent=1)

    n = len(rows)
    W = sum(r["res"] == "win" for r in rows)
    D = sum(r["res"] == "draw" for r in rows)
    L = sum(r["res"] == "loss" for r in rows)
    print(f"\n== {n} games ==  {W}W / {D}D / {L}L  score={100*(W+0.5*D)/n:.0f}%")
    for res in ("win", "draw", "loss"):
        sub = [r for r in rows if r["res"] == res]
        rc = Counter(r["reason"] for r in sub)
        print(f"  {res:5s} {len(sub):3d}  reasons={dict(rc)}")

    print("\n-- LOSSES --")
    for r in rows:
        if r["res"] != "loss":
            continue
        t5 = r["my_tech"].get(5); ot5 = r["op_tech"].get(5)
        print(f"{r['log']:16s} {r['reason']:12s} N={r['N']:3d} d{r['diam']:2d} days={r['days']:3d} "
              f"my={r['my_hq']} op={r['op_hq']} "
              f"inc {r['my_income']:>6}/{r['op_income']:>6} tr {r['my_trains']:>3}/{r['op_trains']:>3} "
              f"hqS {r['my_hqsiege_taken']:>3}@{str(r['my_first_hq_siege']):>4}/{r['op_hqsiege_taken']:>3} "
              f"bases {r['my_bases']}({r['my_bases_lost']}lost)/{r['op_bases']}({r['op_bases_lost']}) "
              f"L5 {t5}/{ot5} gold {r['my_gold']}/{r['op_gold']}")
    print("\n-- DRAWS --")
    for r in rows:
        if r["res"] != "draw":
            continue
        t5 = r["my_tech"].get(5); ot5 = r["op_tech"].get(5)
        print(f"{r['log']:16s} {r['reason']:12s} N={r['N']:3d} d{r['diam']:2d} "
              f"my={r['my_hq']} op={r['op_hq']} inc {r['my_income']:>6}/{r['op_income']:>6} "
              f"hqS {r['my_hqsiege_taken']:>3}/{r['op_hqsiege_taken']:>3} "
              f"bases {r['my_bases']}/{r['op_bases']} L5 {t5}/{ot5} gold {r['my_gold']}/{r['op_gold']}")
    print("\n-- WINS --")
    for r in rows:
        if r["res"] != "win":
            continue
        t5 = r["my_tech"].get(5); ot5 = r["op_tech"].get(5)
        print(f"{r['log']:16s} {r['reason']:12s} N={r['N']:3d} d{r['diam']:2d} "
              f"my={r['my_hq']} op={r['op_hq']} inc {r['my_income']:>6}/{r['op_income']:>6} "
              f"hqS {r['my_hqsiege_taken']:>3}/{r['op_hqsiege_taken']:>3} dealt@{str(r['op_first_hq_siege']):>4} "
              f"bases {r['my_bases']}/{r['op_bases']} L5 {t5}/{ot5}")

    # aggregate signals
    print("\n-- AGGREGATE --")
    tot_hqS_taken = sum(r["my_hqsiege_taken"] for r in rows)
    tot_hqS_dealt = sum(r["op_hqsiege_taken"] for r in rows)
    tot_bS_taken = sum(r["my_basesiege_taken"] for r in rows)
    tot_bS_dealt = sum(r["op_basesiege_taken"] for r in rows)
    print(f"HQ siege   taken={tot_hqS_taken} dealt={tot_hqS_dealt}")
    print(f"base siege taken={tot_bS_taken} dealt={tot_bS_dealt}")
    print(f"bases razed: ours={sum(r['my_bases_lost'] for r in rows)} theirs={sum(r['op_bases_lost'] for r in rows)}")
    myL5 = [r["my_tech"].get(5) for r in rows if r["my_tech"].get(5)]
    opL5 = [r["op_tech"].get(5) for r in rows if r["op_tech"].get(5)]
    print(f"our L5: {len(myL5)}/{n} median t{sorted(myL5)[len(myL5)//2] if myL5 else '-'} | "
          f"opp L5: {len(opL5)}/{n} median t{sorted(opL5)[len(opL5)//2] if opL5 else '-'}")
    print(f"income:  ours med {sorted(r['my_income'] for r in rows)[n//2]}  "
          f"opp med {sorted(r['op_income'] for r in rows)[n//2]}")
    print(f"trains:  ours med {sorted(r['my_trains'] for r in rows)[n//2]}  "
          f"opp med {sorted(r['op_trains'] for r in rows)[n//2]}")


if __name__ == "__main__":
    main()

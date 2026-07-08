#!/usr/bin/env python3
"""ghost_battery.py — validate the current bot against REAL opponents:
replay each weekend loss/draw opponent as a ghost vs main.py, then compare
OUR income/tech/bases at fixed checkpoints against the ORIGINAL log's old-bot
trajectory (same map, same real opponent, same turns).
Phase 1: run games in parallel (subprocesses). Phase 2: analyze sequentially.
"""
import sys, os, json, subprocess, re, importlib.util
from collections import deque
from concurrent.futures import ThreadPoolExecutor

HERE = r"C:\Users\Infocar\NYPC\nation-providing"
SP = os.path.dirname(os.path.abspath(__file__))
LOGDIR = os.environ.get("NYPC_LOGDIR", os.path.join(HERE, "ladder_logs", "0704 ~ 0706"))
CHK = (60, 100)

spec = importlib.util.spec_from_file_location("testing_tool", os.path.join(HERE, "testing-tool.py"))
tt = importlib.util.module_from_spec(spec); sys.modules["testing_tool"] = tt
spec.loader.exec_module(tt)
spec2 = importlib.util.spec_from_file_location("replay_log", os.path.join(HERE, "replay_log.py"))
rl = importlib.util.module_from_spec(spec2); sys.modules["replay_log"] = rl
spec2.loader.exec_module(rl)
Side, BKind = tt.Side, tt.BKind


def extract_map(src, dst):
    lines = [ln.rstrip("\r\n") for ln in open(src, encoding="utf-8", errors="replace")]
    i = next(k for k, ln in enumerate(lines) if ln.strip() == "MAP")
    N = int(lines[i + 1].split()[0])
    out = [lines[i + 1], lines[i + 2], lines[i + 3], " ".join(lines[i + 4].split()[1:])]
    out += lines[i + 5:i + 5 + N]
    open(dst, "w", encoding="utf-8").write("\n".join(out) + "\n")


def side_metrics(path, key):
    """Re-sim a log; return {turn: (income_cum, hq_lvl, n_bases)} at CHK + length."""
    tt._dijkstra_cache.clear()
    m, turns, final = rl.parse_log_file(path)
    st = tt.init_state(m)
    hq_r = 0 if key == "L" else m.N - 1
    inc = {"L": 0, "R": 0}
    out = {}
    for T in turns:
        st.day = T["day"]
        rb_l, rb_r = tt.ResultBlock(), tt.ResultBlock()
        tr = {}
        try:
            for side, k in ((Side.LEFT, "L"), (Side.RIGHT, "R")):
                sub = tt.parse_block(side, T["cmd"][k])
                tt.apply_upgrades(st, m, side, sub, rb_l if k == "L" else rb_r)
                tt.apply_moves(st, m, side, sub)
                tr[k] = tt.apply_train_charge(st, side, sub)
        except tt.WaError:
            break
        siege = {}
        tt.apply_day_movement(st, m, rb_l, rb_r)
        tt.spawn_trained(st, Side.LEFT, tr["L"], rb_l)
        tt.spawn_trained(st, Side.RIGHT, tr["R"], rb_r)
        tt.apply_day_combat(st, rb_l, rb_r, siege)
        tt.apply_day_siege(st, rb_l, rb_r, siege)
        g0 = list(st.gold)
        tt.apply_evening_work(st)
        inc["L"] += st.gold[0] - g0[0]; inc["R"] += st.gold[1] - g0[1]
        tt.apply_evening_upkeep(st, rb_l, rb_r)
        if T["day"] in CHK:
            b = st.buildings.get(hq_r)
            nb = sum(1 for bb in st.buildings.values()
                     if bb.kind is BKind.BASE
                     and bb.side is (Side.LEFT if key == "L" else Side.RIGHT))
            out[T["day"]] = (inc[key], b.level if b else 0, nb)
    return out, len(turns), (final[0] if final else "?")


def main():
    sides = json.load(open(os.path.join(SP, "sides.json"), encoding="utf-8"))
    rows = json.load(open(os.path.join(SP, "weekend_rows.json"), encoding="utf-8"))
    targets = [r for r in rows if r["res"] in ("loss", "draw")]
    jobs = []
    for i, r in enumerate(targets):
        name = r["log"]
        me = sides[name]["side"]                 # LEFT/RIGHT = our side
        opp = "RIGHT" if me == "LEFT" else "LEFT"
        src = os.path.join(LOGDIR, name)
        mp = os.path.join(SP, f"gb_m{i}.txt")
        lg = os.path.join(SP, f"gb_l{i}.txt")
        ol = os.path.join(SP, f"gb_o{i}.txt")    # copy of original (space-free)
        if not os.path.exists(mp):
            extract_map(src, mp)
        if not os.path.exists(ol):
            open(ol, "w", encoding="utf-8").write(open(src, encoding="utf-8", errors="replace").read())
        jobs.append((i, name, me, opp, mp, lg, ol, r["res"]))

    def play(j):
        i, name, me, opp, mp, lg, ol, res0 = j
        if os.path.exists(lg) and os.path.getsize(lg) > 1000:
            return
        ghost = f"python ghost_bot.py {ol} {opp}"
        mine = "python main.py"
        a, b = (mine, ghost) if me == "LEFT" else (ghost, mine)
        subprocess.run(["python", "testing-tool-tune.py", "-i", mp, "-l", lg,
                        "-a", a, "-b", b], cwd=HERE, capture_output=True,
                       text=True, timeout=420)

    with ThreadPoolExecutor(5) as ex:
        list(ex.map(play, jobs))
    print("games done; analyzing...")

    out = []
    for i, name, me, opp, mp, lg, ol, res0 in jobs:
        key = "L" if me == "LEFT" else "R"
        try:
            new_m, new_len, new_res = side_metrics(lg, key)
            old_m, old_len, old_res = side_metrics(ol, key)
        except Exception as e:
            print(f"!! {name}: {e}")
            continue
        rec = dict(log=name, res0=res0, new_len=new_len,
                   new_res=new_res, old_res=old_res)
        for c in CHK:
            if c in new_m and c in old_m:
                rec[f"d_inc{c}"] = new_m[c][0] - old_m[c][0]
                rec[f"d_hq{c}"] = new_m[c][1] - old_m[c][1]
                rec[f"d_nb{c}"] = new_m[c][2] - old_m[c][2]
        out.append(rec)
    json.dump(out, open(os.path.join(SP, "ghost_battery.json"), "w"), indent=1)

    for c in CHK:
        ds = [r[f"d_inc{c}"] for r in out if f"d_inc{c}" in r]
        hq = [r[f"d_hq{c}"] for r in out if f"d_hq{c}" in r]
        nb = [r[f"d_nb{c}"] for r in out if f"d_nb{c}" in r]
        if ds:
            print(f"T{c}: n={len(ds)} d_income med={sorted(ds)[len(ds)//2]} "
                  f"mean={sum(ds)//len(ds)} worse_count={sum(1 for x in ds if x < -200)} | "
                  f"d_hq mean={sum(hq)/len(hq):.2f} | d_bases mean={sum(nb)/len(nb):.2f}")
    print("\nWORST 8 regressions at T100 (d_income):")
    bad = sorted([r for r in out if "d_inc100" in r], key=lambda r: r["d_inc100"])[:8]
    for r in bad:
        print(f"  {r['log']:16s} {r['res0']:4s} d_inc100={r['d_inc100']:>6} "
              f"d_hq100={r.get('d_hq100')} d_nb100={r.get('d_nb100')} len={r['new_len']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
identify_side.py — figure out which side (LEFT/RIGHT) our deterministic bot
played in each anonymised ladder log.

Stage A (fast): spawn main.py as LEFT and as RIGHT on the log's map, read its
turn-1 COMMAND block, compare with the log's recorded turn-1 blocks.
Stage B (deep, only if ambiguous): re-simulate the game with the referee's own
functions, feed the bot the exact wire result blocks turn by turn, and count
how many turns each hypothesis stays command-identical to the log. The side
that survives longer is us.

Usage: python identify_side.py <log-dir> [--out sides.json] [--jobs 4]
"""
import sys, os, json, glob, subprocess, threading, importlib.util
from concurrent.futures import ThreadPoolExecutor

HERE = r"C:\Users\Infocar\NYPC\nation-providing"

spec = importlib.util.spec_from_file_location("testing_tool", os.path.join(HERE, "testing-tool.py"))
tt = importlib.util.module_from_spec(spec)
sys.modules["testing_tool"] = tt
spec.loader.exec_module(tt)

spec2 = importlib.util.spec_from_file_location("replay_log", os.path.join(HERE, "replay_log.py"))
rl = importlib.util.module_from_spec(spec2)
sys.modules["replay_log"] = rl
spec2.loader.exec_module(rl)

Side = tt.Side
BOT_CMD = [sys.executable, "main.py"]


class Bot:
    def __init__(self):
        self.p = subprocess.Popen(BOT_CMD, cwd=HERE, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, bufsize=1)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def readline(self, timeout=10.0):
        out = [None]
        def _r():
            out[0] = self.p.stdout.readline()
        t = threading.Thread(target=_r, daemon=True)
        t.start(); t.join(timeout)
        if out[0] is None or out[0] == "":
            return None
        return out[0].rstrip("\n")

    def close(self):
        try:
            self.send("FINISH")
        except Exception:
            pass
        try:
            self.p.wait(timeout=2)
        except Exception:
            self.p.kill()


def send_ready(bot, side_name, m):
    bot.send(f"READY {side_name}")
    bot.send(f"{m.N} {m.K}")
    bot.send(" ".join(map(str, m.x)))
    bot.send(" ".join(map(str, m.y)))
    bot.send(" ".join(map(str, m.strongholds)))
    for i in range(m.N):
        row = str(len(m.adj[i])) + ("" if not m.adj[i] else " " + " ".join(map(str, m.adj[i])))
        bot.send(row)


def read_cmd_block(bot):
    first = bot.readline()
    if first != "COMMAND":
        return None
    lines = []
    while True:
        ln = bot.readline()
        if ln is None:
            return None
        if ln == "END":
            return lines
        lines.append(ln)


def wire_result_block(st, day, t_self, tok_self, t_opp, tok_opp, rb_self, rb_opp):
    """Exact clone of testing-tool send_result_block, into a list of lines."""
    out = []
    merged_rec, merged_up, merged_mv, merged_dmg, merged_sg = tt._merge_results(rb_self, rb_opp)
    out.append(f"TURN {day}")
    out.append(f"TIME {t_self} {tok_self} {t_opp} {tok_opp}")
    out.append(f"UPGRADE {len(merged_up)}")
    for (region, up_side) in merged_up:
        out.append(f"{up_side.letter} {region}")
    out.append(f"TRAIN {len(merged_rec)}")
    if merged_rec:
        out.append(" ".join(tt.id_str(k) for k in merged_rec))
    out.append(f"MOVE {len(merged_mv)}")
    for (key, new_region) in merged_mv:
        out.append(f"{tt.id_str(key)} {new_region}")
    out.append(f"DAMAGE {len(merged_dmg)}")
    for (cause, key, dmg) in merged_dmg:
        out.append(f"{cause} {tt.id_str(key)} {dmg}")
    out.append(f"SIEGE {len(merged_sg)}")
    for (sg_side, region, dmg) in merged_sg:
        out.append(f"{sg_side.letter} {region} {dmg}")
    out.append("END")
    return out


def deep_agree_turns(path, hypothesis, max_turns=210):
    """Ghost-drive main.py as `hypothesis` ('LEFT'/'RIGHT') along the log's
    trajectory; return number of turns whose commands match the log exactly."""
    tt._dijkstra_cache.clear()
    m, turns, final = rl.parse_log_file(path)
    st = tt.init_state(m)
    bot = Bot()
    agree = 0
    try:
        send_ready(bot, hypothesis, m)
        if bot.readline() != "OK":
            return -1
        my_key = "L" if hypothesis == "LEFT" else "R"
        for T in turns[:max_turns]:
            day = T["day"]
            st.day = day
            bot.send(f"START TURN {day}")
            got = read_cmd_block(bot)
            if got is None:
                break
            want = T["cmd"][my_key]
            if got != want and sorted(got) != sorted(want):
                break
            agree += 1
            # advance the sim with the LOG's commands (both sides)
            rb_l, rb_r = tt.ResultBlock(), tt.ResultBlock()
            trains = {}
            try:
                for side, key, blk, rb in ((Side.LEFT, "L", T["cmd"]["L"], rb_l),
                                           (Side.RIGHT, "R", T["cmd"]["R"], rb_r)):
                    sub = tt.parse_block(side, blk)
                    tt.apply_upgrades(st, m, side, sub, rb)
                    tt.apply_moves(st, m, side, sub)
                    trains[key] = tt.apply_train_charge(st, side, sub)
            except tt.WaError:
                break
            siege = {}
            tt.apply_day_movement(st, m, rb_l, rb_r)
            tt.spawn_trained(st, Side.LEFT, trains["L"], rb_l)
            tt.spawn_trained(st, Side.RIGHT, trains["R"], rb_r)
            tt.apply_day_combat(st, rb_l, rb_r, siege)
            tt.apply_day_siege(st, rb_l, rb_r, siege)
            tt.apply_evening_work(st)
            tt.apply_evening_upkeep(st, rb_l, rb_r)
            rb_self = rb_l if my_key == "L" else rb_r
            rb_opp = rb_r if my_key == "L" else rb_l
            blk = wire_result_block(st, day, 5, 5, 5, 5, rb_self, rb_opp)
            for ln in blk:
                bot.send(ln)
    finally:
        bot.close()
    return agree


def turn1_match(path):
    """Return (matchL, matchR, cmdsL, cmdsR) for turn-1 fingerprint."""
    m, turns, final = rl.parse_log_file(path)
    if not turns:
        return None
    res = {}
    for side_name, key in (("LEFT", "L"), ("RIGHT", "R")):
        bot = Bot()
        try:
            send_ready(bot, side_name, m)
            if bot.readline() != "OK":
                res[key] = None
                continue
            bot.send("START TURN 1")
            got = read_cmd_block(bot)
            want = turns[0]["cmd"][key]
            res[key] = (got == want or (got is not None and sorted(got) == sorted(want)))
        finally:
            bot.close()
    return res.get("L"), res.get("R"), final


def classify_stage_a(path):
    """Turn-1 fingerprint only (no simulation -> thread-safe)."""
    name = os.path.basename(path)
    try:
        mL, mR, final = turn1_match(path)
    except Exception as e:
        return name, dict(side="ERROR", err=str(e))
    if mL and not mR:
        side = "LEFT"; how = "turn1"
    elif mR and not mL:
        side = "RIGHT"; how = "turn1"
    else:
        side = "AMBIG"; how = f"turn1(L={mL},R={mR})"
    return name, dict(side=side, how=how,
                      outcome=final[0] if final else "?",
                      reason=final[1] if final else "?")


def main():
    argv = sys.argv[1:]
    jobs = 4
    out_path = "sides.json"
    if "--jobs" in argv:
        k = argv.index("--jobs"); jobs = int(argv[k + 1]); del argv[k:k + 2]
    if "--out" in argv:
        k = argv.index("--out"); out_path = argv[k + 1]; del argv[k:k + 2]
    d = argv[0]
    paths = sorted(glob.glob(os.path.join(d, "*.txt")))
    results = {}
    with ThreadPoolExecutor(jobs) as ex:
        for name, r in ex.map(classify_stage_a, paths):
            results[name] = r
            print(f"{name:40s} -> {r.get('side'):7s} {r.get('how','')} "
                  f"{r.get('outcome','')} {r.get('reason','')}", flush=True)

    # Stage B: deep replay, STRICTLY SEQUENTIAL (referee dijkstra cache is
    # module-level and map-keyed -> concurrent games poison each other)
    for name, r in results.items():
        if r.get("side") != "AMBIG":
            continue
        path = os.path.join(d, name)
        aL = deep_agree_turns(path, "LEFT")
        aR = deep_agree_turns(path, "RIGHT")
        r["side"] = "LEFT" if aL > aR else ("RIGHT" if aR > aL else "UNKNOWN")
        r["how"] += f" deep(L={aL},R={aR})"
        print(f"{name:40s} -> {r['side']:7s} {r['how']}", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)
    from collections import Counter
    c = Counter(r["side"] for r in results.values())
    print(f"\nSides: {dict(c)}  -> wrote {out_path}")


if __name__ == "__main__":
    main()

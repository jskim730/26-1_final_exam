#!/usr/bin/env python3
"""bt_models.py — backtest defense-projection models on extracted raid events.

For every historical launch, ask each model "would you have certified this?"
and score against the actual outcome:
  SUCCESS = base died within horizon  -> model should APPROVE (keep the win)
  FAIL    = base alive AND >=half the squad died -> model should REFUSE

Models (defenders fed to main.py's referee-exact simulate_hq_siege):
  M0   radius-1 defenders only (current raid_plan view, no path pins)
  M1   every defender reachable before the fight ends (md <= maxA + SLACK)
  M1a  M1 but far defenders (md>1) only if APPROACHING the target
  M1b  M1 but far defenders only if approaching OR staffing their own building
  M2   M1  + production stream (train_cap/day, gold-capped, arrives via HQ march)
  M2a  M1a + production stream
Usage: python tools/bt_models.py tools/raids_0708.jsonl [more.jsonl ...]
"""
import sys, os, json, importlib.util

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, fn))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

mainmod = _load("mainbot", "main.py")
sim = mainmod.simulate_hq_siege
WHP = {lv: mainmod.HQ_LEVELS[lv].warrior_hp for lv in range(6)}
TRAIN_COST = mainmod.TRAIN_COST
SLACK = 3          # fight-completion slack days after the last attacker lands

def defenders_for(ev, model):
    maxA = max((s["md"] for s in ev["squad"]), default=0)
    cap = maxA + SLACK
    out = []
    for d in ev["defs"]:
        if d["md"] <= 1:
            out.append((d["md"], d["hp"]))
        elif model == "M0":
            continue
        elif d["md"] <= cap:
            if model in ("M1", "M2"):
                out.append((d["md"], d["hp"]))
            elif model in ("M1a", "M2a") and d["approaching"]:
                out.append((d["md"], d["hp"]))
            elif model == "M1b" and (d["approaching"] or d["on_own_bld"]):
                out.append((d["md"], d["hp"]))
    if model in ("M2", "M2a"):
        gold = ev["opp_gold"]
        hqmd = ev["opp_hq_md"]
        hp = WHP.get(ev["opp_hq_level"], 4)
        rate = ev["opp_train_cap"]
        t = 1
        while gold >= TRAIN_COST and t + hqmd <= cap:
            for _ in range(rate):
                if gold < TRAIN_COST:
                    break
                out.append((t + hqmd, hp))
                gold -= TRAIN_COST
            t += 1
    return out

def approve(ev, model):
    atk = [(s["md"], s["hp"]) for s in ev["squad"]]
    if not atk:
        return False
    dfd = defenders_for(ev, model)
    kd = sim(ev["tgt_hp"], ev["tgt_turret"], dfd, atk,
             settle=False, return_kill_day=True)
    return kd is not None

def label(ev):
    o = ev["outcome"]
    if o["base_died_turn"] is not None:
        return "SUCCESS"
    if o["squad_n"] > 0 and o["squad_dead"] * 2 >= o["squad_n"]:
        return "FAIL"
    return "OTHER"

def main():
    evs = []
    for p in sys.argv[1:]:
        evs += [json.loads(l) for l in open(p, encoding="utf-8")]
    evs = [e for e in evs if e["squad"]]
    succ = [e for e in evs if label(e) == "SUCCESS"]
    fail = [e for e in evs if label(e) == "FAIL"]
    print(f"events={len(evs)}  SUCCESS={len(succ)}  FAIL={len(fail)}  "
          f"OTHER={len(evs)-len(succ)-len(fail)}")
    print(f"{'model':6s} {'approve%all':>11s} {'keep%SUCC':>10s} "
          f"{'refuse%FAIL':>12s}  (want: high keep + high refuse)")
    for model in ("M0", "M1", "M1a", "M1b", "M2", "M2a"):
        ap = [approve(e, model) for e in evs]
        ks = [approve(e, model) for e in succ]
        rf = [not approve(e, model) for e in fail]
        print(f"{model:6s} {100*sum(ap)/max(1,len(ap)):>10.0f}% "
              f"{100*sum(ks)/max(1,len(ks)):>9.0f}% "
              f"{100*sum(rf)/max(1,len(rf)):>11.0f}%")

if __name__ == "__main__":
    main()

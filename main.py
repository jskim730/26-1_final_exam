#!/usr/bin/env python3
"""
NYPC 2026 Master — "nation-providing" bot (v1).

v2.25 adds EARLY DENY (0708 user meta-read): during the fixed opening the raid
dispatch runs against a nominated tier — enemy bases within EARLY_RAID_HOPS of
our HQ or on our side of the midline — razing the opponent's FIRST base inside
its ~20-day payback window (L1 = 300g at 15/day). EARLY_RAID_TRAIN extra JIT
bodies are minted while a target stands; every kill is still sim-proven, one
squad at a time, silent under a rush tell or active recalls.

v2.26 adds POST-RAZE CAMP as a DEFAULT-OFF tunable (0708 user thesis:
aggression = the economy gap; the camp holds razed enemy sites so rebuilds
feed a pin). Measured twice against a camp-off twin and NEGATIVE both times
(unconditional 2W2D8L, refeed-certified 3W4D5L): empty sites pay no income,
disciplined opponents avoid them, and the re-raid loop already punishes
rebuilds cheaper. Shipped behavior = v2.25; the code stays for CEM/profiles.

v2.27 adds LAST STAND (from the 0708_10 ladder pool, 12W/2D/6L 65%: five of
six losses died the same death — serial raze -> zero bases -> the ARMY-PARITY
floor's solvency caps read 0 with gold banked -> 40-73 turns of no trains ->
executed). With the economy DEAD (n_bases<=1, raze recent) the parity floor
ignores feedable/upkeep caps and trains bank-funded down to the 300g reboot
reserve. Mirror-neutral (control 0W/10D/2L == treatment), panel 36/36.

v2.28 adds the MID-RAZE HOLD (a stationary body on a live enemy BASE holds
until it falls — the opening expand loop stole a whole deny squad off a 4hp
base; combat is positional, so re-tasking is the only way a siege stops) and
the opening partial-squad budget guard. The starting-squad deny experiment
(fill the squad from held workers) was REVERTED: probe pace fixed (T34->T15)
but A/B 2W/0D/10L + broken panel — the opening workforce is untouchable.
Spares-only EARLY DENY re-measured with corrected twins: 62% vs 42% control.

v2.30 adds BASE DEFENSE CONVERGENCE as a DEFAULT-OFF tunable (BASE_DEF_*):
sim-sized minimal reinforcement of a threatened own base, raid-sized threats
only (waves/rushes/recalls stay the HQ solve's — an ungated first cut lost
spar_rush 2W4L by scattering the defence). ON it turns main.py into
spar_defender (`python main.py spar_defender.json`) — and it BEAT the
default bot 8:3/8:2 in mirrors while holding the panel (rush 75%, others
100%): the strongest candidate default found so far.

v2.31 FLIPS BASE_DEF_CONVERGE ON as the default. The residual spar_rush
hole (its kill-waves are exactly RAID_SQUAD=6 bodies) was sealed by the
DETACHMENT TEST (a threat counting more than half their army is a wave, not
a raid — proportional, not absolute) + a mass_signal veto: spar_rush back
to 6-0 both radii. Flip gates all passed: mirror vs converge-off 79%
(9W1D2L), vs v2.25 79% (8W3D1L vs the old default's 75%/3L), panel 36/36,
16ms. spar_defender.json (R=2) stays the calibrated 42% discriminator;
v231_twin_full.json = the off-switch for future A/Bs.

v2.36 adds the DEFENSIVE HQ UPGRADE (user's economical-defense doctrine +
rule discovery: a LEVEL-UP fully refills building HP — apply_upgrades sets
hp = new max — and upgrades resolve FIRST in the day pipeline, so a level
bought before the wave enters the zone is a same-day full heal + turret +
spawn buff). The survival solve, on a provably-LOST current-level stand,
now evaluates the upgraded stand (full new hp/turret/spawn, stream re-
funded from bank minus cost) and buys the level when THAT holds — survival
outranks every freeze/reserve. Mirror A/B 0W/11D/1L (neutral), panel 36/36,
fatal maps 2W; fires rarely vs our spar bots (they either lose to us or
break us economically first — the broke class is LAST STAND/PIVOT's job),
kept ON as a certified zero-cost safety net for banked wave-defense.

v2.35 adds FORWARD STAGING (user observation: surplus always idled AT the
HQ — the v1 "garrison by default" fallback — while the raid backtest shows
distance is the death cause). When home is safe by proof (no recalls + the
closest enemy's HQ-ETA exceeds the surplus' return march + slack), leftover
surplus waits at the forwardmost own base: nearest-first selection turns far
launches into short ones, and the pool sits on an own building (slots,
turret, converge cover, re-taskable). Measured: zero harm anywhere (mirror
1W/10D/1L, panel 42/42, fatal maps win) but also no gain vs the converge
defender (42% = baseline — convergence reacts fast enough either way);
shipped ON as a provably-safe posture fix for the slower opponents the
discriminators can't represent (seed-42 boom: TL win -> HQ kill).

v2.34 adds SMALL-MAP HOVER WATCH as a DEFAULT-OFF tunable (user game-theory
proposal: watch first, pounce on their first base with the starting bodies —
which are LEGAL spares under the workforce law since they never committed).
Mechanism works end-to-end (probe raze launch T34->T7 after fixing a CORE-
block clobber of the hover target list + net-gate/bump interactions), BUT
vs the hover-off twin it went 0W/8D/4L: both sides carry v2.31 converge, and
sim-certified convergence makes first-base sniping unprofitable — the same
discovery that had us flip converge ON now defends us against the meta this
was meant to copy. Rush window + fatal-map regressions confirmed the seal.
Kept for style-profile use vs certified-naive opponents. The CORE-clobber
fix ships (behavior-neutral with hover off).

v2.33 adds the CONDITIONAL OPENING (user direction: the unconditional fixed
opening is the root exposure): claim OPENING_CORE=2 nearest strongholds
unconditionally, then further opening claims wait for the SAFE certification
(they built >=2 bases too, or army parity from OPENING_PROFILE_TURN;
latched). Sweep: CORE=2 vs off = 12/12 mirror DRAWS (a fellow boomer
certifies instantly — zero-cost insurance) while CORE=1 was 6W1D5L noise ->
2 chosen. Panel 42/42; fatal maps still win; and the shrunk opening frees
spares early enough that EARLY DENY finally assembles fast (probe raze
launch T34 -> T18) — the punish-wave the user asked for, without touching
the workforce (the 2W0D10L law stands).

v2.32 adds the ARMY-BOT PROFILE PIVOT (0708_15 pool, v2.30, rank 77->177 at
58%: 7/8 losses were HQ kills T71-185 by L1-L2 army bots on <=5-base
economies — the final-day meta — while OUR HQ never left L1: the fixed
opening kept buying 300g claims that fed the razers, and post-strangle the
L2 fund is unreachable, ~37 days of net income). Their TRAIN record makes
the profile readable by T30-40: army >= ours+1 on <=3 bases = gold->soldiers
=> STOP claiming (shrink targets to committed), start the L2/L3 fund while
income still exists, let PRESS/converge fight with the bank. Fatal-map
replays: pivot @T40-41, tech ladder restored (L2@T73/L3@T108 where the real
loss stayed L1 forever), both maps flip to wins vs spar_army (new sparring
bot: mass-discipline + poverty-lock finish). Mirror A/B 12/12 DRAWS (strict
army-advantage gate = never fires at parity), panel 42/42 incl. spar_army.
Raid-metric vindication from the same pool: v2.27-29 changes IMPROVED real
play (raze 26->35%, casualty 55->32%).

v2.29, from the raid BACKTEST (tools/extract_raids.py + bt_models.py, 141
real 0708_10 launches: 37 razed / 78 squad-died): launch-time defense
projection is measurably blind (counting reachable/producible defenders
vetoes all-or-nothing; "approaching-only" weighting sees nobody because
reactions start AFTER launch), and every launch-restriction variant (ETA cap
always-on 25%, loose tuition 38%, tight tuition draws boom games) LOST to
its off-twin — failed squads still buy campaign value. Kept OFF as tunables
(RAID_ETA_CAP=0 + rfl tuition telemetry). RULE DISCOVERY: MOVE on a MOVING
warrior = WA (testing-tool:910) — mid-march recall is illegal, commitment is
referee law. Shipped: legal RAID_ABORT — ARRIVED un-pinned survivors on a
target the re-plan can't certify release their hold and walk home (A/B 50%
vs 42% control, panel 36/36).

v1 strategy = "out-turtle the turtles", learned from losing to the sample AIs:
the strong samples build 6-10 bases, upgrade their HQ ~4x, mass 60-100 warriors,
then send one overwhelming wave. v0 built 1 base, never upgraded HQ, dribbled
warriors into turrets, and got one-shot (or lost the HQ-HP tiebreak).

v1 therefore:
  * expands onto EVERY safe stronghold (uncapped economy),
  * upgrades the HQ to max (HP wins the tiebreak; also work/train/turret),
  * trains only while income covers upkeep (never starves),
  * keeps the whole army home as a defensive garrison by default,
  * counter-attacks the enemy HQ only when we have an overwhelming edge
    (e.g. after their wave has spent itself on our defense).

v2 adds ECONOMICAL DEFENCE (SECTION 5, simulate_hq_siege / plan_hq_defense):
on an incoming attack we forward-simulate the HQ siege (referee-exact:
siege = max(0, attackers - sum defender HP); turret adds attacks not HP;
same-day trains defend) and recall ONLY the nearest workers (+ a small margin)
and train ONLY the bodies actually needed to survive — instead of the old
"enemy_in_half >= TRIGGER -> recall EVERYONE" heuristic that stalled the economy
whenever the opponent merely parked a probe nearby. S.opp_gold is tracked as an
upper-bound estimate of the enemy economy (read_turn_result) for future use.

v3 uses a FIXED ECONOMIC OPENING (deterministic until HQ L2): claim EVERY nearest
sub-half stronghold first with a just-in-time worker economy (no standing
garrison, workers minted only as bases commit), then raise the HQ to L2; the only
opening defence is training/recall when an enemy actually reaches the HQ region
(trigger_hops=1). It then runs a PHASED post-opening macro (HQ->L3 safety -> bases->L2 income ->
HQ->L5 win-con -> bases->L3 surplus) and a VERIFIED OPPORTUNISTIC ALL-IN
(assess_attack): reusing simulate_hq_siege SYMMETRICALLY as a lethality calc, we
launch the surplus army at the enemy HQ only when a RACE (our_kill_day + margin <
their worst-case counter-kill_day) says we destroy it first — surplus-only (the
home defence is never detached), massed, corridor-clear, hysteresis-gated. It
fires only on a genuine opening (broke/exposed/chipped enemy); a from-HQ all-in
cannot break a solvent turtle (enemy out-builds during the march) — that needs
forward-staging. Pathing.march_days gives the exact referee ETA the race needs.

v2.1 (from replaying the 0701 real-ladder logs with replay_log.py — 8W/5D/7L):
  * TECH-GATE SAFETY VALVES: enemy-squatted targets no longer hold HQ tech
    hostage + hard TECH_GATE_DEADLINE (ladder (19): finished HQ L1 with 8,203
    unspent gold because one contested target kept the gate shut 200 days).
  * TECH-URGENT priority: under pressure (enemy in our half) or from
    TECH_URGENT_TURN, HQ L4/L5 outranks base spending and a tech_reserve
    protects the 2400/3600 savings (stall losses (5),(10),(22),g8: L3-20hp vs
    L4/L5 at turn 200 while our gold went to base rebuilds + army matching).
  * needs_stream: if the defence sim proved survival only WITH the sustained
    training stream, EXECUTE that stream now (g5: died holding 9,645 gold while
    every turn's plan said "safe, given we train from tomorrow").
  * OPENING RUSH DETECTOR: enemies in our half before RUSH_WINDOW freeze base
    spending and widen the defence trigger (ladder (15): dead on day 10 to a
    6-body rush while paying for a 2nd base).
  * hot_regions: never build/upgrade a base an enemy stands on or beside
    ((22): 6,600g of rebuilt bases fed straight into a harasser).
  * ENDGAME HEAL + BLOCKER SQUAD: always repair a chipped max HQ from
    HEAL_FINAL_TURN, and park BLOCK_SQUAD surplus bodies in the enemy HQ region
    from BLOCK_START — their presence makes the enemy's UPGRADE (tech AND heal)
    illegal and overkill chips the tiebreak (5 of 20 games were 30-30 draws).

Structure unchanged from v0 (SECTION 5 = the only problem-specific brain):
  1 RULE CONSTANTS  2 DATA MODEL  3 PROTOCOL I/O  4 PATHING  5 STRATEGY  6 MAIN

Never emit an invalid command (WA), never exceed the time budget (TLE), always
exit cleanly on FINISH. Every command is validity- and gold-checked.
"""
from __future__ import annotations

import os
import sys
import json
import math
import heapq
from collections import deque

_DEBUG = bool(os.environ.get("NYPC_DEBUG"))
from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple, Optional

# ============================================================================
# SECTION 1 — RULE CONSTANTS  (update these if the Final Round changes numbers)
# ============================================================================
MAX_TURN = 200
START_GOLD = 500
START_WARRIORS = 3
MOVE_COST = 10
TRAIN_COST = 120
WORK_INCOME = 15
UPKEEP_PER_WARRIOR = 2
HQ_MAX_LEVEL = 5
BASE_MAX_LEVEL = 3
HQ_HEAL_COST = 1000
BASE_HEAL_COST = 500


class HqLevelEntry(NamedTuple):
    upgrade_cost: int
    warrior_hp: int
    hp: int
    turret: int
    train_cap: int
    work_cap: int


class BaseLevelEntry(NamedTuple):
    cost: int
    hp: int
    turret: int
    work_cap: int


HQ_LEVELS: tuple[HqLevelEntry, ...] = (
    HqLevelEntry(0,     0, 0,  0, 0, 0),
    HqLevelEntry(0,     4, 10, 1, 1, 1),
    HqLevelEntry(600,   5, 15, 2, 1, 2),
    HqLevelEntry(1200,  6, 20, 2, 2, 3),
    HqLevelEntry(2400,  7, 25, 3, 2, 4),
    HqLevelEntry(3600,  8, 30, 3, 3, 5),
)
BASE_LEVELS: tuple[BaseLevelEntry, ...] = (
    BaseLevelEntry(0,    0,  0, 0),
    BaseLevelEntry(300,  6,  1, 1),
    BaseLevelEntry(600,  12, 1, 2),
    BaseLevelEntry(1000, 18, 2, 3),
)


# ============================================================================
# SECTION 2 — DATA MODEL
# ============================================================================
class Side(Enum):
    LEFT = "A"
    RIGHT = "B"

    @property
    def opposite(self) -> "Side":
        return Side.RIGHT if self is Side.LEFT else Side.LEFT

    @classmethod
    def from_word(cls, w: str) -> "Side":
        return cls.LEFT if w == "LEFT" else cls.RIGHT

    @classmethod
    def from_char(cls, c: str) -> "Side":
        return cls.LEFT if c == "A" else cls.RIGHT


class BType(Enum):
    HQ = "HQ"
    BASE = "BASE"


class WState(Enum):
    STATIONARY = 0
    MOVING = 1


@dataclass(frozen=True)
class WarriorId:
    side: Side
    num: int

    def __str__(self) -> str:
        return f"{self.side.value}{self.num}"

    @classmethod
    def parse(cls, tok: str) -> "WarriorId":
        return cls(Side.from_char(tok[0]), int(tok[1:]))


@dataclass
class Warrior:
    id: WarriorId
    region: int
    hp: int
    state: WState = WState.STATIONARY
    target: int = 0


@dataclass
class Building:
    region: int
    side: Side
    type: BType
    level: int = 1
    hp: int = 10

    def current_hp(self) -> int:
        return HQ_LEVELS[self.level].hp if self.type is BType.HQ else BASE_LEVELS[self.level].hp

    def work_cap(self) -> int:
        return HQ_LEVELS[self.level].work_cap if self.type is BType.HQ else BASE_LEVELS[self.level].work_cap

    def turret(self) -> int:
        return HQ_LEVELS[self.level].turret if self.type is BType.HQ else BASE_LEVELS[self.level].turret

    def max_level(self) -> int:
        return HQ_MAX_LEVEL if self.type is BType.HQ else BASE_MAX_LEVEL

    def apply_upgrade(self) -> None:
        self.level += 1
        self.hp = self.current_hp()

    def upgrade_cost(self) -> int:
        if self.type is BType.HQ:
            return HQ_LEVELS[self.level + 1].upgrade_cost
        return BASE_LEVELS[self.level + 1].cost

    def heal_cost(self) -> int:
        return HQ_HEAL_COST if self.type is BType.HQ else BASE_HEAL_COST


@dataclass
class GameMap:
    N: int = 0
    K: int = 0
    x: list[int] = field(default_factory=list)
    y: list[int] = field(default_factory=list)
    strongholds: list[int] = field(default_factory=list)
    adj: list[list[int]] = field(default_factory=list)
    my_side: Side = Side.LEFT
    my_hq: int = 0
    opp_hq: int = 0

    def hq_of(self, s: Side) -> int:
        return 0 if s is Side.LEFT else self.N - 1


@dataclass
class GameState:
    gold: int = START_GOLD
    opp_gold: int = START_GOLD          # UPPER-BOUND estimate of the enemy's gold
    opp_income: int = 0                 # enemy work income last turn (exact, observed)
    attack_streak: int = 0              # consecutive turns the attack race said "commit"
    my_countdown: int = 5
    opp_countdown: int = 5
    warriors: list[Warrior] = field(default_factory=list)
    buildings: list[Building] = field(default_factory=list)
    razed_count: dict = field(default_factory=dict)   # region -> times one of OUR
                                        # buildings was sieged to death there (a
                                        # region with history is a strangle site:
                                        # rebuilding it needs proof of control)

    def find_building(self, region: int) -> Optional[Building]:
        return next((b for b in self.buildings if b.region == region), None)

    def find_warrior(self, wid: WarriorId) -> Optional[Warrior]:
        return next((w for w in self.warriors if w.id == wid), None)


@dataclass
class Actions:
    train_n: int = 0
    moves: list[tuple[WarriorId, int]] = field(default_factory=list)
    upgrades: list[int] = field(default_factory=list)


def make_base(region: int, s: Side) -> Building:
    return Building(region, s, BType.BASE, 1, BASE_LEVELS[1].hp)


# ============================================================================
# SECTION 3 — PROTOCOL I/O
# ============================================================================
def readln() -> str:
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return line.rstrip("\n")


def read_tokens() -> list[str]:
    return readln().split()


def parse_init() -> tuple[GameMap, GameState]:
    M = GameMap()

    t = read_tokens()
    assert t and t[0] == "READY"
    M.my_side = Side.from_word(t[1])

    t = read_tokens()
    M.N, M.K = int(t[0]), int(t[1])
    M.x = [int(v) for v in read_tokens()]
    M.y = [int(v) for v in read_tokens()]
    M.strongholds = sorted(int(v) for v in read_tokens())

    M.adj = [[] for _ in range(M.N)]
    for r in range(M.N):
        t = read_tokens()
        deg = int(t[0])
        M.adj[r] = sorted(int(v) for v in t[1:1 + deg])

    M.my_hq = M.hq_of(M.my_side)
    M.opp_hq = M.hq_of(M.my_side.opposite)

    S = GameState()
    opp = M.my_side.opposite
    for sfx in range(1, START_WARRIORS + 1):
        S.warriors.append(Warrior(WarriorId(M.my_side, sfx), M.my_hq, HQ_LEVELS[1].warrior_hp))
        S.warriors.append(Warrior(WarriorId(opp, sfx), M.opp_hq, HQ_LEVELS[1].warrior_hp))
    S.buildings.append(Building(0, Side.LEFT, BType.HQ, 1, HQ_LEVELS[1].hp))
    S.buildings.append(Building(M.N - 1, Side.RIGHT, BType.HQ, 1, HQ_LEVELS[1].hp))

    print("OK", flush=True)
    return M, S


def read_turn_start() -> Optional[int]:
    line = readln()
    if line == "FINISH":
        return None
    t = line.split()
    assert t and t[0] == "START"
    return int(t[2])


def read_turn_result(S: GameState, M: GameMap, submitted: Actions) -> None:
    # --- replay the costs/effects of our own submission (keeps gold in sync) ---
    for region in submitted.upgrades:
        b = S.find_building(region)
        if b is None:
            S.gold -= BASE_LEVELS[1].cost
            S.buildings.append(make_base(region, M.my_side))
        elif b.level >= b.max_level():
            S.gold -= b.heal_cost()
            b.hp = b.current_hp()
        else:
            S.gold -= b.upgrade_cost()
            b.apply_upgrade()

    for wid, target in submitted.moves:
        b = S.find_building(target)
        cost = 0 if (b is not None and b.side is M.my_side) else MOVE_COST
        S.gold -= cost
        w = S.find_warrior(wid)
        if w is not None:
            w.state = WState.MOVING
            w.target = target

    S.gold -= TRAIN_COST * submitted.train_n

    line = readln()
    if line == "FINISH":
        sys.exit(0)
    t = line.split()
    assert t and t[0] == "TURN"

    t = read_tokens()                       # TIME T_x R_x T_y R_y
    S.my_countdown = int(t[2])
    S.opp_countdown = int(t[4])

    # UPGRADE
    n = int(read_tokens()[1])
    for _ in range(n):
        r = read_tokens()
        s = Side.from_char(r[0][0])
        region = int(r[1])
        b = S.find_building(region)
        if b is None:
            if s is not M.my_side:                       # enemy built a new base
                S.opp_gold -= BASE_LEVELS[1].cost
            S.buildings.append(make_base(region, s))
        elif b.side is not M.my_side:
            if b.level >= b.max_level():
                S.opp_gold -= b.heal_cost()
                b.hp = b.current_hp()
            else:
                S.opp_gold -= b.upgrade_cost()           # cost read before the level rises
                b.apply_upgrade()

    # TRAIN
    n = int(read_tokens()[1])
    if n > 0:
        ids = read_tokens()
        for i in range(n):
            wid = WarriorId.parse(ids[i])
            hq_region = M.hq_of(wid.side)
            hq_b = S.find_building(hq_region)
            hq_level = hq_b.level if hq_b is not None else 1
            S.warriors.append(Warrior(wid, hq_region, HQ_LEVELS[hq_level].warrior_hp))
            if wid.side is not M.my_side:                 # enemy paid to train
                S.opp_gold -= TRAIN_COST

    # MOVE
    n = int(read_tokens()[1])
    opp_movers: set = set()
    for _ in range(n):
        r = read_tokens()
        wid = WarriorId.parse(r[0])
        region = int(r[1])
        w = S.find_warrior(wid)
        if w is not None:
            w.region = region
            if wid.side is M.my_side and w.state is WState.MOVING and w.region == w.target:
                w.state = WState.STATIONARY
            elif wid.side is not M.my_side:
                opp_movers.add(wid)
                # a warrior that was NOT moving last turn just received a move
                # ORDER; unless its first step lands on the enemy's own
                # building (a free staffing hop), that order cost MOVE_COST.
                # Without this, S.opp_gold drifts high by 10g per raid order
                # and the tech-race detector overestimates their tech speed
                # (0703 sample 8: their projected L5 ~T158, actual = never).
                if wid not in getattr(S, "opp_moving", set()):
                    b = S.find_building(region)
                    if b is None or b.side is M.my_side:
                        S.opp_gold = max(0, S.opp_gold - MOVE_COST)
    S.opp_moving = opp_movers

    # DAMAGE
    n = int(read_tokens()[1])
    for _ in range(n):
        r = read_tokens()
        wid = WarriorId.parse(r[1])
        w = S.find_warrior(wid)
        if w is not None:
            w.hp -= int(r[2])
    S.warriors = [w for w in S.warriors if w.hp > 0]

    # SIEGE
    n = int(read_tokens()[1])
    for _ in range(n):
        r = read_tokens()
        region = int(r[1])
        b = S.find_building(region)
        if b is not None:
            b.hp -= int(r[2])
            if b.hp <= 0 and b.side is M.my_side:
                S.razed_count[region] = S.razed_count.get(region, 0) + 1
                S.last_raze_turn = getattr(S, "my_turn_now", 0)
    S.buildings = [b for b in S.buildings if b.hp > 0]

    readln()  # END

    # --- evening: work income then upkeep (mirrors the referee) ---
    income = 0
    opp_income = 0
    for b in S.buildings:
        count = sum(1 for w in S.warriors if w.id.side is b.side and w.region == b.region)
        earn = WORK_INCOME * min(count, b.work_cap())
        if b.side is M.my_side:
            income += earn
        else:
            opp_income += earn
    S.gold += income

    alive = sum(1 for w in S.warriors if w.id.side is M.my_side)
    S.gold = max(0, S.gold - UPKEEP_PER_WARRIOR * alive)

    # enemy gold estimate: income − upkeep (move costs ignored → biased HIGH, so
    # our worst-case defense never *under*-estimates the force they can field).
    opp_alive = sum(1 for w in S.warriors if w.id.side is not M.my_side)
    S.opp_gold = max(0, S.opp_gold + opp_income - UPKEEP_PER_WARRIOR * opp_alive)
    S.opp_income = opp_income     # exact observed enemy income (bounds their reinforcement)


def emit(a: Actions) -> None:
    out: list[str] = ["COMMAND"]
    for wid, target in a.moves:
        out.append(f"MOVE {wid} {target}")
    for r in a.upgrades:
        out.append(f"UPGRADE {r}")
    if a.train_n > 0:
        out.append(f"TRAIN {a.train_n}")
    out.append("END")
    sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()


# ============================================================================
# SECTION 4 — PATHING  (cached Dijkstra + BFS hops; matches referee movement)
# ============================================================================
class Pathing:
    def __init__(self, M: GameMap):
        self.M = M
        self._cache: dict[int, list[int]] = {}
        self._md_cache: dict[tuple[int, int], int] = {}
        self._mp_cache: dict[tuple[int, int], list[int]] = {}
        self.dist_my: list[int] = self.dist_from(M.my_hq)
        self.dist_opp: list[int] = self.dist_from(M.opp_hq)
        self.hops_my: list[int] = self._bfs_hops(M.my_hq)
        self.hops_opp: list[int] = self._bfs_hops(M.opp_hq)

    def edge_weight(self, u: int, v: int) -> int:
        M = self.M
        return math.ceil(math.hypot(M.x[u] - M.x[v], M.y[u] - M.y[v]))

    UNREACH = 1 << 20

    def march_days(self, src: int, target: int) -> int:
        """EXACT number of days (= zones stepped) for a warrior at `src` to reach
        `target`, replicating the referee's greedy weighted walk (testing-tool.py
        apply_day_movement): each day step to the adjacent v minimising
        edge_weight(cur,v)+dist_to_target[v], ties by smallest id (M.adj is
        pre-sorted ascending, strict <). This is the true ETA; the BFS hops_*
        UNDER-estimate it by up to several days, which would make an attack race
        dangerously optimistic. Cached per (src,target)."""
        key = (src, target)
        c = self._md_cache.get(key)
        if c is not None:
            return c
        if src == target:
            self._md_cache[key] = 0
            return 0
        dist = self.dist_from(target)
        if dist[src] < 0:
            self._md_cache[key] = self.UNREACH
            return self.UNREACH
        cur, days = src, 0
        cap = self.M.N + 1
        while cur != target and days <= cap:
            best_v, best_score = -1, -1
            for v in self.M.adj[cur]:
                if dist[v] < 0:
                    continue
                score = self.edge_weight(cur, v) + dist[v]
                if best_score < 0 or score < best_score:
                    best_score, best_v = score, v
            if best_v < 0:
                days = self.UNREACH
                break
            cur, days = best_v, days + 1
        self._md_cache[key] = days
        return days

    def march_path(self, src: int, target: int) -> list[int]:
        """The exact zones a warrior steps through marching src->target (same
        greedy walk as march_days): path[i] is where it stands after day i+1,
        so path[-1] == target. Empty when src == target or unreachable."""
        key = (src, target)
        c = self._mp_cache.get(key)
        if c is not None:
            return c
        path: list[int] = []
        if src != target:
            dist = self.dist_from(target)
            if dist[src] >= 0:
                cur = src
                cap = self.M.N + 1
                while cur != target and len(path) <= cap:
                    best_v, best_score = -1, -1
                    for v in self.M.adj[cur]:
                        if dist[v] < 0:
                            continue
                        score = self.edge_weight(cur, v) + dist[v]
                        if best_score < 0 or score < best_score:
                            best_score, best_v = score, v
                    if best_v < 0:
                        path = []
                        break
                    cur = best_v
                    path.append(cur)
        self._mp_cache[key] = path
        return path

    def dist_from(self, target: int) -> list[int]:
        """Shortest-path cost from every region to `target` (-1 if unreachable)."""
        cached = self._cache.get(target)
        if cached is not None:
            return cached
        M = self.M
        dist = [-1] * M.N
        dist[target] = 0
        heap = [(0, target)]
        while heap:
            du, u = heapq.heappop(heap)
            if du != dist[u]:
                continue
            for v in M.adj[u]:
                dv = du + self.edge_weight(u, v)
                if dist[v] < 0 or dv < dist[v]:
                    dist[v] = dv
                    heapq.heappush(heap, (dv, v))
        self._cache[target] = dist
        return dist

    def _bfs_hops(self, target: int) -> list[int]:
        """Unweighted hop distance from every region to `target` (-1 if unreachable)."""
        M = self.M
        hops = [-1] * M.N
        hops[target] = 0
        q = deque([target])
        while q:
            u = q.popleft()
            for v in M.adj[u]:
                if hops[v] < 0:
                    hops[v] = hops[u] + 1
                    q.append(v)
        return hops


# ============================================================================
# SECTION 5 — STRATEGY   (*** rewrite this section for a new problem ***)
# ============================================================================
HQ_TARGET_LEVEL        = 5      # max the HQ (HP wins the tiebreak; +work/train/turret)
HQ_DEFENSIVE_LEVEL     = 3      # rush the HQ to this early (hp20, turret2, train_cap2)
BASE_ECON_LEVEL        = 2      # income phase: bring EVERY base to this first (L2 = 600g
                               # for +15/day; L2->L3 costs 1000 for the same +15, so it waits)
BASE_TARGET_LEVEL      = 3      # DEPRECATED/unused: base L2->L3 (1000g for the same
                               # +15/day as L1->L2) is too low-payback to be worth it;
                               # bases now cap at BASE_ECON_LEVEL and surplus -> army
MIN_BASES_BEFORE_HQ    = 2      # lay a couple cheap bases before pouring gold into HQ
BASE_FRACTION          = 0.5    # claim round(total_strongholds * this) nearest strongholds
MAX_BASES              = 12     # high hard-cap on claimed strongholds (base_target binds first)
DEFENSE_TRIGGER        = 4      # an enemy force this big in our half triggers recall
MAX_CONCURRENT_BUILDERS = 2     # builders walking to new strongholds at once
THREAT_HOPS            = 5      # enemy this close to our HQ -> defensive posture
MIN_GARRISON           = 3      # always hold at least this many warriors at the HQ
GARRISON_BUFFER        = 2      # extra defenders beyond the enemy force in our half
TRAIN_NET_MARGIN       = 2      # only train while (income - upkeep) exceeds this
ARMY_BUFFER_MIN        = 0      # no standing army beyond work-slots + local garrison (boom HQ)
ARMY_BUFFER_MAX        = 300    # once economy is saturated, train army freely (net-limited)
ENABLE_ATTACK          = True   # opportunistic all-in: march on the enemy HQ when a
                               # verified race says we destroy it before ours can fall
ATTACK_ARMY_MIN        = 12     # min concentrated wave to even consider committing
ATTACK_RACE_SAFETY     = 3      # our_kill_day must beat their_kill_day by this many
                               # days (STRICT: a same-day mutual HQ kill is a DRAW)
ATTACK_ETA_BUFFER      = 2      # days added to our_kill_day for en-route pin/attrition slop
ATTACK_GOLD_WINDOW     = 12     # days of enemy income folded into their reinforce budget
ATTACK_HYSTERESIS      = 2      # commit must hold this many consecutive turns before we
                               # launch (a launched wave is irreversible; kills 1-turn noise)
ATTACK_RATIO           = 1.25   # (legacy, unused — retained for data.bin compatibility)
ATTACK_TURRET_BUFFER   = 4      # (legacy, unused)
# --- v2.1 fixes from the 0701 real-ladder replay analysis --------------------
TECH_GATE_DEADLINE     = 70     # the bases-done tech gate opens unconditionally at this
                               # turn: a permanently-contested target must never hold HQ
                               # tech hostage (ladder (19): HQ L1 + 8,203 unspent gold)
TECH_URGENT_TURN       = 110    # from here HQ tech outranks base-income spending even in
                               # peace (winners' L5 lands ~130-170; ours must not be later)
BASE_SPEND_CUTOFF      = 150    # no base builds/upgrades after this turn — the 40-day
                               # payback can't recoup before turn 200; gold -> tech/heal
RUSH_WINDOW            = 25     # opening rush detector active until this turn
RUSH_MIN_INCURSION     = 2      # this many enemies in our half inside the window = rush
RUSH_MASS_ARMY         = 5      # mass signal: an enemy army this big with ZERO bases is
                               # buying soldiers, not workers (0702_15: both rush killers
                               # showed it by turn 3-5, 8-13 days before impact) — flag
                               # the rush before anyone crosses the midline
RUSH_PREP_HOPS         = 6      # under a rush flag, engage the survival solve while the
                               # wave is still this many hops out: an L1 HQ trains only
                               # 1 body/day, so the defence stream must start days early
RUSH_COMMIT_BODIES     = 4      # a wave this big in our half = a COMMITTED rush: only
                               # then deep-simulate it to impact (settle=False), freeze
                               # base spending and round the stream up — two pester
                               # loiterers simulated that way phantom-drain the opening
HEAL_FINAL_TURN        = 190    # from here always repair a damaged max-level HQ — the
                               # turn-limit tiebreak is literally current HQ HP
BLOCK_START            = 110    # from here park BLOCK_SQUAD surplus warriors in the enemy
                               # HQ region: their presence makes the enemy's UPGRADE (tech
                               # AND the 1000g heal) illegal, and overkill chips the HP
                               # tiebreak. 13 of the 40 0701-0702 ladder games were
                               # mutual-max draws and the enemy's L5 lands at median ~146
                               # (range 123-196) — blockers must ARRIVE before that, so
                               # launch ~110 (+~10-12 days march)
BLOCK_SQUAD            = 4      # blocker RELAY size: BLOCK_DENIERS inside the enemy
                               # HQ region + the rest staged in an adjacent zone OUT
                               # of turret range, stepping in as deniers die (0 = off)
BLOCK_DENIERS          = 2      # bodies kept INSIDE the enemy HQ region during a deny
                               # window. Upgrade legality is checked every MORNING, so
                               # a 1-day relay gap lets the tech through — 2 in-zone +
                               # daily promotion is gapless at ~1 body/day burn, paid
                               # ONLY while denial matters (see deny windows below)
BLOCK_MAX_INTRUDERS    = 2      # (legacy, unused — retained for data.bin compat:
                               # the intruder veto let 2 loitering enemy raiders cancel
                               # our tech-denial; the defence solve is the safety gate)
CHIP_GUARD_TURN        = 165    # from here the HQ survival solve defends against ANY
                               # siege point, not just destruction (hq_hp=1 in the
                               # sim): the turn-limit tiebreak is current HP, and 0703
                               # v2.5 sample 4 was lost 28-30 to a 2-point chip at
                               # T195 whose heal their squatter made illegal (0=off).
                               # 175 -> 165: weekend (37) lost 29-30 to a single
                               # chip landing T168, before the old guard woke up
TECH_RACE_TURN         = 90     # certified stall detector active from here (0=off)
TECH_RACE_DEADLINE     = 190    # commit to the race only if OUR L5 provably lands by
                               # here (leaves heal margin before the tiebreak count)
TECH_RACE_MARGIN       = 8      # our certified L5 turn must beat their earliest
                               # possible L5 by this many days before we commit
GOLD_DUMP_TURN         = 150    # from here, with the HQ maxed, convert bank above
                               # GOLD_DUMP_BANK into bodies at full train cap — 0703
                               # sample 5 ended a DOMINANT draw with 12,138g unspent
                               # (0 = off)
GOLD_DUMP_BANK         = 1500   # bank floor the dump never spends below (keeps the
                               # 1000g heal + a buffer)
FLOOD_TURN             = 180    # from here every surplus body marches on the enemy HQ:
                               # with a denier squatting their region the heal is
                               # illegal, so any siege overkill = permanent HP chip and
                               # one point decides a 30-30 tiebreak (0 = off)
FLOOD_DOM_EARLY        = 25    # start the flood era this many turns EARLY when
                               # DOMINANT (army >= 2x theirs AND income >= 1.2x):
                               # 7 of 10 weekend mutual-L5 30-30 draws had a
                               # crushing lead that the T180 flood cashed too
                               # late (arrival T190+ vs a healed L5). 0 = off
FLOOD_MASS             = 8     # flood bodies MASS at the staging zone and step in
                               # together once this many gathered (a trickle dies 1-by-1
                               # to same-day defender spawns — L5 trains 24hp/day);
                               # near the turn limit whatever gathered goes anyway
RAID_SQUAD             = 6      # MAX bodies per raider squad (0 = raiding off); the
                               # dispatch sizes each squad to the SMALLEST n<=this the
                               # siege sim proves kills the target (0702_15: enemy
                               # squads of 2-5 razed 296 of our bases vs 0 of theirs;
                               # a naked L1 base dies to 3 bodies in 2 days, a staffed
                               # L2 needs ~5)
RAID_MAX_SQUADS        = 3     # raid this many enemy bases concurrently
RAID_MIN_HQ            = 2     # no raiding below this HQ level (home must be able to
                               # defend itself before we detach surplus cross-map)
RAID_BEFORE_TECH       = 1     # 1 = mint raider bodies even while saving for HQ tech
                               # (costs ~15 days of L5 delay, bets that razing enemy
                               # bases returns more — 0702_15 winners raided AND
                               # teched); 0 = raids only from post-tech surplus
BASE_EVAC_DAYS         = 0     # BASE DEFENCE: >0 evacuates a base's staff when
                               # enemies within this many march-days provably overrun
                               # staff + turret (sim-checked). DEFAULT OFF — A/B twin
                               # tests (radius 4 + guards, radius 2 + guards, evac-only
                               # radius 1) each lost 8/8 to a no-defence twin: staying
                               # staff is a SPEED BUMP (absorbs siege, feeds turret
                               # attrition, delays the raze 2-3 days) worth more than
                               # the 120g/body it costs, and every wider trigger
                               # mis-reads passing traffic as an attack. Kept as a
                               # tunable for style-profiles/CEM to revisit.
RETIRE_HP              = 2     # WOUNDED ROTATION: warriors never heal, but work income
                               # is HP-independent — a body at this hp or less is spent
                               # as a combatant (next tick kills it, it absorbs almost
                               # nothing) yet farms at 100%. Retire it from forward
                               # duty to a rear work slot (free move into own
                               # buildings) unless pinned or the building it's sieging
                               # is about to fall; combat picks fresh-HP bodies first.
                               # 0702_15: 105 enemy wounded recycled this way, 28/37
                               # games — mirror it. 0 = rotation off.
RAID_ETA_CAP           = 0     # max march-days for raid squad members, ARMED
                               # ONLY after this opponent has eaten one of our
                               # squads (S.raid_fails "tuition" tracker). The
                               # 0708_10 backtest (141 real launches, tools/
                               # extract_raids.py + bt_models.py): successes
                               # median 4 march-days vs squad-died failures
                               # median 7 (distance = the defender's reaction
                               # time), and 65/78 failures were REPEATS after
                               # a visible failure. Projecting reachable or
                               # producible defenders instead vetoed all-or-
                               # nothing (reaction is unobservable at launch),
                               # and an ALWAYS-ON cap lost 0W/6D/6L to the
                               # uncapped twin + dropped spar_boom to 3W3D
                               # (long raids PAY vs non-defenders). Tuition-
                               # armed cap 6 = backtest keep 35%/refuse 64%
                               # BUT even that drew a boom game the uncapped
                               # bot wins (seed 42): failed squads still buy
                               # CAMPAIGN value (defense/rebuild spend, staff
                               # kills, hp chip) the per-event labels miss.
                               # DEFAULT OFF; the rfl tuition telemetry stays
                               # live for 본선/CEM. Losses are cut mid-flight
                               # instead — see RAID_ABORT. 0 = off
RAID_DEF_RADIUS        = 1     # enemy bodies within this many march-days of a raid
                               # target count as its defenders in the raze check.
                               # Combat only happens in the SAME zone, and 0702_15
                               # showed staffed neighbours do NOT converge to defend
                               # a raided base — radius>1 assumes a coordinated
                               # defence no opponent actually played and vetoes
                               # every raid; the per-turn re-plan catches real
                               # convergence if it ever happens
# --- v2.25 EARLY DENY (0708 user meta-read: top-tier bots hold their own first
# base back, hover, and raze the opponent's FIRST base before it pays for
# itself — an L1 base is 300g at 15/day income = a ~20-day payback window, so
# a raze inside it is a pure economic win before even counting the rebuild
# tempo and the dead claimer. EVERY raid gate here was `not opening`, so for
# the whole fixed opening — exactly the window where this decides games — we
# never attacked at all.) ------------------------------------------------------
EARLY_RAID_HOPS        = 6     # opening raid tier: enemy bases within this many
                               # hops of our HQ, plus every base on our side of
                               # the midline (hops_my <= hops_opp), become raid
                               # targets DURING the opening — one squad at a
                               # time, same sim-proven-kill sizing as the normal
                               # module. Deep bases in their half stay excluded:
                               # the march there costs more opening income than
                               # the 300g it denies. 0 = layer off
EARLY_RAID_TRAIN       = 3    # extra JIT bodies minted while an early deny
                               # target exists — the opening otherwise trains
                               # exactly its worker count, so the dispatch would
                               # see 0-2 spares and the kill sim would refuse
                               # almost every raid ("a naked L1 dies to 3 bodies
                               # in 2 days"). Not wasted on a no-go: they fall
                               # through to workers/garrison. 0 = spares only
EARLY_RAID_BANK        = 150  # (dormant while the v2.28 starting-squad tier
                               # stays reverted): bank floor a WORKER-stripping
                               # deny squad would need — kept for data.bin
                               # compat and a possible 본선 hover-opening
# --- v2.26 POST-RAZE CAMP (0708 user thesis: opening/mid-game aggression is
# how the ECONOMY gap is made. A raze denies 300g once; walking home hands the
# site back for another 300g. The 0704-0706 top tier camped OUR raze sites and
# farmed our rebuilds over and over — mirror it: the raid squad that took a
# base HOLDS the empty site, so a rebuilder walking in is pinned and killed
# and the site's income stream stays dead.) ------------------------------------
CAMP_TURNS             = 0     # POST-RAZE CAMP: hold a razed enemy base site
                               # this many days (up to CAMP_BODIES per site,
                               # refeed-certified: engages only after the
                               # enemy was observed rebuilding a razed site).
                               # DEFAULT OFF — 0708 A/B twin tests: the
                               # unconditional camp lost 2W2D8L and the
                               # refeed-gated variant 3W4D5L to a camp-off
                               # twin. An empty site pays US nothing (no
                               # building = no work income: 2 bodies x 12
                               # days = 360g foregone vs a 300g rebuild), a
                               # disciplined opponent (REBUILD_GUARD logic)
                               # avoids camped sites, and the refeed signal
                               # can't tell "feeds a pin" from "rebuilds a
                               # site the expired camp left empty". Rebuilds
                               # are already punished cheaper by the re-raid
                               # loop (a rebuilt base = a fresh sim-certified
                               # raid target). Kept as a tunable for style
                               # profiles/CEM to revisit.
CAMP_BODIES            = 2    # bodies held per site (2 matches our own
                               # escorted-rebuild protocol, so a mirrored
                               # builder+guard pair is met, pinned and beaten;
                               # the rest of the squad flows to the next raid)
# --- v2.7 TERRITORY DEFENCE pack, from the 0704-0706 weekend ladder pool -----
# (111 high-rated games, 42W/24D/45L: the DOMINANT loss class — 26 of 45 — was
# "eco-strangle": stationary enemy stacks rotate through our half razing bases
# serially while our army sits home; our income dies, the HQ never techs, and
# we fall late. 11 more losses were the milder boom+poke variant of the same.)
OPENING_MAX_TURN       = 55    # the fixed opening also ENDS BY TIME: `opening`
                               # was `hq.level < 2`, and a strangled economy that
                               # can never afford L2 stayed in the opening posture
                               # (JIT worker cap ~6 bodies, garrison 0) for the
                               # whole game — weekend game (10) trained 2 warriors
                               # in 110 days while a 9-body stack razed everything
REBUILD_GUARD_HOPS     = 2     # regions within this many hops of a SQUATTER (a
                               # stationary enemy in our half) are frozen for base
                               # builds/upgrades — the strangle victims fed 300g
                               # rebuilds into the same raiders over and over
                               # (weekend (10): base62 razed twice; (34): 1500g of
                               # rebuilds, 0 tech, income 22/day). 0 = off
PRESS_MIN              = 2     # PRESSURE-MATCH training: this many squatters in
                               # our half = a territorial war; train bodies (bank-
                               # funded, past the net-income gate that a strangled
                               # economy can never pass) until our headcount covers
                               # work slots + garrison + one per squatter. 0 = off
CLEAR_SQUAD            = 8     # INTERCEPT/CLEAR squads: max bodies per squad sent
                               # to kill a squatter group in our half; the dispatch
                               # sizes each squad to the smallest n the referee-
                               # exact combat sim proves WINS the zone fight (their
                               # converging friends priced in). The raid module
                               # pointed inward — 0704-0706 razed-base siege was
                               # 3899 taken with our army idle at home. 0 = off
CLEAR_MAX_SQUADS       = 2     # concurrent intercept squads
CLEAR_DEF_RADIUS       = 1     # enemy bodies within this many march-days of an
                               # intercept target count as defenders in its sim
                               # (same reasoning as RAID_DEF_RADIUS)
# --- counters to the top-tier "wave -> raze -> wounded claim the midline" plan
# (log-verified 0704-0706: 45 of 77 sampled enemy builds were MID/our-half,
# many by lone hp1-4 bodies claiming one stronghold at a time while their main
# force strangled us; their own half sat empty — up to 21 bodies in ours) -----
MID_CLAIM_HUNT         = 1     # include lone claimers squatting MID (equal-hops)
                               # neutral strongholds in the intercept target set —
                               # a fresh spawn kills an isolated hp1-4 claimer 1v1
                               # (sim-proven), erasing the claim AND a veteran. 0=off
RAID_MIN_HQ_INVASIVE   = 1     # enemy bases in OUR half / on the midline are
                               # raided from this HQ level (the normal RAID_MIN_HQ=3
                               # gate is for cross-map detachment; reclaiming our
                               # own territory is home defence — also exempt from
                               # the train_defense==0 gate for the same reason).
                               # 0 = invasive bases wait for the normal gate
COUNTER_EXPAND         = 1     # while STRANGLED but at body parity (PRESS target
                               # met), claim race-won neutral strongholds strictly
                               # in THEIR half — their committed army is in ours,
                               # so their half is open; punish the all-in with a
                               # map trade. 0 = off
COUNTER_EXPAND_MARGIN  = 4     # our builder must beat every enemy body to the
                               # target by this many march-days (returning-wave
                               # safety) before a counter-expansion claim is made
# --- PREDICTIVE layer: read the enemy's TRAIN/MOVE record, not their position -
WAVE_MIN               = 5     # this many enemy bodies APPROACHING (hops-to-our-
                               # HQ shrinking turn-over-turn, not staffing) =
                               # a marching wave: engage the survival solve NOW
                               # with their true ETAs so the train stream starts
                               # days before impact (train_cap bounds production —
                               # a 15-body wave needs the defenders pre-minted).
                               # 0 = off
WAVE_HORIZON           = 12    # approaching bodies further than this many hops
                               # out are ignored by the wave detector (they can
                               # still be re-detected as they come closer)
STRIKE_FORCE           = 8     # COUNTER-RUSH fund: while STRANGLED but stable
                               # (PRESS met, no recalls), pre-train this many
                               # bodies BEYOND the defence target as a strike
                               # force — the strangler's own HQ sits at 10-20hp
                               # with its army committed ~a-full-map's march from
                               # home, and assess_attack already prices their
                               # return ETAs + gold-capped reinforcement. 0 = off
STRIKE_MIN             = 8     # minimum massed force to run the strike race in
                               # strangle mode (the normal opportunistic all-in
                               # keeps ATTACK_ARMY_MIN)
ARMY_PARITY_MIN        = 8     # organizer sample 8 (0706): enemy built an 18-vs-8
                               # army by T60 with ZERO incursion — production is
                               # visible in TRAIN records but nothing answered it
                               # until the hit-and-run waves landed (4 bases razed
                               # in 9 days, war machinery disarmed between waves).
                               # From this enemy army size, keep body PARITY.
                               # v2 REDESIGN after the v2.10 regression: armed
                               # only by the aggro gate + hard solvency caps
                               # below. 0 = off
ARMY_PARITY_FRAC       = 60    # ...train toward this % of their total army
AGGRO_ARM              = 6     # aggro score (3×razes suffered + wave-detected
                               # turns + 2+-intruder turns, cumulative) needed to
                               # ARM production-matching: sample 7's passive army
                               # sat home and won on eco while v2.10's unarmed
                               # parity burned upkeep — passivity stays ignored
TECH_STARVE_DAYS       = 30    # POVERTY discriminator for the raid-mint muzzle
                               # and early tech urgency: if current net income
                               # cannot buy the next HQ level within this many
                               # days, the economy is tech-starved -> bank (mint
                               # muzzled, urgency early); a rich economy funds
                               # raids AND tech simultaneously (v2.14 games 4/5
                               # regressed because the muzzle throttled raids in
                               # RICH games where they were the win condition)
BLOCK_LATE_TURN        = 180   # from here the tech-denial relay THICKENS (the
                               # gold dump mints surplus anyway): a single gap
                               # day in the relay lets the enemy L5 through —
                               # 0706 game 4 lost 47 turns of denial to one gap
BLOCK_DENIERS_LATE     = 4     # in-region deniers from BLOCK_LATE_TURN (was 2)
BLOCK_SQUAD_LATE       = 6     # staging pipeline size from BLOCK_LATE_TURN
STRANGLE_DECAY         = 30    # strangle_mode (war spending freeze) holds only
                               # while the last raze we suffered is within this
                               # many turns — two early razes + two shuttling
                               # loiterers must not freeze the economy forever
PARITY_UPKEEP_PCT      = 35    # parity trains never push standing upkeep above
                               # this % of current work income (v2.10 game 7:
                               # upkeep 4930 of income 9360 = tech frozen at L2)
STACK_ALARM_MIN        = 4     # 0706_21 ladder (6 of 8 losses): a massed 4-7
                               # body stack marched base-to-base razing serially
                               # while PRESS stayed silent — the stack razed
                               # MIDLINE bases without ever counting as "in our
                               # half", and even when it armed, the L2 tech fund
                               # held a 443g bank asleep while our 1-body picket
                               # line was eaten one base at a time. An enemy
                               # cluster of this many bodies (zone + adjacent),
                               # on our side of the midline, within
                               # STACK_ALARM_HOPS march-days of any of our
                               # buildings, is an ACUTE ECONOMY threat even
                               # while the HQ solve reads safe: it arms PRESS
                               # and waives the tech-fund carve-out. 0 = off
STACK_ALARM_HOPS       = 4     # reach (march-days to our nearest building)
                               # that makes a massed stack an active raze threat
BASE_DEF_CONVERGE      = 1     # converge nearby bodies onto a threatened own
                               # BASE when the siege sim proves staff+turret
                               # alone fall but a reachable reinforcement set
                               # holds (minimal set, sim-sized; a provably
                               # lost base still gets NOBODY — the "don't
                               # feed defenders" doctrine survives; what
                               # changed is that a WINNABLE zone fight is now
                               # fought instead of speed-bumped). Built as
                               # the spar_defender module, then FLIPPED TO
                               # DEFAULT (v2.31) after it beat the converge-
                               # off bot 79% in mirrors, beat v2.25 79%
                               # (8W3D1L vs the old default's 75%/3L), held
                               # the panel 36/36 and spar_rush 6-0 once the
                               # wave gates + detachment test were in.
                               # (The old "staff is a speed bump" A/B that
                               # kept BASE_EVAC_DAYS off tested radius-
                               # triggered evac/garrisons, NOT sim-certified
                               # minimal convergence — different mechanism,
                               # different verdict.) 0 = off (old behavior)
BASE_DEF_HORIZON       = 2    # enemy bodies within this many march-days of
                               # an own base count as an inbound threat
ARMY_PIVOT             = 1     # ARMY-BOT PROFILE PIVOT (0708_15 pool, rank
                               # 77->177: 7/8 losses = L1-L2 army bots with
                               # <=5 bases serially razing us while our HQ
                               # sat at L1 ALL GAME — the fixed opening kept
                               # feeding 300g claims and the L2 fund never
                               # formed; once strangled, L2=600g is ~37 days
                               # of net income, i.e. unreachable. The pivot
                               # window is BEFORE the strangle: their TRAIN
                               # record makes the profile readable by T30-40
                               # while our income still lives). While their
                               # army >= ours AND their bases <= ARMY_PIVOT
                               # +2 (profile: gold->soldiers, not workers):
                               # STOP claiming new bases (they are food),
                               # shrink the opening to already-committed
                               # targets so the HQ L2/L3 fund starts NOW, and
                               # let PRESS/converge fight with the bank.
                               # Value = max enemy bases for the profile - 1
                               # (i.e. profile requires enemy_bases <= this
                               # +2). 0 = off
ARMY_PIVOT_MIN         = 6    # profile also requires enemy_army >= this
                               # (tiny early armies are just openings)
OPENING_CORE           = 2    # CONDITIONAL OPENING (user direction after
                               # 0708_15: the unconditional fixed opening
                               # feeds claims to army bots before any profile
                               # is read). Claim this many NEAREST strongholds
                               # unconditionally; every FURTHER opening claim
                               # waits for the opponent's profile to certify
                               # SAFE — they built >=2 bases themselves (a
                               # fellow boomer can't punish us for booming)
                               # or profile-turn parity (see below). Latched
                               # once true. Smaller CORE also frees spare
                               # bodies earlier = the EARLY DENY wave can
                               # actually assemble. -1 = off (old fixed
                               # opening; twin switch)
OPENING_PROFILE_TURN   = 25   # from this turn, army parity (enemy_army <=
                               # ours) also certifies safe expansion — a
                               # quiet opponent who out-armies us is exactly
                               # who claims are food for
HOVER_WATCH            = 0    # SMALL-MAP HOVER (user game-theory read: if
                               # punishing the first base is profitable, WE
                               # should hover too). Until this turn on maps
                               # with HQ<->HQ march <= HOVER_DIST, claim
                               # NOTHING and keep ~5 bodies ready: the
                               # starting warriors stay UNCOMMITTED — legal
                               # spares (the 2W0D10L law forbids stripping
                               # COMMITTED labour, not using bodies that
                               # never worked), so the moment their first
                               # base appears the EARLY DENY dispatch has a
                               # ready squad and a 3-5 day march. Watch ends
                               # (latched) on their first base / any rush
                               # tell / timeout (mutual hover = army game,
                               # resume the conditional opening). Early gold
                               # is the snowball (their 300g + claimer vs
                               # our ~150g of delayed claims).
                               # DEFAULT OFF (0708/09 A/B): vs the hover-off
                               # twin 0W/8D/4L (33%) — BOTH sides have v2.31
                               # converge, and sim-certified convergence
                               # makes first-base sniping unprofitable: the
                               # pounce dies to the converge set while the
                               # watch pays 12 turns of claims + ~480g of
                               # bank. Also spar_rush dropped to 5/6 (the
                               # baseless watch window feeds a fast wave)
                               # and a fatal-map spar_army game flipped to a
                               # loss. Mechanism verified end-to-end though
                               # (probe raze launch T7): keep for style-
                               # profile use vs CERTIFIED-naive opponents.
                               # 0 = off
HOVER_DIST             = 8    # HQ<->HQ march-days cap for the hover watch
                               # (big maps: the pounce arrives too late and
                               # the watch just delays our economy)
FWD_STAGE              = 1    # FORWARD STAGING (user observation: surplus
                               # always idled AT THE HQ — the v1 "garrison
                               # by default" fallback — so every raid launched
                               # from maximum distance, and the backtest says
                               # distance is the death cause: success median
                               # 4 march-days vs squad-died median 7). When
                               # home is safe BY PROOF (no recalls, and the
                               # closest enemy needs longer to reach our HQ
                               # than the surplus needs to march back +
                               # FWD_STAGE_SLACK), the unconsumed surplus
                               # waits at our FORWARDMOST base instead of the
                               # HQ: nearest-first squad selection then turns
                               # far uncertifiable raids into short certified
                               # ones, intercepts/claim escorts launch from
                               # the frontier, and the bodies sit on an OWN
                               # building (work slots, turret, converge
                               # cover, free moves, re-taskable while
                               # stationary — the MOVE-commitment rule makes
                               # a stationary forward pool strictly better
                               # than committed marches). 0 = off
FWD_STAGE_SLACK        = 2    # safety margin (days) in the return-ETA proof
FWD_STAGE_MIN_HQ       = 2    # no forward staging below this HQ level
DEF_UPGRADE            = 1    # DEFENSIVE HQ UPGRADE (user's economical-
                               # defense read, rule-verified: a LEVEL-UP
                               # fully refills building HP — referee
                               # apply_upgrades: b.hp = max_hp_now() — and
                               # upgrades resolve FIRST in the day pipeline,
                               # so a level bought before the wave enters the
                               # zone is a SAME-DAY full heal + bigger turret
                               # + fatter spawns). When the survival solve
                               # proves the current-level stand LOST, it now
                               # also evaluates the upgraded stand (full new
                               # hp/turret/spawn, stream re-funded from the
                               # bank minus the cost); if THAT holds, the
                               # level is bought as a defensive action,
                               # outranking every freeze/reserve. Illegal
                               # with an enemy in the zone => needs >=1 day
                               # of warning (the solve sees ETAs). 0 = off
BASE_DEF_RADIUS        = 3    # our bodies within this many march-days may be
                               # pulled in as converging defenders
RAID_ABORT             = 1     # 1 = a committed raid whose kill the per-turn
                               # re-plan can no longer certify RETREATS home
                               # (un-pinned bodies only; 2-turn hysteresis so
                               # a defender passing through doesn't thrash
                               # the squad). Launch aggression is untouched —
                               # the 0708 backtest/A-B cycle proved capping
                               # launches always loses campaign value; this
                               # only recovers bodies from certified-dead
                               # expeditions (the roadmap's abort/redirect,
                               # ranked top after launch-time prediction
                               # measured blind). 0 = off
WAR_FUNDING            = 1     # 1 = while the war is CERTIFIED (strangle_mode /
                               # stack_alarm / recent raze with n_bases<=1) the
                               # ARMY-PARITY floor ignores its solvency caps
                               # (feedable + upkeep ceiling) and trains bank-
                               # funded down to the 300g reboot reserve.
                               # 13th chronic-vs-acute site (0708_10: three
                               # losses banked gold at ZERO trains for 40-73
                               # turns while a rotating stack executed the
                               # economy). 0 = solvency caps always apply

# Names that may be overridden by an injected parameter set (tune.py / data.bin).
_TUNABLES = (
    "HQ_TARGET_LEVEL", "HQ_DEFENSIVE_LEVEL", "BASE_ECON_LEVEL", "BASE_TARGET_LEVEL",
    "MIN_BASES_BEFORE_HQ", "BASE_FRACTION", "MAX_BASES", "DEFENSE_TRIGGER",
    "MAX_CONCURRENT_BUILDERS", "THREAT_HOPS", "MIN_GARRISON", "GARRISON_BUFFER",
    "TRAIN_NET_MARGIN", "ARMY_BUFFER_MIN", "ARMY_BUFFER_MAX",
    "ATTACK_ARMY_MIN", "ATTACK_RACE_SAFETY", "ATTACK_ETA_BUFFER",
    "ATTACK_GOLD_WINDOW", "ATTACK_HYSTERESIS", "ATTACK_RATIO", "ATTACK_TURRET_BUFFER",
    "TECH_GATE_DEADLINE", "TECH_URGENT_TURN", "BASE_SPEND_CUTOFF",
    "RUSH_WINDOW", "RUSH_MIN_INCURSION", "RUSH_MASS_ARMY", "RUSH_PREP_HOPS",
    "RUSH_COMMIT_BODIES", "HEAL_FINAL_TURN",
    "BLOCK_START", "BLOCK_SQUAD", "BLOCK_MAX_INTRUDERS", "BLOCK_DENIERS",
    "GOLD_DUMP_TURN", "GOLD_DUMP_BANK", "FLOOD_TURN", "FLOOD_MASS",
    "FLOOD_DOM_EARLY",
    "TECH_RACE_TURN", "TECH_RACE_DEADLINE", "TECH_RACE_MARGIN", "CHIP_GUARD_TURN",
    "RAID_SQUAD", "RAID_MAX_SQUADS", "RAID_MIN_HQ", "RAID_DEF_RADIUS",
    "RAID_BEFORE_TECH", "RETIRE_HP", "RAID_ETA_CAP", "RAID_ABORT",
    "BASE_DEF_CONVERGE", "BASE_DEF_HORIZON", "BASE_DEF_RADIUS",
    "ARMY_PIVOT", "ARMY_PIVOT_MIN", "OPENING_CORE", "OPENING_PROFILE_TURN",
    "HOVER_WATCH", "HOVER_DIST",
    "FWD_STAGE", "FWD_STAGE_SLACK", "FWD_STAGE_MIN_HQ", "DEF_UPGRADE",
    "EARLY_RAID_HOPS", "EARLY_RAID_TRAIN", "EARLY_RAID_BANK",
    "CAMP_TURNS", "CAMP_BODIES",
    "BASE_EVAC_DAYS",
    "OPENING_MAX_TURN", "REBUILD_GUARD_HOPS", "PRESS_MIN",
    "CLEAR_SQUAD", "CLEAR_MAX_SQUADS", "CLEAR_DEF_RADIUS",
    "MID_CLAIM_HUNT", "RAID_MIN_HQ_INVASIVE",
    "COUNTER_EXPAND", "COUNTER_EXPAND_MARGIN",
    "WAVE_MIN", "WAVE_HORIZON", "STRIKE_FORCE", "STRIKE_MIN",
    "ARMY_PARITY_MIN", "ARMY_PARITY_FRAC", "AGGRO_ARM", "PARITY_UPKEEP_PCT",
    "STACK_ALARM_MIN", "STACK_ALARM_HOPS", "WAR_FUNDING",
    "TECH_STARVE_DAYS", "STRANGLE_DECAY",
    "BLOCK_LATE_TURN", "BLOCK_DENIERS_LATE", "BLOCK_SQUAD_LATE",
)


_PARAM_SET: dict = {}       # full parsed parameter document (nested schema)
_PRE_PROFILE: dict = {}     # tunable snapshot taken before a style-profile overlay
_ACTIVE_PROFILE: Optional[str] = None


def _overlay(vals: dict, why: str) -> None:
    """Apply {NAME: number} onto the module tunables. Whitelisted (_TUNABLES),
    numeric, bool rejected — an unknown/garbage key can never touch globals."""
    g = globals()
    applied = []
    for k, v in vals.items():
        if k in _TUNABLES and isinstance(v, (int, float)) and not isinstance(v, bool):
            g[k] = v
            applied.append(k)
    if applied and _DEBUG:
        sys.stderr.write(f"PARAMS {why}: {applied}\n")
        sys.stderr.flush()


def _apply_params() -> None:
    """Load the JSON parameter document, priority: argv[1] file path (tuning
    gives each side distinct params) > NYPC_PARAMS env > data.bin (the
    submission carries learned values). The judge's non-file argv "NYPC" is
    ignored gracefully. Two accepted formats:
      * legacy flat: {"NAME": value, ...} — applied directly;
      * nested schema:
          {"default":     {NAME: value, ...},          # applied at import
           "map_buckets": [{"if": {"N_min":..,"N_max":..,"K_min":..,"K_max":..,
                                   "diam_min":..,"diam_max":..},
                            "set": {NAME: value, ...}}, ...],   # apply_map_profile
           "profiles":    {"anti_rush": {NAME: value, ...}, ...}}  # style router
    Only "default" is applied here; the map buckets need the map (hook in
    main()) and profiles are switched by the style router at runtime."""
    global _PARAM_SET
    src = None
    candidates = []
    if len(sys.argv) > 1:
        candidates.append(sys.argv[1])
    env_p = os.environ.get("NYPC_PARAMS")
    if env_p:
        candidates.append(env_p)
    candidates.append("data.bin")
    for path in candidates:
        if not path or not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as f:
                src = json.loads(f.read().decode("utf-8"))
            break
        except Exception:
            src = None
    if not isinstance(src, dict):
        return
    if any(k in src for k in ("default", "map_buckets", "profiles")):
        _PARAM_SET = src
        default = src.get("default", {})
        if isinstance(default, dict):
            _overlay(default, "default")
    else:                                   # legacy flat document
        _PARAM_SET = {"default": src}
        _overlay(src, "legacy")


def _bucket_matches(cond: dict, N: int, K: int, diam: int) -> bool:
    """True iff every {var}_min/{var}_max bound holds for var in N/K/diam.
    An unrecognised condition key makes the bucket never match (fail closed)."""
    vals = {"N": N, "K": K, "diam": diam}
    for key, lim in cond.items():
        base, _, kind = key.rpartition("_")
        v = vals.get(base)
        if v is None or not isinstance(lim, (int, float)):
            return False
        if kind == "min" and v < lim:
            return False
        if kind == "max" and v > lim:
            return False
        if kind not in ("min", "max"):
            return False
    return True


def apply_map_profile(N: int, K: int, diam: int) -> None:
    """Hook A — call once per game as soon as the map is known (main(), right
    after Pathing). Applies EVERY matching map_buckets entry in document order,
    later matches overriding earlier ones (so a generic small-map bucket can be
    refined by a more specific one below it)."""
    for b in _PARAM_SET.get("map_buckets", []):
        if isinstance(b, dict) and _bucket_matches(b.get("if", {}), N, K, diam):
            s = b.get("set", {})
            if isinstance(s, dict):
                _overlay(s, f"bucket{b.get('if', {})}")


def apply_style_profile(name: Optional[str]) -> bool:
    """Hook B — the style-router entry point (the router that CALLS this is a
    later feature; the interface ships now so profiles can live in data.bin).
    Overlays profiles[name] on top of the CURRENT tunables (i.e. after default
    + map bucket). Profiles never stack: switching restores the pre-profile
    baseline first. apply_style_profile(None) just restores the baseline.
    Returns False (and changes nothing) for an unknown profile name."""
    global _ACTIVE_PROFILE, _PRE_PROFILE
    if name == _ACTIVE_PROFILE:
        return True
    prof = None
    if name is not None:
        prof = _PARAM_SET.get("profiles", {}).get(name)
        if not isinstance(prof, dict):
            return False
    g = globals()
    if _ACTIVE_PROFILE is not None:         # restore baseline before switching
        for k, v in _PRE_PROFILE.items():
            g[k] = v
        _PRE_PROFILE = {}
        _ACTIVE_PROFILE = None
    if name is None:
        return True
    vals = {k: v for k, v in prof.items()
            if k in _TUNABLES and isinstance(v, (int, float)) and not isinstance(v, bool)}
    _PRE_PROFILE = {k: g[k] for k in vals}
    _overlay(vals, f"profile:{name}")
    _ACTIVE_PROFILE = name
    return True


_apply_params()

# --- economical-defense simulator constants (structural, not tuned) ----------
DEF_HORIZON     = 40    # days to forward-simulate a siege
DEF_SETTLE_DAYS = 2     # once the current wave is cleared, a next arrival more
                        # than this many days out is a *separate* wave we re-plan
                        # for next turn (keeps distant reinforcements from forcing
                        # pointless over-defense today)
DEF_RECALL_MARGIN = 2   # recall this many workers BEYOND the bare survival
                        # minimum: the one-shot sim can't see recalled workers
                        # dying/pinned en route or ETA slop, so a small cushion
                        # buys a decisive break instead of a knife-edge survival
DEF_SIEGE_DAYS = 8      # typical siege length: window over which we amortise
                        # banked gold + income into a sustainable training rate
DEF_TRAIN_ONLY = False  # experiment flag: True = never recall, defend by training
                        # (+HQ upgrade HP-refill) only, keeping every farmer working
DEF_MIN_HQ_FOR_RECALL = 2  # don't recall farmers to defend until the HQ has teched
                        # to at least this level (the opening ~HQ-L2 mark): below
                        # it, defend by training only and protect the economy


def _apply_hits(hps: list[int], hits: int) -> None:
    """Deal `hits` points of damage, lowest-HP-warrior first (referee
    _damage_tick targets min hp, ties by id). The aggregate of those 1-damage
    ticks is: sort ascending, then fully consume each warrior's HP before the
    next. Mutates `hps` in place, leaving only survivors, still sorted."""
    if hits <= 0:
        return
    hps.sort()
    i = 0
    while hits > 0 and i < len(hps):
        absorb = hps[i] if hps[i] <= hits else hits
        hps[i] -= absorb
        hits -= absorb
        i += 1
    hps[:] = [h for h in hps if h > 0]


def simulate_hq_siege(hq_hp: int, turret: int,
                      defenders: list[tuple[int, int]],
                      attackers: list[tuple[int, int]],
                      reinforce_hp: int = 0, reinforce_rate: int = 0,
                      reinforce_from: int = 1,
                      horizon: int = DEF_HORIZON,
                      settle: bool = True, return_kill_day: bool = False):
    """Forward-simulate the siege of ONE HQ, mirroring the referee day pipeline
    (movement/spawn -> combat -> siege). Default (settle=True, return_kill_day
    =False): returns True iff the HQ survives — the DEFENSIVE reading.

    The function is SYMMETRIC and doubles as the OFFENSIVE lethality calc: set
    defenders = the ENEMY (their hq_hp, their turret, their warriors + their
    gold-capped reinforcement) and attackers = MY army; then a kill (hq_hp<=0)
    means we destroy their HQ. For that use pass return_kill_day=True to get the
    earliest kill DAY (else None), and settle=False so a staggered schedule is
    simulated to the full horizon instead of being declared "settled" the moment
    the current wave clears (that per-turn-replan shortcut is only valid for the
    live defensive solve, never for an irreversible attack/counter race).

    defenders / attackers: (arrival_day, hp) — a unit fights from `arrival_day`
    on (referee spawns/moves before combat, so a unit that arrives or is trained
    on day D fights day D). Day 0 = the turn being decided.
    reinforce_*: a sustained self-train stream (rate warriors of reinforce_hp
    each, from day reinforce_from).

    Core referee facts encoded (see nypc-combat-mechanics):
      * attack counts are FIXED at the start of the combat day,
      * a turret adds attacks against the enemy but NOT defender HP,
      * siege_that_day = max(0, attacker_count - sum(defender HP at start)).
    """
    def_hp: list[int] = []
    att_hp: list[int] = []
    di = sorted(defenders)
    ai = sorted(attackers)
    dpos = apos = 0
    for day in range(horizon + 1):
        # arrivals + same-day trains happen before combat
        while dpos < len(di) and di[dpos][0] <= day:
            def_hp.append(di[dpos][1]); dpos += 1
        while apos < len(ai) and ai[apos][0] <= day:
            att_hp.append(ai[apos][1]); apos += 1
        if reinforce_rate and day >= reinforce_from:
            def_hp.extend([reinforce_hp] * reinforce_rate)
        if not att_hp:
            # no attackers present. Truly done only if none remain to arrive;
            # otherwise (settle) treat a far-off next wave as a separate
            # engagement we re-plan for — a shortcut valid ONLY for the live
            # defensive solve, so an offence/race call passes settle=False.
            if apos >= len(ai) or (settle and ai[apos][0] > day + DEF_SETTLE_DAYS):
                return None if return_kill_day else True
            continue
        # combat — counts fixed at start of day (referee builds them first)
        d_alive = len(def_hp)
        a_alive = len(att_hp)
        d_hpsum = sum(def_hp)
        siege = a_alive - d_hpsum
        if siege > 0:
            hq_hp -= siege
            if hq_hp <= 0:
                return day if return_kill_day else False   # the ONLY true kill signal
        _apply_hits(att_hp, d_alive + turret)   # our warriors + turret hit them
        _apply_hits(def_hp, a_alive)            # each attacker lands one hit
    # ran the whole horizon with attackers STILL present: a siege we can't break
    # is not "safe" — it pins our HQ region and blocks tech/economy. Demand a
    # decisive defence (recall/train more) rather than a bare HP-positive stall.
    # For offense (return_kill_day) this NON-kill correctly reads as None.
    if return_kill_day:
        return None
    return not att_hp and hq_hp > 0


def plan_hq_defense(hq_hp: int, turret: int,
                    home: list[tuple[int, int]],
                    recall_pool: list[tuple[int, int, "Warrior"]],
                    attackers: list[tuple[int, int]],
                    train_cap: int, spawn_hp: int, sustain_rate: int,
                    settle: bool = True
                    ) -> tuple[list["Warrior"], int, bool, bool]:
    """Minimum-cost survival solve for the HQ. Returns (warriors_to_recall,
    trains_now, needs_stream, holds). holds=False means even the maximum plan
    from the given resources is NOT proven to survive — the caller can retry
    with a bigger recall_pool before accepting a losing stand.

    needs_stream=True means survival was proven only WITH the assumed
    `sustain_rate` training stream from day 1 on — so the caller MUST actually
    train at that rate while the threat persists. (The 0701 ladder showed the
    procrastination failure when this was implicit: every turn the sim said
    "safe, given we train from tomorrow", the bot trained nothing today, and
    the promised stream never materialised — the HQ fell with 9,600 gold
    banked. Every re-plan is day 0 of a fresh sim; "tomorrow" never comes
    unless it is executed TODAY.)

    Priority = TRAIN before RECALL. A trained warrior spawns at the HQ and
    defends the SAME day (spawn precedes combat), is paid out of income rather
    than pulled off a farm, and — once the wave breaks — is released back to work
    or the army (the garrison hold drops to MIN_GARRISON when we're no longer
    actively defending). Recalling a farmer instead costs income AND travel time
    and, done reflexively, spirals the economy into insolvency. So we only recall
    the nearest idle workers as a STOPGAP, when same-day training (this turn's
    train_cap plus the sustained stream) still can't muster bodies fast enough.
    `recall_pool` must be pre-sorted by arrival ETA (nearest first).

    settle=False makes the sim engage a wave still marching instead of declaring
    a far next-arrival "settled" (pass it during a committed opening rush: the
    L1 train_cap-1 stream must start days before impact, so the per-turn-replan
    shortcut would systematically cap the warning at ~DEF_SETTLE_DAYS hops)."""
    def survives(trains: int, n_recalls: int, stream: int = sustain_rate) -> bool:
        defs = list(home)
        defs.extend((0, spawn_hp) for _ in range(trains))
        defs.extend((eta, hp) for eta, hp, _ in recall_pool[:n_recalls])
        return simulate_hq_siege(hq_hp, turret, defs, attackers,
                                 reinforce_hp=spawn_hp, reinforce_rate=stream,
                                 settle=settle)

    if not attackers:
        return ([], 0, False, True)
    if survives(0, 0, stream=0):
        return ([], 0, False, True)  # holds with NO training at all — truly safe
    if survives(0, 0):
        return ([], 0, True, True)   # holds only if the stream is real -> execute it
    # 1) TRAIN first — fewest same-day trains that suffice, no farm disruption
    for t in range(1, train_cap + 1):
        if survives(t, 0):
            return ([], t, True, True)
    # 2) full-cap training still too slow -> recall nearest workers as a stopgap
    #    (on top of training at train_cap), fewest that suffice + a safety margin
    for k in range(1, len(recall_pool) + 1):
        if survives(train_cap, k):
            kk = min(len(recall_pool), k + DEF_RECALL_MARGIN)
            return ([w for _, _, w in recall_pool[:kk]], train_cap, True, True)
    # 3) maximum effort (still may fall — we re-plan and keep training next turn)
    return ([w for _, _, w in recall_pool], train_cap, True, False)


def _project_enemy_hq_level(level: int, gold: int, days: int) -> int:
    """Worst-case enemy HQ level after `days` (they may tech up while we march).
    Spends a COPY of their gold up the upgrade ladder (~one level/day). The same
    gold is also (separately) counted toward their trains — deliberate double
    count = pessimistic = we never over-commit."""
    lvl = level
    g = gold
    steps = 0
    while lvl < HQ_MAX_LEVEL and steps < days:
        cost = HQ_LEVELS[lvl + 1].upgrade_cost
        if g < cost:
            break
        g -= cost
        lvl += 1
        steps += 1
    return lvl


def assess_attack(S: "GameState", M: "GameMap", P: "Pathing", turn: int,
                  hq: "Building", my_warriors: list, enemy_warriors: list,
                  wave: list, work_income: int) -> tuple:
    """Verified opportunistic all-in as a RACE (returns (commit, our_kd, their_kd, A)).

    Commit iff, under the enemy's WORST-CASE play, our army destroys their HQ
    strictly before their worst-case counter can destroy ours — with margin. All
    timing uses P.march_days (the exact referee ETA, NOT the optimistic BFS hops).
    Both siege calls use the validated simulate_hq_siege with settle=False (a
    launched army is irreversible, so we may NOT lean on 'we re-plan next turn').

    SAFETY: home defenders are only the bodies NOT sent (and NOT already flying to
    the enemy HQ), with reinforce_rate=0 and current HQ hp (no phantom trains, no
    assumed heal) → home is modelled pessimistically. The enemy defence is modelled
    at its richest (recall-all + gold-capped pre-build-up + during-siege trains +
    projected HQ tech-up + one heal) → offence is modelled pessimistically. Both
    biases push toward NOT attacking, so a commit is a genuine, robust kill."""
    opp_b = S.find_building(M.opp_hq)
    if opp_b is None or opp_b.side is M.my_side:         # enemy HQ gone / is ours
        return (False, None, None, 0)

    def md_o(r: int) -> int:
        return P.march_days(r, M.opp_hq)

    def md_m(r: int) -> int:
        return P.march_days(r, M.my_hq)

    atk = [(md_o(w.region), w.hp) for w in wave]
    A = min((d for d, _ in atk), default=P.UNREACH)
    if A >= P.UNREACH:
        return (False, None, None, 0)

    # corridor pricing: an enemy warrior sitting BETWEEN the HQs can pin our
    # marching blob. A body in OUR half is the committed force we are racing —
    # its return is already modelled in edef below, and if it sits on our
    # route the blob kills it in ~a day (attack counts are fixed at day start,
    # a big blob one-shots a picket): price +1 day each instead of refusing —
    # the old binary veto made every counter-rush vs a deep intruder illegal,
    # which is backwards (their commitment IS the opening). A picket in THEIR
    # half guarding the road still hard-refuses (it delays us next to their
    # reinforcements, the genuinely dangerous stall).
    pins = 0
    for w in enemy_warriors:
        d = md_o(w.region)
        if 0 < d < A:
            hm, ho = P.hops_my[w.region], P.hops_opp[w.region]
            _wb = S.find_building(w.region)
            if (hm >= 0 and (ho < 0 or hm < ho)) or (
                    _wb is not None and _wb.side is not M.my_side):
                pins += 1          # our-half straggler OR their own base staff:
            else:                  # a real fight, priced at ~a day each
                return (False, None, None, A)
    A += pins

    # ---- our_kill_day: WE siege THEIR HQ (offence, pessimistic enemy defence) ----
    e_lvl = _project_enemy_hq_level(opp_b.level, S.opp_gold, A)
    e_hp = HQ_LEVELS[e_lvl].warrior_hp
    e_cap = HQ_LEVELS[e_lvl].train_cap
    e_full = HQ_LEVELS[e_lvl].hp                          # assume one heal to full
    e_tur = HQ_LEVELS[e_lvl].turret
    atk_rel = [(d - A, hp) for d, hp in atk]              # shift so contact = sim day 0
    pool = (S.opp_gold + S.opp_income * ATTACK_GOLD_WINDOW) // TRAIN_COST
    edef = [(max(0, md_o(w.region) - A), w.hp) for w in enemy_warriors]   # recall-all
    pre = min(pool, e_cap * A)                            # pre-arrival build-up
    edef += [(0, e_hp)] * pre
    pool -= pre
    d = 1
    while pool > 0 and d <= DEF_HORIZON:                  # during-siege reinforce
        k = min(e_cap, pool)
        edef += [(d, e_hp)] * k
        pool -= k
        d += 1
    rel = simulate_hq_siege(e_full, e_tur, edef, atk_rel, reinforce_rate=0,
                            settle=False, return_kill_day=True)
    if rel is None:
        return (False, None, None, A)                    # can't actually kill it
    our_kd = A + rel + ATTACK_ETA_BUFFER
    if turn + our_kd > MAX_TURN:
        return (False, our_kd, None, A)                  # kill lands after the game ends

    # ---- their_kill_day: enemy counter-alls-in OUR HQ with our home force detached ----
    attack_ids = {w.id for w in wave}
    attack_ids |= {w.id for w in my_warriors
                   if w.state is WState.MOVING and w.target == M.opp_hq}
    home_kept = [w for w in my_warriors if w.id not in attack_ids]
    if not enemy_warriors:
        their_kd = None
    else:
        Ap = min(md_m(w.region) for w in enemy_warriors)
        if Ap >= P.UNREACH:
            their_kd = None
        else:
            e_atk = [(md_m(w.region) - Ap, w.hp) for w in enemy_warriors
                     if md_m(w.region) < P.UNREACH]
            mdef = [((0, w.hp) if (w.region == hq.region and w.state is WState.STATIONARY)
                     else (max(1, md_m(w.region)), w.hp)) for w in home_kept]
            tkd = simulate_hq_siege(hq.hp, hq.turret(), mdef, e_atk,
                                    reinforce_rate=0, settle=False, return_kill_day=True)
            their_kd = None if tkd is None else Ap + tkd

    commit = their_kd is None or our_kd + ATTACK_RACE_SAFETY < their_kd
    return (commit, our_kd, their_kd, A)


def decide(S: GameState, M: GameMap, P: Pathing, turn: int) -> Actions:
    S.my_turn_now = turn
    # STYLE ROUTER apply (Hook B): the classification made at the END of the
    # previous turn switches the parameter profile BEFORE anything reads a
    # tunable this turn — profiles live in data.bin, overlay is whitelisted,
    # restore-then-overlay never stacks, unknown names are ignored.
    apply_style_profile(getattr(S, "style_profile", None))
    a = Actions()
    my = M.my_side

    my_warriors = [w for w in S.warriors if w.id.side is my]
    enemy_warriors = [w for w in S.warriors if w.id.side is not my]
    my_buildings = [b for b in S.buildings if b.side is my]
    hq = next((b for b in my_buildings if b.type is BType.HQ), None)
    if hq is None:
        return a

    # FIXED OPENING = HQ still L1: claim every nearest sub-half stronghold with a
    # just-in-time worker economy, hold NO standing garrison, then raise HQ to L2.
    # The opening also ENDS BY TIME (OPENING_MAX_TURN): a strangled economy that
    # can never afford L2 used to stay in this posture — JIT worker cap, zero
    # garrison — for the entire game (weekend (10)/(34): 2-3 trains in 100+ days
    # while an enemy stack razed every base; the opening never ended because the
    # razed targets kept `bases_all_done` false and income never reached 600g).
    opening = hq.level < 2 and (OPENING_MAX_TURN <= 0 or turn <= OPENING_MAX_TURN)

    enemy_regions = {w.region for w in enemy_warriors}
    # regions an enemy warrior stands on OR next to: claiming/upgrading a base
    # there just feeds 300-600g plus a worker into a harasser (ladder (22):
    # 6,600g of rebuilt bases while the HQ never left L3 — a tiebreak loss).
    hot_regions: set[int] = set()
    for _er in enemy_regions:
        hot_regions.add(_er)
        for _v in M.adj[_er]:
            hot_regions.add(_v)

    # ENEMIES IN OUR HALF — the strangle/harass archetype's fuel. SQUATTERS are
    # the stationary ones (`S.opp_moving` holds the ids that moved in the last
    # result block; everyone else standing deep in our territory is besieging,
    # pinning or denying something of ours). A ROTATING stack spends half its
    # days "moving" between our bases, so pressure ACCOUNTING (how many bodies
    # to train) counts everyone in our half, while INTERCEPT targeting (below)
    # only aims at the stationary ones.
    _opp_moving = getattr(S, "opp_moving", None) or set()
    in_half_enemies = [w for w in enemy_warriors
                       if P.hops_my[w.region] >= 0
                       and (P.hops_opp[w.region] < 0
                            or P.hops_my[w.region] < P.hops_opp[w.region]
                            or ((_b := S.find_building(w.region)) is not None
                                and _b.side is my))]
    squatters = [w for w in in_half_enemies if w.id not in _opp_moving]
    # freeze base spending anywhere within REBUILD_GUARD_HOPS of a squatter —
    # the weekend strangle victims fed 300g rebuilds into the same rotating
    # stack over and over (rebuilt bases died within 2-3 days, every time).
    if squatters and REBUILD_GUARD_HOPS > 0:
        _frontier = {w.region for w in squatters}
        _guarded = set(_frontier)
        for _ in range(REBUILD_GUARD_HOPS):
            _frontier = {v for r in _frontier for v in M.adj[r]} - _guarded
            _guarded |= _frontier
        hot_regions |= _guarded
    # RAZE-SITE MEMORY: a region we already lost a building on is a proven
    # strangle site, and the rotating stack is MOVING (invisible to the
    # squatter guard) exactly when our rebuilt base would go up — ghost-replay
    # of weekend game (10) still leaked 2,100g of rebuilds through the
    # memoryless guard. A razed-once site rebuilds only with no enemy within
    # REBUILD_GUARD_HOPS+1 hops (any state); razed twice+, +1 hop further.
    _raz = getattr(S, "razed_count", None) or {}
    _danger: list[set[int]] = []
    if _raz and REBUILD_GUARD_HOPS > 0 and enemy_warriors:
        _frontier = set(enemy_regions)
        _seen = set(_frontier)
        for _ in range(REBUILD_GUARD_HOPS + 2):
            _frontier = {v for r in _frontier for v in M.adj[r]} - _seen
            _seen |= _frontier
            _danger.append(set(_seen))

    # MID-CLAIM HUNT targets: lone enemy bodies squatting a NEUTRAL stronghold
    # on the midline (equal hops — one step outside the strict-half squatter
    # test) are the "wounded veterans claim the map one by one" play the
    # 0704-0706 top tier ran. They are not counted into strangle/PRESS
    # pressure (they are not attacking anything) — they are cheap KILLS for
    # the intercept dispatch: a lone hp1-4 body loses 1v1 to a fresh spawn.
    mid_claimers: list[Warrior] = []
    if MID_CLAIM_HUNT:
        for w in enemy_warriors:
            if w.id in _opp_moving:
                continue
            hm, ho = P.hops_my[w.region], P.hops_opp[w.region]
            if (hm >= 0 and ho >= 0 and hm == ho
                    and w.region in M.strongholds
                    and S.find_building(w.region) is None):
                mid_claimers.append(w)

    # STRANGLE MODE — the unified war-posture switch. Distinguishes a STRANGLE
    # (they are actually destroying our economy: razes suffered, force in our
    # half) from a mere PESTER (loiterers, no kills — keep expanding through
    # those, v2.6 beat pesters precisely by not flinching). While strangled,
    # ALL base spending pauses (g10 ghost probe: the contest-tier expansion
    # kept reserving 300-600g for bases that died within days, starving the
    # PRESS trains + intercept squads that actually answer the stack) and the
    # bank funds bodies instead. Expansion resumes the turn the half is clear.
    # AUDIT FIND (chronic-freeze): razed_count never decays, so two early
    # razes + two shuttling loiterers used to freeze ALL base spending for the
    # rest of the game. War posture now requires the destruction to be RECENT.
    _last_raze = getattr(S, "last_raze_turn", None)
    strangle_mode = (PRESS_MIN > 0 and len(in_half_enemies) >= PRESS_MIN
                     and sum(_raz.values()) >= 2
                     and _last_raze is not None
                     and turn - _last_raze <= STRANGLE_DECAY)

    def rebuild_ok(r: int) -> bool:
        n_razed = _raz.get(r, 0)
        if n_razed <= 0:
            return True
        if strangle_mode:
            return False        # razed ground rebuilds only once the half is clear
        # (the v2.10 global-parity gate lived here and DEADLOCKED game 8:
        # rebuild←parity←trains←income←rebuild. Replaced by the ESCORT rule
        # at the build/dispatch sites — funding-independent, cannot deadlock.)
        if not _danger:
            return True
        d = _danger[min(len(_danger), REBUILD_GUARD_HOPS + (2 if n_razed >= 2 else 1)) - 1]
        return r not in d

    # COUNTER-EXPANSION: the strangler's own half is open while its army camps
    # in ours (0704-0706 logs: up to 21 of their bodies in our half). Once the
    # PRESS body target is met (we're not losing the home fight for a worker),
    # a race-won neutral stronghold strictly in THEIR half may be claimed even
    # under the strangle_mode spending freeze — punish the all-in with a map
    # trade. The march-day margin prices in their returning wave.
    _press_want_early = (sum(b.work_cap() for b in my_buildings)
                         + MIN_GARRISON + len(in_half_enemies))

    def counter_expand_ok(r: int) -> bool:
        if not (COUNTER_EXPAND and strangle_mode):
            return False
        if len(my_warriors) < _press_want_early:
            return False
        dmy, dop = P.dist_my[r], P.dist_opp[r]
        if dmy < 0 or dop < 0 or dmy <= dop:
            return False                     # only strictly THEIR-half targets
        my_md = min([P.march_days(w.region, r) for w in my_warriors]
                    + [P.march_days(hq.region, r)])
        e_md = min([P.march_days(w.region, r) for w in enemy_warriors]
                   + [P.march_days(M.opp_hq, r)])
        return my_md + COUNTER_EXPAND_MARGIN <= e_md

    my_at: dict[int, list[Warrior]] = {}
    for w in my_warriors:
        my_at.setdefault(w.region, []).append(w)
    moving_to: dict[int, int] = {}
    for w in my_warriors:
        if w.state is WState.MOVING:
            moving_to[w.target] = moving_to.get(w.target, 0) + 1

    def present(r: int) -> int:
        return len(my_at.get(r, []))

    def buildable(r: int) -> bool:
        return present(r) > 0 and r not in enemy_regions

    # ---- economy bookkeeping (income vs upkeep -> never starve) ----
    work_income = 0
    for b in my_buildings:
        work_income += WORK_INCOME * min(present(b.region), b.work_cap())
    upkeep = UPKEEP_PER_WARRIOR * len(my_warriors)
    net = work_income - upkeep
    starve_reserve = max(0, -net)                 # keep enough to cover a deficit next turn
    budget = max(0, S.gold - starve_reserve)

    # ---- threat / posture ----
    enemy_army = len(enemy_warriors)
    enemy_def = sum(1 for w in enemy_warriors if 0 <= P.hops_opp[w.region] <= THREAT_HOPS)
    diam = P.hops_my[M.opp_hq]
    # early-warning radius. CAPPED below the midline: on a tiny map the old
    # max(5, diam//2) covered the ENTIRE map, so the enemy's home garrison and
    # its expansion workers read as a permanent incursion — 0703 sample game 6
    # (diam 5) spent 194 turns in that phantom rush emergency: base spending
    # frozen + defensive trains ate every coin, HQ ended L1 with 0 tech spend
    # while the real enemy never crossed the midline until turn 191.
    def_hops = (min(max(THREAT_HOPS, diam // 2), max(2, diam - 3))
                if diam > 0 else THREAT_HOPS)
    # How close an enemy must be to trigger the defensive solve. In the FIXED
    # OPENING we react ONLY to an enemy that has actually reached our HQ region
    # (or is one hop away) — a distant probe must NOT pull workers off bases or
    # burn base gold on defensive trains and stall the economic opening. Once past
    # the opening we use the wider half-map window for early warning.
    enemy_in_half = sum(1 for w in enemy_warriors if 0 <= P.hops_my[w.region] <= def_hops)
    # OPENING RUSH DETECTOR (ladder (15): a 6-body rush killed our L1 HQ on day
    # 10 while we paid 600g for a 2nd base and trained nothing). Several enemies
    # already in our half this early = a committed rush: widen the trigger back
    # to the half-map window for early warning and FREEZE base spending below so
    # every coin can become a same-day defender instead.
    # MASS SIGNAL (0702_15 rush deaths (13)/(23)): both killers were readable by
    # turn 3-5 — an army of RUSH_MASS_ARMY+ with ZERO bases is buying soldiers,
    # not workers. Waiting for the midline crossing left an L1 HQ (train_cap 1)
    # a single day of warning; the mass signal buys the days the stream needs.
    enemy_bases = sum(1 for b in S.buildings
                      if b.side is not my and b.type is not BType.HQ)
    # POST-RAZE CAMP sites (cross-turn): an enemy base region that vanished
    # since last turn was razed by us (bases never self-delete) — remember it
    # for CAMP_TURNS so the squad on it is held at the fallback instead of
    # walking home. Pruned on timeout or when ANY building reappears there
    # (their rebuild while unguarded = a fresh raid target; our own claim =
    # job done).
    if not hasattr(S, "camp"):
        S.camp = {}
        S.raze_sites = set()      # every enemy-base region we ever razed
        S.opp_refeeds = 0         # times they rebuilt ON such a site
    _cur_ob = {b.region for b in S.buildings
               if b.side is not my and b.type is BType.BASE}
    _prev_ob = getattr(S, "opp_base_prev", set())
    for _r in _cur_ob - _prev_ob:
        if _r in S.raze_sites:    # they rebuilt a site we razed = a FEEDER
            S.opp_refeeds += 1
    for _r in _prev_ob - _cur_ob:
        S.raze_sites.add(_r)
        # camp only once the opponent is a certified feeder (see CAMP_TURNS)
        if CAMP_TURNS > 0 and S.opp_refeeds >= 1:
            S.camp[_r] = turn
    S.opp_base_prev = _cur_ob
    for _r in [r for r, t0 in S.camp.items()
               if turn - t0 > CAMP_TURNS or S.find_building(r) is not None]:
        del S.camp[_r]
    # RAID TUITION tracker (v2.29): watch every dispatched raid squad; a squad
    # half-dead with the base still standing = this opponent PUNISHES raids
    # (converges/trains in response — unobservable at launch, provable in
    # blood). From the first observed failure the ETA cap arms (see
    # RAID_ETA_CAP): 65 of the 78 failed launches in the 0708_10 backtest
    # were REPEATS after such a failure was already visible.
    if not hasattr(S, "raid_watch"):
        S.raid_watch = {}    # region -> (frozenset ids, launch turn, max md)
        S.raid_fails = 0
    _alive = {w.id for w in S.warriors}
    for _r in list(S.raid_watch):
        _ids, _t0, _md = S.raid_watch[_r]
        _b = S.find_building(_r)
        if _b is None or _b.side is my or turn - _t0 > 25:
            del S.raid_watch[_r]     # razed / we claimed it / stale
        elif _ids and 2 * sum(1 for i in _ids if i not in _alive) >= len(_ids):
            # PUNISHED only if the deaths came fast — half-dead within a few
            # days of ARRIVAL is the convergence/ambush signature. A slow
            # attrition grind (turret trades over many days, often while the
            # kill still lands) must NOT count: the first trigger had no
            # window and read spar_boom's slow sieges as punishment (rfl=3,
            # 6-0 dropped to a draw; A/B 38%).
            if turn - _t0 <= _md + 4:
                S.raid_fails += 1
            del S.raid_watch[_r]
    mass_signal = enemy_bases == 0 and enemy_army >= RUSH_MASS_ARMY
    # The incursion emergency is NOT time-boxed to RUSH_WINDOW: the posture
    # exists because an L1 HQ (10hp, turret 1, train_cap 1) cannot defend
    # itself, and that is true for as long as the opening lasts — spar_rush's
    # first 6-wave lands ~T39 on big maps and met a disarmed detector. Only the
    # mass PRE-warning stays windowed (early on, army-with-no-bases is a rush
    # tell; later it's just any aggressive bot and the incursion test catches
    # the actual wave).
    rush_flag = opening and (
        enemy_in_half >= RUSH_MIN_INCURSION or
        (turn <= RUSH_WINDOW and mass_signal))
    # COMMITTED rush (the mass tell, or an actual multi-body wave in our half)
    # vs a poke/loiterer pair: only the former justifies the settle=False deep
    # sim, the base-spend freeze and the stream round-up. A pester's two
    # loiterers fed through the deep sim read as a phantom wave and drain the
    # opening into a permanent defensive crouch; for them rush_flag only widens
    # the warning radius while the settled sim correctly ignores non-threats.
    rush_commit = rush_flag and (mass_signal or enemy_in_half >= RUSH_COMMIT_BODIES)
    # EARLY DENY target tier (v2.25): enemy bases the OPENING may raid — in
    # reach (EARLY_RAID_HOPS of our HQ) or on our side of the midline. Feeds
    # the JIT train bump and unlocks the raid dispatch during the opening;
    # the raid sim still proves every kill, so this only nominates targets.
    # Silent under a rush tell: every opening body is a same-day defender then.
    early_deny: set = set()
    if EARLY_RAID_HOPS > 0 and opening and not rush_flag:
        for b in S.buildings:
            if b.side is my or b.type is not BType.BASE:
                continue
            _hm = P.hops_my[b.region]
            _ho = P.hops_opp[b.region]
            if _hm >= 0 and (_hm <= EARLY_RAID_HOPS
                             or (_ho >= 0 and _hm <= _ho)):
                early_deny.add(b.region)
    trigger_hops = ((max(def_hops, RUSH_PREP_HOPS) if rush_flag else 1)
                    if opening else def_hops)
    near_hq_probe = [w for w in enemy_warriors
                     if 0 <= P.hops_my[w.region] <= trigger_hops]
    # PREDICTIVE WAVE DETECTOR — read their MOVEMENT, not just their position.
    # An enemy body whose hops-to-our-HQ shrank since last turn is APPROACHING
    # (a staffer sits still; expansion walkers head sideways). WAVE_MIN of them
    # inside WAVE_HORIZON = a marching wave: feed them to the survival solve
    # NOW (settle=False, they are committed) so the defensive train stream
    # starts days before impact — train_cap bounds production per day, so a
    # wave met at def_hops leaves too few minting days (the user's point: the
    # counter needs the bodies pre-trained).
    prev_hops: dict = getattr(S, "opp_prev_hops", None) or {}
    approaching = []
    for w in enemy_warriors:
        h = P.hops_my[w.region]
        ph = prev_hops.get(w.id)
        if (ph is not None and 0 <= h < ph and h <= WAVE_HORIZON
                and ((_wb := S.find_building(w.region)) is None or _wb.side is my)):
            approaching.append(w)
    wave_detected = WAVE_MIN > 0 and len(approaching) >= WAVE_MIN
    S.opp_prev_hops = {w.id: P.hops_my[w.region] for w in enemy_warriors}
    # AGGRO score — PROVEN aggression only, accumulated over the whole game:
    # razes suffered weigh heaviest; wave-detected turns and 2+-intruder turns
    # add up. A passive big army (sample 7 sat home and won on eco while the
    # v2.10 parity trains burned upkeep) never arms the production-matching
    # counter; anyone who actually hits us arms it for good.
    S.wave_turns = getattr(S, "wave_turns", 0) + (1 if wave_detected else 0)
    S.incur_turns = (getattr(S, "incur_turns", 0)
                     + (1 if len(in_half_enemies) >= 2 else 0))
    aggro = 3 * sum(_raz.values()) + S.wave_turns + S.incur_turns
    # keep the *economy*'s threat sense exactly as before (near-HQ only) so the
    # new defence planner doesn't perturb expansion/HQ-tech; `incoming` (a wider
    # window) feeds ONLY the survival solve below.
    under_threat = any(0 <= P.hops_my[w.region] <= THREAT_HOPS for w in enemy_warriors)

    # STACK ALARM — massed base-hunter detector (0706_21 ladder, 6 of 8 losses:
    # a 4-7 body stack marched base-to-base razing our economy serially while
    # the HQ survival solve correctly read "safe" the whole time). A cluster of
    # STACK_ALARM_MIN+ enemy bodies (zone plus adjacent zones — a rotating
    # stack straddles two zones on move days), NOT strictly in their own half
    # and NOT standing on their own building (that's a home garrison), within
    # STACK_ALARM_HOPS march-days of one of our buildings, WILL serially raze
    # whatever it can reach. It arms PRESS below even with zero bodies "in our
    # half" (the midline blind spot) and waives the tech-fund carve-out that
    # let a 443g bank sleep through a picket massacre — the 11th member of the
    # chronic-vs-acute bug family: bodies first while the stack is in reach,
    # the fund resumes the turn it leaves.
    stack_alarm = False
    stack_ids: set[int] = set()
    if STACK_ALARM_MIN > 0 and my_buildings and enemy_warriors:
        _ez: dict[int, list[Warrior]] = {}
        for w in enemy_warriors:
            _ez.setdefault(w.region, []).append(w)
        _bld_r = [b.region for b in my_buildings]
        for r, grp in _ez.items():
            _hm, _ho = P.hops_my[r], P.hops_opp[r]
            if _hm < 0 or (0 <= _ho < _hm):     # strictly their side = garrison
                continue
            _rb = S.find_building(r)
            if _rb is not None and _rb.side is not my:
                continue                        # staffing their own building
            _cl = list(grp)
            for _v in M.adj[r]:
                _cl += _ez.get(_v, [])
            if len(_cl) < STACK_ALARM_MIN:
                continue
            if min(P.march_days(r, _br) for _br in _bld_r) <= STACK_ALARM_HOPS:
                stack_alarm = True
                stack_ids |= {w.id for w in _cl}

    # INTENT CLASSIFIER: `wave_detected` is only "a stack moved closer to our
    # side"; it is not automatically an HQ kill wave. Split that public signal
    # before deciding whether the HQ survival solve may recall workers.
    threat_intent = "MAP_PRESSURE"
    threat_target = -1
    hq_direct_ids: set[WarriorId] = set()
    local_threat_ids: set[WarriorId] = set()
    local_defense_regions: set[int] = set()
    threat_pool: dict[WarriorId, Warrior] = {}
    for w in approaching + near_hq_probe:
        threat_pool[w.id] = w
    if stack_ids:
        for w in enemy_warriors:
            if w.id in stack_ids:
                threat_pool[w.id] = w
    if rush_flag:
        for w in enemy_warriors:
            if 0 <= P.hops_my[w.region] <= trigger_hops:
                threat_pool[w.id] = w
    threat_group = list(threat_pool.values())

    def _closest_own_base(w: Warrior) -> tuple[int, int]:
        best = (P.UNREACH, -1)
        for b in my_buildings:
            if b.type is BType.HQ:
                continue
            d = P.march_days(w.region, b.region)
            if d < best[0]:
                best = (d, b.region)
        return best

    def _own_base_on_hq_path(w: Warrior) -> int:
        path = P.march_path(w.region, hq.region)
        for z in path[:-1]:
            b = S.find_building(z)
            if b is not None and b.side is my and b.type is BType.BASE:
                return z
        return -1

    base_votes: dict[int, set[WarriorId]] = {}
    harass_votes: dict[int, set[WarriorId]] = {}
    near_hq_ids = {w.id for w in enemy_warriors
                   if 0 <= P.hops_my[w.region] <= 1}
    for w in threat_group:
        hq_eta = P.march_days(w.region, hq.region)
        base_eta, base_r = _closest_own_base(w)
        path_base = _own_base_on_hq_path(w)
        if path_base >= 0:
            base_r = path_base
            base_eta = P.march_days(w.region, path_base)
        if w.id in near_hq_ids:
            hq_direct_ids.add(w.id)
        elif base_r >= 0 and (path_base >= 0 or base_eta + 1 <= hq_eta):
            local_threat_ids.add(w.id)
            if len(threat_group) <= max(2, RUSH_MIN_INCURSION):
                harass_votes.setdefault(base_r, set()).add(w.id)
            else:
                base_votes.setdefault(base_r, set()).add(w.id)
        elif hq_eta < P.UNREACH and (base_r < 0 or hq_eta + 1 <= base_eta):
            hq_direct_ids.add(w.id)

    if near_hq_ids:
        threat_intent = "HQ_DIRECT"
        hq_direct_ids |= near_hq_ids
        threat_target = hq.region
    elif len(hq_direct_ids) >= (WAVE_MIN if wave_detected else RUSH_MIN_INCURSION):
        threat_intent = "HQ_DIRECT"
        threat_target = hq.region
    elif base_votes:
        threat_target, ids = max(base_votes.items(), key=lambda kv: len(kv[1]))
        local_defense_regions.add(threat_target)
        local_threat_ids |= ids
        threat_intent = "BASE_RAID"
    elif harass_votes:
        threat_target, ids = max(harass_votes.items(), key=lambda kv: len(kv[1]))
        local_defense_regions.add(threat_target)
        local_threat_ids |= ids
        threat_intent = "WORKER_HARASS"
    elif opening and (wave_detected or stack_alarm or mass_signal
                      or (rush_flag and threat_group)):
        threat_intent = "UNKNOWN_EARLY_THREAT"
    elif wave_detected or stack_alarm:
        threat_intent = "UNKNOWN"

    hq_survival_mode = threat_intent == "HQ_DIRECT"
    hq_rush_commit = (hq_survival_mode
                      and (rush_commit or len(hq_direct_ids) >= RUSH_COMMIT_BODIES))
    hq_attacker_ids = set(hq_direct_ids)
    incoming = [w for w in enemy_warriors if w.id in hq_attacker_ids]
    if not hq_survival_mode:
        incoming = [w for w in enemy_warriors if w.id in near_hq_ids]
        hq_attacker_ids = {w.id for w in incoming}
    early_defense_posture = opening and threat_intent in (
        "HQ_DIRECT", "BASE_RAID", "WORKER_HARASS", "UNKNOWN_EARLY_THREAT")
    if early_defense_posture and threat_intent != "MAP_PRESSURE":
        early_deny.clear()

    # ---- economical HQ defense: minimum-cost survival solve --------------------
    # Replaces the old "enemy_in_half >= DEFENSE_TRIGGER -> recall EVERYONE"
    # heuristic. Forward-simulate the siege (simulate_hq_siege) and recall only
    # the nearest workers (and train only the bodies) actually needed to survive;
    # everyone else keeps farming. See plan_hq_defense / nypc-combat-mechanics.
    recall_targets: list[Warrior] = []
    train_defense = 0
    def_upgrade = False
    spawn_hp = HQ_LEVELS[hq.level].warrior_hp
    train_cap = HQ_LEVELS[hq.level].train_cap
    if incoming:
        # attacker schedule: every enemy warrior by its ETA (hops) to our HQ.
        # (We track S.opp_gold as an upper-bound on the enemy's economy for a
        # future worst-case reinforcement model, but feeding a 30-days-away
        # synthetic wave into the *immediate* survival solve just over-defends;
        # the per-turn re-plan picks up real reinforcements as they approach.)
        attackers = [(P.hops_my[w.region], w.hp) for w in enemy_warriors
                     if w.id in hq_attacker_ids and P.hops_my[w.region] >= 0]
        # our defenders: those already home (fight day 0) or walking home
        home = [(0, w.hp) for w in my_at.get(hq.region, [])
                if w.state is WState.STATIONARY]
        home += [(max(1, P.hops_my[w.region]), w.hp) for w in my_warriors
                 if w.state is WState.MOVING and w.target == hq.region]
        # recall candidates: idle workers not pinned by an enemy, nearest first
        # (recall into our HQ is a free move, so nearest = cheapest + soonest)
        pool = [(P.hops_my[w.region], w.hp, w) for w in my_warriors
                if (w.state is WState.STATIONARY and w.region != hq.region
                    and w.region not in enemy_regions and P.hops_my[w.region] >= 0)]
        pool.sort(key=lambda t: t[0])
        # sustained-training rate the sim may assume: during a defence we stop
        # expanding and pour BOTH income and banked gold into training, so credit
        # what we can fund over a typical siege (~DEF_SIEGE_DAYS) — not just
        # income. HQ HP is a renewable buffer (an upgrade refills it to full), so
        # out-training a wave while tanking HP beats stripping farms (which kills
        # the income that pays for the very upgrades that refill the HQ).
        fundable = (S.gold + work_income * DEF_SIEGE_DAYS) // (TRAIN_COST * DEF_SIEGE_DAYS)
        # In a rush emergency don't let integer flooring zero the stream: at an
        # L1 economy 0.9 trains/day floors to 0, the sim then proves "no stream
        # -> dead" and the bank sits unspent while the wave lands (0702_15 (13)).
        # Round to nearest instead — execution clamps to real gold each turn.
        if hq_rush_commit and fundable == 0 and 2 * (S.gold + work_income * DEF_SIEGE_DAYS) >= TRAIN_COST * DEF_SIEGE_DAYS:
            fundable = 1
        sustain = max(0, min(train_cap, fundable))
        # Before the opening finishes (HQ still below DEF_MIN_HQ_FOR_RECALL) DON'T
        # strip farmers to defend: the starting garrison + turret + a home-trained
        # body handle a realistic early poke, and keeping the economy intact is
        # what actually gets the HQ teched up (recalling here just death-spirals
        # income → can't afford the very upgrade that would make us safe).
        allow_recall = hq.level >= DEF_MIN_HQ_FOR_RECALL and not DEF_TRAIN_ONLY
        pool_for_plan = pool if allow_recall else []
        # CHIP GUARD: late game the tiebreak is literally current HQ HP, so the
        # solve must prevent ANY siege point, not just destruction — feed it 1hp
        # so a single point of overkill reads as death and gets defended against
        # (defenders spawn same-day; late-game gold funds it easily).
        solve_hp = 1 if (CHIP_GUARD_TURN > 0 and turn >= CHIP_GUARD_TURN) else hq.hp
        recall_targets, train_defense, needs_stream, holds = plan_hq_defense(
            solve_hp, hq.turret(), home, pool_for_plan, attackers, train_cap, spawn_hp,
            sustain, settle=not hq_rush_commit)
        # L1-RUSH OVERRIDE (0702_15 ladder: two 5-6-body rushes killed the L1 HQ
        # on day 13/20 while both workers farmed one hop away). The recall lock
        # above protects the opening economy against a POKE, but an L1 HQ trains
        # 1 body/day — against a committed rush the train-only plan is provably
        # lost, and a dead HQ has no economy to protect. Survival outranks the
        # lock: re-plan with the real pool, still recalling only the nearest
        # workers the solve actually needs.
        if not holds and not allow_recall and pool and not DEF_TRAIN_ONLY:
            recall_targets, train_defense, needs_stream, holds = plan_hq_defense(
                solve_hp, hq.turret(), home, pool, attackers, train_cap, spawn_hp,
                sustain, settle=not hq_rush_commit)
        # EXECUTE the stream the sim credited: if survival depends on training
        # `sustain`/day, actually train it THIS turn (see plan_hq_defense doc —
        # otherwise every turn is day 0 of a fresh plan and the stream never
        # materialises; the bank stays full and the HQ falls).
        if needs_stream:
            train_defense = max(train_defense, sustain)
        # DEFENSIVE UPGRADE (v2.36, see DEF_UPGRADE): the solve accepted
        # provably-lost stands at L1 (10hp, cap 1) with 600g banked — a
        # level-up is a same-day FULL HEAL + turret/spawn buff (rule-
        # verified). When the best current-level plan does not hold,
        # evaluate the upgraded stand; survival outranks every freeze.
        if (DEF_UPGRADE > 0 and not holds
                and hq.level < HQ_MAX_LEVEL
                and hq.region not in enemy_regions
                and S.gold >= hq.upgrade_cost()):
            _nl = hq.level + 1
            _pool2 = (pool if (not allow_recall and not DEF_TRAIN_ONLY)
                      else pool_for_plan)
            _nfund = ((S.gold - hq.upgrade_cost()
                       + work_income * DEF_SIEGE_DAYS)
                      // (TRAIN_COST * DEF_SIEGE_DAYS))
            _nsus = max(0, min(HQ_LEVELS[_nl].train_cap, _nfund))
            _nhp = (1 if (CHIP_GUARD_TURN > 0 and turn >= CHIP_GUARD_TURN)
                    else HQ_LEVELS[_nl].hp)
            _r2, _t2, _ns2, _h2 = plan_hq_defense(
                _nhp, HQ_LEVELS[_nl].turret, home, _pool2, attackers,
                HQ_LEVELS[_nl].train_cap, HQ_LEVELS[_nl].warrior_hp, _nsus,
                settle=not hq_rush_commit)
            if _h2:
                def_upgrade = True
                recall_targets, train_defense, needs_stream, holds = \
                    _r2, _t2, _ns2, _h2
                if needs_stream:
                    train_defense = max(train_defense, _nsus)
    # how many to KEEP stationed at the HQ. Only when the survival solve is
    # ACTIVELY defending (it recalled workers or ordered defensive trains) do we
    # pin the whole home force (the sim assumed those defenders stay); otherwise
    # hold just a token MIN_GARRISON so everyone else farms and expands. Gating on
    # "any enemy in our half" instead feeds back into pinning the entire army at
    # the HQ forever whenever the opponent parks a single probe nearby.
    active_defense = bool(recall_targets) or train_defense > 0
    home_now = sum(1 for w in my_at.get(hq.region, []) if w.state is WState.STATIONARY)
    # In the fixed opening we send EVERY worker to claim/work bases (max economy),
    # holding a standing garrison only when actively defending; post-opening keep
    # the usual token MIN_GARRISON at the HQ.
    garrison_hold = ((home_now + len(recall_targets)) if active_defense
                     else (0 if opening else MIN_GARRISON))

    # ---- target strongholds, in two expansion tiers (nearest-first) -------------
    #  * OPENING tier = strongholds strictly closer to us (dmy < dop): unambiguously
    #    ours, claimed during the fixed opening (HQ L1) before HQ L2.
    #  * CONTEST tier = the border (dmy == dop) + still-NEUTRAL enemy-side
    #    strongholds we can WIN THE RACE to (our nearest source reaches it no later
    #    than the enemy's) — claimed after HQ L2, before HQ L3. This grabs the 50%
    #    line and contested middle to grow income AND deny the enemy, while the
    #    race guard avoids wasting 300 gold + a worker on a base we'd lose.
    open_c: list[tuple[int, int]] = []
    for s in M.strongholds:
        dmy, dop = P.dist_my[s], P.dist_opp[s]
        if dmy < 0:
            continue
        b = S.find_building(s)
        if b is not None and b.side is not my:        # enemy owns it -> not a target
            continue
        if dop < 0 or dmy < dop:                       # strictly ours
            open_c.append((dmy, s))
    open_c.sort()
    opening_targets = [s for _, s in open_c][:MAX_BASES]

    hovering = False
    if opening:
        target_strongholds = opening_targets
        # SMALL-MAP HOVER WATCH (v2.34, see HOVER_WATCH): claim nothing for
        # the first turns — the starting bodies stay uncommitted spares, so
        # the opponent's FIRST base meets a ready deny squad on a short
        # march. Latched off on their first base / rush tells / timeout.
        if HOVER_WATCH > 0 and not getattr(S, "hover_done", False):
            _hd = P.march_days(hq.region, M.opp_hq)
            if (_hd >= P.UNREACH or _hd > HOVER_DIST
                    or enemy_bases > 0 or rush_flag or mass_signal
                    or turn > HOVER_WATCH):
                S.hover_done = True
                # ended BY THEIR FIRST BASE -> pounce FIRST, claim after:
                # resumed claims were stealing the squad (launch T21, not
                # T8-12); hold the claim resume until the deny dispatches.
                if enemy_bases > 0 and not rush_flag and not mass_signal:
                    S.hover_pounce = True
            else:
                hovering = True
                target_strongholds = []
        if getattr(S, "hover_pounce", False) and opening:
            if S.raid_watch or turn > HOVER_WATCH + 6 or rush_flag:
                S.hover_pounce = False       # squad committed (or bail out)
            else:
                hovering = True              # keep the JIT squad floor too
                target_strongholds = []
        # CONDITIONAL OPENING (v2.33): beyond the OPENING_CORE nearest
        # claims, expansion waits for the SAFE certification — the opponent
        # built >=2 bases too (a boomer can't punish booming), or from
        # OPENING_PROFILE_TURN we hold army parity. Latched once true so a
        # flicker never strands walking builders. The 0708_15 killers were
        # readable exactly this way; the unconditional opening handed them
        # 3-9 claims before ARMY_PIVOT could arm.
        if OPENING_CORE >= 0:
            if not hasattr(S, "open_expanded"):
                S.open_expanded = False
            if not S.open_expanded and (
                    enemy_bases >= 2
                    or (turn >= OPENING_PROFILE_TURN
                        and enemy_army <= len(my_warriors))):
                S.open_expanded = True
            if not S.open_expanded:
                # slice the CURRENT list, not opening_targets — the hover
                # watch above may have emptied it, and re-assigning from
                # opening_targets silently clobbered the hover (claims went
                # through at hv1, the squad never formed, launches sat T21)
                target_strongholds = target_strongholds[:OPENING_CORE]
    else:
        contest_c: list[tuple[int, int]] = []
        for s in M.strongholds:
            dmy, dop = P.dist_my[s], P.dist_opp[s]
            if dmy < 0 or (dop >= 0 and dmy < dop):    # unreachable or already-opening tier
                continue
            b = S.find_building(s)
            if b is not None:
                if b.side is my:                       # our border/enemy-side base -> keep
                    contest_c.append((dmy, s))
                continue                               # enemy's -> skip
            # neutral border / enemy-side: claim only if we win the race to it
            e_md = min([P.march_days(w.region, s) for w in enemy_warriors]
                       + [P.march_days(M.opp_hq, s)])
            my_md = min([P.march_days(w.region, s) for w in my_warriors]
                        + [P.march_days(hq.region, s)])
            if my_md <= e_md:
                contest_c.append((dmy, s))
        contest_c.sort()
        target_strongholds = (opening_targets + [s for _, s in contest_c])[:MAX_BASES]
    # ARMY-BOT PROFILE PIVOT (0708_15, rank 177: 7/8 losses = L1 army bots
    # razing us while our HQ never left L1 because the opening kept feeding
    # 300g claims). Their TRAIN record is exact: an army >= ours built on
    # <= ARMY_PIVOT+2 bases means gold->soldiers, not workers — every NEW
    # claim of ours is their food. Shrink the target list to what is already
    # committed: bases_all_done flips, the L2/L3 fund starts while income
    # still exists (post-strangle it never can — 600g = ~37 days of strangled
    # net), and PRESS/converge fight with the bank instead.
    army_pivot = (ARMY_PIVOT > 0
                  and enemy_bases <= ARMY_PIVOT + 2
                  and enemy_army >= max(ARMY_PIVOT_MIN,
                                        len(my_warriors) + 1))
    if army_pivot:
        target_strongholds = [r for r in target_strongholds
                              if S.find_building(r) is not None
                              or present(r) > 0 or moving_to.get(r, 0) > 0]
    if early_defense_posture:
        # Do not keep feeding fresh 300g claims into an unread early fight.
        # Already-committed builders may finish; new greedy claims wait.
        target_strongholds = [r for r in target_strongholds
                              if S.find_building(r) is not None
                              or present(r) > 0 or moving_to.get(r, 0) > 0]
    n_bases = sum(1 for b in my_buildings if b.type is BType.BASE)

    # ======================== UPGRADES / ECONOMY ========================
    upgraded: set[int] = set()

    def do_upgrade(r: int, cost: int) -> None:
        nonlocal budget
        a.upgrades.append(r); upgraded.add(r); budget -= cost

    # DEFENSIVE UPGRADE purchase (flag set by the survival solve above):
    # survival outranks every freeze/reserve/gate — buy it before anything
    # else touches the budget. Requires a friendly body at the HQ (referee
    # legality) — the garrison/worker is normally there.
    if (def_upgrade and hq.region not in upgraded
            and present(hq.region) > 0 and hq.region not in enemy_regions
            and budget >= hq.upgrade_cost()):
        do_upgrade(hq.region, hq.upgrade_cost())

    # EXPANSION-FIRST gate: the HQ does NOT tech until EVERY active target base is
    # claimed. In the opening (HQ L1) that's the strictly-ours tier -> HQ L2; after
    # HQ L2 the target set also holds the contested border/enemy-side bases, so the
    # HQ stays L2 until those are claimed too -> then HQ L3 and onward. This is the
    # user's plan: claim ours -> HQ L2 -> claim the 50%/enemy-side -> HQ L3 -> ...
    bases_all_done = all(S.find_building(s) is not None for s in target_strongholds)
    # TECH-GATE SAFETY VALVES (ladder (19): one permanently-contested target held
    # this gate shut for 200 days — we finished HQ L1 with 8,203 unspent gold and
    # lost the HP tiebreak to an L4). A target an enemy warrior is squatting on
    # doesn't count against the gate (building there is illegal anyway) — and
    # neither does a hot/REBUILD_GUARDed one (we won't build there either, so it
    # must not hold the tech fund hostage while a strangler camps it), and past
    # TECH_GATE_DEADLINE the gate opens no matter what.
    allow_hq_tech = (turn >= TECH_GATE_DEADLINE
                     or all(S.find_building(s) is not None
                            for s in target_strongholds
                            if s not in enemy_regions and s not in hot_regions))
    if early_defense_posture and not hq_survival_mode:
        allow_hq_tech = False

    # PRESSURE / TECH-URGENCY posture: under persistent contact (a real force in
    # our half — a single deep scout doesn't count unless it is AT the HQ) or
    # simply late in the game, HQ tech outranks base-income spending — HQ tech
    # IS defence (+5 max HP, +turret, +train cap, +spawn HP) and current HP
    # decides the turn-limit tiebreak. The 0701 stall losses ((5),(10),(22),g8)
    # all read: enemy pressures mid-game, our gold drains into base rebuilds
    # + army matching, we sit at L3-20hp while they finish L4/L5 behind the
    # pressure and win 25/30-vs-20 at turn 200.
    pressured = (not opening) and (enemy_in_half >= 2
                                   or (enemy_in_half >= 1 and under_threat))
    # CERTIFIED TECH RACE / STALL DETECTOR (0703 sample 8: mutual raid grind,
    # both sides stalled at L4 25-25 while our income could have bought the
    # 3600 by ~T160 — the small reactive spends never let it accumulate). All
    # inputs are certified, not guessed: their tech level is a public UPGRADE
    # event, their income is exact (every enemy position is visible), and
    # S.opp_gold is a one-sided UPPER bound — so their_eta below is a hard
    # LOWER bound on when they can reach max HQ (every unobserved spend of
    # theirs only pushes it later). If our own ringfenced savings provably
    # finish first with margin, commit: RINGFENCE the economy (base spends and
    # raider minting pause below) and treat tech as urgent. 30 vs 25 decides
    # exactly these stalled games.
    race_mode = False
    if (TECH_RACE_TURN > 0 and not opening and turn >= TECH_RACE_TURN
            and hq.level < min(HQ_TARGET_LEVEL, hq.max_level())):
        _ohb = S.find_building(M.opp_hq)
        if _ohb is not None and _ohb.side is not my and _ohb.level < HQ_MAX_LEVEL:
            their_need = sum(HQ_LEVELS[l].upgrade_cost
                             for l in range(_ohb.level + 1, HQ_MAX_LEVEL + 1)
                             ) - S.opp_gold
            their_eta = (turn if their_need <= 0 else
                         turn + (their_need + max(1, S.opp_income) - 1)
                         // max(1, S.opp_income))
            our_need = sum(HQ_LEVELS[l].upgrade_cost
                           for l in range(hq.level + 1,
                                          min(HQ_TARGET_LEVEL, hq.max_level()) + 1)
                           ) - S.gold
            our_eta = (turn if our_need <= 0 else
                       turn + (our_need + max(1, net) - 1) // max(1, net))
            race_mode = (our_eta <= TECH_RACE_DEADLINE
                         and our_eta + TECH_RACE_MARGIN <= their_eta)
    tech_urgent = (allow_hq_tech and not opening
                   and hq.level < min(HQ_TARGET_LEVEL, hq.max_level())
                   and (pressured or race_mode or turn >= TECH_URGENT_TURN
                        # STARVED + AGGRESSED (v2.14 game 8 residue: the L4
                        # fund only armed at T110, the raid mint spent the
                        # T55-110 window, and 1679 < 2400 at game end): a poor
                        # economy under proven aggression saves from the tech
                        # deadline on — tech is its only ladder out.
                        or (aggro >= AGGRO_ARM
                            and net * TECH_STARVE_DAYS < hq.upgrade_cost())))
    tech_reserve = hq.upgrade_cost() if tech_urgent else 0

    # (A) HQ HP management: upgrading refills HP to the new max; at max level an
    #     UPGRADE is the 1000g repair. Repair when threatened, when badly
    #     chipped, and ALWAYS from HEAL_FINAL_TURN on — the turn-limit tiebreak
    #     is literally current HQ HP (five of the twenty 0701 ladder games ended
    #     30-vs-30; a single unanswered chip decides those).
    if buildable(hq.region) and not opening:
        if under_threat and hq.level < min(HQ_TARGET_LEVEL, hq.max_level()) \
                and budget >= hq.upgrade_cost():
            do_upgrade(hq.region, hq.upgrade_cost())
        elif (hq.level >= hq.max_level() and hq.hp < hq.current_hp()
              and (under_threat or turn >= HEAL_FINAL_TURN
                   or hq.current_hp() - hq.hp >= 10)
              and budget >= hq.heal_cost()):
            do_upgrade(hq.region, hq.heal_cost())

    # claim every active target stronghold (no MIN_BASES anti-sprawl cap — the
    # expansion-first plan deliberately grabs the whole target set before teching).
    allowed = target_strongholds
    # ECONOMY REBOOT (0706_21 game (4): first base razed d13 by a doorstep camp
    # -> 120-day freeze: the strangle/rush spend gates froze every rebuild
    # while PRESS trickle-trained the bank back to ~125g forever; income stayed
    # capped at 15/day — HQ L1 work_cap is 1 — and the game was unrecoverable
    # long before the T136 kill). With ZERO bases there is no economy left for
    # the war ringfence to protect: the bank's only job is restarting income.
    # While the survival solve reads safe, rebuild THROUGH the freezes —
    # escorted (builder + guard, both held at the site, same protocol as
    # twice-razed sites) so the 300g isn't fed to the same stack again;
    # hot_regions and the raze-memory distance test still veto suicidal sites.
    reboot_mode = (n_bases == 0 and sum(_raz.values()) >= 1
                   and turn <= BASE_SPEND_CUTOFF
                   and train_defense == 0 and not recall_targets)
    # base spending is frozen while a rush is inbound (every coin -> defenders),
    # near a harasser (hot_regions: the 300-600g + worker just feed them), and
    # after BASE_SPEND_CUTOFF (payback can't recoup before turn 200).
    base_spend_ok = (((not rush_commit) and turn <= BASE_SPEND_CUTOFF
                      and not race_mode     # race ringfence: savings -> tech
                      and not strangle_mode   # war ringfence: bank -> bodies
                      and not army_pivot)   # army-bot pivot: claims are food
                     or reboot_mode)

    # (1) build bases where a builder is already standing (among allowed targets)
    for r in allowed:
        if r in upgraded or not buildable(r):
            continue
        if not (base_spend_ok or counter_expand_ok(r)) \
                or r in hot_regions or not rebuild_ok(r):
            continue
        # ESCORT rule (replaces v2.10's deadlocking parity gate): a site we
        # already lost TWICE only rebuilds with a second body standing guard —
        # the guard is dispatched below and both are held at the site above.
        # Every REBOOT rebuild (n_bases 0) is escorted too: it is our last 300g.
        if (_raz.get(r, 0) >= 2 or reboot_mode) and present(r) < 2:
            continue
        if S.find_building(r) is None and budget >= BASE_LEVELS[1].cost:
            do_upgrade(r, BASE_LEVELS[1].cost)

    # (2) reserve gold for bases whose builder is walking/waiting
    build_reserve = 0
    for r in allowed:
        if not (base_spend_ok or counter_expand_ok(r)):
            continue
        if (r not in upgraded and r not in hot_regions and rebuild_ok(r)
                and S.find_building(r) is None
                and (present(r) > 0 or moving_to.get(r, 0) > 0)):
            build_reserve += BASE_LEVELS[1].cost

    def afford(c: int) -> bool:
        # BASE spending must not eat the tech fund (tech_reserve)
        return budget - build_reserve - tech_reserve >= c

    def afford_hq(c: int) -> bool:
        # the tech fund itself only waits for committed base builds
        return budget - build_reserve >= c

    # the "2 bases before HQ tech" opener guard becomes a DEADLOCK in a grind
    # where razed bases can't be re-held (v2.12 sample-8 probe: bases razed ->
    # rebuild guarded -> tech gated on bases -> HQ stuck at L1 for 200 days).
    # Under armed aggression past the tech deadline, tech anyway: L2/L3 turret
    # + train cap + HP is exactly what a besieged low-base economy needs.
    have_min_bases = (n_bases >= min(MIN_BASES_BEFORE_HQ, len(target_strongholds))
                      or (turn >= TECH_GATE_DEADLINE and aggro >= AGGRO_ARM)
                      # ZERO bases under proven aggression: don't hold the
                      # defensive tech hostage to an expansion that is being
                      # actively denied (0706_21 (4): L1 for 138 days) — L2's
                      # turret/train-cap/work-cap IS the way back onto the map.
                      or (n_bases == 0 and aggro >= AGGRO_ARM))

    def upgrade_bases_to(target_level: int) -> None:
        """Upgrade owned bases (nearest-first = safest) up to `target_level`,
        each gated by afford(); a base blocked by an enemy in its region is
        skipped (upgrading there would be a WA), as is one a harasser sits
        next to (hot_regions — it would be sieged right back down)."""
        for r in allowed:
            if r in upgraded or not buildable(r) or r in hot_regions:
                continue
            b = S.find_building(r)
            if (b is not None and b.side is my and b.type is BType.BASE
                    and b.level < min(target_level, b.max_level())
                    and afford(b.upgrade_cost())):
                do_upgrade(r, b.upgrade_cost())

    def hq_upto(target_level: int) -> None:
        if (have_min_bases and hq.region not in upgraded and buildable(hq.region)
                and hq.level < min(target_level, hq.max_level())
                and afford_hq(hq.upgrade_cost())):
            do_upgrade(hq.region, hq.upgrade_cost())

    # Post-opening macro spends gold in strict phase order (user's plan):
    # (3) SAFETY   — rush the HQ to its defensive level first (HP20/turret2/train2)
    if allow_hq_tech:
        hq_upto(HQ_DEFENSIVE_LEVEL)
    # (3b) TECH-URGENT — under pressure (or late), the WIN-CON tech comes BEFORE
    #      base income: see `tech_urgent` above. afford() keeps holding the
    #      tech_reserve so bases/army can't nibble the 2400/3600 savings.
    if tech_urgent:
        hq_upto(HQ_TARGET_LEVEL)
    # (4) INCOME   — bring every base to the efficient BASE_ECON_LEVEL (L2). This
    #     is the cheapest income in the game and it comes BEFORE maxing the HQ.
    if hq.level >= HQ_DEFENSIVE_LEVEL and base_spend_ok:
        upgrade_bases_to(BASE_ECON_LEVEL)
    # (5) WIN-CON  — tech the HQ toward max: HP (L5=30) wins the turn-limit
    #     tiebreak, train_cap (army production) and turret power the finish/defence.
    if allow_hq_tech:
        hq_upto(HQ_TARGET_LEVEL)
    # NOTE: bases are intentionally capped at BASE_ECON_LEVEL (L2). A base L2->L3
    # costs 1000 gold for the same +1 work_cap (+15/day) as the 600-gold L1->L2 —
    # a 67-day payback that, arriving only after the HQ is maxed (~turn 140+),
    # cannot recoup before turn 200, and its extra HP/turret are moot since we
    # defend the HQ, not bases. So surplus gold goes to the ARMY (econ_saturated
    # below), which is useful for defence, an opportunistic strike, or staging.

    # ======================== TRAIN ========================
    # Train only enough bodies to fill current work slots + garrison (+ a small
    # army) so leftover gold goes into building upgrades; once the economy is
    # fully upgraded, lift the cap and mass an army. Never train into starvation.
    work_capacity = sum(b.work_cap() for b in my_buildings)
    econ_saturated = (
        hq.level >= min(HQ_TARGET_LEVEL, hq.max_level())
        and all(b.level >= min(BASE_ECON_LEVEL, b.max_level())
                for b in my_buildings if b.type is BType.BASE)
        and all(S.find_building(s) is not None for s in target_strongholds)
    )
    # Always want enough bodies to match a full enemy commit. Below the HQ's
    # defensive level we cap training at that defensive minimum and reserve the
    # surplus for the HQ; once teched, fill the economy and (when saturated) mass.
    # Always develop a baseline economy/army (independent of the enemy, so we
    # don't mirror a weak opponent into a stall), and scale up to match a full
    # enemy commit if theirs is bigger.
    # match only the enemy force ACTUALLY IN OUR HALF (not their whole army) so a
    # boomer's distant masses don't drain our gold away from HQ tech.
    army_buffer = ARMY_BUFFER_MAX if econ_saturated else ARMY_BUFFER_MIN
    if opening:
        # FIXED OPENING: just-in-time worker economy, NO standing garrison. Want
        # one body per sub-half base to build-then-work it; grow the target only
        # as bases get committed (built / worker present or walking) + one spare,
        # so we never pre-train idle garrison (the wasteful early trains the play
        # logs showed). The train loop paces it 1/turn, net- and build_reserve-
        # gated, so a body is minted only when 300 for its base stays affordable.
        committed_bases = sum(1 for s in target_strongholds
                              if S.find_building(s) is not None
                              or present(s) > 0 or moving_to.get(s, 0) > 0)
        # want one body per committed base PLUS two spare (one to staff the HQ
        # slot, one free to march to the next stronghold) so expansion never
        # stalls with every worker pinned to a building; capped at a full
        # complement (one per target + HQ). Grows as bases commit -> just-in-time.
        desired_warriors = min(len(target_strongholds) + 1, committed_bases + 2)
        # EARLY DENY bodies on top of the worker complement: without the bump
        # the JIT cap leaves 0-2 spares and the raid sim refuses every kill.
        if early_deny and EARLY_RAID_TRAIN > 0 and not hovering:
            desired_warriors += EARLY_RAID_TRAIN
        # (while hovering the 5-body floor below IS the squad — stacking the
        # deny bump on top kept the trainer eating every coin to T20 and the
        # move budget never formed: launches slid T18->T21)
        # HOVER posture: no targets means the JIT would want 1 body and never
        # train — keep the watch force ready instead (1 HQ worker + the
        # 4-body pounce squad the user specified).
        if hovering:
            desired_warriors = max(desired_warriors, 5)
        if early_defense_posture and not hovering:
            threat_bodies = max(len(local_threat_ids), len(hq_direct_ids),
                                RUSH_COMMIT_BODIES if threat_intent == "UNKNOWN_EARLY_THREAT" else 0)
            desired_warriors = max(desired_warriors,
                                   min(work_capacity + MIN_GARRISON,
                                       max(RUSH_COMMIT_BODIES, threat_bodies + 2)))
        min_army = desired_warriors
        hq_reserve = 0                                     # bases first; no HQ save yet
    else:
        min_army = work_capacity + MIN_GARRISON           # staff + token garrison
        # mint the raider squads on top of staff+garrison once raiding is live —
        # pre-saturation the army_buffer is 0, so without this the surplus the
        # raid dispatch draws from would never exist mid-game (exactly when the
        # enemy's outer bases are up and worth razing). Still paced by the same
        # net/feedable/hq_reserve gates below: raiders never starve us or delay
        # HQ tech, they only consume leftover budget.
        raid_buffer = (RAID_SQUAD
                       if (RAID_SQUAD > 0 and hq.level >= RAID_MIN_HQ
                           and enemy_bases > 0 and not race_mode)
                       else 0)
        desired_warriors = min_army + army_buffer + raid_buffer
        # once we hold that minimum army, reserve the next HQ level (up to the
        # defensive level) so the HQ techs up instead of pouring gold into army.
        hq_reserve = (hq.upgrade_cost()
                      if (have_min_bases and hq.region not in upgraded
                          and hq.level < HQ_DEFENSIVE_LEVEL
                          and len(my_warriors) >= min_army)
                      else 0)
    cap = HQ_LEVELS[hq.level].train_cap
    # economy trains respect BOTH the pre-L3 hq_reserve and the tech-urgent
    # reserve (defensive trains below still ignore both — survival first).
    avail = budget - build_reserve - max(hq_reserve, tech_reserve)
    if (len(my_warriors) < desired_warriors
            and (net > TRAIN_NET_MARGIN or hovering or early_defense_posture)
            and avail >= TRAIN_COST):
        feedable = (net - TRAIN_NET_MARGIN) // UPKEEP_PER_WARRIOR
        # the HOVER watch force is bought from the STARTING BANK by design
        # (claims are deliberately delayed, so income stays flat 15/day and
        # the net gate would choke the squad at ~4 bodies -> launches slid
        # to T21): the 500g start covers the 5-body floor + upkeep easily.
        if hovering:
            feedable = max(feedable, desired_warriors - len(my_warriors))
        if early_defense_posture:
            feedable = max(feedable, desired_warriors - len(my_warriors))
        short = desired_warriors - len(my_warriors)
        n = min(cap, avail // TRAIN_COST, feedable, short)
        # OPENING JIT TIMING (user-observed leak): the build_reserve protects
        # COMMITTED builds, but the worker minted for the NEXT (uncommitted)
        # stronghold has no reserve yet — trained at low gold, it arrives and
        # stands on the site for days waiting for the 300g to accumulate,
        # ticking upkeep. Train only when the projected gold AT ITS ARRIVAL
        # (income accrues while it walks) covers every pending build plus its
        # own; when income during the walk suffices, the early start is kept.
        # ...PEACETIME ONLY: under any rush tell a body is a same-day defender
        # and recall stock even if its base must wait (8-seed probe: applying
        # the delay under rush dropped spar_rush from ~88% to 62%).
        # ...and not while an early deny target stands: inside the payback
        # window a 120g body that razes their 300g base outranks starting our
        # own next 300g claim a few days sooner (the whole point of the meta).
        if (n > 0 and opening and not rush_flag and not in_half_enemies
                and not early_defense_posture
                and not early_deny):
            _nxt = next((r for r in target_strongholds
                         if S.find_building(r) is None and present(r) == 0
                         and moving_to.get(r, 0) == 0), None)
            if _nxt is not None:
                _d = P.march_days(hq.region, _nxt)
                if (_d < P.UNREACH
                        and budget - TRAIN_COST + max(0, net) * _d
                        < build_reserve + BASE_LEVELS[1].cost):
                    n = 0
        if n > 0:
            a.train_n = n
            budget -= n * TRAIN_COST

    # raid trains (priority knob): with RAID_BEFORE_TECH the raider squad is
    # minted even while the tech_reserve starves economy trains — mid-game is
    # when the enemy's outer bases are worth razing, and waiting for post-L5
    # surplus made every raid land after the tiebreak was already decided
    # (probe: all raids fired T136+, converted nothing). Still respects the
    # build_reserve and the feed cap: raiders never starve us.
    if (RAID_BEFORE_TECH and not opening and raid_buffer > 0
            and not race_mode
            and len(my_warriors) < desired_warriors and net > TRAIN_NET_MARGIN
            and a.train_n < cap):
        feedable = (net - TRAIN_NET_MARGIN) // UPKEEP_PER_WARRIOR
        # ...but the tech fund outranks raider MINTING while the survival solve
        # is idle (ghost-r8 probe vs the real sample 8: raid trains minted 30+
        # bodies over 100 quiet turns, raids DISPATCHED ZERO times, and the
        # 2400g L4 fund never accumulated — the L3 tiebreak loss in one line).
        # An active defense (stream running) keeps the old bodies-first rule.
        n = min(cap - a.train_n,
                (budget - build_reserve
                 - (tech_reserve
                   if (train_defense == 0
                       and net * TECH_STARVE_DAYS < tech_reserve)
                   else 0)) // TRAIN_COST,
                feedable, desired_warriors - len(my_warriors) - a.train_n)
        if n > 0:
            a.train_n += n
            budget -= n * TRAIN_COST

    # defensive trains OUTRANK economy: the survival solve may demand bodies the
    # economy cap wouldn't fund. Train up to train_defense from the full budget
    # (ignoring build/hq reserves AND the feed cap — a defender that later starves
    # still absorbs attacks for days, and surviving beats staying solvent).
    if train_defense > a.train_n:
        # HEAL RESERVE (sample-4 loss, 23-30): the chip-guard-era defensive
        # stream drained the bank 1400->0 over a 10-day wave, so when a 7-point
        # chip finally landed the 1000g repair was unaffordable — a heal would
        # have made it 30-30. While the HQ is maxed and still at COMFORTABLE
        # hp (the wave threatens chips, not destruction), keep the heal money;
        # a genuinely lethal wave (hp already low) may spend everything.
        heal_keep = (HQ_HEAL_COST
                     if (CHIP_GUARD_TURN > 0 and turn >= CHIP_GUARD_TURN
                         and hq.level >= hq.max_level()
                         and 2 * hq.hp >= hq.current_hp())
                     else 0)
        extra = min(train_defense - a.train_n, cap - a.train_n,
                    max(0, budget - heal_keep) // TRAIN_COST)
        if extra > 0:
            a.train_n += extra
            budget -= extra * TRAIN_COST

    # PRESSURE-MATCH trains (weekend strangle class): enemy bodies in our half
    # are a territorial war, and the economy gate (`net > TRAIN_NET_MARGIN`) is
    # unpassable exactly when they've killed our income — the death spiral that
    # lost 26/45 weekend games (we trained 9-21 bodies vs their 23-58). Train
    # toward work slots + garrison + one body per intruder (counting MOVERS too:
    # a rotating stack spends half its days in transit), funded from the BANK
    # like defensive trains (ignore the feed cap: a cleared squatter zone re-
    # earns its own upkeep). Respects committed builds only: the L1 economy's
    # L2 fund (hq_reserve, 600g = 5 bodies) starved this block in the g10
    # ghost probe — under an active strangle, bodies NOW outrank tech; the
    # normal phases resume the tech saving the turn the half is clear.
    # ... and the wave detector arms it EARLY: a marching stack still outside
    # our half (heading for the HQ or for a serial base hunt — indistinguishable
    # and irrelevant, both need bodies) starts the minting before first contact.
    # Train cap bounds production/day, so these approach-days ARE the army.
    _press_ids = ({w.id for w in in_half_enemies}
                  | {w.id for w in approaching}
                  | local_threat_ids | hq_direct_ids | stack_ids)
    if (PRESS_MIN > 0 and a.train_n < cap
            and (len(in_half_enemies) >= PRESS_MIN or wave_detected
                 or stack_alarm or early_defense_posture)):
        press_want = work_capacity + MIN_GARRISON + len(_press_ids)
        # GRIND vs STRANGLE discriminator (v2.12 sample-8 loss, 20-25): under
        # a permanent poke-grind that never actually threatens the HQ (the
        # survival solve idle: no recalls, no stream — local s8 probe: 2 of
        # 200 turns), PRESS eating the L2/L3 fund every turn locked the HQ at
        # L1-L3 for 200 days while the opponent out-teched us 2:1 on income.
        # When the solve reads SAFE, the cheap defensive tech fund survives —
        # tech through a grind; a REAL kill-threat (solve active) still gets
        # every coin turned into bodies (the g10 strangle behavior, unchanged).
        avail_press = budget - build_reserve - (max(hq_reserve, tech_reserve)
                                                if (train_defense == 0
                                                    and not recall_targets
                                                    and not stack_alarm)
                                                else 0)
        extra = min(cap - a.train_n, avail_press // TRAIN_COST,
                    press_want - len(my_warriors) - a.train_n)
        if extra > 0:
            a.train_n += extra
            budget -= extra * TRAIN_COST

    # STRIKE FUND (counter-rush pre-training, the user's key point: the strike
    # force must EXIST before the window opens). While strangled but STABLE —
    # defence target met, no recalls — keep minting bodies beyond press_want:
    # the strangler's army is a full map's march from its own 10-20hp HQ, and
    # the launch check below (assess_attack) prices their return ETAs + their
    # gold-capped reinforcement. Until the race certifies, these bodies are
    # extra garrison/intercept material — never wasted.
    # ...but only from the defensive HQ level up: an L1 strike (hp-4 bodies,
    # train cap 1) never certifies, and on the s8-map grind the fund sat at
    # L1 minting press_want+8 bodies forever — eating the very 600g whose L2
    # would have made the strike (and everything else) actually work.
    if (STRIKE_FORCE > 0 and strangle_mode and not recall_targets
            and not opening and hq.level >= HQ_DEFENSIVE_LEVEL
            and len(my_warriors) >= _press_want_early
            and a.train_n < cap):
        want = _press_want_early + STRIKE_FORCE
        _sf_avail = budget - build_reserve - (max(hq_reserve, tech_reserve)
                                              if train_defense == 0 else 0)
        extra = min(cap - a.train_n, _sf_avail // TRAIN_COST,
                    want - len(my_warriors) - a.train_n)
        if extra > 0:
            a.train_n += extra
            budget -= extra * TRAIN_COST

    # ARMY PARITY FLOOR v2 (sample-8 loss; v2.10's v1 regressed sample 7 and
    # was pulled): answer their PRODUCTION — army counts are exact from TRAIN
    # records — but ONLY for proven aggressors (aggro gate: sample 7's passive
    # army never arms this) and never past solvency: feed-capped AND a hard
    # upkeep ceiling (standing upkeep ≤ PARITY_UPKEEP_PCT% of work income —
    # v2.10 died of upkeep 4930 on 9360 income), and it respects the tech/HQ
    # funds (a STANDING posture must not eat the L4/L5 savings; acute defense
    # keeps its own ungated paths above).
    if (ARMY_PARITY_MIN > 0 and not opening and aggro >= AGGRO_ARM
            and enemy_army >= ARMY_PARITY_MIN and a.train_n < cap):
        want_mil = (enemy_army * ARMY_PARITY_FRAC) // 100
        feedable = (net - TRAIN_NET_MARGIN) // UPKEEP_PER_WARRIOR
        up_room = ((work_income * PARITY_UPKEEP_PCT) // 100
                   - UPKEEP_PER_WARRIOR * (len(my_warriors) + a.train_n))
        avail_par = budget - build_reserve - max(hq_reserve, tech_reserve)
        # LAST STAND (13th chronic-vs-acute site, 0708_10 pool: losses
        # 1(7)/1(8)/1(11) sat on banked gold with ZERO trains for 40-73
        # turns while a rotating stack executed their economy — the solvency
        # caps above read 0 exactly then: feedable needs net income, up_room
        # needs work income, and both die with the bases. Solvency is a
        # PEACETIME constraint; once the economy is DEAD (n_bases<=1, raze
        # recent) the bank is the war chest — hunger costs 1hp/day, death
        # costs the game. Only the escorted-reboot 300g is kept back: it is
        # the recovery path the trained bodies exist to escort.
        # Deliberately NOT triggered by strangle_mode/stack_alarm alone
        # (first cut was, and lost the mirror A/B 4W3D5L: a HEALTHY economy
        # in an ordinary raid exchange over-trained into upkeep bleed — the
        # v2.10 lesson; mid-collapse at nb>=2 the caps aren't binding yet,
        # so the terminal phase is the only real gate site).
        if (WAR_FUNDING > 0 and n_bases <= 1
                and _last_raze is not None
                and turn - _last_raze <= STRANGLE_DECAY):
            feedable = up_room = 1 << 30
            avail_par = budget - build_reserve - BASE_LEVELS[1].cost
        extra = min(cap - a.train_n, avail_par // TRAIN_COST, feedable,
                    up_room // UPKEEP_PER_WARRIOR,
                    want_mil - len(my_warriors) - a.train_n)
        if extra > 0:
            a.train_n += extra
            budget -= extra * TRAIN_COST

    # LATE-GAME GOLD DUMP (draw-breaker): with the HQ maxed, bank above
    # GOLD_DUMP_BANK (heal money + buffer) is an unbuilt army — 0703 sample 5
    # ended a dominant 30-30 draw with 12,138g idle. Convert it to bodies at
    # full cap; they feed the blocker relay and the FLOOD_TURN overkill.
    # AUDIT FIND (idle bank): the dump used to wait for a maxed HQ, so a game
    # stalled at L3/L4 with income that provably cannot buy the next level by
    # ~T190 idled its bank to the end. If tech is unreachable, bodies now.
    _tech_unreachable = (hq.level < min(HQ_TARGET_LEVEL, hq.max_level())
                         and turn >= GOLD_DUMP_TURN
                         and budget + max(0, net) * max(0, 190 - turn)
                         < hq.upgrade_cost())
    if (GOLD_DUMP_TURN > 0 and turn >= GOLD_DUMP_TURN and not opening
            and (hq.level >= min(HQ_TARGET_LEVEL, hq.max_level())
                 or _tech_unreachable)
            and a.train_n < cap):
        extra = min(cap - a.train_n, max(0, budget - GOLD_DUMP_BANK) // TRAIN_COST)
        if extra > 0:
            a.train_n += extra
            budget -= extra * TRAIN_COST

    # ======================== MOVES ========================
    assigned: set[WarriorId] = set()
    moved_now: set[WarriorId] = set()

    def move(w: Warrior, dest: int) -> bool:
        nonlocal budget
        if w.id in assigned or w.id in moved_now or w.region == dest:
            return False
        b = S.find_building(dest)
        cost = 0 if (b is not None and b.side is my) else MOVE_COST
        if budget < cost:
            return False
        a.moves.append((w.id, dest))
        assigned.add(w.id)
        moved_now.add(w.id)
        budget -= cost
        return True

    def idle() -> list[Warrior]:
        return [w for w in my_warriors if w.state is WState.STATIONARY and w.id not in assigned]

    # ECONOMICAL DEFENSE: recall ONLY the workers the survival solve selected
    # (nearest-first), not the whole economy. Everyone else keeps farming below.
    if recall_targets:
        for w in recall_targets:
            move(w, hq.region)
        if _DEBUG:
            sys.stderr.write(
                f"T{turn} DEF ehalf{enemy_in_half} recall{len(recall_targets)} "
                f"trdef{train_defense} hq{hq.level}/{hq.hp} oppg~{S.opp_gold} "
                f"w{len(my_warriors)}\n"
            )
            sys.stderr.flush()

    # BASE DEFENSE CONVERGENCE (spar_defender module, default OFF — see the
    # BASE_DEF_CONVERGE tunable). For each own base with an inbound threat:
    # if staff+turret provably fall, pull the MINIMAL nearby set the siege
    # sim proves flips the fight; a provably lost base still gets nobody.
    # Converge moves onto our own building cost 0g. Staff at a threatened
    # base is held (the raiders must clear it, not chase it away).
    converged = 0
    stage_r = -1          # forward-staging destination (set in disposition)
    # Convergence is disabled only for true HQ survival, not for every stack
    # whose HQ-distance shrank. A base-raiding main stack is handled here if the
    # classifier named the threatened base; the sim still refuses lost stands.
    if (BASE_DEF_CONVERGE > 0 and not hq_survival_mode
            and not recall_targets):
        for _bb in my_buildings:
            if _bb.type is BType.HQ:
                continue                     # the HQ has its own solve
            _thr = [w for w in enemy_warriors
                    if 0 <= P.march_days(w.region, _bb.region)
                    <= BASE_DEF_HORIZON
                    and ((_tb := S.find_building(w.region)) is None
                         or _tb.side is my)]
            _local_named = _bb.region in local_defense_regions
            if not _thr:
                continue
            if (not _local_named and (len(_thr) > RAID_SQUAD
                    or 2 * len(_thr) > max(1, enemy_army))):
                continue                     # detachment test: see above
            _atk = [(P.march_days(w.region, _bb.region), w.hp) for w in _thr]
            _staff = [w for w in my_at.get(_bb.region, [])
                      if w.state is WState.STATIONARY]
            _dfd = [(0, w.hp) for w in _staff]
            for w in _staff:
                assigned.add(w.id)           # pinned to the defence
            if simulate_hq_siege(_bb.hp, _bb.turret(), _dfd, _atk):
                continue                     # staff+turret already hold
            _cands = [w for w in my_warriors
                      if w.state is WState.STATIONARY
                      and w.id not in assigned
                      and w.region not in enemy_regions
                      and 0 <= P.march_days(w.region, _bb.region)
                      <= BASE_DEF_RADIUS]
            _cands.sort(key=lambda w: (P.march_days(w.region, _bb.region),
                                       -w.hp))
            _take: list = []
            _ok = False
            for w in _cands:
                _take.append(w)
                _dfd2 = _dfd + [(P.march_days(x.region, _bb.region), x.hp)
                                for x in _take]
                if simulate_hq_siege(_bb.hp, _bb.turret(), _dfd2, _atk):
                    _ok = True
                    break
            if _ok:
                for w in _take:
                    if move(w, _bb.region):
                        converged += 1

    # ---- draw-breaker posture (computed early so the holds below can pin the
    # staged relay): blocker relay keeps ONE denier inside the enemy HQ region
    # (their UPGRADE = L5 tech AND 1000g heal becomes illegal) with the rest of
    # BLOCK_SQUAD staged in an adjacent zone OUT of turret range, stepping in
    # as deniers die. From FLOOD_TURN the relay becomes a full overkill flood.
    # Deny windows — keyed to the ENEMY's state, not ours (0703 backup probe:
    # our old our-L4 gate opened AFTER their L5 had already landed, so the
    # relay burned bodies denying nothing):
    #  * deny_tech: their HQ is one level short of max AND their gold (upper
    #    bound, S.opp_gold) approaches the upgrade cost — the only window in
    #    which squatting their region actually blocks the tiebreak level.
    #  * from FLOOD_TURN: heal denial (every chipped point must stay chipped).
    # (7th chronic-vs-acute site: the maintenance train stream kept home_safe
    # false through entire games — in ALL 24 weekend draws the flood/blockers
    # dealt 0 HQ siege, because vs loiterer-heavy opponents the stream never
    # rests. Acute danger = recalls; the flood's own home-sufficiency hold and
    # the solve's same-day trains are the real safety.)
    home_safe = not recall_targets
    block_ok = (BLOCK_SQUAD > 0 and not opening and home_safe
                and hq.level >= HQ_DEFENSIVE_LEVEL)
    opp_hq_b0 = S.find_building(M.opp_hq)
    opp_penult = (opp_hq_b0 is not None and opp_hq_b0.side is not my
                  and opp_hq_b0.level == HQ_MAX_LEVEL - 1)
    # STAGE the squad the moment their L4 lands (marching from home after the
    # funding signal arrives ~5 days too late — 0703 backup probe: signal
    # @T151, their L5 @T156, our deniers still 10 hops out). Stepping IN (the
    # body burn) waits for the funding signal: S.opp_gold is an upper bound,
    # so >= 3/4 of the L5 cost means the purchase may be imminent.
    block_stage_on = block_ok and opp_penult
    deny_tech = (opp_penult
                 and S.opp_gold >= (HQ_LEVELS[HQ_MAX_LEVEL].upgrade_cost * 3) // 4)
    # DOMINANCE-EARLY FLOOD (30-30 dissection: 7 of 10 mutual-L5 draws were
    # dominant — army 85v56, +6k income — but the T180 flood arrived T190+
    # against a healed L5; a crushing material lead should cash in earlier).
    _dominant = (FLOOD_DOM_EARLY > 0
                 and len(my_warriors) >= 2 * max(1, enemy_army)
                 and work_income * 10 >= max(1, S.opp_income) * 12)
    flood = (FLOOD_TURN > 0 and block_ok
             and turn >= FLOOD_TURN - (FLOOD_DOM_EARLY if _dominant else 0))
    block_on = block_ok and (deny_tech or flood or block_stage_on)
    block_staging = -1
    if block_on:
        stage_cands = []
        for v in M.adj[M.opp_hq]:
            bb = S.find_building(v)
            if bb is None or bb.side is my:
                stage_cands.append(v)
        if stage_cands:
            block_staging = min(stage_cands,
                                key=lambda v: P.hops_my[v] if P.hops_my[v] >= 0
                                else (1 << 30))

    # 0) a STATIONARY body standing on a live enemy BASE is mid-raze: combat
    # and siege are positional, so the only way it stops sieging is another
    # module re-tasking it — the opening expand loop stole a whole T8 deny
    # squad off a 4hp base (probe ss7: squad scattered to strongholds, income
    # zero, starved to w0 by T24). Hold it until the base falls. Enemy-HQ
    # siegers stay un-held (flood/attack own them; retire's wounded rotation
    # keeps its about-to-fall exception).
    for w in my_warriors:
        if (w.state is WState.STATIONARY and w.id not in assigned
                and (_eb := S.find_building(w.region)) is not None
                and _eb.side is not my and _eb.type is BType.BASE):
            assigned.add(w.id)

    # 1) hold workers on buildings (HQ + bases) up to work_cap — WOUNDED first
    # (rotation: a low-hp body is a full-rate worker but a dead combatant, so
    # it takes the work slot and frees a fresh body for the army)
    for b in my_buildings:
        here = [w for w in my_at.get(b.region, []) if w.state is WState.STATIONARY and w.id not in assigned]
        here.sort(key=lambda w: w.hp)
        for w in here[:b.work_cap()]:
            assigned.add(w.id)
    # hold the defensive garrison at the HQ (garrison_hold was computed above)
    held_at_hq = sum(1 for w in my_at.get(hq.region, []) if w.id in assigned)
    extra_hq = [w for w in my_at.get(hq.region, [])
                if w.state is WState.STATIONARY and w.id not in assigned]
    extra_hq.sort(key=lambda w: -w.hp)      # garrison value = absorbable HP
    garrison_ids: list[WarriorId] = []      # releasable to INTERCEPT squads: an
    for w in extra_hq[:max(0, garrison_hold - held_at_hq)]:
        assigned.add(w.id)                  # idle token garrison is over-insurance
        garrison_ids.append(w.id)           # while the survival solve reads safe
    # hold a builder already standing on an unbuilt target stronghold — but only
    # if we would actually BUILD there (spend allowed, not hot/rebuild-guarded):
    # holding a body on a frozen site parks it next to the strangler stack as
    # dead weight (ghost g10: 3 of 7 bodies stood on frozen targets all game
    # while the intercept pool stayed empty)
    for r in target_strongholds:
        if (S.find_building(r) is None and base_spend_ok
                and r not in hot_regions and rebuild_ok(r)):
            _hold_n = (2 if (_raz.get(r, 0) >= 2 or reboot_mode)
                       else 1)                          # keep the escort too
            for w in [w for w in my_at.get(r, [])
                      if w.state is WState.STATIONARY and w.id not in assigned][:_hold_n]:
                assigned.add(w.id)
    # WOUNDED ROTATION: a forward body at RETIRE_HP or less is released from
    # its siege hold to walk home and farm (the next tick kills it anyway and
    # it absorbs almost nothing, but it works at full rate) — UNLESS pinned
    # (enemy in its zone: leaving is impossible) or the building it stands on
    # is about to fall (hp <= bodies on site ~= one more day of siege: stay
    # for the kill). Released bodies flow into the normal staffing/army logic.
    def retire(w: Warrior, b: "Building", n_here: int) -> bool:
        return (RETIRE_HP > 0 and w.hp <= RETIRE_HP
                and w.region not in enemy_regions
                and b.hp > n_here)

    # keep attackers that reached the enemy HQ sieging it (never recall them)
    opp_hq_b = S.find_building(M.opp_hq)
    hq_here = [w for w in my_at.get(M.opp_hq, []) if w.state is WState.STATIONARY]
    for w in hq_here:
        if opp_hq_b is not None and retire(w, opp_hq_b, len(hq_here)):
            continue
        assigned.add(w.id)
    # keep raiders standing on a still-alive enemy BASE sieging it — their
    # presence also makes the enemy's UPGRADE there (repair!) illegal. When the
    # base falls it leaves S.buildings, so they rejoin the surplus pool and the
    # raid dispatch below re-aims them at the next target automatically.
    for b in S.buildings:
        if b.side is not my and b.type is BType.BASE:
            b_here = [w for w in my_at.get(b.region, [])
                      if w.state is WState.STATIONARY]
            for w in b_here:
                if retire(w, b, len(b_here)):
                    continue
                assigned.add(w.id)
    # bodies sharing a zone with enemy warriors are PINNED (the referee ignores
    # their moves until the zone clears) and ARE the fight in progress — never
    # re-order them: a move order burns 10g/turn doing nothing and, the day the
    # zone clears, walks the victor off the objective it just won.
    for w in my_warriors:
        if w.state is WState.STATIONARY and w.region in enemy_regions:
            assigned.add(w.id)
    # hold the staged blocker relay / massing flood next to the enemy HQ
    # (the flood release below explicitly discards these holds)
    if block_on and block_staging >= 0:
        for w in my_at.get(block_staging, []):
            if w.state is WState.STATIONARY:
                assigned.add(w.id)

    # BASE DEFENCE (minimal): EVACUATE the staff of a base that is about to
    # be overrun — enemies ADJACENT (1 march-day: they arrive and pin next
    # day) whom the staff + turret provably cannot repel. The building dies
    # either way (300g); the 120g/body staff + retrain time is the saveable
    # half. Deliberately NO guard dispatch and NO wide threat radius: we
    # cannot read which base an enemy is heading for, and every wider variant
    # (radius 4, radius 2 + guards) mis-fired on passing traffic/expansion
    # workers and lost 8/8 A/B games to a no-defence twin on pure churn.
    evac_regions: set[int] = set()
    if BASE_EVAC_DAYS > 0:
        for b in my_buildings:
            if b.type is not BType.BASE:
                continue
            r = b.region
            atk = [(P.march_days(w.region, r), w.hp) for w in enemy_warriors
                   if P.march_days(w.region, r) <= BASE_EVAC_DAYS]
            if not atk:
                continue
            staff0 = [w for w in my_at.get(r, []) if w.state is WState.STATIONARY]
            if not staff0:
                continue
            staff = [(0, w.hp) for w in staff0]
            if simulate_hq_siege(b.hp, b.turret(), staff, atk, settle=False):
                continue                       # staff + turret repel: stay put
            evac_regions.add(r)
            moved_ids = {mid for mid, _ in a.moves}
            for w in staff0:
                # discard releases a work-HOLD; a warrior that already got a
                # MOVE this turn (e.g. an HQ-defence recall) must NOT be
                # ordered twice — duplicate MOVE is an instant WA
                if w.id in moved_ids or w.region in enemy_regions:
                    continue
                assigned.discard(w.id)
                move(w, hq.region)

    # 2) fill understaffed slots on existing (built) bases — immediate income
    for b in my_buildings:
        if b.region in evac_regions:
            continue                  # never feed replacements to a lost base
        need = b.work_cap() - present(b.region) - moving_to.get(b.region, 0)
        dist_b = None
        while need > 0:
            pool = idle()
            if not pool:
                break
            if dist_b is None:
                dist_b = P.dist_from(b.region)
            pool.sort(key=lambda w: (dist_b[w.region] if dist_b[w.region] >= 0 else (1 << 30), w.hp))
            if not move(pool[0], b.region):
                break
            need -= 1

    # 3) expand: dispatch builders to new strongholds. While still expanding (any
    #    target base unclaimed) send EVERY spare worker (nearest-first) to grab them
    #    fast; once fully expanded, cap concurrency so gold isn't spread thin.
    build_concurrency = MAX_CONCURRENT_BUILDERS if bases_all_done else len(target_strongholds)
    committed = sum(1 for r in target_strongholds
                    if S.find_building(r) is None and (present(r) > 0 or moving_to.get(r, 0) > 0))
    for r in (target_strongholds if base_spend_ok
              else [r for r in target_strongholds if counter_expand_ok(r)]):
        if committed >= build_concurrency:
            break
        if S.find_building(r) is not None or r in hot_regions or not rebuild_ok(r):
            continue
        # twice-razed sites get a builder AND an escort (build waits for both);
        # so does every reboot rebuild (n_bases 0: it is our last 300g)
        if present(r) + moving_to.get(r, 0) >= (2 if (_raz.get(r, 0) >= 2
                                                      or reboot_mode) else 1):
            continue
        # dispatch eagerly (the move only costs MOVE_COST); build_reserve saves
        # the 300 gold so the base goes up when the builder arrives
        pool = idle()
        if not pool:
            break
        dist_r = P.dist_from(r)
        pool.sort(key=lambda w: dist_r[w.region] if dist_r[w.region] >= 0 else (1 << 30))
        if move(pool[0], r):
            committed += 1

    # 4) army disposition: garrison the HQ by default. Launch an OPPORTUNISTIC
    #    ALL-IN only when a verified race (assess_attack) says our concentrated
    #    surplus destroys the enemy HQ strictly before their worst-case counter
    #    could destroy ours — SURPLUS only (idle() excludes workers, the garrison,
    #    builders, defensive recalls and siegers), massed at the HQ, corridor
    #    clear, and confirmed for ATTACK_HYSTERESIS consecutive turns (a launched
    #    wave cannot be recalled, so we never bet the game on one noisy turn).
    army = idle()
    army_n0 = len(army)
    siegers = [w for w in my_at.get(M.opp_hq, []) if w.state is WState.STATIONARY]
    our_kd = their_kd = None
    launch = False
    # Note: no `under_threat` guard — the race's own their_kill_day home-safety
    # check (honest post-detach defenders vs the enemy's worst-case counter) is
    # the correct gate; `under_threat` would just redundantly veto safe openings
    # where an enemy probe is near but our home still provably holds.
    # STRIKE MODE — the counter-rush window vs a committed strangler: home is
    # stable (defence target met, no recalls; the permanent maintenance train
    # stream must NOT veto — it silenced this exactly like it silenced raids)
    # and the pre-trained STRIKE_FORCE is massed. assess_attack itself prices
    # their return ETAs, so "their army is deep in our half" IS the opening.
    strike_mode = (STRIKE_FORCE > 0 and strangle_mode
                   and len(my_warriors) >= _press_want_early)
    massed = army and all(w.region == hq.region for w in army)
    # in strike mode "massed" relaxes to "STRIKE_MIN bodies AT the HQ": with
    # intercept survivors trickling home, all-of-army-massed almost never
    # holds — and assess_attack prices every body's individual march ETA, so
    # a converging launch is modelled exactly, not optimistically.
    at_hq_n = sum(1 for w in army if w.region == hq.region)
    strike_gate = (strike_mode and at_hq_n + len(siegers)
                   >= min(STRIKE_MIN, ATTACK_ARMY_MIN))
    # (6th chronic-vs-acute site, from the 30-30 draw dissection: 7 of 10
    # mutual-L5 weekend draws were DOMINANT — e.g. army 85v56, +6k income,
    # L5 51 turns earlier — yet the maintenance train stream vetoed the
    # certified kill race all game. Acute danger = recalls; the race's own
    # worst-case home check is the real safety gate.)
    if (ENABLE_ATTACK and not recall_targets
            and ((massed and len(army) + len(siegers) >= ATTACK_ARMY_MIN)
                 or strike_gate)):
        commit, our_kd, their_kd, _A = assess_attack(
            S, M, P, turn, hq, my_warriors, enemy_warriors, army + siegers, work_income)
        S.attack_streak = S.attack_streak + 1 if commit else 0
        launch = S.attack_streak >= ATTACK_HYSTERESIS
    else:
        S.attack_streak = 0

    raid_sent = 0
    clear_sent = 0
    if launch:
        for w in army:
            move(w, M.opp_hq)
    else:
        # ENDGAME OVERKILL FLOOD (draw-breaker): from FLOOD_TURN surplus
        # bodies MASS at the staging zone and step into the enemy HQ region
        # TOGETHER once FLOOD_MASS gathered (arrival sync = the attack counts
        # spike past the defenders' HP so overkill lands; a trickle dies
        # one-by-one to same-day defender spawns). The denier keeps their heal
        # illegal, so every chipped point is permanent — and one point decides
        # a 30-30 tiebreak. Near the turn limit whatever gathered goes anyway.
        if flood:
            # HOME SUFFICIENCY (sample-4 loss): their whole army is a potential
            # counter-flood (theirs was 24 bodies at T185 and won the mutual
            # exchange 7-0). siege = attackers − Σ defender hp, so keep enough
            # HP at the HQ to ZERO their maximum wave before flooding the rest.
            home_hp = sum(w.hp for w in my_at.get(hq.region, [])
                          if w.state is WState.STATIONARY and w.id in assigned)
            need_hp = enemy_army + 2 - home_hp
            for w in sorted((w for w in army if w.region == hq.region),
                            key=lambda x: -x.hp):
                if need_hp <= 0:
                    break
                assigned.add(w.id)
                need_hp -= w.hp
            army = [w for w in army if w.id not in assigned]
            stagers_f = ([w for w in my_at.get(block_staging, [])
                          if w.state is WState.STATIONARY]
                         if block_staging >= 0 else [])
            release = (len(stagers_f) >= FLOOD_MASS or turn >= 192
                       or block_staging < 0)
            if release:
                moved_ids = {mid for mid, _ in a.moves}
                for w in stagers_f:
                    if w.id in moved_ids or w.region in enemy_regions:
                        continue
                    assigned.discard(w.id)
                    move(w, M.opp_hq)
            dest = M.opp_hq if release else block_staging
            for w in army:
                move(w, dest)
            army = [w for w in army if w.id not in assigned]

        # STANDING BLOCKER — RELAY (draw-breaker): ONE denier inside the enemy
        # HQ region (their L4->L5 tech AND 1000g heal turn illegal) + the rest
        # of BLOCK_SQUAD staged next door out of turret range, promoted in as
        # deniers die (continuous denial at ~1/3 the body burn of parking the
        # whole squad under turret fire — 0703 sample 5: the enemy's L5 landed
        # @171 through our old gappy coverage and turned a dominant game into a
        # 30-30 draw). No intruder veto: the defence solve is the safety gate,
        # and letting two loitering enemy raiders cancel our tech-denial was
        # priority inversion.
        if block_on and not flood:
            deniers = len(siegers) + sum(1 for w in my_warriors
                                         if w.state is WState.MOVING
                                         and w.target == M.opp_hq)
            stagers = ([w for w in my_at.get(block_staging, [])
                        if w.state is WState.STATIONARY]
                       if block_staging >= 0 else [])
            n_staged = len(stagers) + sum(1 for w in my_warriors
                                          if w.state is WState.MOVING
                                          and w.target == block_staging)
            stagers.sort(key=lambda w: -w.hp)
            # ENDGAME DENIER REINFORCEMENT (0706 game 4: the relay held their
            # L5 from ~T151 to T198, then ONE gap day let the 3600g through ->
            # 30-30 instead of 30-25. Upgrade legality re-checks every morning,
            # so late game — when the gold dump mints surplus bodies with no
            # better use — thicken the in-region crew and the staging pipeline
            # so a same-day double-death cannot open a purchase window.)
            _blk_late = BLOCK_LATE_TURN > 0 and turn >= BLOCK_LATE_TURN
            _want_den = ((BLOCK_DENIERS_LATE if _blk_late else BLOCK_DENIERS)
                         if deny_tech else 0)
            while deniers < _want_den:
                # promote a stager (arrives next day) else send a body direct
                sent = False
                while stagers:
                    w = stagers.pop(0)
                    assigned.discard(w.id)       # release the staging hold
                    if move(w, M.opp_hq):
                        sent = True
                        n_staged -= 1
                        break
                if not sent:
                    army.sort(key=lambda w: (P.hops_opp[w.region]
                                             if P.hops_opp[w.region] >= 0
                                             else (1 << 30), -w.hp))
                    for w in army:
                        if move(w, M.opp_hq):
                            sent = True
                            break
                deniers += 1
                if not sent:
                    break
            need = (BLOCK_SQUAD_LATE if _blk_late else BLOCK_SQUAD) - deniers - n_staged
            if need > 0:
                dest = block_staging if block_staging >= 0 else M.opp_hq
                army.sort(key=lambda w: (P.hops_opp[w.region]
                                         if P.hops_opp[w.region] >= 0
                                         else (1 << 30), -w.hp))
                for w in army:
                    if need <= 0:
                        break
                    if move(w, dest):
                        need -= 1
            army = [w for w in army if w.id not in assigned]

        # INTERCEPT / CLEAR SQUADS (0704-0706 weekend pool: 26/45 losses were
        # stationary enemy stacks rotating through our half razing bases
        # serially — 3,899 base siege taken — while our army idled at home).
        # The raid module pointed INWARD: send the smallest squad the referee-
        # exact combat sim proves WINS the zone fight against a squatter group
        # (their converging friends priced in, CLEAR_DEF_RADIUS). Arrival pins
        # both sides, combat is automatic; the engaged-hold above keeps the
        # squad on the fight, and when the zone clears the survivors rejoin the
        # pool (and the region drops out of hot_regions, unfreezing the
        # rebuild). Squatters ON an enemy building are the raid dispatch's job;
        # our own HQ region belongs to the survival solve. Same no-drip rule as
        # raids: a committed fight is topped up only for our OWN building
        # (staff already fighting there), never for a field chase.
        # gate on ACUTE home danger only (recalls ordered / solve not holding):
        # under a permanent low-grade strangle the solve keeps a maintenance
        # train stream running (train_defense >= 1 most turns), and gating on
        # it — as raids do — silenced the intercept for entire games.
        local_clear_ok = threat_intent in (
            "BASE_RAID", "WORKER_HARASS", "UNKNOWN_EARLY_THREAT")
        if (CLEAR_SQUAD > 0 and (not opening or local_clear_ok) and not recall_targets
                and (squatters or mid_claimers)):
            sq_at: dict[int, list[Warrior]] = {}
            for w in squatters + mid_claimers:
                _sb = S.find_building(w.region)
                if w.region == hq.region or (_sb is not None and _sb.side is not my):
                    continue
                sq_at.setdefault(w.region, []).append(w)
            # the token garrison beyond one body is candidate material too: an
            # idle garrison is over-insurance while the solve reads safe (it
            # re-proves safety and can train same-day defenders every turn),
            # and under a strangle the L1-cap economy can't mint a squad from
            # PRESS trains alone before the next base falls.
            # Gate on RECALLS only, not the maintenance stream (12th chronic-
            # vs-acute site, 0706_21 (7) rematch: train_defense=1 hedge turns
            # pinned all 8 home bodies every turn while a 5-stack razed 5 bases
            # 2-4 hops out — CLEAR could never prove a win with the pool
            # zeroed; the stream re-mints home cover same-day anyway).
            _gar_pool = [w for w in my_at.get(hq.region, [])
                         if w.id in garrison_ids][1:] if not recall_targets else []

            def clear_plan(r: int, group: list) -> Optional[tuple[int, list]]:
                onsite = [w for w in my_at.get(r, [])
                          if w.state is WState.STATIONARY]
                inbound = [w for w in my_warriors
                           if w.state is WState.MOVING and w.target == r]
                committed = ([(0, w.hp) for w in onsite]
                             + [(P.march_days(w.region, r), w.hp)
                                for w in inbound])
                _moved_now = {mid for mid, _ in a.moves}
                cand = ([w for w in army if w.id not in assigned
                         and w.region not in enemy_regions]
                        + [w for w in _gar_pool if w.id not in _moved_now])
                cand.sort(key=lambda w: (P.march_days(w.region, r), -w.hp))
                cand = cand[:max(0, CLEAR_SQUAD - len(committed))]
                gids = {w.id for w in group}
                dfd = [(0, w.hp) for w in group]
                for w in enemy_warriors:
                    if w.id in gids:
                        continue
                    if P.march_days(w.region, r) <= CLEAR_DEF_RADIUS:
                        dfd.append((P.march_days(w.region, r), w.hp))
                own_b = S.find_building(r)
                fresh_only = not (own_b is not None and own_b.side is my)
                if committed and fresh_only:
                    sizes = [0]
                else:
                    sizes = list(range(0 if committed else 1, len(cand) + 1))
                for n in sizes:
                    atk = committed + [(P.march_days(w.region, r), w.hp)
                                       for w in cand[:n]]
                    if simulate_hq_siege(1, 0, dfd, atk, settle=False,
                                         return_kill_day=True) is not None:
                        return (n, cand[:n])
                return None

            # value order: squatters ON our building / a target stronghold
            # first (they strangle income), then cheapest kill, then nearest
            scored_c = []
            for r, group in sq_at.items():
                plan = clear_plan(r, group)
                if plan is not None:
                    onmy = (S.find_building(r) is not None
                            or r in target_strongholds)
                    hops_r = P.hops_my[r]
                    scored_c.append((0 if onmy else 1, plan[0],
                                     hops_r if hops_r >= 0 else (1 << 30),
                                     r, group))
            scored_c.sort(key=lambda s: (s[0], s[1], s[2]))
            csq = 0
            for _, _, _, r, group in scored_c:
                if csq >= CLEAR_MAX_SQUADS:
                    break
                plan = clear_plan(r, group)   # re-plan: earlier squads took bodies
                if plan is None:
                    continue
                for w in plan[1]:
                    assigned.discard(w.id)    # release a garrison hold (a body
                    if move(w, r):            # that already MOVEd this turn was
                        clear_sent += 1       # filtered out via a.moves above)
                csq += 1
            army = [w for w in army if w.id not in assigned]

        # RAIDER SQUADS (0702_15 meta: high-rated bots razed 296 of our bases,
        # we razed 0; a razed base costs its owner ~600g+ in sunk cost + rebuild
        # + lost income while the raiders' marginal cost is move orders). Send
        # RAID_SQUAD surplus bodies at the nearest enemy bases, but only when
        # the referee-exact siege sim confirms the squad KILLS the base against
        # its turret + every enemy body near enough to contest — otherwise try
        # a softer target. Squads already committed (standing on the base or en
        # route) are topped up, not duplicated; when a base falls its raiders
        # rejoin the surplus pool and this dispatch re-aims them.
        # Two raid tiers: the NORMAL tier (cross-map detachment) keeps the
        # conservative gates (HQ >= RAID_MIN_HQ, no defensive train stream);
        # the INVASIVE tier — enemy bases in OUR half or on the midline, the
        # 0704-0706 top-tier's wounded-claimer expansion — is home defence and
        # only waits for acute danger (recalls) to pass: it may fire from
        # RAID_MIN_HQ_INVASIVE and alongside a maintenance train stream.
        # AGGRESSION: cross-map raids gate on ACUTE danger only (recalls) —
        # the maintenance train stream silenced them for whole games under a
        # standing low-grade pressure, the same chronic-vs-acute bug family as
        # intercepts/attack/press/raid-mint (5th site). The home solve stays
        # the safety net: raids draw only from surplus it does not hold.
        raid_full = hq.level >= RAID_MIN_HQ

        def _invasive(r: int) -> bool:
            return (RAID_MIN_HQ_INVASIVE > 0
                    and hq.level >= RAID_MIN_HQ_INVASIVE
                    and P.hops_my[r] >= 0
                    and (P.hops_opp[r] < 0 or P.hops_my[r] <= P.hops_opp[r]))

        # EARLY DENY (v2.25): the opening runs this same dispatch against the
        # early_deny tier only — one squad, sim-proven kills, silent under a
        # rush tell or active recalls. Razing their first base inside its
        # ~20-day payback window is the top-ladder meta this answers.
        early_mode = opening and bool(early_deny) and not recall_targets
        if (RAID_SQUAD > 0 and not recall_targets
                and (early_mode
                     or (not opening
                         and (raid_full or RAID_MIN_HQ_INVASIVE > 0)))):
            def raid_plan(tb) -> Optional[tuple[int, list]]:
                """Smallest reinforcement (0..RAID_SQUAD nearest surplus bodies,
                on top of whoever is already on-site/en-route) that the sim
                proves KILLS base `tb` against its turret + every enemy body
                within RAID_DEF_RADIUS march-days. None = not worth raiding."""
                r = tb.region
                onsite = [w for w in my_at.get(r, [])
                          if w.state is WState.STATIONARY]
                inbound = [w for w in my_warriors
                           if w.state is WState.MOVING and w.target == r]
                committed = ([(0, w.hp) for w in onsite]
                             + [(P.march_days(w.region, r), w.hp) for w in inbound])
                cand = [w for w in army if w.id not in assigned
                        and w.region not in enemy_regions    # pinned can't leave
                        # ETA CAP, TUITION-ARMED (v2.29 backtest): far marches
                        # give the defender reaction time (success median 4
                        # md vs failure median 7) — but an ALWAYS-ON cap lost
                        # 0W/6D/6L to an uncapped twin and dropped spar_boom
                        # to 3W3D (long raids PAY vs non-defending bots). The
                        # cap therefore arms only after this opponent has
                        # eaten a squad (S.raid_fails, tracker above):
                        # backtest keep 35% / refuse 64%, structurally
                        # neutral until the tuition is paid.
                        and (RAID_ETA_CAP <= 0
                             or getattr(S, "raid_fails", 0) == 0
                             or P.march_days(w.region, r) <= RAID_ETA_CAP)]
                # NOTE (v2.28 experiment, REVERTED): extending this pool with
                # the opening's held WORKERS ("starting-squad deny", the top-
                # meta mirror) fixed the launch pace (probe raze T34->T15)
                # but lost 2W/0D/10L to a deny-off twin — the workforce pause
                # loses more than the 300g deny gains, and the raiders feed
                # the opponent's own invasive-raid/squatter counters. Third
                # confirmation of the law in one day (er_experiment 0707,
                # camp, this): the opening workforce is untouchable;
                # aggression comes from true surplus only. The real meta
                # version (hover BEFORE building anything) = a full opening
                # redesign, 본선. (Experiment: pool ext of held workers on our
                # buildings gated by EARLY_RAID_BANK + hold release at
                # dispatch; panel broke too — spar_rush 4/6.)
                cand.sort(key=lambda w: (P.march_days(w.region, r), -w.hp))
                cand = cand[:max(0, RAID_SQUAD - len(committed))]
                # defenders: bodies on/near the target PLUS every enemy standing
                # on the squad's march path — walking into a staffed zone PINS
                # the raiders and forces that fight, so an inner base behind a
                # picket line prices in the whole fight-through (this is what
                # steers squads to raze the enemy's OUTER bases first)
                dfd_map: dict = {}
                for w in enemy_warriors:
                    md = P.march_days(w.region, r)
                    if md <= RAID_DEF_RADIUS:
                        dfd_map[w.id] = (md, w.hp)
                if cand:
                    steps = P.march_path(cand[0].region, r)
                    pz = {z: d for d, z in enumerate(steps[:-1], start=1)}
                    for w in enemy_warriors:
                        d = pz.get(w.region)
                        if d is not None and (w.id not in dfd_map
                                              or d < dfd_map[w.id][0]):
                            dfd_map[w.id] = (d, w.hp)
                dfd = list(dfd_map.values())
                # NEVER drip reinforcements into a raid in progress: piecemeal
                # top-ups arrive staggered and die one by one to a re-staffed
                # defence (seed-1 probe: 60 turns of 1-3-body feeds for one
                # razed base). A committed squad either finishes the job alone
                # or the raid is over; fresh FULL squads only launch at targets
                # with nobody committed yet.
                sizes = [0] if committed else range(1, len(cand) + 1)
                for n in sizes:
                    atk = committed + [(P.march_days(w.region, r), w.hp)
                                       for w in cand[:n]]
                    if simulate_hq_siege(tb.hp, tb.turret(), dfd, atk,
                                         settle=False,
                                         return_kill_day=True) is not None:
                        return (n, cand[:n])
                return None
            # cheapest kill first (fewest bodies), nearest as the tiebreak —
            # a naked L1 two extra hops away beats a staffed L2 next door
            scored = []
            for tb in (b for b in S.buildings
                       if b.side is not my and b.type is BType.BASE):
                if opening:
                    if tb.region not in early_deny:
                        continue             # opening: deny tier only
                elif not raid_full and not _invasive(tb.region):
                    continue                 # invasive tier only right now
                plan = raid_plan(tb)
                if plan is not None:
                    hops = P.hops_my[tb.region]
                    scored.append((plan[0], hops if hops >= 0 else (1 << 30), tb))
            scored.sort(key=lambda s: (s[0], s[1]))
            squads = 0
            max_squads = 1 if opening else RAID_MAX_SQUADS
            for _, _, tb in scored:
                if squads >= max_squads:
                    break
                plan = raid_plan(tb)         # re-plan: earlier squads took bodies
                if plan is None:
                    continue
                if opening and budget < MOVE_COST * len(plan[1]):
                    continue                 # never launch a PARTIAL squad: the
                                             # sim proved n bodies, opening gold
                                             # can be too thin for n move orders
                _launched = set()
                for w in plan[1]:
                    if move(w, tb.region):
                        raid_sent += 1
                        _launched.add(w.id)
                # register the tuition watch at FIRST dispatch (fresh squads
                # only — a committed squad keeps its original watch entry)
                if _launched and tb.region not in S.raid_watch:
                    _mdmax = max((P.march_days(w.region, tb.region)
                                  for w in plan[1]), default=0)
                    _launched |= {w.id for w in my_warriors
                                  if (w.state is WState.MOVING
                                      and w.target == tb.region)
                                  or (w.region == tb.region
                                      and w.state is WState.STATIONARY)}
                    S.raid_watch[tb.region] = (frozenset(_launched), turn,
                                               _mdmax)
                squads += 1

            # RAID ABORT (v2.29): RULE DISCOVERY — re-ordering a MOVING
            # warrior is a WA (testing-tool:910 "warrior already moving"):
            # mid-march recall/redirect is IMPOSSIBLE, commitment is rule-
            # enforced. The only recoverable bodies are ARRIVED survivors
            # standing un-pinned on a target the re-plan can no longer
            # certify (a hopeless turret grind): release their mid-raze
            # hold (CLEAR's release pattern) and walk them home. 2-turn
            # hysteresis so one passing defender doesn't thrash the squad.
            if RAID_ABORT > 0:
                if not hasattr(S, "raid_replan_fail"):
                    S.raid_replan_fail = {}
                for r0 in list(S.raid_watch):
                    b0 = S.find_building(r0)
                    if b0 is None or b0.side is my:
                        S.raid_replan_fail.pop(r0, None)
                        continue
                    if raid_plan(b0) is not None:
                        S.raid_replan_fail.pop(r0, None)
                        continue
                    n0 = S.raid_replan_fail.get(r0, 0) + 1
                    S.raid_replan_fail[r0] = n0
                    if n0 < 2:
                        continue
                    retreated = False
                    for w in my_warriors:
                        if (w.state is WState.STATIONARY
                                and w.region == r0
                                and w.region not in enemy_regions):
                            assigned.discard(w.id)   # release mid-raze hold
                            if move(w, hq.region):
                                retreated = True
                    # an aborted expedition is neither success nor tuition;
                    # keep watching if bodies are still en route (they will
                    # arrive, stand, and be retreated by a later pass)
                    if retreated:
                        S.raid_watch.pop(r0, None)
                        S.raid_replan_fail.pop(r0, None)
            army = [w for w in army if w.id not in assigned]

        # POST-RAZE CAMP hold: leftover squad bodies standing on a recent raze
        # site stay put (up to CAMP_BODIES per site, healthiest first — a
        # camper must survive the field fight vs an escorted rebuilder).
        # Everything above (recalls, blockers/flood, intercepts, new raid
        # squads) already took what it needed from the pool, so only true
        # surplus camps; a rebuilt base on the site re-enters the raid target
        # loop instead (the tracker pruned the camp entry).
        if CAMP_TURNS > 0 and S.camp:
            for r in S.camp:
                here = [w for w in army if w.region == r]
                here.sort(key=lambda w: -w.hp)
                for w in here[:CAMP_BODIES]:
                    assigned.add(w.id)
            army = [w for w in army if w.id not in assigned]

        # FORWARD STAGING (v2.35, see FWD_STAGE): the leftover surplus waits
        # at the forwardmost own base instead of walking home — every module
        # above (recalls, blockers/flood, intercepts, raids) already took
        # what it needed, and next turn their nearest-first selection finds
        # this pool a short march from the enemy's territory.
        if (FWD_STAGE > 0 and not opening and home_safe and army
                and hq.level >= FWD_STAGE_MIN_HQ):
            _fwd = [b for b in my_buildings
                    if b.type is BType.BASE and b.region != hq.region
                    and P.hops_opp[b.region] >= 0]
            if _fwd:
                _sb = min(_fwd, key=lambda b: P.hops_opp[b.region])
                _back = P.march_days(_sb.region, hq.region)
                _eeta = min((P.march_days(w.region, hq.region)
                             for w in enemy_warriors), default=1 << 30)
                if _eeta > _back + FWD_STAGE_SLACK:
                    stage_r = _sb.region
        for w in army:
            _dest = stage_r if stage_r >= 0 else hq.region
            if w.region != _dest:
                move(w, _dest)

    # STYLE ROUTER classify (for NEXT turn): certified public signals only —
    # their army/base counts, HQ level, our aggro score, their presence in our
    # half. 3 consecutive identical reads switch the profile (hysteresis; a
    # None read for 3 turns restores the default). Archetypes = the log-
    # verified 0704-0706 classes the counters were built against.
    _ob = S.find_building(M.opp_hq)
    _olvl = _ob.level if (_ob is not None and _ob.side is not my) else HQ_MAX_LEVEL
    _prof = None
    if turn >= 12:
        if opening and enemy_bases == 0 and enemy_army >= RUSH_MASS_ARMY:
            _prof = "rusher"
        elif aggro >= AGGRO_ARM and _olvl <= 3 and enemy_army >= 8:
            _prof = "strangler"
        elif enemy_bases >= 8 and len(in_half_enemies) <= 1:
            _prof = "megaboomer"
    if _prof == getattr(S, "style_pending", "?"):
        S.style_streak = getattr(S, "style_streak", 0) + 1
    else:
        S.style_pending = _prof
        S.style_streak = 1
    if S.style_streak >= 3:
        S.style_profile = _prof

    if _DEBUG:
        sys.stderr.write(
            f"T{turn} g{S.gold} nb{n_bases} ntgt{len(target_strongholds)} "
            f"w{len(my_warriors)} hq{hq.level} wi{work_income} net{net} "
            f"thr{int(under_threat)} idle{sum(1 for w in my_warriors if w.state is WState.STATIONARY)} "
            f"tr{a.train_n} up{a.upgrades} mv{len(a.moves)} raid{raid_sent} "
            f"er{len(early_deny)} cp{len(S.camp)} rf{S.opp_refeeds} "
            f"rfl{S.raid_fails} cv{converged} ap{int(army_pivot)} "
            f"hv{int(hovering)} fs{int(stage_r >= 0)} du{int(def_upgrade)} "
            f"sq{len(squatters)} ih{len(in_half_enemies)} mc{len(mid_claimers)} "
            f"clr{clear_sent} war{int(strangle_mode)} wv{int(wave_detected)} "
            f"sa{int(stack_alarm)} rb{int(reboot_mode)} "
            f"ti{threat_intent} "
            f"ag{aggro} pf{S.style_profile if hasattr(S, 'style_profile') else None} "
            f"sk{int(strike_mode)} "
            f"army{army_n0} tdef{train_defense} dt{int(deny_tech)} fl{int(flood)} rc{int(race_mode)} og{S.opp_gold} "
            f"ATK strk{S.attack_streak} okd{our_kd} tkd{their_kd} launch{int(launch)}\n"
        )
        sys.stderr.flush()

    return a


# ============================================================================
# SECTION 6 — MAIN LOOP
# ============================================================================
def main() -> None:
    try:
        M, S = parse_init()
        P = Pathing(M)
        # Hook A: map-conditioned tunables from data.bin (small maps need e.g.
        # tighter rush thresholds; timing consts should scale with the diameter)
        apply_map_profile(M.N, M.K, P.hops_my[M.opp_hq])
        while (turn := read_turn_start()) is not None:
            try:
                a = decide(S, M, P, turn)
            except Exception:
                a = Actions()   # strategy bug -> emit a safe empty turn, never miss a turn
            emit(a)
            read_turn_result(S, M, a)
    except SystemExit:
        raise                   # clean FINISH / EOF exit (code 0)
    except Exception:
        pass                    # unexpected failure: exit code 0 rather than a runtime error


if __name__ == "__main__":
    main()

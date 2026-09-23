# laya_controller/bench.py
"""Headless checks for the Laya versions (versions.py).

  read  can the untuned model read our states? Laya's answer vs each version's scripted rules
  play  matches against the Basic bot (full game, goalkeepers on)

    uv run python -m laya_controller.bench read                         # every version
    uv run python -m laya_controller.bench read --versions v2-shots v2-split --confusion
    uv run python -m laya_controller.bench play --mode HOCKEY --contenders shoot rules:v4-shots v4-challenge-focused
"""
import argparse
import collections
import math
import random
import statistics

from rl.core_engine import RocketSoccerLogic
from src.settings import GAME_MODES, HEIGHT
from laya_controller import motor
from laya_controller.controller import LayaController, ask
from laya_controller.features import BALL_R, CAR_R, facts
from laya_controller.versions import VERSIONS


def scatter(engine, rng):
    """A random kickoff: each car on its own half, the ball anywhere in between."""
    engine.agent.x, engine.agent.y = rng.uniform(100, 450), rng.uniform(60, HEIGHT - 60)
    engine.opponent.x, engine.opponent.y = rng.uniform(550, 900), rng.uniform(60, HEIGHT - 60)
    engine.ball.x, engine.ball.y = rng.uniform(150, 850), rng.uniform(60, HEIGHT - 60)


def sample_states(n, seed=0):
    """Realistic states: the v1 rules vs the Basic bot from random kickoffs, every 15th frame."""
    rng, engine, states = random.Random(seed), RocketSoccerLogic(), []
    while len(states) < n:
        engine.reset()
        scatter(engine, rng)
        for frame in range(150):
            f = facts(engine.get_state())
            if frame % 15 == 0:
                states.append(f)
            _, _, done = engine.step(motor.act(motor.rule_tactic(f), f))
            if done:
                break
    return states[:n]


def read(names, n, confusion):
    states = sample_states(n)
    print(f"{n} states from headless play. agrees = Laya's action matches the version's rules;")
    print("majority = what always giving the most common right answer would score.")
    print("balanced = the average hit rate per action - always giving one answer scores 1 / actions.\n")
    print(f"{'version':22} {'agrees':>6} {'majority':>8} {'balanced':>8}  {'Laya picks most':28} {'calls':>5} {'ms p50':>6}")
    for name in names:
        v = VERSIONS[name]
        expected = [v.teacher(f) for f in states]
        majority = collections.Counter(expected).most_common(1)[0][1] / n
        answers = {}  # one call per distinct text
        for f in states:
            text = v.describe(f)
            if text not in answers:
                a, ms = ask(v.questions, text)
                answers[text] = (v.decide(a)[0], ms)
        got = [answers[v.describe(f)][0] for f in states]
        agrees = sum(g == e for g, e in zip(got, expected)) / n
        hit_rates = collections.defaultdict(list)
        for g, e in zip(got, expected):
            hit_rates[e].append(g == e)
        balanced = statistics.mean(statistics.mean(hits) for hits in hit_rates.values())
        top, top_n = collections.Counter(got).most_common(1)[0]
        ms = statistics.median(a[1] for a in answers.values())
        picks = f"{top} ({top_n / n:.0%})"
        print(
            f"{name:22} {agrees:6.2f} {majority:8.2f} {balanced:8.2f}  {picks:28} {len(answers):5} {ms:6.0f}",
            flush=True,
        )
        if confusion:
            pairs = collections.Counter(zip(expected, got))
            actions = list(dict.fromkeys(expected + got))
            print(" " * 24 + "".join(f"{a[:13]:>14}" for a in actions) + "   <- Laya's answer")
            for want in actions:
                if any(pairs[(want, g)] for g in actions):
                    print(f"  rules: {want[:14]:14}" + "".join(f"{pairs[(want, g)]:>14}" for g in actions))
            print()


def drive(contender, f):
    """A scripted contender's move: rules:<version> (its rules), <version>:<action> (that one plan
    all the time, with the version's driving), or a v1 plan name (e.g. shoot)."""
    if contender.startswith("rules:"):
        v = VERSIONS[contender[len("rules:"):]]
        return v.act(v.teacher(f), f)
    if ":" in contender:
        name, action = contender.split(":", 1)
        return VERSIONS[name].act(action, f)
    return motor.act(contender, f)


def play(contender, episodes, seconds, mode="SOCCER", seed=0):
    """First-goal results for `contender` driving Blue vs the Basic bot, from the same random kickoffs.

    Also, each time the car starts touching the ball (a hit): its speed, and whether it had slowed
    down by more than 1.5 in the half second before.
    """
    engine = RocketSoccerLogic()
    engine.max_frames = seconds * 60
    frictions = {"ball_friction": GAME_MODES[mode]["friction_ball"], "car_friction": GAME_MODES[mode]["friction_car"]}
    for car in (engine.agent, engine.opponent, engine.gk1, engine.gk2):
        car.friction = frictions["car_friction"]
    engine.ball.friction = frictions["ball_friction"]
    results, asks, cache_hits, ms = collections.Counter(), 0, 0, []
    hit_speeds, slowed = [], []
    for episode in range(episodes):
        engine.reset()
        scatter(engine, random.Random(seed + episode))
        ctrl = LayaController(contender, sync=True, **frictions) if contender in VERSIONS else None
        scores = engine.score_agent, engine.score_opponent
        obs, done, touching = engine.get_state(), False, False
        car, ball = engine.agent, engine.ball
        recent = collections.deque(maxlen=30)  # speeds over the last half second
        while not done:
            speed = math.hypot(car.vx, car.vy)
            recent.append(speed)
            action = ctrl.predict(obs)[0] if ctrl else drive(contender, {**facts(obs), **frictions})
            obs, _, done = engine.step(action)
            was_touching, touching = touching, math.hypot(ball.x - car.x, ball.y - car.y) <= CAR_R + BALL_R + 0.5
            if touching and not was_touching:
                hit_speeds.append(speed)
                slowed.append(max(recent) - speed > 1.5)
        if engine.score_agent > scores[0]:
            results["win"] += 1
        elif engine.score_opponent > scores[1]:
            results["loss"] += 1
        else:
            results["draw"] += 1
        if ctrl:
            asks, cache_hits, ms = asks + ctrl.asks, cache_hits + ctrl.hits, ms + ctrl.ms
    return results, hit_speeds, slowed, asks, cache_hits, ms


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=("read", "play"))
    parser.add_argument("--versions", nargs="+", default=list(VERSIONS), help="read: which versions")
    parser.add_argument("--states", type=int, default=200, help="read: how many states to test")
    parser.add_argument("--confusion", action="store_true", help="read: show rules vs Laya tables")
    parser.add_argument("--episodes", type=int, default=100, help="play: kickoffs per contender")
    parser.add_argument("--seconds", type=int, default=30, help="play: time limit per kickoff")
    parser.add_argument("--mode", choices=list(GAME_MODES), default="SOCCER", help="play: the game mode's friction")
    parser.add_argument(
        "--contenders", nargs="+",
        default=["shoot", "v3-shots:shoot_straight", "v4-shots:shoot_straight", "rules:v4-shots", "rules:v4-challenge"],
        help="play: a version (Laya drives), rules:<version> (its rules drive), <version>:<action> "
        "(one plan all the time), or a v1 plan such as shoot",
    )
    args = parser.parse_args()

    if args.mode == "read":
        read(args.versions, args.states, args.confusion)
        return
    print(f"{args.episodes} kickoffs each in {args.mode}, first goal within {args.seconds}s, Blue vs the Basic bot.")
    print("noise = typical random swing of wins - losses; smaller differences mean nothing.")
    print("At each hit (the car starts touching the ball): hard = speed 6+ (top 7, 9.8 boosted),")
    print("light = under 2, slowed = lost more than 1.5 speed in the half second before.\n")
    print(
        f"{'contender':26} {'wins':>5} {'losses':>6} {'draws':>5} {'W-L':>5} {'noise':>5} "
        f"{'hits/kick':>9} {'hard':>5} {'light':>5} {'slowed':>6}  {'Laya calls':>10} {'cache hits':>10} {'ms p50':>6}"
    )
    for contender in args.contenders:
        r, hit_speeds, slowed, asks, cache_hits, ms = play(contender, args.episodes, args.seconds, args.mode)
        noise = math.sqrt(r["win"] + r["loss"])
        n = len(hit_speeds)
        hard, light = sum(s >= 6 for s in hit_speeds) / n, sum(s < 2 for s in hit_speeds) / n
        laya = f"{asks:10} {cache_hits:10} {statistics.median(ms):6.0f}" if ms else ""
        print(
            f"{contender:26} {r['win']:5} {r['loss']:6} {r['draw']:5} {r['win'] - r['loss']:+5} {noise:5.0f} "
            f"{n / args.episodes:9.1f} {hard:5.0%} {light:5.0%} {sum(slowed) / n:6.0%}  {laya}",
            flush=True,
        )


if __name__ == "__main__":
    main()

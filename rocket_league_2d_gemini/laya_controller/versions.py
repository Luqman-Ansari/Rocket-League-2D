# laya_controller/versions.py
"""Every Laya setup we try, by name. Pick one in the game menu (LEFT/RIGHT) or in bench.py.

A version never changes once it has results: to try something new, add a new version.
"Read" results are `bench read` (200 game states): how often Laya's answer matches the version's
scripted rules; "balanced" is that averaged per action, so always giving one answer scores
1 / actions. Probe results are the 16 made-up states tried while planning v2. "Play" is
`bench play`: wins - losses in 2400 kickoffs vs the Basic bot in Soccer (noise about +-35), "Hockey"
the same with --mode HOCKEY (noise about +-42). For reference, always shooting straight scores
+69 / Hockey +43 with the v1 driving, +456 / +395 with v3, +436 / +617 with v4, +933 / +1169 with v5.
"""
from dataclasses import dataclass
from functools import partial
from typing import Callable

from laya_controller import motor, prompt


@dataclass(frozen=True)
class Version:
    note: str  # what it tries, and what we found
    questions: dict  # what Laya is asked; all answered in one forward pass
    describe: Callable  # facts -> the state text Laya reads
    decide: Callable  # Laya's answers -> (action, probability)
    teacher: Callable  # facts -> the scripted action: drives while Laya loads, bench.py's reference
    act: Callable  # (action, facts) -> move 0-4 or held keys, for TrainedAICar.apply_ai_action()


def _choice(answers):
    a = answers["decision"]
    return a["choice"], a["probabilities"][a["choice"]]


def _most_likely_yes(answers):
    best = max(answers, key=lambda k: answers[k]["noul"])
    return best, answers[best]["noul"]


def _direction_then_angle(answers):
    move, aim = answers["move"], answers["aim"]
    if move["choice"] == "go_back":
        return "go_back", move["probabilities"]["go_back"]
    return prompt.AIM_ACTIONS[aim["choice"]], aim["probabilities"][aim["choice"]]


def _move_then_angle(answers):
    move, aim = answers["move"], answers["aim"]
    if move["choice"] != "attack":
        return move["choice"], move["probabilities"][move["choice"]]
    return prompt.AIM_ACTIONS[aim["choice"]], aim["probabilities"][aim["choice"]]


def _move(move, f):
    return prompt.MOVE_NAMES.index(move)


MOVES_WITHOUT_WAIT = {k: v for k, v in prompt.MOVES.items() if k != "wait"}

V1_TACTICS = dict(teacher=motor.rule_tactic, act=motor.act)
V1_DIRECT = dict(teacher=motor.ball_direction, act=_move)
V2 = dict(decide=_choice, act=motor.act_shot)
V3 = dict(decide=_choice, act=motor.act_v3)
V4 = dict(decide=_choice, act=motor.act_v4)
V5 = dict(decide=_choice, act=motor.act_v5)

VERSIONS = {
    # v1: 5 options, the whole game in 7 sentences
    "v1-tactics": Version(
        "5 plans. Read 0.07, balanced 0.18 - answers 'defend' 94% of the time",
        prompt.TACTIC_QUESTION, prompt.describe, _choice, **V1_TACTICS,
    ),
    "v1-tactics-json": Version(
        "v1-tactics with the state as JSON. Read 0.04, balanced 0.20",
        prompt.TACTIC_QUESTION, partial(prompt.describe, fmt="json"), _choice, **V1_TACTICS,
    ),
    "v1-tactics-raw": Version(
        "v1-tactics with the state as raw numbers. Read 0.12, balanced 0.18",
        prompt.TACTIC_QUESTION, partial(prompt.describe, fmt="raw"), _choice, **V1_TACTICS,
    ),
    "v1-tactics-yesno": Version(
        "v1-tactics as one yes/no question per plan. Read 0.37, balanced 0.31",
        prompt.yes_no(prompt.TACTICS), prompt.describe, _most_likely_yes, **V1_TACTICS,
    ),
    "v1-direct": Version(
        "5 moves. Read 0.26, balanced 0.46 - answers 'back' 73% of the time",
        prompt.MOVE_QUESTION, prompt.describe, _choice, **V1_DIRECT,
    ),
    "v1-direct-json": Version(
        "v1-direct with the state as JSON. Read 0.12, balanced 0.32",
        prompt.MOVE_QUESTION, partial(prompt.describe, fmt="json"), _choice, **V1_DIRECT,
    ),
    "v1-direct-raw": Version(
        "v1-direct with the state as raw numbers. Read 0.05, balanced 0.21",
        prompt.MOVE_QUESTION, partial(prompt.describe, fmt="raw"), _choice, **V1_DIRECT,
    ),
    "v1-direct-yesno": Version(
        "v1-direct as one yes/no question per move (no wait). Read 0.77, balanced 0.81",
        prompt.yes_no(MOVES_WITHOUT_WAIT), prompt.describe, _most_likely_yes, **V1_DIRECT,
    ),
    # v2: 3-4 actions and only the needed facts; the code handles speed, lining up and the wall
    "v2-shots": Version(
        "3 actions, all 4 facts: Laya decides priority. Probe 12/16. Read 0.77, balanced 0.47 - mostly shoots",
        prompt.SHOTS_QUESTION, prompt.shot_facts, teacher=motor.rule_shots, **V2,
    ),
    "v2-shots-focused": Version(
        "3 actions, only the facts needed right now. Read 0.71, balanced 0.33 - always shoots",
        prompt.SHOTS_QUESTION, partial(prompt.shot_facts, focused=True), teacher=motor.rule_shots, **V2,
    ),
    "v2-challenge": Version(
        "4 actions (+challenge), all 5 facts. Read 0.37, balanced 0.35 - never challenges",
        prompt.CHALLENGE_QUESTION, partial(prompt.shot_facts, race=True), teacher=motor.rule_challenge, **V2,
    ),
    "v2-challenge-focused": Version(
        "4 actions (+challenge), only the needed facts. Read 0.46, balanced 0.51",
        prompt.CHALLENGE_QUESTION,
        partial(prompt.shot_facts, race=True, focused=True),
        teacher=motor.rule_challenge,
        **V2,
    ),
    "v2-split": Version(
        "direction and angle as two questions in one pass. Probe 9/16. Read 0.68, balanced 0.77",
        prompt.SPLIT_QUESTIONS, prompt.shot_facts, _direction_then_angle, motor.rule_shots, motor.act_shot,
    ),
    # v3: the v2 questions and facts (so Laya reads them the same), driven like a player: two keys
    # at once, no easing off before a hit, a bump of boost at top speed (motor.act_v3)
    "v3-shots": Version(
        "v2-shots with the v3 driving. Play +273",
        prompt.SHOTS_QUESTION, prompt.shot_facts, teacher=motor.rule_shots, **V3,
    ),
    "v3-shots-focused": Version(
        "v2-shots-focused with the v3 driving. Play +456 - Laya always shoots, so = always shoot_straight",
        prompt.SHOTS_QUESTION, partial(prompt.shot_facts, focused=True), teacher=motor.rule_shots, **V3,
    ),
    "v3-challenge": Version(
        "v2-challenge with the v3 driving. Play +375",
        prompt.CHALLENGE_QUESTION, partial(prompt.shot_facts, race=True), teacher=motor.rule_challenge, **V3,
    ),
    "v3-challenge-focused": Version(
        "v2-challenge-focused with the v3 driving. Play +473, Hockey +415 - slows before about half its hits",
        prompt.CHALLENGE_QUESTION,
        partial(prompt.shot_facts, race=True, focused=True),
        teacher=motor.rule_challenge,
        **V3,
    ),
    "v3-split": Version(
        "v2-split with the v3 driving. Play +344",
        prompt.SPLIT_QUESTIONS, prompt.shot_facts, _direction_then_angle, motor.rule_shots, motor.act_v3,
    ),
    # v4: the same questions and facts again, with the slowdowns before hits removed (motor.act_v4)
    "v4-shots": Version(
        "v2-shots with the v4 driving. Play +393, Hockey +574",
        prompt.SHOTS_QUESTION, prompt.shot_facts, teacher=motor.rule_shots, **V4,
    ),
    "v4-shots-focused": Version(
        "v2-shots-focused with the v4 driving. Play +436, Hockey +617 - Laya always shoots",
        prompt.SHOTS_QUESTION, partial(prompt.shot_facts, focused=True), teacher=motor.rule_shots, **V4,
    ),
    "v4-challenge": Version(
        "v2-challenge with the v4 driving. Play +420, Hockey +560",
        prompt.CHALLENGE_QUESTION, partial(prompt.shot_facts, race=True), teacher=motor.rule_challenge, **V4,
    ),
    "v4-challenge-focused": Version(
        "v2-challenge-focused with the v4 driving. Play +477, Hockey +644",
        prompt.CHALLENGE_QUESTION,
        partial(prompt.shot_facts, race=True, focused=True),
        teacher=motor.rule_challenge,
        **V4,
    ),
    "v4-split": Version(
        "v2-split with the v4 driving. Play +411, Hockey +506 - cleanest hits, fewer wins",
        prompt.SPLIT_QUESTIONS, prompt.shot_facts, _direction_then_angle, motor.rule_shots, motor.act_v4,
    ),
    # v5: the same questions and facts, with angle perception in the driving: meet the ball where it
    # will be, hit a moving ball at the corrected angle, defend when it can't be reached (motor.act_v5)
    "v5-shots": Version(
        "v2-shots with the v5 driving. Not played yet (its rules: +892, Hockey +1054)",
        prompt.SHOTS_QUESTION, prompt.shot_facts, teacher=motor.rule_shots, **V5,
    ),
    "v5-shots-focused": Version(
        "v2-shots-focused with the v5 driving. Laya always shoots, so = always shoot_straight: +933, Hockey +1169",
        prompt.SHOTS_QUESTION, partial(prompt.shot_facts, focused=True), teacher=motor.rule_shots, **V5,
    ),
    "v5-challenge": Version(
        "v2-challenge with the v5 driving. Not played yet (its rules: +878, Hockey +939)",
        prompt.CHALLENGE_QUESTION, partial(prompt.shot_facts, race=True), teacher=motor.rule_challenge, **V5,
    ),
    "v5-challenge-focused": Version(
        "v2-challenge-focused with the v5 driving. Play +958, Hockey +1135 - best so far",
        prompt.CHALLENGE_QUESTION,
        partial(prompt.shot_facts, race=True, focused=True),
        teacher=motor.rule_challenge,
        **V5,
    ),
    "v5-split": Version(
        "v2-split with the v5 driving. Play +868, Hockey +859",
        prompt.SPLIT_QUESTIONS, prompt.shot_facts, _direction_then_angle, motor.rule_shots, motor.act_v5,
    ),
    # v6: the v5 driving, and Laya reads the angle perception too (prompt.angle_facts_text)
    "v6-challenge-focused": Version(
        "4 actions; reads whether the ball is getting past you, who gets to it first, and the shots where you meet it. Read 0.42, balanced 0.50 - never goes back or challenges",
        prompt.ANGLE_QUESTION, prompt.angle_facts_text, _choice, motor.rule_v6, motor.act_v5,
    ),
    "v6-split": Version(
        "the v6 facts, as a move question (go back / challenge / attack) and an angle question in one pass. Read 0.46, balanced 0.47 - reads challenge (72/85) but never go back, and banks nearly always",
        prompt.ANGLE_SPLIT_QUESTIONS, prompt.angle_facts_text, _move_then_angle, motor.rule_v6, motor.act_v5,
    ),
}

DEFAULT_VERSION = "v5-challenge-focused"  # the one the game menu starts on: best in play so far

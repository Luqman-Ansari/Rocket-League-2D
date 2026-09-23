# laya_controller/prompt.py
"""What Laya reads: the state as text, and the question each design asks.

Once we fine-tune, this becomes the training format, so change it deliberately.
"""
import json

from laya_controller.perception import angle_facts

FORMATS = ("sentences", "json", "raw")

# Plans for the "tactics" design. Each description echoes the fact (features.py) that calls
# for it, so the untuned model only has to match text.
TACTICS = {
    "shoot": "you are behind the ball and lined up with the enemy goal",
    "get_behind_ball": "you are on the wrong side of the ball",
    "chase": "the opponent is closer to the ball than you",
    "defend": "your goal is in danger",
    "clear": "the ball is close to you and near your own goal",
}

# Moves for the "direct" design, in the order TrainedAICar.apply_ai_action() numbers them
MOVES = {
    "wait": "you are already where you need to be",
    "up": "the ball is above you",
    "down": "the ball is below you",
    "back": "the ball is behind you, toward your own goal",
    "forward": "the ball is ahead of you, toward the enemy goal",
}
MOVE_NAMES = list(MOVES)

TACTIC_QUESTION = {
    "decision": {
        "type": "choice",
        "instructions": "You drive a car in a 2D soccer game. Which plan should you follow right now?",
        "criteria": TACTICS,
    }
}
MOVE_QUESTION = {
    "decision": {
        "type": "choice",
        "instructions": "You drive a car in a 2D soccer game. Which way should you drive right now?",
        "criteria": MOVES,
    }
}


def yes_no(criteria):
    """One yes/no question per option; the answer is the option with the most likely yes."""
    return {name: {"type": "noul", "instructions": f"Is it true that {text}?"} for name, text in criteria.items()}


# ---- v2: few actions, only the needed facts. The driving code handles speed, lining up and
# which wall a bank shot uses.

SHOTS = {
    "shoot_straight": "the straight path to the goal is clear",
    "bank_shot": "the straight path is blocked and the bank shot off the wall is clear",
    "go_back": "you are ahead of the ball and it is heading toward your goal",
}
CHALLENGE = {**SHOTS, "challenge": "the opponent is closer to the ball than you"}

V2_INSTRUCTIONS = "You drive a car in a 2D soccer game. What should you do now?"
SHOTS_QUESTION = {"decision": {"type": "choice", "instructions": V2_INSTRUCTIONS, "criteria": SHOTS}}
CHALLENGE_QUESTION = {"decision": {"type": "choice", "instructions": V2_INSTRUCTIONS, "criteria": CHALLENGE}}

# v2-split: direction and angle as two questions, answered in the same forward pass
SPLIT_QUESTIONS = {
    "move": {
        "type": "choice",
        "instructions": "You drive a car in a 2D soccer game. Where should you drive now?",
        "criteria": {
            "go_back": "you are ahead of the ball and it is heading toward your goal",
            "attack": "you are behind the ball, or the ball is heading away from your goal",
        },
    },
    "aim": {
        "type": "choice",
        "instructions": "You drive a car in a 2D soccer game. Which way should you hit the ball?",
        "criteria": {
            "straight": "the straight path to the goal is clear",
            "bank": "the straight path is blocked and the bank shot off the wall is clear",
        },
    },
}
AIM_ACTIONS = {"straight": "shoot_straight", "bank": "bank_shot"}


def shot_facts(f, race=False, focused=False):
    """v2 state: where you are vs the ball, where it is heading, and which shots are clear.

    race: add who is closer to the ball (for the challenge action).
    focused: only what the decision needs right now - the two go-back facts when the ball is
    getting past you, otherwise only the shot facts.
    """
    position = "You are ahead of the ball." if f["ahead"] else "You are behind the ball."
    heading = {
        "toward": "The ball is heading toward your goal.",
        "away": "The ball is heading away from your goal.",
        "neither": "The ball is not heading toward either goal.",
    }[f["heading"]]
    shots = [
        f"The straight path to the goal is {'clear' if f['straight_clear'] else 'blocked'}.",
        f"The bank shot off the wall is {'clear' if f['bank_clear'] else 'blocked'}.",
    ]
    if race:
        shots.append(f["race"])
    if focused:
        return " ".join([position, heading] if f["ahead"] and f["heading"] == "toward" else shots)
    return " ".join([position, heading, *shots])


# ---- v6: Laya also reads the angle perception (perception.angle_facts): whether the ball is getting
# past you, who gets to it first, and which shots are open where the car meets it.

ANGLE = {
    "shoot_straight": "the straight path to the goal is clear",
    "bank_shot": "the straight path is blocked and the bank shot off the wall is clear",
    "go_back": "the ball is getting past you toward your goal",
    "challenge": "the opponent will get to the ball first",
}
ANGLE_QUESTION = {"decision": {"type": "choice", "instructions": V2_INSTRUCTIONS, "criteria": ANGLE}}
ANGLE_SPLIT_QUESTIONS = {
    "move": {
        "type": "choice",
        "instructions": V2_INSTRUCTIONS,
        "criteria": {
            "go_back": ANGLE["go_back"],
            "challenge": ANGLE["challenge"],
            "attack": "you will get to the ball first",
        },
    },
    "aim": SPLIT_QUESTIONS["aim"],
}


def angle_facts_text(f):
    """v6 state, only the needed facts: the getting-past sentence on its own, or else the shots
    and the race, judged where the car meets the ball."""
    angle_facts(f)
    if f["getting_past"]:
        return "The ball is getting past you toward your goal."
    return " ".join([
        f"The straight path to the goal is {'clear' if f['straight_clear_meet'] else 'blocked'}.",
        f"The bank shot off the wall is {'clear' if f['bank_clear_meet'] else 'blocked'}.",
        "The opponent will get to the ball first." if f["opp_first"] else "You will get to the ball first.",
    ])


def describe(f, fmt="sentences"):
    """v1 state: the whole game in 7 sentences (or as JSON / raw numbers, see FORMATS)."""
    if fmt == "sentences":
        return (
            f"The ball is {f['dist']}, {f['where']}. It is {f['motion']}, {f['zone']}. "
            f"{f['race']} {f['position']} {f['goal']}"
        )
    if fmt == "json":
        return json.dumps(
            {
                "ball distance": f["dist"],
                "ball position": f["where"],
                "ball motion": f["motion"],
                "ball zone": f["zone"],
                "race": f["race"],
                "your position": f["position"],
                "your goal": f["goal"],
            }
        )
    return json.dumps(f["raw"])

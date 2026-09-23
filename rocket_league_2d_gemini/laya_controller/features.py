# laya_controller/features.py
"""The game as seen by the car Laya drives.

Input is the 14-value observation the RL bots already use (Match._create_observation(), the rl/
envs' get_state()): me x, y, vx, vy / opponent x, y, vx, vy / ball x, y, vx, vy / own goalkeeper y,
enemy goalkeeper y, with positions divided by the screen size.
"""
import math

from src.settings import GOAL_BOTTOM_Y, GOAL_TOP_Y, HEIGHT, WIDTH

# Speed scales used by that observation
CAR_SPEED = 7.0
BALL_SPEED = 15.0

CAR_R, BALL_R = 22, 16  # Car.radius, Ball.radius
OWN_GOAL = (0.0, HEIGHT / 2)
ENEMY_GOAL = (float(WIDTH), HEIGHT / 2)


def canonical(obs, side):
    """Mirror the right-hand car's view, so every car attacks toward x = 1."""
    obs = [float(v) for v in obs]
    if side == "right":
        for i in (0, 4, 8):  # x positions
            obs[i] = 1.0 - obs[i]
        for i in (2, 6, 10):  # x velocities
            obs[i] = -obs[i]
    return obs


def world_action(action, side):
    """Undo canonical() for a move: left and right swap for the right-hand car.

    action: a move 0-4 (left 3, right 4), or held keys (up, down, left, right, boost).
    """
    if side != "right":
        return action
    if isinstance(action, tuple):
        up, down, left, right, boost = action
        return up, down, right, left, boost
    return 7 - action if action in (3, 4) else action


def facts(obs):
    """Positions in pixels plus the facts Laya reads, from a canonical observation."""
    me = (obs[0] * WIDTH, obs[1] * HEIGHT)
    opp = (obs[4] * WIDTH, obs[5] * HEIGHT)
    ball = (obs[8] * WIDTH, obs[9] * HEIGHT)
    ball_v = (obs[10] * BALL_SPEED, obs[11] * BALL_SPEED)

    dx, dy = ball[0] - me[0], ball[1] - me[1]
    dist = math.hypot(dx, dy)
    opp_dist = math.hypot(ball[0] - opp[0], ball[1] - opp[1])
    gx, gy = ENEMY_GOAL[0] - ball[0], ENEMY_GOAL[1] - ball[1]

    wrong_side = me[0] > ball[0] - 10  # the ball is between you and your own goal
    lined_up = not wrong_side and dx * gx + dy * gy > 0.8 * dist * math.hypot(gx, gy)
    near_own_goal = ball[0] < WIDTH / 3
    opp_closer = opp_dist < dist - 30
    danger = near_own_goal and (ball_v[0] < -1 or opp_closer)

    if opp_closer:
        race = "The opponent is closer to the ball than you."
    elif dist < opp_dist - 30:
        race = "You are closer to the ball than the opponent."
    else:
        race = "You and the opponent are about as close to the ball."

    if wrong_side:
        position = "You are on the wrong side of the ball."
    elif lined_up:
        position = "You are behind the ball and lined up with the enemy goal."
    else:
        position = "You are behind the ball but not lined up with the enemy goal."

    if near_own_goal:
        zone = "near your own goal"
    elif ball[0] > 2 * WIDTH / 3:
        zone = "near the enemy goal"
    else:
        zone = "in midfield"

    if ball_v[0] < -1:
        heading = "toward"  # your goal
    elif ball_v[0] > 1:
        heading = "away"
    else:
        heading = "neither"

    return {
        "me": me,
        "me_v": (obs[2] * CAR_SPEED, obs[3] * CAR_SPEED),
        "opp": opp,
        "opp_v": (obs[6] * CAR_SPEED, obs[7] * CAR_SPEED),
        "ball": ball,
        "ball_v": ball_v,
        # v2: shots and going back
        "ahead": me[0] > ball[0],  # further upfield than the ball
        "heading": heading,
        **_shots(ball, opp),
        "dist_px": dist,
        "wrong_side": wrong_side,
        "lined_up": lined_up,
        "near_own_goal": near_own_goal,
        "opp_closer": opp_closer,
        "danger": danger,
        # the words Laya reads (prompt.describe)
        "dist": _distance(dist),
        "where": _where(dx, dy),
        "motion": _motion(*ball_v),
        "zone": zone,
        "race": race,
        "position": position,
        "goal": "Your goal is in danger." if danger else "Your goal is safe.",
        "raw": {
            "field": "x runs from your goal (0) to the enemy goal (1), y from top (0) to bottom (1)",
            "you": _numbers(obs[0:4]),
            "opponent": _numbers(obs[4:8]),
            "ball": _numbers(obs[8:12]),
            "your goalkeeper y": round(obs[12], 2),
            "enemy goalkeeper y": round(obs[13], 2),
        },
    }


def _shots(ball, opp):
    """Where to aim a straight shot and a bank shot, and whether the opponent car blocks each path.

    The keeper follows the ball, so it is not counted as a blocker. The walls bounce the ball like
    a mirror (Ball.update flips vy), so a bank shot aims at the goal's reflection in the wall.
    """
    top, bottom = GOAL_TOP_Y + 25, GOAL_BOTTOM_Y - 25  # just inside the posts
    straight = ENEMY_GOAL  # where the straight shot (motor.act("shoot")) aims

    banks = []  # (clear, path length, aim point) per wall
    for wall_y, goal_y in ((BALL_R, bottom), (HEIGHT - BALL_R, top)):  # finish on the side away from the wall
        mirror = (float(WIDTH), 2 * wall_y - goal_y)
        t = (wall_y - ball[1]) / (mirror[1] - ball[1])
        bounce = (ball[0] + t * (mirror[0] - ball[0]), wall_y)
        path = [ball, bounce, (float(WIDTH), goal_y)]
        banks.append((_clear(path, opp), math.dist(ball, bounce) + math.dist(bounce, path[2]), mirror))
    bank_clear, _, bank_aim = min(banks, key=lambda b: (not b[0], b[1]))  # a clear wall, then the nearer

    return {
        "aim_straight": straight,
        "straight_clear": _clear([ball, straight], opp),
        "aim_bank": bank_aim,
        "bank_clear": bank_clear,
    }


def _clear(path, blocker):
    """Whether the ball can roll along `path` (a list of points) without meeting `blocker`."""
    gap = CAR_R + BALL_R + 8
    return all(segment_distance(blocker, a, b) > gap for a, b in zip(path, path[1:]))


def segment_distance(p, a, b):
    """Distance from point p to the segment a-b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / max(dx * dx + dy * dy, 1e-9)
    t = min(max(t, 0.0), 1.0)
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _distance(d):
    if d < 45:
        return "touching you"
    if d < 150:
        return "close"
    if d < 350:
        return "a medium distance away"
    return "far away"


def _where(dx, dy):
    """Main direction first, then the smaller offset if there is one."""
    if abs(dx) >= abs(dy):
        main = "ahead of you" if dx > 0 else "behind you"
        return main + (f" and slightly {'above' if dy < 0 else 'below'}" if abs(dy) > 25 else "")
    main = "above you" if dy < 0 else "below you"
    return main + (f" and slightly {'ahead' if dx > 0 else 'behind'}" if abs(dx) > 25 else "")


def _motion(vx, vy):
    speed = math.hypot(vx, vy)
    if speed < 0.5:
        return "not moving"
    pace = "fast" if speed > 6 else "slowly"
    if vx < -0.5 * speed:
        return f"rolling {pace} toward your goal"
    if vx > 0.5 * speed:
        return f"rolling {pace} toward the enemy goal"
    return f"rolling {pace} sideways"


def _numbers(values):
    return dict(zip(("x", "y", "vx", "vy"), (round(v, 2) for v in values)))

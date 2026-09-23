# laya_controller/motor.py
"""Hand-written driving: turns a plan into one of the 5 moves, every frame.

Works in the canonical view from features.py: your goal on the left, move 4 heads for the enemy goal.
"""
import math

from src.settings import BALL_FRICTION, CAR_FRICTION, HEIGHT, WIDTH
from laya_controller.features import BALL_R, CAR_R, ENEMY_GOAL, OWN_GOAL, _shots, segment_distance
from laya_controller.perception import angle_facts, ball_path, first_reachable, hit_direction, intercept

MAX_SPEED = 7  # Car.max_speed
DIRECTIONS = {1: (0, -1), 2: (0, 1), 3: (-1, 0), 4: (1, 0)}  # up, down, left, right


def rule_tactic(f):
    """Scripted plan choice: drives while Laya loads, and is the reference Laya is compared to."""
    if f["near_own_goal"] and f["dist_px"] < 150:
        return "clear"
    if f["danger"]:
        return "defend"
    if f["wrong_side"]:
        return "get_behind_ball"
    if f["opp_closer"]:
        return "chase"
    return "shoot"


def act(tactic, f):
    """The move that best heads for where `tactic` wants the car to be."""
    return steer(target(tactic, f), f["me"], f["me_v"])


def target(tactic, f):
    bx, by = f["ball"]
    mx, my = f["me"]
    if tactic in ("shoot", "clear") and f["wrong_side"]:
        tactic = "get_behind_ball"  # pushing from the wrong side sends the ball at your own goal
    if tactic == "shoot":
        tx, ty = _push(f, ENEMY_GOAL)
    elif tactic == "clear":
        tx, ty = _push(f, (bx + 300, by))  # anywhere away from your own goal
    elif tactic == "get_behind_ball":
        side = 1 if my >= by else -1  # go round on the side you are already on
        tx, ty = bx - 90, by + side * 70
    elif tactic == "defend":
        tx, ty = max(100, bx * 0.35), HEIGHT / 2 + (by - HEIGHT / 2) * 0.5
    else:  # chase: where the ball will be in a moment
        tx, ty = bx + f["ball_v"][0] * 8, by + f["ball_v"][1] * 8
    return min(max(tx, CAR_R), WIDTH - CAR_R), min(max(ty, CAR_R), HEIGHT - CAR_R)


def steer(target, me, me_v):
    """Pick the move whose push best turns the current velocity into one heading for `target`."""
    dx, dy = target[0] - me[0], target[1] - me[1]
    speed = min(MAX_SPEED, math.hypot(dx, dy) * 0.08)  # slow down near the target
    ux, uy = _unit(dx, dy)
    ax, ay = ux * speed - me_v[0], uy * speed - me_v[1]  # velocity change we want
    best = max(DIRECTIONS, key=lambda m: DIRECTIONS[m][0] * ax + DIRECTIONS[m][1] * ay)
    if DIRECTIONS[best][0] * ax + DIRECTIONS[best][1] * ay < 0.1:
        return 0  # close enough: coast
    return best


def _push(f, aim):
    """Line up behind the ball on the line to `aim`, then drive through it."""
    bx, by = f["ball"]
    mx, my = f["me"]
    ux, uy = _unit(aim[0] - bx, aim[1] - by)
    tx, ty = _unit(bx - mx, by - my)
    if tx * ux + ty * uy > 0.9:  # lined up
        return bx + ux * 60, by + uy * 60
    gap = CAR_R + BALL_R + 12
    return bx - ux * gap, by - uy * gap  # the spot just behind the ball


def ball_direction(f):
    """v1-direct teacher: the ball's main direction, as its move question words it."""
    dx, dy = f["ball"][0] - f["me"][0], f["ball"][1] - f["me"][1]
    if abs(dx) >= abs(dy):
        return "forward" if dx > 0 else "back"
    return "down" if dy > 0 else "up"


# ---- v2: straight shots, bank shots, going back, challenging


def rule_shots(f):
    """v2 teacher: go back when the ball is getting past you, otherwise take the clear shot."""
    if f["ahead"] and f["heading"] == "toward":
        return "go_back"
    if f["bank_clear"] and not f["straight_clear"]:
        return "bank_shot"
    return "shoot_straight"


def rule_challenge(f):
    """v2 teacher with challenge: race the opponent to the ball when it is closer."""
    if f["ahead"] and f["heading"] == "toward":
        return "go_back"
    if f["opp_closer"]:
        return "challenge"
    return rule_shots(f)


def rule_v6(f):
    """v6 teacher: the challenge rules, judged at the moment the car can meet the ball (perception)."""
    angle_facts(f)
    if f["getting_past"]:
        return "go_back"
    if f["opp_first"]:
        return "challenge"
    if f["bank_clear_meet"] and not f["straight_clear_meet"]:
        return "bank_shot"
    return "shoot_straight"


def act_shot(action, f):
    """v2 driving: the move toward where `action` wants the car to be."""
    if action == "shoot_straight":
        # v1's quick hit: vs a bot that never stops chasing, lining up carefully loses the ball
        # (bench play, 2400 kickoffs: +69 for this vs -105 with _strike's careful run-up)
        return act("shoot", f)
    if action == "go_back":
        target = _go_back(f)
    elif action == "challenge":  # straight at where the ball is going, no lining up
        target = predict_ball(f, 8)
    else:  # bank_shot; the code picked the wall (features._shots)
        target = _strike(f, f["aim_bank"])
    x, y = target
    return steer((min(max(x, CAR_R), WIDTH - CAR_R), min(max(y, CAR_R), HEIGHT - CAR_R)), f["me"], f["me_v"])


def predict_ball(f, frames):
    """Where the ball will be after `frames`, with friction and wall bounces (cars ignored)."""
    (x, y), (vx, vy) = f["ball"], f["ball_v"]
    for _ in range(frames):
        vx, vy = vx * BALL_FRICTION, vy * BALL_FRICTION
        x, y = x + vx, y + vy
        if not BALL_R <= y <= HEIGHT - BALL_R:
            y, vy = min(max(y, BALL_R), HEIGHT - BALL_R), -vy
        if not BALL_R <= x <= WIDTH - BALL_R:
            x, vx = min(max(x, BALL_R), WIDTH - BALL_R), -vx
    return x, y


def _strike(f, aim):
    """Line up behind the ball on the line to `aim`, then run through it (speed comes from steer())."""
    (bx, by), (mx, my) = f["ball"], f["me"]
    ux, uy = _unit(aim[0] - bx, aim[1] - by)
    along = (mx - bx) * ux + (my - by) * uy  # < 0: behind the ball on the shot line
    off = (mx - bx) * -uy + (my - by) * ux  # sideways distance from the shot line
    if along > -CAR_R:  # beside or in front of the ball: go round it on the side you are on
        side = 1 if off >= 0 else -1
        return bx - ux * 80 - uy * side * 80, by - uy * 80 + ux * side * 80
    if abs(off) < max(12, 0.25 * -along):  # close to the line: commit, and correct on the way in
        ahead = min(along + 90, 60)  # a point on the line 90px ahead of you, at most 60px past the ball
        return bx + ux * ahead, by + uy * ahead
    return bx - ux * 90, by - uy * 90  # back onto the line, far enough behind to build up speed


def _go_back(f):
    """Your own goal's side of where the ball is going; step round the ball if it is in the way."""
    px, py = predict_ball(f, 30)
    ux, uy = _unit(OWN_GOAL[0] - px, OWN_GOAL[1] - py)
    target = (max(px + ux * 90, 100), py + uy * 90)
    (bx, by), (mx, my) = f["ball"], f["me"]
    if segment_distance((bx, by), (mx, my), target) < CAR_R + BALL_R + 10:
        return bx - 40, by + (85 if my >= by else -85)
    return target


# ---- v3: the v2 plans, driven like a player - two keys at once, no easing off before a hit,
# and a bump of boost once at top speed. Returns held keys (up, down, left, right, boost).

BOOST_SPEED = MAX_SPEED * 1.4  # Car.limit_speed() with boost


def act_v3(action, f):
    """v3 driving: the keys that carry out `action`."""
    if action == "go_back":
        return drive(_go_back(f), f, arrive=True)  # a position to hold: ease off on the way in
    if action == "challenge":
        return drive(predict_ball(f, 8), f)
    return drive(_strike_v3(f, f["aim_bank"] if action == "bank_shot" else ENEMY_GOAL), f)


def drive(target, f, arrive=False, hold_boost=False):
    """Keys that turn the current velocity into one heading for `target`.

    Full speed unless arriving at a position; at top speed and already heading the right way,
    boost is held for the extra speed (no decision involved).
    hold_boost (v4): once boosting, keep it while still roughly on course - letting go snaps the
    speed back to 7 (Car.limit_speed), which was the main slowdown right before hits.
    """
    (mx, my), (vx, vy) = f["me"], f["me_v"]
    tx, ty = min(max(target[0], CAR_R), WIDTH - CAR_R), min(max(target[1], CAR_R), HEIGHT - CAR_R)
    ux, uy = _unit(tx - mx, ty - my)
    speed = math.hypot(vx, vy)
    if hold_boost and not arrive and speed > MAX_SPEED:
        boost = vx * ux + vy * uy > 0.3 * speed
    else:
        boost = not arrive and speed >= 0.95 * MAX_SPEED and vx * ux + vy * uy > 0.9 * speed
    want = BOOST_SPEED if boost else MAX_SPEED
    if arrive:
        want = min(want, math.hypot(tx - mx, ty - my) * 0.08)
    dx, dy = ux * want - vx, uy * want - vy  # velocity change we want
    return dy < -0.15, dy > 0.15, dx < -0.15, dx > 0.15, boost


def _strike_v3(f, aim, smooth_run_up=False):
    """Where to head to hit the ball toward `aim` at full speed: round it, onto the line, through it.

    smooth_run_up (v4): far off the line, head for the line and gain ground toward the ball as the
    car gets closer to it, instead of backing off to a run-up point that can be behind the car.
    """
    (bx, by), (mx, my) = f["ball"], f["me"]
    ux, uy = _unit(aim[0] - bx, aim[1] - by)
    along = (mx - bx) * ux + (my - by) * uy  # < 0: behind the ball on the shot line
    off = (mx - bx) * -uy + (my - by) * ux  # sideways distance from the shot line
    if along > -CAR_R:  # in front of or beside the ball: go round it on the side you are on
        side = 1 if off >= 0 else -1
        return bx - ux * 80 - uy * side * 80, by - uy * 80 + ux * side * 80
    cone = 0.5 * -along + 10
    if abs(off) < cone:  # in the cone behind the ball: home in on the line and through
        ahead = min(along + 100, 60)
        return bx + ux * ahead, by + uy * ahead
    if smooth_run_up:
        ahead = min(along + 100 * max(0.0, 1 - (abs(off) - cone) / 60), 60)
        return bx + ux * ahead, by + uy * ahead
    back = max(100, -along)  # far off the line: a run-up point on it
    return bx - ux * back, by - uy * back


# ---- v4: v3 with the slowdowns before hits removed (traced over thousands of hits): boost held
# while on course, no backing off for a run-up, and a lined-up straight shot is finished rather
# than switching plans at the last moment - except with the ball against a wall, where finishing
# a bank line kept pushing the ball into the wall.


def act_v4(action, f):
    """v4 driving: the keys that carry out `action`."""
    if action == "go_back":
        return drive(_go_back(f), f, arrive=True)
    if not _against_wall(f["ball"]) and _lined_up(f, ENEMY_GOAL):
        return drive(_strike_v3(f, ENEMY_GOAL, smooth_run_up=True), f, hold_boost=True)
    if action == "challenge":
        return drive(predict_ball(f, 8), f, hold_boost=True)
    aim = f["aim_bank"] if action == "bank_shot" else ENEMY_GOAL
    return drive(_strike_v3(f, aim, smooth_run_up=True), f, hold_boost=True)


# ---- v5: v4, but every move toward the ball meets it where it will be, and shots hit it at the
# angle that sends it toward the aim (perception.py). f carries the mode's frictions (LayaController).


def act_v5(action, f):
    """v5 driving: the keys that carry out `action`."""
    ball_friction = f.get("ball_friction", BALL_FRICTION)
    car_friction = f.get("car_friction", CAR_FRICTION)
    meet = None if action == "go_back" else intercept(f, ball_friction, car_friction)
    if meet is None and action != "go_back":  # can't be reached within 1.5 s
        path = ball_path(f["ball"], f["ball_v"], ball_friction)
        if path and not (path[-1][2][0] < -1 and math.hypot(*path[-1][2]) > 3):
            meet = path[-1]  # not racing toward your goal: go for where it ends up
    if meet is None:  # going back, or the ball is getting past you fast: defend
        return drive(_go_back_v5(f, ball_friction, car_friction), f, arrive=True)
    _, ball, ball_v = meet
    if action == "challenge":
        return drive(ball, f, hold_boost=True)
    at = dict(f, ball=ball, ball_v=ball_v)  # the moment the car meets the ball
    lines = {
        "shoot_straight": _hit_line(ball, ball_v, ENEMY_GOAL),
        "bank_shot": _hit_line(ball, ball_v, _shots(ball, f["opp"])["aim_bank"]),
    }
    if not _against_wall(ball) and _lined_up(at, lines["shoot_straight"]):
        action = "shoot_straight"  # finish the straight shot you are lined up for (v4)
    return drive(_strike_v3(at, lines[action], smooth_run_up=True), f, hold_boost=True)


def _hit_line(ball, ball_v, aim):
    """A far point along the direction to hit the moving ball in, so it leaves toward `aim`."""
    (nx, ny), _ = hit_direction(ball_v, _unit(aim[0] - ball[0], aim[1] - ball[1]))
    return ball[0] + nx * 500, ball[1] + ny * 500


def _go_back_v5(f, ball_friction, car_friction):
    """Your own goal's side of the ball's path: the first point along it the car can get to in time."""
    spots = []
    for t, (px, py), _ in ball_path(f["ball"], f["ball_v"], ball_friction):
        ux, uy = _unit(OWN_GOAL[0] - px, OWN_GOAL[1] - py)
        spots.append((t, (max(px + ux * 90, 100), py + uy * 90)))
    if not spots:  # it is about to go in: v4's go-back
        return _go_back(f)
    meet = first_reachable(f, spots, car_friction, slack=20)
    target = meet[1] if meet else spots[-1][1]  # too late for all of them: where it ends up
    (bx, by), (mx, my) = f["ball"], f["me"]
    if segment_distance((bx, by), (mx, my), target) < CAR_R + BALL_R + 10:
        return bx - 40, by + (85 if my >= by else -85)  # the ball is in the way: step round it
    return target


def _lined_up(f, aim):
    """Behind the ball within 150px, inside the cone that leads through it toward `aim`."""
    (bx, by), (mx, my) = f["ball"], f["me"]
    ux, uy = _unit(aim[0] - bx, aim[1] - by)
    along = (mx - bx) * ux + (my - by) * uy
    off = (mx - bx) * -uy + (my - by) * ux
    return -150 < along < -CAR_R and abs(off) < 0.5 * -along + 10


def _against_wall(ball, margin=20):
    x, y = ball
    return min(y - BALL_R, HEIGHT - BALL_R - y, x - BALL_R, WIDTH - BALL_R - x) < margin


def _unit(x, y):
    d = math.hypot(x, y)
    return (x / d, y / d) if d > 1e-9 else (0.0, 0.0)

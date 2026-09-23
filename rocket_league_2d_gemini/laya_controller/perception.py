# laya_controller/perception.py
"""Angle perception (v5): where the ball is going, where the car can meet it, and the angle to hit it at.

The ball rolls in straight lines, slows by friction and bounces off the walls like a mirror
(Ball.update), so its path is predictable until a car touches it. A hit (Physics.resolve_car_ball)
pushes the ball along the car-to-ball line and keeps its sideways motion, so a moving ball has to
be hit at a corrected angle to leave toward the aim.

Everything works in the canonical view from features.py and needs the game mode's frictions.
"""
import math

from src.settings import BALL_FRICTION, CAR_FRICTION, GOAL_BOTTOM_Y, GOAL_TOP_Y, HEIGHT, WIDTH
from laya_controller.features import BALL_R, CAR_R, ENEMY_GOAL, _shots

HORIZON = 90  # frames looked ahead: 1.5 s
STEP = 2  # check every 2nd frame of the path
ACCEL = 0.22  # the car's push per frame, between one key (0.2) and two keys at once (0.28)
OPP_ACCEL = 0.2  # the Basic bot (SimpleAICar.chase_ball): 0.2 toward the ball, no boost
HIT = 1.3  # Physics.resolve_car_ball: the ball gets 1.3x the closing speed along the hit line
_tables = {}


def ball_path(ball, ball_v, friction):
    """The ball's (frame, position, velocity) every STEP frames for HORIZON frames, until it enters a goal."""
    (x, y), (vx, vy) = ball, ball_v
    path = []
    for t in range(1, HORIZON + 1):
        vx, vy = vx * friction, vy * friction
        x, y = x + vx, y + vy
        if y < BALL_R or y > HEIGHT - BALL_R:
            y, vy = min(max(y, BALL_R), HEIGHT - BALL_R), -vy
        if x < BALL_R or x > WIDTH - BALL_R:
            if GOAL_TOP_Y < y < GOAL_BOTTOM_Y:
                break  # it goes in
            x, vx = min(max(x, BALL_R), WIDTH - BALL_R), -vx
        if t % STEP == 0:
            path.append((t, (x, y), (vx, vy)))
    return path


def first_reachable(f, points, car_friction, slack=0.0, accel=ACCEL, boost=True):
    """The first (t, point, ...) in `points` the car can get within `slack` of by frame t, or None.

    Best case for the car: flat out in a straight line from its current speed, boost once at top speed.
    """
    reach_from_rest, per_start_speed = _reach_tables(car_friction, accel, boost)
    (mx, my), (vx, vy) = f["me"], f["me_v"]
    for item in points:
        t, (px, py) = item[0], item[1]
        dx, dy = px - mx, py - my
        d = math.hypot(dx, dy)
        start = max(0.0, (vx * dx + vy * dy) / d) if d > 1e-9 else 0.0  # speed already heading there
        if d - slack <= min(reach_from_rest[t] + start * per_start_speed[t], 9.8 * t):
            return item
    return None


def intercept(f, ball_friction, car_friction):
    """(t, ball position, ball velocity) where the car can first meet the ball, or None within 1.5 s."""
    return first_reachable(f, ball_path(f["ball"], f["ball_v"], ball_friction), car_friction, CAR_R + BALL_R)


def hit_direction(ball_v, aim_dir, car_speed=7.0):
    """The car-to-ball direction to hit along so the ball leaves along aim_dir, and how many degrees
    off the best achievable direction still is (the ball keeps its sideways motion through a hit)."""
    ax, ay = aim_dir
    best = (180.0, aim_dir)
    for k in range(-15, 16):  # -75..75 degrees around the aim, 5 degree steps
        a = math.radians(5 * k)
        nx, ny = ax * math.cos(a) - ay * math.sin(a), ax * math.sin(a) + ay * math.cos(a)
        closing = car_speed - (ball_v[0] * nx + ball_v[1] * ny)
        if closing <= 0:
            continue  # the ball runs away from a car driving this way
        ox, oy = ball_v[0] + HIT * closing * nx, ball_v[1] + HIT * closing * ny
        cos = (ox * ax + oy * ay) / math.hypot(ox, oy)
        off = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        if off < best[0]:
            best = (off, (nx, ny))
    return best[1], best[0]


def angle_facts(f):
    """v6: what the car perceives about the moving ball, for Laya to read (added to f once).

    getting_past: the ball is getting past you toward your goal - you are ahead of it and it heads
    home, or it can't be reached in time and races home. opp_first: the opponent meets it first.
    straight_clear_meet / bank_clear_meet: from where you meet the ball, the opponent is off that
    path and a hit can still send the ball along it.
    """
    if "getting_past" in f:
        return f
    ball_friction = f.get("ball_friction", BALL_FRICTION)
    car_friction = f.get("car_friction", CAR_FRICTION)
    path = ball_path(f["ball"], f["ball_v"], ball_friction)
    meet = first_reachable(f, path, car_friction, CAR_R + BALL_R)
    opp = first_reachable({"me": f["opp"], "me_v": f["opp_v"]}, path, car_friction, CAR_R + BALL_R,
                          accel=OPP_ACCEL, boost=False)
    racing_home = bool(path) and path[-1][2][0] < -1 and math.hypot(*path[-1][2]) > 3
    if meet:
        ball, ball_v = meet[1], meet[2]
    elif path:
        ball, ball_v = path[-1][1], path[-1][2]
    else:
        ball, ball_v = f["ball"], f["ball_v"]
    shots = _shots(ball, f["opp"])
    _, straight_off = hit_direction(ball_v, _unit(ENEMY_GOAL[0] - ball[0], ENEMY_GOAL[1] - ball[1]))
    _, bank_off = hit_direction(ball_v, _unit(shots["aim_bank"][0] - ball[0], shots["aim_bank"][1] - ball[1]))
    f.update(
        getting_past=(f["ahead"] and f["heading"] == "toward") or (meet is None and racing_home),
        opp_first=opp is not None and (meet is None or opp[0] < meet[0]),
        straight_clear_meet=shots["straight_clear"] and straight_off < 12,
        bank_clear_meet=shots["bank_clear"] and bank_off < 12,
    )
    return f


def _unit(x, y):
    d = math.hypot(x, y)
    return (x / d, y / d) if d > 1e-9 else (1.0, 0.0)


def _reach_tables(car_friction, accel=ACCEL, boost=True):
    """Distance covered from rest in t frames, and the extra distance per unit of starting speed."""
    key = car_friction, accel, boost
    if key not in _tables:
        rest, extra, v, d, w, e = [0.0], [0.0], 0.0, 0.0, 1.0, 0.0
        for _ in range(HORIZON):
            v = min(9.8 if boost and v >= 6.65 else 7.0, v + accel) * car_friction
            d += v
            w *= car_friction
            e += w
            rest.append(d)
            extra.append(e)
        _tables[key] = rest, extra
    return _tables[key]

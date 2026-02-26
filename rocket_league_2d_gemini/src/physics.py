# physics.py
import math
from settings import *

def collide_circle(a_x, a_y, a_r, b_x, b_y, b_r):
    dx = b_x - a_x; dy = b_y - a_y
    dist = math.hypot(dx, dy)
    if dist == 0 or dist >= (a_r + b_r): return False, 0,0,0
    overlap = (a_r + b_r) - dist
    return True, dx/dist, dy/dist, overlap

def resolve_car_ball(car, ball):
    collided, nx, ny, overlap = collide_circle(car.x, car.y, car.radius, ball.x, ball.y, ball.radius)
    if collided:
        # Positional Correction
        ball.x += nx * overlap; ball.y += ny * overlap
        
        # Velocity Calculations
        rx = ball.vx - car.vx
        ry = ball.vy - car.vy
        impact_speed = rx * nx + ry * ny
        
        if impact_speed < 0:
            impulse = -impact_speed * 1.3
            ball.vx += nx * impulse
            ball.vy += ny * impulse
            
            car.vx -= nx * impulse * 0.3
            car.vy -= ny * impulse * 0.3

            # Add Spin (Tangent Impulse)
            tx = -ny; ty = nx
            tangent_speed = rx * tx + ry * ty
            ball.ang_vel += tangent_speed * 2.0

def resolve_car_car(c1, c2):
    collided, nx, ny, overlap = collide_circle(c1.x, c1.y, c1.radius, c2.x, c2.y, c2.radius)
    if collided:
        sep = overlap / 2 + 0.1
        c1.x -= nx * sep; c1.y -= ny * sep
        c2.x += nx * sep; c2.y += ny * sep
        v1n = c1.vx * nx + c1.vy * ny
        v2n = c2.vx * nx + c2.vy * ny
        c1.vx += (v2n - v1n) * nx * 0.6; c1.vy += (v2n - v1n) * ny * 0.6
        c2.vx += (v1n - v2n) * nx * 0.6; c2.vy += (v1n - v2n) * ny * 0.6
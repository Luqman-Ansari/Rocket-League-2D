# objects.py
import pygame
import math
import random
from settings import *
import assets_loader

def clamp(v, a, b): return max(a, min(b, v))

class Car:
    def __init__(self, x, y, color, controls, texture_key, friction=CAR_FRICTION):
        self.x = x; self.y = y
        self.vx = 0; self.vy = 0
        self.radius = 22
        self.color = color
        self.max_speed = 7
        
        # UPDATED: Accept friction override for Ice Hockey mode
        self.friction = friction
        
        self.controls = controls 
        self.speed_power = 0.25
        self.texture_key = texture_key
        self.boost_active = False

    def handle(self, keys):
        if not self.controls: return
        ax = ay = 0
        
        self.boost_active = keys[self.controls.get('boost', 0)] if self.controls.get('boost') else False
        
        if keys[self.controls['up']]:
            ay -= self.speed_power * (1.5 if self.boost_active else 1.0)
        if keys[self.controls['down']]:
            ay += self.speed_power * 0.8
        if keys[self.controls['left']]:
            ax -= self.speed_power * 0.8
        if keys[self.controls['right']]:
            ax += self.speed_power * 0.8

        # Play boost sound if just activated (simple check)
        # Note: In a robust engine we'd check previous state, but this is simple object logic
        
        self.vx += ax; self.vy += ay
        self.limit_speed()

    def limit_speed(self):
        limit = self.max_speed
        if self.boost_active:
            limit *= 1.4
        sp = math.hypot(self.vx, self.vy)
        if sp > limit:
            scale = limit / sp
            self.vx *= scale; self.vy *= scale

    def update(self):
        self.vx *= self.friction
        self.vy *= self.friction
        self.x += self.vx
        self.y += self.vy
        self.x = clamp(self.x, self.radius, WIDTH - self.radius)
        self.y = clamp(self.y, self.radius, HEIGHT - self.radius)

    def draw(self, surf):
        texture = assets_loader.GRAPHICS.get(self.texture_key)
        if texture:
            angle = math.degrees(math.atan2(-self.vy, self.vx))
            rotated_img = pygame.transform.rotate(texture, angle)
            rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(rotated_img, rect)
        else:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surf, BLACK, (int(self.x), int(self.y)), 6)

class Goalkeeper(Car):
    def __init__(self, x, y, color, side, texture_key, friction=CAR_FRICTION):
        super().__init__(x, y, color, None, texture_key, friction)
        self.side = side 
        self.max_speed = GK_SPEED_VAL 
        
    def update_ai(self, ball):
        dy = ball.y - self.y
        if abs(dy) > 10:
            if dy > 0: self.vy += 0.5 
            else: self.vy -= 0.5
        target_x = 50 if self.side == 'left' else WIDTH - 50
        dx = target_x - self.x
        if abs(dx) > 5:
            if dx > 0: self.vx += 0.5
            else: self.vx -= 0.5
        self.limit_speed()
        self.update() 

class Ball:
    def __init__(self, texture_key='ball', friction=BALL_FRICTION):
        self.texture_key = texture_key
        self.friction = friction
        self.reset()
        
    def reset(self):
        self.x = WIDTH//2; self.y = HEIGHT//2
        ang = random.uniform(0, 2*math.pi)
        self.vx = 0; self.vy = 0
        self.radius = 16
        self.angle = 0
        self.ang_vel = 0
        
    def update(self):
        self.vx *= self.friction
        self.vy *= self.friction
        
        self.x += self.vx; self.y += self.vy
        
        # Walls
        if self.y < self.radius: self.y = self.radius; self.vy *= -1
        if self.y > HEIGHT - self.radius: self.y = HEIGHT - self.radius; self.vy *= -1
        if self.x < self.radius:
            if not (GOAL_TOP_Y < self.y < GOAL_BOTTOM_Y): self.x = self.radius; self.vx *= -1
        if self.x > WIDTH - self.radius:
            if not (GOAL_TOP_Y < self.y < GOAL_BOTTOM_Y): self.x = WIDTH - self.radius; self.vx *= -1

        # Rotation Physics
        natural_roll_speed = -self.vx * 3.0 
        self.ang_vel += (natural_roll_speed - self.ang_vel) * 0.04
        self.angle = (self.angle + self.ang_vel) % 360

    def draw(self, surf):
        texture = assets_loader.GRAPHICS.get(self.texture_key)
        # Fallback to standard ball if specific texture not found
        if not texture: texture = assets_loader.GRAPHICS.get('ball')

        if texture:
            rotated_img = pygame.transform.rotate(texture, self.angle)
            new_rect = rotated_img.get_rect(center=(int(self.x), int(self.y)))
            surf.blit(rotated_img, new_rect)
        else:
            pygame.draw.circle(surf, ORANGE, (int(self.x), int(self.y)), self.radius)
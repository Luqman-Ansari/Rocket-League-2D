# rl/envs/phase2_defender.py
"""
CURRICULUM PHASE 2: THE 1v1 DUEL
Opponent: Active (Basic chase AI enabled)
Goalkeepers: Disabled
Objective: Learn to outmaneuver a moving target and protect the home net
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math
from src.settings import WIDTH, HEIGHT, GOAL_TOP_Y, GOAL_BOTTOM_Y, CAR_FRICTION, BALL_FRICTION
from src.objects import Ball, TrainedAICar, SimpleAICar, Goalkeeper
from src.physics import resolve_car_ball, resolve_car_car
import random


class Phase2DefenderEnv(gym.Env):
    """Phase 2: 1v1 with active opponent, learn defense and positioning."""
    
    metadata = {'render_modes': []}
    
    def __init__(self):
        super(Phase2DefenderEnv, self).__init__()
        
        # Actions: 0: Nothing, 1: Up, 2: Down, 3: Left, 4: Right
        self.action_space = spaces.Discrete(5)
        
        # Observation space: 14 floats
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(14,), 
            dtype=np.float32
        )
        
        # Initialize entities
        self.agent = TrainedAICar(200, HEIGHT//2, (40, 120, 255), 'car_blue', CAR_FRICTION)
        self.opponent = SimpleAICar(WIDTH-200, HEIGHT//2, (255, 80, 80), 'car_red', CAR_FRICTION)
        self.gk1 = Goalkeeper(50, HEIGHT//2, (20, 60, 128), 'left', 'gk_blue', CAR_FRICTION)
        self.gk2 = Goalkeeper(WIDTH-50, HEIGHT//2, (128, 40, 40), 'right', 'gk_red', CAR_FRICTION)
        self.ball = Ball('ball_soccer', BALL_FRICTION)
        
        self.score_agent = 0
        self.score_opponent = 0
        self.frames_passed = 0
        self.max_frames = 60 * 30  # 30 seconds per episode
        
        # Track previous ball state for save detection
        self.prev_ball_x = 0
        self.prev_ball_vx = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # 1. RANDOMIZE AGENT SPAWN (Left side of the field)
        self.agent.x = random.randint(150, WIDTH // 3)
        self.agent.y = random.randint(100, HEIGHT - 100)
        self.agent.vx = self.agent.vy = 0
        
        # 2. RANDOMIZE OPPONENT SPAWN (Right side of the field)
        self.opponent.x = random.randint(2 * (WIDTH // 3), WIDTH - 150)
        self.opponent.y = random.randint(100, HEIGHT - 100)
        self.opponent.vx = self.opponent.vy = 0
        
        # 3. RANDOMIZE BALL SPAWN (Middle of the field)
        self.ball.reset()
        self.ball.x = random.randint(WIDTH // 3, 2 * (WIDTH // 3))
        self.ball.y = random.randint(100, HEIGHT - 100)
        
        # Reset goalkeepers (disabled in this phase)
        self.gk1.x, self.gk1.y = 50, HEIGHT//2
        self.gk1.vx = self.gk1.vy = 0
        
        self.gk2.x, self.gk2.y = WIDTH-50, HEIGHT//2
        self.gk2.vx = self.gk2.vy = 0
        
        # Reset scores and timer
        self.score_agent = 0
        self.score_opponent = 0
        self.frames_passed = 0
        self.prev_ball_x = self.ball.x
        self.prev_ball_vx = self.ball.vx
        
        obs = self.get_state()
        return obs, {}
    
    def step(self, action):
        self.frames_passed += 1
        reward = 0.0
        done = False
        
        # Store previous ball state for save detection
        self.prev_ball_x = self.ball.x
        self.prev_ball_vx = self.ball.vx
        
        # 1. Apply agent action
        self.agent.apply_ai_action(action)
        
        # 2. ACTIVE OPPONENT: Chase ball
        self.opponent.chase_ball(self.ball)
        
        # 3. Goalkeepers disabled (but we keep them in observation for consistency)
        self.gk1.vx = 0
        self.gk1.vy = 0
        self.gk2.vx = 0
        self.gk2.vy = 0
        
        # 4. Update ball physics
        self.ball.update()
        
        # 5. Resolve collisions
        cars = [self.agent, self.opponent, self.gk1, self.gk2]
        
        # Check if agent touches ball (before collision resolution)
        dist_to_ball = math.hypot(self.ball.x - self.agent.x, self.ball.y - self.agent.y)
        touched_by_agent = dist_to_ball <= (self.agent.radius + self.ball.radius + 2)
        
        for car in cars:
            resolve_car_ball(car, self.ball)
            
        for i in range(len(cars)):
            for j in range(i + 1, len(cars)):
                resolve_car_car(cars[i], cars[j])
        
        # ==========================================
        # FIXED PHASE 2 REWARDS: Anti-Sandwich & Defense
        # ==========================================
        
        # Calculate opponent touch for sandwich detection
        dist_opp_to_ball = math.hypot(self.ball.x - self.opponent.x, self.ball.y - self.opponent.y)
        opp_touched_ball = dist_opp_to_ball <= (self.opponent.radius + self.ball.radius + 2)

        # A. TOUCH REWARD
        if touched_by_agent:
            reward += 0.1 
            
        # B. THE ANTI-SANDWICH (DEADLOCK) PENALTY
        # If both cars are touching the ball, but the ball isn't moving forward, punish the agent!
        # This teaches it: "If you are stuck against the opponent, back up and go around!"
        if touched_by_agent and opp_touched_ball:
            if self.ball.vx <= 1.0: 
                reward -= 0.5 
                
        # C. BALL ADVANCE REWARD (Encourages pushing past the opponent)
        # We give a tiny drip of points if the ball is actively rolling right
        if self.ball.vx > 0:
            reward += (self.ball.vx * 0.01)
            
        # D. SAVE/CLEAR REWARD
        defensive_zone_x = WIDTH / 3
        if self.prev_ball_x < defensive_zone_x and touched_by_agent:
            if self.ball.vx > self.prev_ball_vx:
                reward += 2.0  
        
        # E. GOAL SCORED (Right Net)
        if self.ball.x + self.ball.radius > WIDTH and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score_agent += 1
            reward += 1000.0 
            done = True
        
        # F. OWN GOAL (Left Net)
        elif self.ball.x - self.ball.radius < 0 and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score_opponent += 1
            reward -= 50.0  
            done = True
        
        # G. TIME PENALTY
        reward -= 0.05 
        
        # H. TIME LIMIT
        if self.frames_passed >= self.max_frames:
            done = True
        
        obs = self.get_state()
        terminated = done
        truncated = False
        
        info = {
            'agent_score': self.score_agent,
            'opp_score': self.score_opponent,
            'frames': self.frames_passed
        }
        
        return obs, reward, terminated, truncated, info

    def get_state(self):
        """Returns 14 normalized values to the Neural Network."""
        return np.array([
            self.agent.x / WIDTH, 
            self.agent.y / HEIGHT,
            self.agent.vx / self.agent.max_speed, 
            self.agent.vy / self.agent.max_speed,
            
            self.opponent.x / WIDTH, 
            self.opponent.y / HEIGHT,
            self.opponent.vx / self.opponent.max_speed, 
            self.opponent.vy / self.opponent.max_speed,
            
            self.ball.x / WIDTH, 
            self.ball.y / HEIGHT,
            self.ball.vx / 15.0, 
            self.ball.vy / 15.0,
            
            self.gk1.y / HEIGHT, 
            self.gk2.y / HEIGHT
        ], dtype=np.float32)

    def render(self):
        pass

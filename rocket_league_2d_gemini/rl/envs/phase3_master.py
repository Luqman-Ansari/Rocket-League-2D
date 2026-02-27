# rl/envs/phase3_master.py
"""
CURRICULUM PHASE 3: THE FULL GAME
Opponent: Active (Basic chase AI enabled)
Goalkeepers: ACTIVE
Objective: Full free exploration to discover advanced tactics (wall bounces, jukes)
Rewards: Strict sparse rewards - mostly just goal scored/conceded
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math
from src.settings import WIDTH, HEIGHT, GOAL_TOP_Y, GOAL_BOTTOM_Y, CAR_FRICTION, BALL_FRICTION
from src.objects import Ball, TrainedAICar, SimpleAICar, Goalkeeper
from src.physics import resolve_car_ball, resolve_car_car


class Phase3MasterEnv(gym.Env):
    """Phase 3: Full game with active goalkeepers and sparse rewards."""
    
    metadata = {'render_modes': []}
    
    def __init__(self):
        super(Phase3MasterEnv, self).__init__()
        
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

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Reset agent
        self.agent.x, self.agent.y = 200, HEIGHT//2
        self.agent.vx = self.agent.vy = 0
        
        # Reset opponent
        self.opponent.x, self.opponent.y = WIDTH-200, HEIGHT//2
        self.opponent.vx = self.opponent.vy = 0
        
        # Reset goalkeepers (ACTIVE in this phase)
        self.gk1.x, self.gk1.y = 50, HEIGHT//2
        self.gk1.vx = self.gk1.vy = 0
        
        self.gk2.x, self.gk2.y = WIDTH-50, HEIGHT//2
        self.gk2.vx = self.gk2.vy = 0
        
        # Reset ball
        self.ball.reset()
        
        # Reset scores and timer
        self.score_agent = 0
        self.score_opponent = 0
        self.frames_passed = 0
        
        obs = self.get_state()
        return obs, {}

    def step(self, action):
        self.frames_passed += 1
        reward = 0.0
        done = False
        
        # 1. Apply agent action
        self.agent.apply_ai_action(action)
        
        # 2. ACTIVE OPPONENT: Chase ball
        self.opponent.chase_ball(self.ball)
        
        # 3. ACTIVE GOALKEEPERS: Both goalkeepers defend
        self.gk1.update_ai(self.ball)
        self.gk2.update_ai(self.ball)
        
        # 4. Update ball physics
        self.ball.update()
        
        # 5. Resolve collisions
        cars = [self.agent, self.opponent, self.gk1, self.gk2]
        for car in cars:
            resolve_car_ball(car, self.ball)
            
        for i in range(len(cars)):
            for j in range(i + 1, len(cars)):
                resolve_car_car(cars[i], cars[j])
        
        # ==========================================
        # PHASE 3 REWARDS: STRICT SPARSE REWARDS
        # ==========================================
        # Remove hand-holding rewards so agent learns strategic positioning
        # and advanced tactics through pure goal-based reinforcement
        
        # A. GOAL SCORED (Right Net) - MASSIVE REWARD
        if self.ball.x + self.ball.radius > WIDTH and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score_agent += 1
            reward += 100.0  # Increased from phase 2
            done = True
        
        # B. OWN GOAL (Left Net) - SIGNIFICANT PENALTY
        elif self.ball.x - self.ball.radius < 0 and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score_opponent += 1
            reward -= 50.0
            done = True
        
        # C. NO TIME PENALTY
        # Remove the -0.01 per frame so agent can take its time and position strategically
        
        # D. TIME LIMIT
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

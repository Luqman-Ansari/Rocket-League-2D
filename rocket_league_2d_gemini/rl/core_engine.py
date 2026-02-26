# rl/core_engine.py
import math
from src.settings import *
from src.objects import Goalkeeper, Ball, SimpleAICar, TrainedAICar
from src.physics import resolve_car_ball, resolve_car_car

class RocketSoccerLogic:
    def __init__(self):
        # The RL Agent (Blue Team - Left side)
        self.agent = TrainedAICar(200, HEIGHT//2, BLUE, 'car_blue', CAR_FRICTION)
        # The Chase Bot (Red Team - Right side)
        self.opponent = SimpleAICar(WIDTH-200, HEIGHT//2, RED, 'car_red', CAR_FRICTION)
        
        # The Goalkeepers (Vertical obstacles)
        self.gk1 = Goalkeeper(50, HEIGHT//2, DARK_BLUE, 'left', 'gk_blue', CAR_FRICTION)
        self.gk2 = Goalkeeper(WIDTH-50, HEIGHT//2, DARK_RED, 'right', 'gk_red', CAR_FRICTION)
        
        self.ball = Ball('ball_soccer', BALL_FRICTION)
        
        self.score_agent = 0
        self.score_opponent = 0
        self.frames_passed = 0
        self.max_frames = 60 * 30 # 30 seconds per episode for fast learning iterations
        
    def reset(self):
        """Resets all entities to starting positions."""
        self.agent.x, self.agent.y = 200, HEIGHT//2
        self.agent.vx = self.agent.vy = 0
        
        self.opponent.x, self.opponent.y = WIDTH-200, HEIGHT//2
        self.opponent.vx = self.opponent.vy = 0

        self.gk1.x, self.gk1.y = 50, HEIGHT//2
        self.gk1.vx = self.gk1.vy = 0

        self.gk2.x, self.gk2.y = WIDTH-50, HEIGHT//2
        self.gk2.vx = self.gk2.vy = 0
        
        self.ball.reset()
        self.frames_passed = 0
        
        return self.get_state()

    def step(self, action):
        """Advances the game by one frame."""
        self.frames_passed += 1
        
        # 1. Apply Actions & Updates
        self.agent.apply_ai_action(action)
        self.opponent.chase_ball(self.ball)
        self.gk1.update_ai(self.ball)
        self.gk2.update_ai(self.ball)
        self.ball.update()
        
        # 2. Resolve Collisions (Agent, Opponent, and both GKs)
        cars = [self.agent, self.opponent, self.gk1, self.gk2]
        for car in cars:
            resolve_car_ball(car, self.ball)
            
        for i in range(len(cars)):
            for j in range(i + 1, len(cars)):
                resolve_car_car(cars[i], cars[j])
                
        # 3. Check Goals & Rewards
        reward = -0.01 # Time penalty
        done = False
        
        # Red Goal (Agent Scored)
        if self.ball.x + self.ball.radius > WIDTH and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score_agent += 1
            reward += 10.0
            done = True
        # Blue Goal (Opponent Scored)
        elif self.ball.x - self.ball.radius < 0 and GOAL_TOP_Y < self.ball.y < GOAL_BOTTOM_Y:
            self.score_opponent += 1
            reward -= 10.0
            done = True
            
        # Time limit check
        if self.frames_passed >= self.max_frames:
            done = True

        return self.get_state(), reward, done

    def get_state(self):
        """
        Returns 14 normalized values to the Neural Network:
        Agent(4), Opponent(4), Ball(4), Goalkeepers Y pos(2)
        """
        return [
            self.agent.x / WIDTH, self.agent.y / HEIGHT,
            self.agent.vx / self.agent.max_speed, self.agent.vy / self.agent.max_speed,
            
            self.opponent.x / WIDTH, self.opponent.y / HEIGHT,
            self.opponent.vx / self.opponent.max_speed, self.opponent.vy / self.opponent.max_speed,
            
            self.ball.x / WIDTH, self.ball.y / HEIGHT,
            self.ball.vx / 15.0, self.ball.vy / 15.0,
            
            self.gk1.y / HEIGHT, self.gk2.y / HEIGHT
        ]
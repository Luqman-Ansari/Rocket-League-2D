# rl/env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from rl.core_engine import RocketSoccerLogic

class RocketSoccerEnv(gym.Env):
    """Custom Environment that follows the Gymnasium interface."""
    
    def __init__(self):
        super(RocketSoccerEnv, self).__init__()
        self.engine = RocketSoccerLogic()
        
        # Actions: 0: Nothing, 1: Up, 2: Down, 3: Left, 4: Right
        self.action_space = spaces.Discrete(5)
        
        # Observation space now expects an array of 14 floats
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(14,), 
            dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs = self.engine.reset()
        obs = np.array(obs, dtype=np.float32)
        return obs, {}

    def step(self, action):
        obs, reward, done = self.engine.step(action)
        obs = np.array(obs, dtype=np.float32)
        
        terminated = done
        truncated = False 
        
        info = {
            'agent_score': self.engine.score_agent,
            'opp_score': self.engine.score_opponent
        }
        return obs, reward, terminated, truncated, info

    def render(self):
        pass
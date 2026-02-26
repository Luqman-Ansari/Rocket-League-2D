# rl/train.py
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stable_baselines3 import PPO
from rl.env import RocketSoccerEnv

class RocketSoccerTrainer:
    def __init__(self, model_version="v2_aggressive", timesteps=1000000):
        self.model_version = model_version
        self.timesteps = timesteps
        self.save_dir = os.path.join(os.path.dirname(__file__), "versions")
        self.env = None
        self.model = None

    def setup(self):
        print("\n=== ROCKET SOCCER AI TRAINING ===")
        print("1. Initializing Environment...")
        os.makedirs(self.save_dir, exist_ok=True)
        self.env = RocketSoccerEnv()

    def build_model(self):
        print("2. Building PPO Brain...")
        self.model = PPO(
            policy="MlpPolicy", 
            env=self.env, 
            verbose=1,
            learning_rate=0.0003,
            device="auto"
        )

    def train(self):
        print(f"3. Starting Training for {self.timesteps} timesteps...")
        if self.model is None:
            self.build_model()
            
        self.model.learn(total_timesteps=self.timesteps)

    def save_model(self):
        save_path = os.path.join(self.save_dir, self.model_version)
        self.model.save(save_path)
        print(f"\n4. Success! Model securely saved to: {save_path}.zip")

if __name__ == "__main__":
    # 1 MILLION STEPS for the real brain!
    trainer = RocketSoccerTrainer(model_version="v2_aggressive", timesteps=1000000)
    
    trainer.setup()
    trainer.build_model()
    trainer.train()
    trainer.save_model()
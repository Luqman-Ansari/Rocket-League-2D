# rl/train.py
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stable_baselines3 import PPO, DQN
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
        self.model = DQN(
            policy="MlpPolicy", 
            env=self.env, 
            learning_rate=1e-3,
            buffer_size=100000,      # Can remember 100,000 frames of gameplay
            learning_starts=1000,    # Plays randomly for 1000 frames to fill memory before learning
            batch_size=64,
            gamma=0.99,
            exploration_fraction=0.2, # Forces it to try random moves for the first 20% of training!
            target_update_interval=500, # This is the "Double" part of DDQN
            verbose=1,
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
    trainer = RocketSoccerTrainer(model_version="v2_aggressive", timesteps=500000)
    
    trainer.setup()
    trainer.build_model()
    trainer.train()
    trainer.save_model()
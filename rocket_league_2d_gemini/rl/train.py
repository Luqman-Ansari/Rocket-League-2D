# rl/train.py
import os
import sys

# Ensure Python can find the 'src' directory for your game files
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stable_baselines3 import PPO
from rl.env import RocketSoccerEnv

class RocketSoccerTrainer:
    """Manages the Reinforcement Learning training pipeline."""
    
    def __init__(self, model_version="v1", timesteps=20000):
        self.model_version = model_version
        self.timesteps = timesteps
        
        # Save path will be directly in your rl/versions/ folder
        self.save_dir = os.path.join(os.path.dirname(__file__), "versions")
        self.env = None
        self.model = None

    def setup(self):
        """Initializes the Gymnasium environment and save directories."""
        print("\n=== ROCKET SOCCER AI TRAINING ===")
        print("1. Initializing Environment...")
        os.makedirs(self.save_dir, exist_ok=True)
        self.env = RocketSoccerEnv()

    def build_model(self):
        """Creates the PPO neural network."""
        print("2. Building PPO Brain...")
        self.model = PPO(
            policy="MlpPolicy", 
            env=self.env, 
            verbose=1, # Prints the progress tables to your terminal
            learning_rate=0.0003,
            device="auto" # Automatically uses your CPU locally, and GPU when on Colab
        )

    def train(self):
        """Executes the learning loop."""
        print(f"3. Starting Training for {self.timesteps} timesteps...")
        if self.model is None:
            self.build_model()
            
        self.model.learn(total_timesteps=self.timesteps)

    def save_model(self):
        """Saves the trained model to the versions directory."""
        save_path = os.path.join(self.save_dir, self.model_version)
        self.model.save(save_path)
        print(f"\n4. Success! Model securely saved to: {save_path}.zip")


if __name__ == "__main__":
    trainer = RocketSoccerTrainer(model_version="v1", timesteps=20000)
    
    trainer.setup()
    trainer.build_model()
    trainer.train()
    trainer.save_model()
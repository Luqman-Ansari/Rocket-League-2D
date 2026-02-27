#!/usr/bin/env python3
"""
UNIFIED CURRICULUM TRAINER
Easily switch between phases and load checkpoints for curriculum learning.
"""

import os
import sys
from datetime import datetime
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor

# ==========================================
# CONFIGURATION BLOCK - EDIT HERE
# ==========================================

# Set the current training phase (1, 2, or 3)
PHASE = 1

# Load a checkpoint to continue training (None to start fresh)
LOAD_CHECKPOINT = None  # Example: "models/phase1_v1.zip"

# Model save name (will be prefixed with timestamp)
SAVE_NAME = "phase1_v1"

# Number of training timesteps
TIMESTEPS = 500_000

# ==========================================
# Advanced Settings (Optional)
# ==========================================

# Learning rate
LEARNING_RATE = 1e-4

# Exploration settings
EXPLORATION_FRACTION = 0.3  # Explore for first 30% of training
EXPLORATION_INITIAL_EPS = 1.0
EXPLORATION_FINAL_EPS = 0.05

# Buffer size
BUFFER_SIZE = 100_000

# Network architecture
NET_ARCH = [256, 256]

# Checkpoint frequency (saves every N steps)
CHECKPOINT_FREQ = 50_000

# Evaluation settings
N_EVAL_EPISODES = 10
EVAL_FREQ = 25_000

# ==========================================
# Dynamic Environment Loading
# ==========================================

def load_phase_env(phase):
    """Dynamically loads the correct environment based on phase."""
    if phase == 1:
        from rl.envs import Phase1StrikerEnv
        print("\n" + "="*60)
        print("PHASE 1: THE OPEN NET")
        print("Opponent: Lobotomized | Goalkeepers: Disabled")
        print("Objective: Learn basic driving, ball contact, and scoring")
        print("="*60 + "\n")
        return Phase1StrikerEnv
    elif phase == 2:
        from rl.envs import Phase2DefenderEnv
        print("\n" + "="*60)
        print("PHASE 2: THE 1v1 DUEL")
        print("Opponent: Active | Goalkeepers: Disabled")
        print("Objective: Learn to outmaneuver and defend")
        print("="*60 + "\n")
        return Phase2DefenderEnv
    elif phase == 3:
        from rl.envs import Phase3MasterEnv
        print("\n" + "="*60)
        print("PHASE 3: THE FULL GAME")
        print("Opponent: Active | Goalkeepers: ACTIVE")
        print("Objective: Master advanced tactics with sparse rewards")
        print("="*60 + "\n")
        return Phase3MasterEnv
    else:
        raise ValueError(f"Invalid phase {phase}. Must be 1, 2, or 3.")


def main():
    # Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)
    
    # Load the appropriate environment
    EnvClass = load_phase_env(PHASE)
    env = Monitor(EnvClass())
    eval_env = Monitor(EnvClass())
    
    # Generate unique save path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_save_path = f"models/{SAVE_NAME}_{timestamp}"
    checkpoint_dir = f"checkpoints/{SAVE_NAME}_{timestamp}/"
    log_dir = f"logs/{SAVE_NAME}_{timestamp}/"
    
    print(f"Model will be saved to: {model_save_path}.zip")
    print(f"Checkpoints will be saved to: {checkpoint_dir}")
    print(f"Logs will be saved to: {log_dir}")
    
    # ==========================================
    # Model Creation or Loading
    # ==========================================
    
    if LOAD_CHECKPOINT and os.path.exists(LOAD_CHECKPOINT):
        print(f"\n🔄 Loading checkpoint from: {LOAD_CHECKPOINT}")
        model = DQN.load(
            LOAD_CHECKPOINT,
            env=env,
            learning_rate=LEARNING_RATE,
            buffer_size=BUFFER_SIZE,
            exploration_fraction=EXPLORATION_FRACTION,
            exploration_initial_eps=EXPLORATION_INITIAL_EPS,
            exploration_final_eps=EXPLORATION_FINAL_EPS,
            tensorboard_log=log_dir,
            verbose=1
        )
        print("✅ Checkpoint loaded successfully!")
        print("   Continuing training from existing model...")
    else:
        if LOAD_CHECKPOINT:
            print(f"⚠️  WARNING: Checkpoint '{LOAD_CHECKPOINT}' not found!")
            print("   Starting training from scratch...\n")
        else:
            print("\n🆕 Starting fresh training (no checkpoint loaded)\n")
        
        # Create new model
        model = DQN(
            "MlpPolicy",
            env,
            learning_rate=LEARNING_RATE,
            buffer_size=BUFFER_SIZE,
            learning_starts=1000,
            batch_size=32,
            tau=1.0,
            gamma=0.99,
            train_freq=4,
            gradient_steps=1,
            target_update_interval=1000,
            exploration_fraction=EXPLORATION_FRACTION,
            exploration_initial_eps=EXPLORATION_INITIAL_EPS,
            exploration_final_eps=EXPLORATION_FINAL_EPS,
            policy_kwargs=dict(net_arch=NET_ARCH),
            tensorboard_log=log_dir,
            verbose=1,
            device='auto'  # Automatically use GPU if available
        )
    
    # ==========================================
    # Callbacks
    # ==========================================
    
    # Checkpoint callback: Save model periodically
    checkpoint_callback = CheckpointCallback(
        save_freq=CHECKPOINT_FREQ,
        save_path=checkpoint_dir,
        name_prefix=SAVE_NAME,
        save_replay_buffer=True,
        save_vecnormalize=True,
    )
    
    # Evaluation callback: Periodically evaluate and save best model
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=f"models/best_{SAVE_NAME}_{timestamp}/",
        log_path=log_dir,
        eval_freq=EVAL_FREQ,
        n_eval_episodes=N_EVAL_EPISODES,
        deterministic=True,
        render=False,
    )
    
    callbacks = [checkpoint_callback, eval_callback]
    
    # ==========================================
    # Training
    # ==========================================
    
    print("\n" + "="*60)
    print(f"🚀 STARTING TRAINING")
    print(f"Total Timesteps: {TIMESTEPS:,}")
    print(f"Phase: {PHASE}")
    print(f"Learning Rate: {LEARNING_RATE}")
    print(f"Exploration: {EXPLORATION_INITIAL_EPS} → {EXPLORATION_FINAL_EPS}")
    print(f"Buffer Size: {BUFFER_SIZE:,}")
    print(f"Network: {NET_ARCH}")
    print("="*60 + "\n")
    
    try:
        model.learn(
            total_timesteps=TIMESTEPS,
            callback=callbacks,
            log_interval=100,
            progress_bar=True
        )
        
        print("\n" + "="*60)
        print("✅ TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n" + "="*60)
        print("⚠️  Training interrupted by user")
        print("="*60)
    
    # ==========================================
    # Save Final Model
    # ==========================================
    
    print(f"\n💾 Saving final model to: {model_save_path}.zip")
    model.save(model_save_path)
    print("✅ Model saved successfully!")
    
    # ==========================================
    # Training Summary
    # ==========================================
    
    print("\n" + "="*60)
    print("📊 TRAINING SUMMARY")
    print("="*60)
    print(f"Phase: {PHASE}")
    print(f"Timesteps: {TIMESTEPS:,}")
    print(f"Model saved to: {model_save_path}.zip")
    print(f"Best model saved to: models/best_{SAVE_NAME}_{timestamp}/")
    print(f"Checkpoints saved to: {checkpoint_dir}")
    print(f"Tensorboard logs: {log_dir}")
    print("\n📈 View training progress with:")
    print(f"   tensorboard --logdir {log_dir}")
    print("="*60 + "\n")
    
    env.close()
    eval_env.close()


if __name__ == "__main__":
    main()

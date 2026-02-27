# 🎮 Rocket League 2D - Curriculum Learning Guide

## 📋 Overview

This curriculum learning system progressively trains an RL agent through three distinct phases, each building upon the skills learned in the previous phase.

## 🎯 Three-Phase Curriculum

### Phase 1: The Open Net (Striker Training)
**Goal:** Learn basic driving, ball contact, and scoring

- **Opponent:** Lobotomized (velocity = 0, AI disabled)
- **Goalkeepers:** Disabled
- **Duration:** ~500K timesteps recommended

**Rewards:**
- `+0.05` per frame for velocity pointing toward ball
- `+2.0` for touching the ball
- `+0.5 × ball.vx` bonus if hit toward right
- `+50.0` for scoring a goal (ends episode)
- `-2.0` for own goal (ends episode)
- `-0.01` time penalty per frame

**What the agent learns:**
- Basic movement controls
- Ball chasing behavior
- How to make contact with the ball
- Scoring into an open net

---

### Phase 2: The 1v1 Duel (Defender Training)
**Goal:** Learn to outmaneuver a moving opponent and defend

- **Opponent:** Active (chase AI enabled)
- **Goalkeepers:** Disabled
- **Duration:** ~750K timesteps recommended

**Rewards:**
- `+1.0` for touching the ball (reduced from Phase 1)
- `+5.0` for saves/clears (hitting ball away from defensive zone)
- `+50.0` for scoring a goal (ends episode)
- `-20.0` for conceding a goal (ends episode)
- `-0.01` time penalty per frame

**What the agent learns:**
- Competing against a moving opponent
- Defensive positioning
- Intercepting the ball
- Balancing offense and defense

---

### Phase 3: The Full Game (Master Training)
**Goal:** Discover advanced tactics through sparse rewards

- **Opponent:** Active (chase AI enabled)
- **Goalkeepers:** ACTIVE (both teams)
- **Duration:** ~1M timesteps recommended

**Rewards:**
- `+100.0` for scoring a goal (ends episode)
- `-50.0` for conceding a goal (ends episode)
- **No time penalty** (encourages strategic positioning)
- **No touch/velocity rewards** (pure goal-based learning)

**What the agent learns:**
- Advanced tactics (wall bounces, jukes)
- Strategic positioning without explicit rewards
- Playing against full defense
- Long-term planning

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install stable-baselines3[extra] gymnasium numpy torch
```

### 2. Training Phase 1

Edit [rl/train_curriculum.py](rl/train_curriculum.py):

```python
PHASE = 1
LOAD_CHECKPOINT = None
SAVE_NAME = "phase1_striker"
TIMESTEPS = 500_000
```

Then run:

```bash
python rl/train_curriculum.py
```

### 3. Training Phase 2 (with Phase 1 checkpoint)

After Phase 1 completes, load the trained model:

```python
PHASE = 2
LOAD_CHECKPOINT = "models/phase1_striker_<timestamp>.zip"
SAVE_NAME = "phase2_defender"
TIMESTEPS = 750_000
```

### 4. Training Phase 3 (with Phase 2 checkpoint)

```python
PHASE = 3
LOAD_CHECKPOINT = "models/phase2_defender_<timestamp>.zip"
SAVE_NAME = "phase3_master"
TIMESTEPS = 1_000_000
```

---

## 📊 Monitoring Training

### TensorBoard

View training progress in real-time:

```bash
tensorboard --logdir logs/
```

Then open: http://localhost:6006

### Key Metrics to Watch

- **Reward Mean:** Should increase over time
- **Episode Length:** May vary by phase
- **Success Rate:** Goal scoring percentage

---

## 💾 Checkpoints & Model Management

### Automatic Checkpoints

Models are automatically saved every 50K timesteps to:
```
checkpoints/<save_name>_<timestamp>/
```

### Best Model

The best performing model (based on evaluation) is saved to:
```
models/best_<save_name>_<timestamp>/
```

### Manual Checkpoint Loading

To continue from a specific checkpoint:

```python
LOAD_CHECKPOINT = "checkpoints/phase1_striker_20260227_143022/phase1_striker_250000_steps.zip"
```

---

## ⚙️ Advanced Configuration

### Hyperparameters

Edit these in [train_curriculum.py](rl/train_curriculum.py):

```python
# Learning rate (lower = more stable, higher = faster but unstable)
LEARNING_RATE = 1e-4

# Exploration settings
EXPLORATION_FRACTION = 0.3      # Explore for first 30% of training
EXPLORATION_INITIAL_EPS = 1.0   # Start exploring randomly
EXPLORATION_FINAL_EPS = 0.05    # End with 5% random actions

# Memory buffer
BUFFER_SIZE = 100_000

# Network architecture
NET_ARCH = [256, 256]  # Two hidden layers with 256 neurons each
```

### Episode Length

Edit `max_frames` in each environment file:

```python
self.max_frames = 60 * 30  # 30 seconds at 60 FPS = 1800 frames
```

---

## 🎮 Testing Trained Models

To test a trained model in the actual game, update your game code to load the model:

```python
from stable_baselines3 import DQN

# Load the trained model
model = DQN.load("models/phase3_master_final.zip")

# In your game loop:
obs = env.get_state()
action, _states = model.predict(obs, deterministic=True)
```

---

## 📈 Expected Training Timeline

| Phase | Timesteps | Wall Time (GPU) | Wall Time (CPU) |
|-------|-----------|----------------|-----------------|
| Phase 1 | 500K | ~1-2 hours | ~4-6 hours |
| Phase 2 | 750K | ~2-3 hours | ~6-9 hours |
| Phase 3 | 1M | ~3-4 hours | ~8-12 hours |
| **Total** | **2.25M** | **~6-9 hours** | **~18-27 hours** |

*Times are approximate and depend on hardware*

---

## 🐛 Troubleshooting

### Issue: Training is too slow
- **Solution:** Use a GPU-enabled PyTorch installation
- Check with: `python -c "import torch; print(torch.cuda.is_available())"`

### Issue: Agent not learning in Phase 3
- **Solution:** Phase 3 has sparse rewards - may need longer training
- Try reducing `EXPLORATION_FINAL_EPS` to 0.02 for more exploitation

### Issue: Memory error during training
- **Solution:** Reduce `BUFFER_SIZE` to 50_000 or lower
- Or reduce `NET_ARCH` to `[128, 128]`

### Issue: Model file not found
- **Solution:** Check the exact filename with timestamp
- List files: `ls models/` or `dir models`

---

## 📁 Project Structure

```
rl/
├── envs/
│   ├── __init__.py
│   ├── phase1_striker.py      # Phase 1 environment
│   ├── phase2_defender.py     # Phase 2 environment
│   └── phase3_master.py       # Phase 3 environment
├── train_curriculum.py        # Main training script
├── env.py                     # Original environment (legacy)
└── core_engine.py            # Game logic engine

models/                        # Saved models
checkpoints/                   # Training checkpoints
logs/                          # TensorBoard logs
```

---

## 🎓 Tips for Best Results

1. **Don't skip phases** - Each phase builds on the previous one
2. **Monitor TensorBoard** - Watch for plateaus and adjust hyperparameters
3. **Save often** - Don't lose progress to crashes or interruptions
4. **Experiment with rewards** - Fine-tune reward values in environment files
5. **Use GPU if available** - 3-4x faster training
6. **Be patient with Phase 3** - Sparse rewards take longer to converge

---

## 📚 Further Reading

- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [DQN Paper](https://arxiv.org/abs/1312.5602)
- [Curriculum Learning Paper](https://ronan.collobert.com/pub/matos/2009_curriculum_icml.pdf)

---

## 📝 License

This curriculum learning system is part of the Rocket League 2D project.

---

**Happy Training! 🚀⚽**

# train.py
# Training script for Pitch game using NFSP self-play.
# Uses minimal params to avoid keyword errors; relies on RLCard defaults for networks.

import os
import numpy as np
import matplotlib.pyplot as plt
import rlcard  # For utils.is_cuda_available

from rlcard.agents import NFSPAgent, RandomAgent
from rlcard.utils import tournament

from RLPitch.env import PitchEnv

# Config
NUM_EPISODES = 1_000_000
EVAL_INTERVAL = 10_000
EVAL_EPISODES = 1000
SAVE_DIR = './models/pitch_nfsp'
os.makedirs(SAVE_DIR, exist_ok=True)

# Create env
config = {'seed': 42, 'allow_step_back': True}
env = PitchEnv(config=config)

# Flattened observation size
flat_obs_size = np.prod(env.state_shape[0])
print(f"Flattened observation size: {flat_obs_size}")

# Create 4 NFSP agents (minimal args - RLCard will use default hidden layers)
agents = [NFSPAgent(
    num_actions=env.game.get_num_actions(),
    state_shape=flat_obs_size,  # Scalar flattened size
    hidden_layers_sizes=[128, 128],
    device='cuda',
    # Remove mlp_layers / hidden_layers_sizes - let RLCard use defaults (usually [64, 64] or similar)
) for _ in range(4)]

env.set_agents(agents)

# Random agents for evaluation
random_agents = [RandomAgent(num_actions=env.game.get_num_actions()) for _ in range(4)]

win_rates = []
print("Starting NFSP training...")

for episode in range(1, NUM_EPISODES + 1):
    env.run(is_training=True)  # Self-play episode

    if episode % EVAL_INTERVAL == 0:
        env.set_agents(random_agents)
        payoffs = [tournament(env, EVAL_EPISODES)[0] for _ in range(4)]
        avg_win_rate = np.mean([p > 0 for p in payoffs])
        win_rates.append(avg_win_rate)
        print(f"Episode {episode}: Avg win rate vs random: {avg_win_rate:.3f}")

        for i, agent in enumerate(agents):
            agent.save_weights(os.path.join(SAVE_DIR, f'nfsp_player{i}_ep{episode}.pth'))

        env.set_agents(agents)  # Back to training

# Plot
plt.plot(range(EVAL_INTERVAL, NUM_EPISODES + 1, EVAL_INTERVAL), win_rates)
plt.xlabel('Episodes')
plt.ylabel('Win Rate vs Random')
plt.title('NFSP Training Progress for Pitch')
plt.savefig(os.path.join(SAVE_DIR, 'training_curve.png'))
plt.show()

print("Training complete! Models saved in", SAVE_DIR)
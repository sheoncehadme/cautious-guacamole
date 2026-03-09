# train.py
# Training script for Pitch game using NFSP self-play.
# Corrected network input size to match your env's obs shape (74).

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

# Get actual observation size from env
obs_shape = env.state_shape[0]  # Should be 74 in your case
print(f"Using observation shape: {obs_shape}")

# Create 4 NFSP agents with correct input size
agents = [NFSPAgent(
    num_actions=env.game.get_num_actions(),
    state_shape=obs_shape,  # Explicitly use your env's obs size
    hidden_layers_sizes=[128, 128],  # Average policy network layers
    q_hidden_layers_sizes=[128, 128],  # Q network layers (separate to avoid mismatch)
    device='cuda'
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
# train.py
import rlcard
from rlcard.agents import NFSPAgent, RandomAgent
from RLPitch.env import PitchEnv
import numpy as np
import os

# Config
NUM_EPISODES = 1_000_000  # 1M for good convergence
EVAL_INTERVAL = 10_000  # Evaluate every 10k
SAVE_DIR = './models/pitch_nfsp'
os.makedirs(SAVE_DIR, exist_ok=True)

# Create env
config = {'seed': 42, 'allow_step_back': True}
env = PitchEnv(config=config)

# 4 NFSP agents for self-play
agents = [NFSPAgent(
    num_actions=env.game.get_num_actions(),
    state_shape=env.state_shape[0],
    action_shape=env.action_shape,
    hidden_sizes=[64, 64],
    q_mlp_layers=[64, 64],
    mlp_layers=[64, 64],
    device='cuda' if rlcard.utils.is_cuda_available() else 'cpu'
) for _ in range(4)]

env.set_agents(agents)

# Eval against random
eval_agents = [RandomAgent(num_actions=env.game.get_num_actions()) for _ in range(4)]

print("Starting NFSP training...")

win_rates = []
for episode in range(1, NUM_EPISODES + 1):
    env.run(is_training=True)  # Self-play

    if episode % EVAL_INTERVAL == 0:
        env.set_agents(eval_agents)
        eval_traj, eval_payoffs = env.run(is_training=False)
        win_rate = np.mean([p > 0 for p in eval_payoffs])  # Fraction positive payoffs (wins)
        win_rates.append(win_rate)
        print(f"Episode {episode}: Win rate vs random: {win_rate:.3f}")

        # Save models
        for i, agent in enumerate(agents):
            agent.save_weights(f"{SAVE_DIR}/nfsp_player{i}_ep{episode}.pth")

        env.set_agents(agents)  # Back to training

# Plot
import matplotlib.pyplot as plt
plt.plot(range(EVAL_INTERVAL, NUM_EPISODES + 1, EVAL_INTERVAL), win_rates)
plt.xlabel('Episodes')
plt.ylabel('Win Rate vs Random')
plt.title('NFSP Training')
plt.savefig(f"{SAVE_DIR}/curve.png")
plt.show()

# Test
env.set_agents(agents)
test_traj, test_payoffs = env.run(is_training=False)
print("Test payoffs:", test_payoffs)
# train.py
# Training script for Pitch game using NFSP self-play.
# Loads your PitchEnv and trains 4 NFSP agents.
# Evaluates vs random every 10k episodes, saves models.
# Run: python3 train.py

import os
import numpy as np
import matplotlib.pyplot as plt
import rlcard  # Add this import for rlcard.utils

from rlcard.agents import NFSPAgent, RandomAgent
from rlcard.utils import tournament  # For evaluation

from RLPitch.env import PitchEnv
from main import log_hand

# Config
NUM_EPISODES = 1_000  # Adjust based on time/GPU
EVAL_INTERVAL = 10_000  # Evaluate every N episodes
EVAL_EPISODES = 1000  # Games per evaluation
SAVE_DIR = './models/pitch_nfsp'
os.makedirs(SAVE_DIR, exist_ok=True)

# Create env with your config
config = {'seed': 42, 'allow_step_back': True}  # Step-back for NFSP
env = PitchEnv(config=config)
print(env.state_shape)
# Create 4 NFSP agents for self-play
agents = [NFSPAgent(
    num_actions=env.game.get_num_actions(),
    state_shape=env.state_shape,
    hidden_layers_sizes=[128, 128],  # Layers for both average policy and Q
    q_mlp_layers=[128, 128],
    device='cuda'
) for _ in range(4)]

env.set_agents(agents)

# Random agents for evaluation
random_agents = [RandomAgent(num_actions=env.game.get_num_actions()) for _ in range(4)]

win_rates = []
print("Starting NFSP training...")

for episode in range(1, NUM_EPISODES + 1):
    hand_num = 1
while max(env.game.team_scores) < 34:
    state, player_id = env.game.init_game()  # Deal and start bidding
    print(f" State: {env.get_state(player_id)} ")

    log_hand(env, hand_num, "initial")

    # Step through bidding and declare trump
    while env.game.round.phase in ['bidding', 'declare_trump']:
        state = env.get_state(player_id)
        action = agents[player_id].step(state)
        state, player_id = env.step(action)

    log_hand(env, hand_num, "bids")

    # Log post-discard (after kitty)
    log_hand(env, hand_num, "post_discard")

    # Step through play
    max_steps = 0
    while not env.is_over():
        state = env.get_state(player_id)
        action = agents[player_id].step(state)
        state, player_id = env.step(action)
        # print(f" State: {env.get_state(player_id)} ")
        # max_steps += 1
        # if max_steps > 10000:
        #     print(f" State: {env.get_state(player_id)} ")
        #     print("Max steps reached in play phase, possible loop. Ending hand.")
        #     break

    log_hand(env, hand_num, "plays")
    log_hand(env, hand_num, "scoring")

    hand_num += 1

    if episode % EVAL_INTERVAL == 0:
        # Evaluate vs random
        env.set_agents(random_agents)
        res = tournament(env, EVAL_EPISODES)
        print(f"Tournament result type: {type(res)}, value: {res}")

        payoffs = [tournament(env, EVAL_EPISODES)[0] for _ in range(4)]  # Avg payoff per player
        avg_win_rate = np.mean([p > 0 for p in payoffs])  # Fraction wins
        win_rates.append(avg_win_rate)
        print(f"Episode {episode}: Avg win rate vs random: {avg_win_rate:.3f}")

        # Save models
        for i, agent in enumerate(agents):
            agent.save_weights(os.path.join(SAVE_DIR, f'nfsp_player{i}_ep{episode}.pth'))

        env.set_agents(agents)  # Back to training

# Plot training curve
plt.plot(range(EVAL_INTERVAL, NUM_EPISODES + 1, EVAL_INTERVAL), win_rates)
plt.xlabel('Episodes')
plt.ylabel('Win Rate vs Random')
plt.title('NFSP Training Progress for Pitch')
plt.savefig(os.path.join(SAVE_DIR, 'training_curve.png'))
plt.show()

print("Training complete! Models saved in", SAVE_DIR)
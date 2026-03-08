from RLPitch.env import PitchEnv  # Adjust relative path/case if needed
from rlcard.agents.random_agent import RandomAgent

# Usage example
env = PitchEnv(config={'seed': 42, 'allow_step_back': False, 'name': 'pitch'})  # Add this key
agents = [RandomAgent(num_actions=env.game.get_num_actions()) for _ in range(4)]
env.set_agents(agents)
trajectories, payoffs = env.run(is_training=True)
print(payoffs)
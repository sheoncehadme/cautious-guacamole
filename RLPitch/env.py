# RLPitch/env.py
from typing import Any, Dict, List

import numpy as np
from rlcard.envs.env import Env
from RLPitch.Game import PitchGame
from .utils import PASS_ACTION

class PitchEnv(Env):
    def __init__(self, config=None):
        self.name = 'pitch'
        self.game = PitchGame(allow_step_back=config.get('allow_step_back', False))
        super().__init__(config)
        self.state_shape = [[1, 4, 54 + 10]]
        self.action_shape = [None]

    def _extract_state(self, state: Dict) -> Dict:
        obs = np.zeros(54 + 20, dtype=np.float32)
        action_ids = self.game.get_legal_actions()
        if not action_ids:
            action_ids = [PASS_ACTION]
        legal_actions = {aid: None for aid in action_ids}
        raw_legal_actions = [str(i) for i in action_ids]
        return {'obs': obs, 'legal_actions': legal_actions, 'raw_obs': state, 'raw_legal_actions': raw_legal_actions}

    def _decode_action(self, action_id: int) -> Any:
        return action_id

    def get_payoffs(self) -> List[float]:
        return self.game.get_payoffs()

    def step(self, action, raw_action=False):
        # Get current legal actions
        legal_actions = self.game.get_legal_actions()
        if not legal_actions:
            print("Legal actions empty, force advancing player.")
            self.game.current_player = (self.game.current_player + 1) % self.game.num_players
            state = self.get_state(self.game.get_player_id())
            return state, self.game.get_player_id()

        # Validate action
        if action not in legal_actions:
            print(f"Invalid action {action} (legal: {legal_actions}), choosing random legal.")
            action = np.random.choice(legal_actions)

        return super().step(action, raw_action)
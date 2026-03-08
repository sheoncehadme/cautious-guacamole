# rlpitch/env.py
from typing import Any, Dict, List

import numpy as np
from rlcard.envs.env import Env  # Assuming this import works; adjust if needed
from RLPitch.Game import PitchGame

class PitchEnv(Env):
    def __init__(self, config=None):
        self.name = 'env'
        self.game = PitchGame(allow_step_back=config.get('allow_step_back', False))
        super().__init__(config)
        self.state_shape = [[1, 4, 54 + 10]]
        self.action_shape = [None]

    def _extract_state(self, state: Dict) -> Dict:
        obs = np.zeros(54 + 20, dtype=np.float32)
        action_ids = self.game.get_legal_actions()
        legal_actions = {aid: None for aid in action_ids}
        raw_legal_actions = [str(i) for i in action_ids]
        return {'obs': obs, 'legal_actions': legal_actions, 'raw_obs': state, 'raw_legal_actions': raw_legal_actions}

    def _decode_action(self, action_id: int) -> Any:
        return action_id

    def get_payoffs(self) -> List[float]:
        return self.game.get_payoffs()
    
    def _extract_state(self, state: Dict) -> Dict:
        # Stub: Encode hand one-hot, phase, etc.
        obs = np.zeros(54 + 20, dtype=np.float32)  # Adjust
        action_ids = self.game.get_legal_actions()  # List of int
        legal_actions = {aid: None for aid in action_ids}  # Dict with dummy values
        raw_legal_actions = [str(i) for i in action_ids]
        return {'obs': obs, 'legal_actions': legal_actions, 'raw_obs': state, 'raw_legal_actions': raw_legal_actions}
    
    def step(self, action, raw_action=False):
        if len(self.game.get_legal_actions()) == 0:
            # Skip turn for players with no cards
            self.game.current_player = (self.game.current_player + 1) % self.game.num_players
            state = self.get_state(self.game.get_player_id())
            return state, self.game.get_player_id()
        return super().step(action, raw_action)
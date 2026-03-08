import numpy as np

from typing import Any, Dict, List

from RLPitch.Player import PitchPlayer
from RLPitch.Dealer import PitchDealer
from RLPitch.Round import PitchRound
from RLPitch.Judger import PitchJudger

PASS_ACTION = 11

class PitchGame:

    def __init__(self, allow_step_back=False):
        self.name = 'pitch'
        self.allow_step_back = allow_step_back
        self.np_random = np.random
        self.num_players = 4
        self.players = [PitchPlayer(i, i % 2) for i in range(4)]
        self.dealer = PitchDealer(self.np_random)
        self.judger = PitchJudger()
        self.round = None
        self.state = {}
        self.team_scores = [0, 0]  # Cumulative

    def init_game(self):
        self.dealer.shuffle()
        self.dealer.deal_cards(self.players)
        self.round = PitchRound(self.players, self.judger, self.dealer, self.np_random)
        self.current_player = 0
        self.state = self.get_state(self.current_player)
        return self.state, self.current_player

    def step(self, action: int):
        if action == PASS_ACTION:
            self.current_player = (self.current_player + 1) % 4
        else:
            self.round.proceed_action(action)
        self.state = self.get_state(self.current_player)
        if self.is_over():
            score_changes = self.judger.judge_hand(self.state)
            self.team_scores[0] += score_changes[0]
            self.team_scores[1] += score_changes[1]
            for i, p in enumerate(self.players):
                p.score = self.team_scores[p.team_id]
        return self.state, self.current_player
    
    def get_state(self, player_id: int) -> Dict[str, Any]:
        state = {
            'hand': self.players[player_id].hand.copy(),
            'current_player': self.current_player,
            'phase': self.round.phase,
            'bids': self.round.bids.copy(),
            'high_bid': self.round.high_bid,
            'high_bidder': self.round.high_bidder,
            'high_bidder_team': self.round.high_bidder_team,
            'trump': self.round.trump,
            'played_history': self.round.played_history.copy(),
            'current_trick': self.round.current_trick.copy(),
            'teams': [p.team_id for p in self.players],
            'team_scores': self.team_scores.copy(),
        }
        return state

    def is_over(self) -> bool:
        return self.round.is_over() if self.round else False

    def get_payoffs(self) -> List[float]:
        # For RL: Per-hand score changes, or 1/-1 if win/set, but stub as normalized scores
        payoffs = [0.0] * 4
        for i, p in enumerate(self.players):
            payoffs[i] = p.score / 34.0  # Progress to win
        # Adjust for teams: positive for winning team if >=34
        if max(self.team_scores) >= 34:
            winning_team = np.argmax(self.team_scores)
            for i in range(4):
                payoffs[i] = 1.0 if self.players[i].team_id == winning_team else -1.0
        return payoffs

    def get_legal_actions(self) -> List[int]:
        return self.judger.get_legal_actions(self.state, self.current_player)

    def get_num_actions(self) -> int:
        return 12  # Max bids, but play up to 6-9 hand size; use dynamic legal
    
    def get_num_players(self):
        return self.num_players
    
    def get_player_id(self):
        return self.current_player
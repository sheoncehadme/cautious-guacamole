# rlpitch/player.py
# Custom PitchPlayer class, standalone (no RLCard dependency).

from typing import List
from RLPitch.Card import Card  # If using custom Card; else import as needed

class PitchPlayer:
    def __init__(self, player_id: int, team_id: int):
        self.player_id = player_id
        self.team_id = team_id
        self.name = 'player'
        self.score = 0  # Cumulative
        self.hand: List[Card] = []  # List of cards in hand
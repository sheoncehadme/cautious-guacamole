from typing import List
from RLPitch.Card import Card
from RLPitch.Player import PitchPlayer

class PitchDealer:
    def __init__(self, np_random):
        self.name = 'dealer'
        self.np_random = np_random
        self.deck = [Card(suit, rank) for suit in 'SHDC' for rank in 'AKQJT98765432']
        self.deck.append(Card('J', 'H'))
        self.deck.append(Card('J', 'L'))
        self.remaining_deck = []

    def shuffle(self):
        self.remaining_deck = self.deck.copy()
        self.np_random.shuffle(self.remaining_deck)

    def deal_cards(self, players: List[PitchPlayer], num_cards: int = 9):
        for player in players:
            player.hand = [self.remaining_deck.pop() for _ in range(num_cards)]
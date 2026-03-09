# RLPitch/Dealer.py
from typing import List

from RLPitch.Card import Card

from RLPitch.Player import PitchPlayer

class PitchDealer:
    def __init__(self, np_random):
        self.np_random = np_random
        self.deck = [Card(suit, rank) for suit in 'SHDC' for rank in 'AKQJT98765432']
        self.deck.append(Card('J', 'H'))
        self.deck.append(Card('J', 'L'))
        self.remaining_deck = []
        print("Dealer initialized with full deck of", len(self.deck), "cards.")

    def shuffle(self):
        self.remaining_deck = self.deck.copy()
        self.np_random.shuffle(self.remaining_deck)
        print("Deck shuffled. Remaining cards:", len(self.remaining_deck))

    def deal_cards(self, players: List[PitchPlayer], num_cards: int = 9):
        if len(self.remaining_deck) < num_cards * len(players):
            print("Warning: Not enough cards in deck for deal!")
            return
        for player in players:
            player.hand = [self.remaining_deck.pop() for _ in range(num_cards)]
            print(f"Dealt {num_cards} cards to Player {player.player_id}. Hand size: {len(player.hand)}")
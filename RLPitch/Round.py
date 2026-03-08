from typing import List

from RLPitch.Player import PitchPlayer
from RLPitch.Judger import PitchJudger
from RLPitch.Dealer import PitchDealer

from .utils import SUIT_NAMES, is_trump

class PitchRound:
    def __init__(self, players: List[PitchPlayer], judger: PitchJudger, dealer: PitchDealer, np_random):
        self.name = 'round'
        self.current = 0
        self.players = players
        self.judger = judger
        self.dealer = dealer
        self.np_random = np_random
        self.current_player = 0  # Starts with bidding
        self.bids = [-1] * 4
        self.high_bid = -1
        self.high_bidder = -1
        self.high_bidder_team = -1
        self.trump = None
        self.phase = 'bidding'  # 'bidding', 'declare_trump', 'discard', 'redeal', 'kitty', 'play'
        self.played_history = []  # List of (pid, card)
        self.current_trick = []

    def proceed_action(self, action: int):
        if self.phase == 'bidding':
            self.proceed_bidding(action)
        elif self.phase == 'declare_trump':
            self.trump = SUIT_NAMES[action]
            self.phase = 'discard'
            self.discard_phase()
            self.phase = 'redeal'
            self.redeal_phase()
            self.phase = 'kitty'
            self.kitty_phase()
            self.phase = 'play'
            self.current_player = self.high_bidder  # Leads
        elif self.phase == 'play':
            self.proceed_trick(action)

    def proceed_bidding(self, action: int):
        if action < 10:
            if action > self.high_bid:
                self.high_bid = action
                self.high_bidder = self.current_player
                self.high_bidder_team = self.players[self.current_player].team_id
        self.bids[self.current_player] = action
        self.current_player = (self.current_player + 1) % 4
        if all(b >= 0 for b in self.bids):
            if self.high_bid > -1:
                self.phase = 'declare_trump'
                self.current_player = self.high_bidder
            else:
                # No bids, redeal? Stub: assume always bid
                pass

    def discard_phase(self):
        for player in self.players:
            trump_cards = [c for c in player.hand if is_trump(c, self.trump)]
            if len(trump_cards) > 6:
                self.np_random.shuffle(trump_cards)
                player.hand = trump_cards[:6]
            else:
                player.hand = trump_cards

    def redeal_phase(self):
        players_below_6 = [p for p in self.players if len(p.hand) < 6]
        while self.dealer.remaining_deck and players_below_6:
            for player in self.players:  # Clockwise, but since list is 0-3
                if len(player.hand) < 6 and self.dealer.remaining_deck:
                    player.hand.append(self.dealer.remaining_deck.pop())

            players_below_6 = [p for p in self.players if len(p.hand) < 6]

    def kitty_phase(self):
        high_bidder = self.players[self.high_bidder]
        added_trump = [c for c in self.dealer.remaining_deck if is_trump(c, self.trump)]
        high_bidder.hand.extend(added_trump)
        if len(high_bidder.hand) > 6:
            self.np_random.shuffle(high_bidder.hand)
            high_bidder.hand = high_bidder.hand[:6]
        self.dealer.remaining_deck = []  # Clear kitty

    def proceed_trick(self, action: int):
        if not self.players[self.current_player].hand:
            # Skip out players
            self.current_player = (self.current_player + 1) % 4
            return
        card = self.players[self.current_player].hand.pop(action)
        self.played_history.append((self.current_player, card))
        self.current_trick.append((self.current_player, card))
        self.current_player = (self.current_player + 1) % 4
        if len(self.current_trick) == 4 or all(len(p.hand) == 0 for p in self.players[ self.current : ] + self.players[ : self.current ] if len(self.current_trick) < 4):  # Full or all remaining out
            winner_pid = self.judger.judge_trick(self.current_trick, self.trump)
            self.current_trick = []
            self.current_player = winner_pid

    def is_over(self) -> bool:
        return self.phase == 'play' and all(len(p.hand) == 0 for p in self.players)
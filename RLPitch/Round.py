from typing import List

from RLPitch.Player import PitchPlayer
from RLPitch.Judger import PitchJudger
from RLPitch.Dealer import PitchDealer

from .utils import SUIT_NAMES, get_card_power, is_trump, PASS_ACTION

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

        self.tricks = []  # List of won tricks per team (optional, but used in code)

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
            else:
                # Optional: Log invalid bid (shouldn't happen with legal_actions)
                print(f"Warning: Invalid bid {action} <= high_bid {self.high_bid}; treating as pass")
                action = 10
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
        # No burning or discard non-trump; keep initial hand as is
        pass  # Or minimal: print("No discard for non-trump.")

    def redeal_phase(self):
        players_below_6 = [p for p in self.players if len(p.hand) < 6]
        while self.dealer.remaining_deck and players_below_6:
            for player in self.players:
                if len(player.hand) < 6 and self.dealer.remaining_deck:
                    player.hand.append(self.dealer.remaining_deck.pop())

            players_below_6 = [p for p in self.players if len(p.hand) < 6]

    def kitty_phase(self):
        high_bidder = self.players[self.high_bidder]
        trump = self.trump

        # Add trump from kitty
        added_trump = [c for c in self.dealer.remaining_deck if c.is_trump(trump)]
        high_bidder.hand.extend(added_trump)

        # If >6 after add, burn lowest power until 6, log burnt trump
        while len(high_bidder.hand) > 6:
            high_bidder.hand.sort(key=lambda c: get_card_power(c, trump))  # Ascending power (lowest first)
            burnt_card = high_bidder.hand.pop(0)  # Burn lowest
            if burnt_card.is_trump(trump):
                print(f"Player {high_bidder.player_id} burnt trump card: {burnt_card} (out of play)")

        self.dealer.remaining_deck = []  # Clear kitty

    def proceed_trick(self, action: int):
        if action == PASS_ACTION:
            # Skip turn, mark as passed for this trick (but since no mark, just advance)
            self.current_player = (self.current_player + 1) % 4
            return

        if not self.players[self.current_player].hand:
            self.current_player = (self.current_player + 1) % 4
            return

        card = self.players[self.current_player].hand.pop(action)
        self.played_history.append((self.current_player, card))
        self.current_trick.append((self.current_player, card))
        self.current_player = (self.current_player + 1) % 4

        # Check if trick complete: 4 cards or all remaining players have no cards (passed/out)
        remaining_players = [self.current_player + k % 4 for k in range(4 - len(self.current_trick))]
        if len(self.current_trick) == 4 or all(len(self.players[p].hand) == 0 for p in remaining_players):
            if self.current_trick:  # Judge if any cards played
                winner_pid = self.judger.judge_trick(self.current_trick, self.trump)
                winner_team = self.players[winner_pid].team_id
                self.tricks.append((winner_team, [c for _, c in self.current_trick]))  # Optional
                self.current_trick = []
                self.current_player = winner_pid  # Winner leads next
            else:
                # No cards in trick (all passed), skip or end if all out
                self.current_player = (self.current_player + 1) % 4
            # Reset for next trick

    def is_over(self) -> bool:
        return self.phase == 'play' and all(len(p.hand) == 0 for p in self.players)
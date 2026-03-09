from typing import List

from RLPitch.Player import PitchPlayer
from RLPitch.Judger import PitchJudger
from RLPitch.Dealer import PitchDealer

from .utils import SUIT_NAMES, is_trump, get_card_power, PASS_ACTION

class PitchRound:
    def __init__(self, players: List[PitchPlayer], judger: PitchJudger, dealer: PitchDealer, np_random):
        self.name = 'round'
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
        self.tricks = []  # List of won tricks per team (optional)
        self.pass_count = 0  # Consecutive passes

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
                # All passed, redeal (reset for new bidding)
                print("All players passed - redealing for new bidding.")
                self.bids = [-1] * 4
                self.high_bid = -1
                self.high_bidder = -1
                self.high_bidder_team = -1
                self.current_player = 0  # Restart bidding
                # Optional: self.dealer.shuffle() and deal again if full redeal wanted, but per rules, just re-bid

    def redeal_phase(self):
        players_below_6 = [p for p in self.players if len(p.hand) < 6]
        while self.dealer.remaining_deck and players_below_6:
            for player in self.players:
                if len(player.hand) < 6 and self.dealer.remaining_deck:
                    player.hand.append(self.dealer.remaining_deck.pop())

            players_below_6 = [p for p in self.players if len(p.hand) < 6]

    def discard_phase(self):
        for player in self.players:
            if player.player_id == self.high_bidder:
                continue  # Skip for high bidder, keep all until kitty
            trump_cards = [c for c in player.hand if c.is_trump(self.trump)]
            player.hand = trump_cards  # Discard non-trump
            if len(player.hand) > 6:
                self.np_random.shuffle(player.hand)
                player.hand.sort(key=lambda c: get_card_power(c, self.trump))  # Ascending
                burnt = player.hand[6:]
                player.hand = player.hand[:6]
                for b in burnt:
                    print(f"Player {player.player_id} burnt trump card: {b} (out of play)")

    def kitty_phase(self):
        high_bidder = self.players[self.high_bidder]
        trump = self.trump

        # High bidder adds trump from kitty
        added_trump = [c for c in self.dealer.remaining_deck if c.is_trump(trump)]
        high_bidder.hand.extend(added_trump)

        # Burn excess if >6 (now after keeping all + kitty)
        if len(high_bidder.hand) > 6:
            high_bidder.hand.sort(key=lambda c: get_card_power(c, trump))  # Ascending (burn lowest)
            burnt = high_bidder.hand[6:]
            high_bidder.hand = high_bidder.hand[:6]
            for b in burnt:
                if b.is_trump(trump):
                    print(f"Player {high_bidder.player_id} burnt trump card: {b} (out of play)")

        self.dealer.remaining_deck = []  # Clear kitty

    def proceed_trick(self, action: int):
        if action == PASS_ACTION:
            print(f"Player {self.current_player} declares out (no trump left)")
            self.pass_count += 1
            self.current_player = (self.current_player + 1) % 4
            if self.pass_count >= 4:
                self.current_trick = []  # Clear
                self.pass_count = 0
                return
            return

        self.pass_count = 0
        hand = self.players[self.current_player].hand
        if not hand:
            self.current_player = (self.current_player + 1) % 4
            return

        if action >= len(hand) or action < 0:
            print(f"Invalid action {action} for hand size {len(hand)}, choosing random legal")
            trump_indices = [i for i, c in enumerate(hand) if c.is_trump(self.trump)]
            if trump_indices:
                action = self.np_random.choice(trump_indices)
            else:
                action = PASS_ACTION
            if action == PASS_ACTION:
                print(f"Player {self.current_player} declares out (no trump left)")
                self.pass_count += 1
                self.current_player = (self.current_player + 1) % 4
                if self.pass_count >= 4:
                    self.current_trick = []  # Clear
                    self.pass_count = 0
                    return
                return

        card = hand.pop(action)
        self.played_history.append((self.current_player, card))
        self.current_trick.append((self.current_player, card))
        self.current_player = (self.current_player + 1) % 4

        remaining_count = 4 - len(self.current_trick)
        remaining_players = [(self.current_player + k) % 4 for k in range(remaining_count)]
        if len(self.current_trick) == 4 or all(not any(c.is_trump(self.trump) for c in self.players[p].hand) for p in remaining_players):
            if self.current_trick:
                winner_pid = self.judger.judge_trick(self.current_trick, self.trump)
                winner_team = self.players[winner_pid].team_id
                self.tricks.append((winner_team, [c for _, c in self.current_trick]))
            self.current_trick = []
            self.current_player = winner_pid if 'winner_pid' in locals() else (self.current_player + remaining_count) % 4
            self.pass_count = 0

    def is_over(self) -> bool:
        if self.phase != 'play':
            return False
        all_out = all(not any(c.is_trump(self.trump) for c in p.hand) for p in self.players)
        if all_out:
            print("All players out (no trump left), ending hand.")
        return all_out or all(len(p.hand) == 0 for p in self.players)
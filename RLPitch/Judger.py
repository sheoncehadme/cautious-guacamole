from typing import Dict, List
from RLPitch.Card import Card
from .utils import get_card_power, get_card_points, is_low_trump, PASS_ACTION

class PitchJudger:
    def get_legal_actions(self, state: Dict, player_id: int) -> List[int]:
        if state['phase'] == 'bidding':
            high_bid = state.get('high_bid', -1)
            bid_count = state.get('bid_count', 0)
            is_last_bidder = bid_count == 3
            must_bid = is_last_bidder and high_bid == -1
            min_bid = 4 if must_bid else (high_bid + 1)
            valid_bids = [bid for bid in range(min_bid, 10)]
            if not must_bid:
                valid_bids += [10]  # Pass
            return valid_bids
        elif state['phase'] == 'declare_trump':
            return list(range(4))  # 0=S,1=H,2=D,3=C
        elif state['phase'] == 'play':
            hand = state['hand']
            trump = state['trump']
            if not hand:
                return [PASS_ACTION]  # Out (no cards)
            trump_indices = [i for i, c in enumerate(hand) if c.is_trump(trump)]
            if trump_indices:
                return trump_indices  # Must play trump if have
            else:
                return [PASS_ACTION]  # Out (no trump)
        return []

    def judge_trick(self, current_trick: List[tuple[int, Card]], trump: str) -> int:
        if not current_trick:
            return -1  # No winner if empty
        max_power = -1
        winner_id = -1
        for pid, card in current_trick:
            power = get_card_power(card, trump)
            if power > max_power:
                max_power = power
                winner_id = pid
        return winner_id

    def judge_hand(self, state: Dict) -> List[int]:
        trump = state['trump']
        played_history = state['played_history']  # List of (pid, card)
        high_bid = state['high_bid']
        high_bidder_team = state['high_bidder_team']

        team_points = [0, 0]
        for i in range(0, len(played_history), 4):
            trick_plays = played_history[i:i+4]
            winner_pid = self.judge_trick(trick_plays, trump)
            if winner_pid == -1:
                continue
            winner_team = state['teams'][winner_pid]
            for pid, card in trick_plays:
                pts = get_card_points(card, trump)
                score_team = state['teams'][pid] if is_low_trump(card, trump) else winner_team
                team_points[score_team] += pts

        bidder_points = team_points[high_bidder_team]
        opp_team = 1 - high_bidder_team
        if bidder_points >= high_bid:
            score_changes = [team_points[0], team_points[1]]
        else:
            score_changes = [team_points[0] if high_bidder_team != 0 else -high_bid, 
                             team_points[1] if high_bidder_team != 1 else -high_bid]
            score_changes[opp_team] += team_points[opp_team]  # Opp gets theirs

        return score_changes  # [team0_change, team1_change]
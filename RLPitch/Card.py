# rlpitch/card.py
# Custom Card class for Pitch game, based on your rules.
# Suits: 'S' (spades), 'H' (hearts), 'D' (diamonds), 'C' (clubs), 'J' (jokers).
# Ranks: 'A', 'K', 'Q', 'J', 'T' (10), '9'...'2'; for jokers: 'H' (high), 'L' (low).
# Order/power and points depend on trump suit (passed to methods).
# OJ (off jack): Jack of same color/opposite suit as trump, treated as trump with power after J.
# Special: 2 of trump points go to playing team regardless of trick winner.

from typing import Optional

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit.upper()  # Normalize: 'S', 'H', 'D', 'C', 'J'
        self.rank = rank.upper()  # 'A', 'K', 'Q', 'J', 'T', '9'...'2', 'H'/'L' for jokers
        if self.suit not in ['S', 'H', 'D', 'C', 'J']:
            raise ValueError(f"Invalid suit: {suit}")
        if self.suit == 'J' and self.rank not in ['H', 'L']:
            raise ValueError(f"Invalid joker rank: {rank}")
        elif self.suit != 'J' and self.rank not in ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']:
            raise ValueError(f"Invalid rank: {rank}")

    def __repr__(self) -> str:
        return f"{self.rank}{self.suit}"  # e.g., 'AH', 'JS', 'HH' for high joker (but use 'JH' as per rules)

    def __eq__(self, other: 'Card') -> bool:
        return self.suit == other.suit and self.rank == other.rank

    def is_trump(self, trump_suit: str) -> bool:
        """Determine if this card is trump for the given trump suit."""
        if self.suit == trump_suit:
            return True
        if self.suit == 'J':
            return True
        off_suit = self._off_suit(trump_suit)
        if self.rank == 'J' and self.suit == off_suit:
            return True
        return False

    def get_power(self, trump_suit: str) -> int:
        """Get numerical power (higher = better) for trick resolution, based on rules order: A > K > Q > J > OJ > JH > JL > 10 > 9 > ... > 2.
        Non-trump cards have power only if played (but in rules, all plays are trump after discard)."""
        if not self.is_trump(trump_suit):
            return self._base_rank_power()  # Low for non-trump, but adjust if needed

        # Trump order mapping (highest to lowest)
        order_map = {
            'A': 15, 'K': 14, 'Q': 13, 'J': 12,  # Right J (trump suit J)
            'OJ': 11,  # Off jack
            'JH': 10,  # High joker
            'JL': 9,   # Low joker
            'T': 8, '9': 7, '8': 6, '7': 5, '6': 4, '5': 3, '4': 2, '3': 1, '2': 0
        }

        if self.suit == 'J':
            return order_map['JH'] if self.rank == 'H' else order_map['JL']
        elif self.is_off_jack(trump_suit):
            return order_map['OJ']
        else:
            return order_map.get(self.rank, 0)

    def get_points(self, trump_suit: str) -> int:
        """Get points value if this is a trump card (incl. OJ/jokers). Non-trump = 0."""
        if not self.is_trump(trump_suit):
            return 0

        points_map = {
            'A': 1, 'K': 0, 'Q': 0, 'J': 1, 'T': 1, '9': 0, '8': 0, '7': 0, '6': 0, '5': 0, '4': 0, '3': 3, '2': 1
        }

        if self.suit == 'J':
            return 1  # Both jokers 1 point
        elif self.is_off_jack(trump_suit):
            return 1  # OJ 1 point
        else:
            return points_map.get(self.rank, 0)

    def is_low_trump(self, trump_suit: str) -> bool:
        """Check if this is the 2 of trump (special scoring: points to playing team)."""
        return self.rank == '2' and self.is_trump(trump_suit)

    def is_off_jack(self, trump_suit: str) -> bool:
        """Check if this is the off jack for the trump suit."""
        off_suit = self._off_suit(trump_suit)
        return self.rank == 'J' and self.suit == off_suit

    def _off_suit(self, trump_suit: str) -> Optional[str]:
        """Helper: Get off suit for OJ (same color, opposite suit)."""
        if trump_suit in ['H', 'D']:
            return 'D' if trump_suit == 'H' else 'H'
        elif trump_suit in ['S', 'C']:
            return 'C' if trump_suit == 'S' else 'S'
        return None

    def _base_rank_power(self) -> int:
        """Base power for non-trump cards (A high to 2 low)."""
        rank_map = {'A': 15, 'K': 14, 'Q': 13, 'J': 12, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        return rank_map.get(self.rank, 0)
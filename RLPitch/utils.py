import RLPitch.Card as Card

SUITS = {'S': 0, 'H': 1, 'D': 2, 'C': 3}  # For action encoding
SUIT_NAMES = ['S', 'H', 'D', 'C']

def off_suit(trump: str) -> str:
    if trump in ['H', 'D']:
        return 'D' if trump == 'H' else 'H'
    elif trump in ['S', 'C']:
        return 'C' if trump == 'S' else 'S'
    return None

def is_trump(card: Card, trump: str) -> bool:
    if card.suit == trump:
        return True
    if card.suit == 'J':
        return True
    if card.rank == 'J' and card.suit == off_suit(trump):
        return True
    return False

def is_off_jack(card: Card, trump: str) -> bool:
    return card.rank == 'J' and card.suit == off_suit(trump)

def is_low_trump(card: Card, trump: str) -> bool:
    return card.rank == '2' and is_trump(card, trump)

def get_card_power(card: Card, trump: str) -> int:
    rank_map = {'A': 15, 'K': 14, 'Q': 13, 'J': 12, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
    base = 100 if is_trump(card, trump) else 0  # All plays are trump, but kept for consistency
    if card.suit == 'J':
        if card.rank == 'H': return base + 11  # JH after OJ (12), but order: J=12, OJ=11? Wait, previous: A15 K14 Q13 J12 OJ11 JH10 JL9 10=10 ...
        if card.rank == 'L': return base + 10
    elif is_off_jack(card, trump):
        return base + 12  # Adjust based on order: A K Q J OJ JH JL 10 ...
    return base + rank_map.get(card.rank, 0)

def get_card_points(card: Card, trump: str) -> int:
    if not is_trump(card, trump):
        return 0
    points_map = {'A': 1, 'K': 0, 'Q': 0, 'J': 1, 'T': 1, '9': 0, '8': 0, '7': 0, '6': 0, '5': 0, '4': 0, '3': 3, '2': 1}
    if card.suit == 'J':
        return 1
    if is_off_jack(card, trump):
        return 1
    return points_map.get(card.rank, 0)
# main.py
# Manual stepping to log at key phases, with trump count after each play in trick.

from RLPitch.env import PitchEnv
from rlcard.agents.random_agent import RandomAgent

# Helper to pretty-print cards
def print_cards(cards):
    return ", ".join(str(c) for c in cards) if cards else "EMPTY HAND (issue!)"

# Helper to log hand at key points
def log_hand(env, hand_num, phase):
    if phase == "initial":
        print(f"\n=== Hand {hand_num} - Initial Deals ===")
        for i in range(4):
            hand = env.game.players[i].hand
            print(f"Player {i} (Team {i % 2}) hand: {print_cards(hand)} (size: {len(hand)})")
    elif phase == "bids":
        print(f"\n=== Hand {hand_num} - Bids ===")
        for i, bid in enumerate(env.game.round.bids):
            print(f"Player {i}: {bid if bid != 10 else 'Pass'}")
        trump = env.game.round.trump
        print(f"Trump Suit: {trump if trump else 'None'}")
    elif phase == "post_discard":
        print(f"\n=== Hand {hand_num} - After Discard/Redeal/Kitty ===")
        for i in range(4):
            hand = env.game.players[i].hand
            print(f"Player {i} hand: {print_cards(hand)} (size: {len(hand)})")
    elif phase == "plays":
        print(f"\n=== Hand {hand_num} - Plays ===")
        history = env.game.round.played_history
        if not history:
            print("No plays occurred")
            return
        running_team_points = [0, 0]
        trump = env.game.round.trump
        for j in range(0, len(history), 4):
            trick = history[j:j+4]
            print(f"Trick {j//4 + 1}:")
            for pid, card in trick:
                # Count trump left after play (since pop after choice, but history is post)
                trump_left = sum(1 for c in env.game.players[pid].hand if c.is_trump(trump))  # After pop
                print(f"  Player {pid}: {card} (trump left: {trump_left})")
            winner = env.game.judger.judge_trick(trick, trump)
            print(f"  Winner: Player {winner if winner != -1 else 'None (empty trick)'}")
            
            # Calculate points for this trick and add to running
            winner_team = env.game.players[winner].team_id if winner != -1 else -1
            for pid, card in trick:
                pts = card.get_points(trump)
                score_team = env.game.players[pid].team_id if card.is_low_trump(trump) else winner_team
                if score_team != -1:
                    running_team_points[score_team] += pts
            
            # Log running scores after this trick
            print(f"  Scores after trick: Team 0 = {running_team_points[0]}, Team 1 = {running_team_points[1]}")
    elif phase == "scoring":
        print(f"\n=== Hand {hand_num} - Final Scoring ===")
        score_changes = env.game.judger.judge_hand(env.game.state)
        for team in range(2):
            print(f"Team {team} change: {score_changes[team]}")
        print(f"Team Scores: Team 0 = {env.game.team_scores[0]}, Team 1 = {env.game.team_scores[1]}")

# Main
config = {'seed': 42, 'allow_step_back': False}
env = PitchEnv(config=config)
agents = [RandomAgent(num_actions=env.game.get_num_actions()) for _ in range(4)]
env.set_agents(agents)

hand_num = 1
while max(env.game.team_scores) < 34:
    state, player_id = env.game.init_game()  # Deal and start bidding
    print(f" State: {env.get_state(player_id)} ")

    log_hand(env, hand_num, "initial")

    # Step through bidding and declare trump
    while env.game.round.phase in ['bidding', 'declare_trump']:
        state = env.get_state(player_id)
        action = agents[player_id].step(state)
        state, player_id = env.step(action)

    log_hand(env, hand_num, "bids")

    # Log post-discard (after kitty)
    log_hand(env, hand_num, "post_discard")

    # Step through play
    max_steps = 0
    while not env.is_over():
        state = env.get_state(player_id)
        action = agents[player_id].step(state)
        state, player_id = env.step(action)
        max_steps += 1
        if max_steps > 1000:
            print(f" State: {env.get_state(player_id)} ")
            print("Max steps reached in play phase, possible loop. Ending hand.")
            break

    log_hand(env, hand_num, "plays")
    log_hand(env, hand_num, "scoring")

    hand_num += 1

winning_team = 0 if env.game.team_scores[0] >= 34 else 1
print(f"\nGame Over! Team {winning_team} wins with {env.game.team_scores[winning_team]} points.")
from catan2 import read_and_filter_lines, process_game, do, plot_total_dice_stats, only_plot_total_dice_stats
from calculate_rankings import *
from operator import itemgetter
import pprint

pp = pprint.PrettyPrinter(indent=4)


def rankings():
    reset_rankings()
    rankings = read_rankings()
    seen_games = rankings["seen_games"]

    games_to_process = list(filter(lambda g : g not in seen_games, [f"{i}.txt" for i in range(27, 28)]))

    for g in games_to_process:
        lines = read_and_filter_lines(f"gamelogs/{g}")
        res = process_game(lines)

        players, player_points, winner = itemgetter('players', 'player_points', 'winner')(res)
        game_rankings = calculate_game_rankings(players, player_points, winner)
        print("game", g, players, player_points, winner, game_rankings)

        rankings = update_rankings(rankings, game_rankings, g)

        print()
        pp.pprint(rankings)
        print()
    
    pp.pprint(rankings)

    write_rankings(rankings)


    make_graphs()

def game(n):
    do(f"gamelogs/{n}.txt", True, False)

def games(m,n):
    for i in range(m, n+1):
        do(f"gamelogs/{i}.txt", True, False)
        print(f"-------------------------------DONE--------------------------------")
        print(f"-------------------------------{i}--------------------------------")

def reset_dices():
    with open("dice_stats.txt", "w"):
        pass

def main():
    # only_plot_total_dice_stats(True)
    reset_dices()
    reset_rankings()
    games(1,45)
    # game(33)

if __name__ == "__main__":
	main()

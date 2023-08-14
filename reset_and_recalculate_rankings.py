from calculate_rankings import update_rankings_file_directly, reset_rankings, make_graphs
from catan2 import process_game, read_and_filter_lines

import os
# resets rankings, reads all gamelogs again and makes them anew
def main():
	gamelogs = os.listdir('gamelogs')
	
	reset_rankings()

	for gamelog in gamelogs:
		lines = read_and_filter_lines(os.path.join('gamelogs', gamelog))
		res = process_game(lines)

		update_rankings_file_directly(res['players'], res['player_points'], res['winner'], gamelog)



if __name__ == "__main__":
	main()

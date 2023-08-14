import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np


def read_rankings():
	with open("rankings.json") as file:
		rankings = json.load(file)
		return rankings

def write_rankings(rankings):
	with open("rankings.json", "w") as file:
		json.dump(rankings, file, indent = 4)


def update_rankings(current_rankings, game_rankings, game_name):
	current_rankings["seen_games"].append(game_name)
	for started, (finished, points) in game_rankings.items():
		current_rankings[started][finished] += 1
		current_rankings[started]["total_points"] += points
		current_rankings[started]["avg_points"] = current_rankings[started]["total_points"] / len(current_rankings["seen_games"])

	return current_rankings

def calculate_game_rankings(players, player_points, winner):
	print("calculate_game_rankings", players, player_points, winner)
	player_points[players[winner]] = 10
	game_rankings = {}

	for i,p in enumerate(player_points):
		rank = sum(1 for x in player_points if x > p)
		game_rankings[str(i)] = (str(rank), p)


	print("calculated game rankings - input", players, player_points, winner)
	print("calculated game rankings - output", game_rankings)

	return game_rankings

def update_rankings_file_directly(players, player_points, winner, game_name):
	rankings = read_rankings()
	if game_name in rankings["seen_games"]:
		print(f"already seen {game_name}")
		return

	print("update_rankings_file_directly", players, player_points, winner, game_name)
	game_rankings = calculate_game_rankings(players, player_points, winner)
	rankings = update_rankings(rankings, game_rankings, game_name)
	write_rankings(rankings)
	make_graphs()

def reset_rankings():
	rankings = {}
	for i in range(4):
		pos_details = {"total_points": 0, "avg_points": 0.0}
		for j in range(4):
			pos_details[str(j)] = 0
		rankings[str(i)] = pos_details
	rankings["seen_games"] = []

	write_rankings(rankings)


def make_pie_chart(rankings):
	figure = plt.figure(figsize=(13,13))

	i_to_grid = {0: (0,0), 1: (0,1), 2: (1,0), 3: (1,1)}

	for i in range(4):
		pos_details = rankings[str(i)]
		pos_rankings = [pos_details[str(j)] for j in range(4)]
		pos_avgpoints = pos_details["avg_points"]

		def value_str(val):
			value = 0.01 * val * sum(pos_rankings)
			return f"{value:.0f} ({val:.2f}%)"

		#first row, first column
		ax1 = plt.subplot2grid((2,2), i_to_grid[i])
		labels = ["1st", "2nd", "3rd", "4th"]
		plt.pie(pos_rankings, colors=("gold","silver", "peru", "saddlebrown"), labels=labels, autopct=value_str)
		plt.title(f"Starting position {i+1} - Avg. points: {pos_avgpoints:.2f}")

	plt.savefig(f"rankings_piechart.png")


def make_heatmap(rankings):
	results = np.rot90(np.array([[rankings[str(i)][str(j)] for j in range(4)] for i in range(4)]))
	starting_positions = [f"{i+1}." for i in range(4)]
	rankings = [f"{i+1}." for i in range(3, -1, -1)]

	fig, ax = plt.subplots()
	im = ax.imshow(results, cmap="Greys")

	# Show all ticks and label them with the respective list entries
	ax.set_xticks(np.arange(len(starting_positions)), labels=starting_positions)
	ax.set_yticks(np.arange(len(rankings)), labels=rankings)


	plt.xlabel("Starting position")
	plt.ylabel("Ranking")

	# Loop over data dimensions and create text annotations.
	for i in range(len(rankings)):
		for j in range(len(starting_positions)):
			text = ax.text(j, i, results[i, j],
						ha="center", va="center", color="gold")

	ax.set_title("Starting position vs ranking")
	fig.tight_layout()

	plt.savefig(f"rankings_heatmap.png")


def make_graphs():
	rankings = read_rankings()
	make_pie_chart(rankings)
	make_heatmap(rankings)



if __name__ == "__main__":
	make_graphs()

from cmath import log
import matplotlib.pyplot as plt
from collections import defaultdict
import re
from sys import argv
from sys import stdout
import os
import logging
import numpy as np
from itertools import zip_longest

from calculate_rankings import update_rankings_file_directly

logging.basicConfig(
	level=logging.CRITICAL,
	format="%(asctime)s [%(levelname)s] %(message)s",
	handlers=[
		logging.FileHandler("debug.log"),
		logging.StreamHandler(stdout)
	]
)

possible_resources = ["grain", "ore", "wool", "brick", "lumber"]
resource_colors = ["gold", "silver", "lawngreen", "firebrick", "seagreen"]
resource_colors_alt = ["goldenrod", "darkgray", "yellowgreen", "darkred", "darkgreen"]
replacements = [
	("icon_helmet passed from", "Guestlongest road passed from"),
	("Guest passed from", "Guestlongest road passed from"),
	("Guest", ""),
	("User", ""),
	("bot", ""),
	("Settler", ""),
	("icon_helmet", ""),
	("icon_cactus", ""),
	("icon_crown", ""),
	("icon_avocado", ""),
	("Colonist", ""),
	("Christmas", ""),
	("Settle", ""),
	("icon_sombrero", ""),
	("You", "Myrna8511"),
	("you", "Myrna8511"),
	("has passed from", "passed from"),
	("(", ""),
	(")", ""),
]

def check_args():
	assert len(argv) >= 2, "oi you forgot the file"
	file_name = argv[1]

	skip_show = False
	if len(argv) == 3 and argv[2] == "skip":
		skip_show = True

	logging.info(f"check_args finished: {file_name=}, {skip_show=}")

	return file_name, skip_show

def make_folder(folder_name):
	logging.debug(f"make_folder({folder_name})")
	try:
		os.mkdir(folder_name)
		logging.info(f"folder: {folder_name=} made")
	except FileExistsError:
		logging.warning("folder already exists")


def filter_lines(lines):
	filteredLines = []
	for l in lines:
		l = l.strip()
		for r1,r2 in replacements:
			l = l.replace(r1, r2)			
		filteredLines.append(l)
	return filteredLines

def read_and_filter_lines(file_name):
	logging.debug(f"read_and_filter_lines({file_name})")
	with open(file_name) as file:
		lines = filter_lines(file.readlines())
		return lines

def process_game(lines):
	dices = [0]*11; dices_until_turn = []; turn = 0
	players = {}; player_points = [2]*4; player_points_until_turn = {}
	special = {"longest": "", "largest": "", "winner": "", "last_rolled": 0}
	resources_per_player = defaultdict(int)
	resources_per_player_per_dice = defaultdict(int)
	steal_map = defaultdict(int)
	player_card_count = defaultdict(int)
	player_card_count_through_turns = {}

	player_card_count_per_change = defaultdict(list)

	player_dice_rolls = defaultdict(lambda : [0]*11)

	trades = {
		"p2p_received": defaultdict(list),
		"p2p_given": defaultdict(list),
		"p2b_received": defaultdict(list),
		"p2b_given": defaultdict(list),
	}

	def player_to_index(player):
		logging.debug(f"player_to_index({player})")
		logging.debug(f"\tresult = {players[player]=}")
		return players[player]
	def index_to_player(i):
		logging.debug(f"index_to_player({i})")
		logging.debug(f"\tresult = {list(players.keys())[i]=}")
		return list(players.keys())[len(players)-i-1]
	def count_resources(res):
		logging.debug(f"count_resources({res})")
		for x in possible_resources:
			logging.debug(f"x={x}: res count={res.count(x)}")
		return [res.count(x) for x in possible_resources]
	def index_to_resource(i):
		logging.debug(f"index_to_resource({i})")
		logging.debug(f"\tresult = {possible_resources[i]=}")
		return possible_resources[i]


	def handle_starting_resources(line, i, player, turn):
		logging.debug(f"handle_starting_resources({player})")
		players[player] = 3 - len(players)
		logging.debug(f"\tresult = {players[player]}")
		return turn

	def handle_get_resources(line, i, player, turn):
		logging.debug(f"got_resources({line}), {resources_per_player=}")

		last_rolled = special["last_rolled"]

		m = re.match(r"^(?P<player>[\w#]+) got.* (?P<resources>\w+)$", line)
		resources = count_resources(m.group('resources'))

		# resources = count_resources(l.split(":")[1].strip())
		for i,res in enumerate(resources):
			resources_per_player[(player, index_to_resource(i))] += res
			resources_per_player_per_dice[(player, index_to_resource(i), last_rolled)] += res
		logging.debug(f"\tresult = {resources_per_player=}")

		return turn

	def handle_roll(line, i, player, turn):
		logging.debug(f"handle_roll({line}), {dices=}, {dices_until_turn=}")
		m = re.match(r"^(?P<player>[\w#]+) rolled.* dice_(?P<dice1>\d) dice_(?P<dice2>\d)$", line)
		rolled1 = int(m.group('dice1'))
		rolled2 = int(m.group('dice2'))
		dice_roll = rolled1 + rolled2
		dices[dice_roll-2] += 1

		logging.debug(f"\tline num: {i+1}, roll: {dice_roll}")
		dices_until_turn.append(dices.copy())
		logging.debug(f"\tresult = {dices=}, {dices_until_turn=}")

		special["last_rolled"] = dice_roll

		player_dice_rolls[player][dice_roll-2] += 1

		return turn + 1
	
	def handle_vp(line, i, player, turn):
		logging.debug(f"handle_roll({line}, {player}), {special=}, {player_points=}")
		longest = special["longest"]
		largest = special["largest"]

		m = re.match(r".*\+(?P<howMany>\w+) VP.*$", line)

		VPs = int(m.group('howMany'))

		if "longest" in line:
			special["longest"] = player
		elif "largest" in line:
			special["largest"] = player
			
		if "passed" in line:
			m = re.match(r"^.* passed from.* (?P<fromPlayer>[\w#]+) to.* (?P<toPlayer>[\w#]+).* \+2 VPs$",line)
			player_who_lost = m.group('fromPlayer')
			player = m.group('toPlayer')

			print("player_who_lost and won passed from", player_who_lost, player)
			player_points[player_to_index(player_who_lost)] -= VPs

		player_points[player_to_index(player)] += VPs


		logging.debug(f"\tresult = {special=}, {player_points=}")
		return turn

	def handle_win(line, i, player, turn):
		m = re.match(r"^trophy\s*(?P<winner>[\w#]+) won the game.*$", line)
		winner = m.group('winner')
		print("winn er", winner, line)
		special["winner"] = winner
		return turn

	def handle_steal(line, i, player, turn):
		logging.debug(f"handle_steal({line}, {i}, {player}, {turn}), {steal_map=}")
		if re.match(r"^(?P<stealer>[\w#]+) stole.* (?P<stolenResource>\w+) from.* (?P<victim>[\w#]*)$", line) is None: return turn

		m = re.match(r"^(?P<stealer>[\w#]+) stole.* (?P<stolenResource>\w+) from.* (?P<victim>[\w#]*)$", line)
		stealer = m.group('stealer')
		victim = m.group('victim')

		steal_map[(stealer, victim)] += 1
		logging.debug(f"\tresult = {steal_map}")
		return turn

	def handle_trade(line, i, player, turn):
		if re.match(r"^(?P<player>[\w#]+) traded.* (?P<givenResources>\w*) for.* (?P<receivedResources>\w*) with.* (?P<otherPlayer>[\w#]+)$", line) is not None:
			m = re.match(r"^(?P<player>[\w#]+) traded.* (?P<givenResources>\w*) for.* (?P<receivedResources>\w*) with.* (?P<otherPlayer>[\w#]+)$", line)
			player = m.group('player')
			other_player = m.group('otherPlayer')
			given = count_resources(m.group('givenResources'))
			taken = count_resources(m.group('receivedResources'))

			trades["p2p_given"][player].append(given)
			trades["p2p_given"][other_player].append(taken)
			trades["p2p_received"][player].append(taken)
			trades["p2p_received"][other_player].append(given)

		elif re.match(r"^(?P<player>[\w#]+) gave bank.* (?P<spentResources>\w*) and took (?P<receivedResources>\w*)$", line) is not None:
			m = re.match(r"^(?P<player>[\w#]+) gave bank.* (?P<spentResources>\w*) and took (?P<receivedResources>\w*)$", line)
			player = m.group('player')
			given = count_resources(m.group('spentResources'))
			taken = count_resources(m.group('receivedResources'))

			trades["p2b_given"][player].append(given)
			trades["p2b_received"][player].append(taken)
		return turn


	def handle_count(line, i, player, turn):
		logging.debug(f"handle_count({line}), {player_card_count=}")

		if "starting resources" in line or "got" in line:
			resources_gotten = sum(count_resources(line.split()[-1]))
			player_card_count[player] += resources_gotten
		elif re.match(r"^(?P<stealer>[\w#]+) stole.* (?P<stolenResource>\w+) from.* (?P<victim>[\w#]*)$", line) is not None:
			m = re.match(r"^(?P<stealer>[\w#]+) stole.* (?P<stolenResource>\w+) from.* (?P<victim>[\w#]*)$", line)
			stealer = m.group('stealer')
			victim = m.group('victim')

			player_card_count[stealer] += 1
			player_card_count[victim] -= 1
		elif "discarded" in line:
			resources_discared = sum(count_resources(line.split()[-1]))
			player_card_count[player] -= resources_discared
		elif "used Year of Plenty" in line:
			player_card_count[player] += 2
		elif "built a settlement" in line:
			player_card_count[player] -= 4
		elif "built a road" in line:
			player_card_count[player] -= 2
		elif "built a city" in line:
			player_card_count[player] -= 5
		elif "bought development card" in line:
			player_card_count[player] -= 3
		elif re.match(r"^(?P<player>[\w#]+) stole (?P<howMany>\d+).* (?P<resources>\w+)$", line) is not None:
			m = re.match(r"^(?P<player>[\w#]+) stole (?P<howMany>\d+).* (?P<resource>\w+)$", line)
			player = m.group('player')
			howMany = m.group('howMany')
			
			stoleHowMany = int(howMany)
			player_card_count[player] += stoleHowMany
		elif re.match(r"^(?P<player>[\w#]+) gave bank.* (?P<spentResources>\w*) and took (?P<receivedResources>\w*)$", line) is not None:
			m = re.match(r"^(?P<player>[\w#]+) gave bank.* (?P<spentResources>\w*) and took (?P<receivedResources>\w*)$", line)
			player = m.group('player')
			given = sum(count_resources(m.group('spentResources')))
			taken = sum(count_resources(m.group('receivedResources')))

			player_card_count[player] -= given
			player_card_count[player] += taken
		elif re.match(r"^(?P<player>[\w#]+) traded.* (?P<givenResources>\w*) for.* (?P<receivedResources>\w*) with.* (?P<otherPlayer>[\w#]+)$", line) is not None:
			m = re.match(r"^(?P<player>[\w#]+) traded.* (?P<givenResources>\w*) for.* (?P<receivedResources>\w*) with.* (?P<otherPlayer>[\w#]+)$", line)
			player = m.group('player')
			other_player = m.group('otherPlayer')
			given = sum(count_resources(m.group('givenResources')))
			taken = sum(count_resources(m.group('receivedResources')))

			player_card_count[player] -= given
			player_card_count[player] += taken

			player_card_count[other_player] += given
			player_card_count[other_player] -= taken

		for p in players.keys():
			cards_before = player_card_count_per_change[p][-1] if len(player_card_count_per_change[p]) > 0 else 0
			cards_after = player_card_count[p]

			
			if cards_before != cards_after:
				player_card_count_per_change[p].append(cards_after)
			

		logging.debug(f"\tresult = {player_card_count=}\n")
		return turn

	def handle_end_of_turn(turn):
		player_points_until_turn[turn] = player_points.copy()
		player_card_count_through_turns[turn] = player_card_count.copy()



	line_handlers = {
		"starting resources": [handle_starting_resources, handle_count],
		"got": [handle_get_resources, handle_count],
		"rolled": [handle_roll],
		"VP": [handle_vp],
		"stole": [handle_steal, handle_count],
		"won the game": [handle_win],
		"discarded": [handle_count],
		"built a road": [handle_count],
		"built a city": [handle_count],
		"gave bank": [handle_count, handle_trade],
		"built a settlement": [handle_count],
		"used Monopoly card": [handle_count],
		"used Year of Plenty": [handle_count],
		"bought development card": [handle_count],
		"traded": [handle_count, handle_trade],
	}

	print("handling lines", lines)
	for i,l in enumerate(lines):
		player = l.split()[0]
		for line_key, handlers in line_handlers.items():
			if line_key in l:
				for h in handlers:
					turn = h(l, i, player, turn)
		handle_end_of_turn(turn)

	logging.info("Finished game processing", player_points_until_turn)

	for trade_type, trades_per_player in trades.items():
		summed = defaultdict(list)
		for p in players.keys():
			playerSummed = [sum(x) for x in zip(*trades_per_player[p])]
			summed[p] = playerSummed if len(playerSummed) > 0 else [0]*5
		trades[trade_type] = summed

	result = {
		"dices": dices,
		"dices_until_turn": dices_until_turn,
		"players": players,
		"player_points": player_points,
		"player_points_until_turn": player_points_until_turn,
		"resources_per_player": resources_per_player,
		"resources_per_player_per_dice": resources_per_player_per_dice,
		"index_to_player": index_to_player,
		"player_to_index": player_to_index,
		"index_to_resource": index_to_resource,
		"turn": turn,
		"steal_map": steal_map,
		"winner": special["winner"],
		"player_card_count_through_turns": player_card_count_through_turns,
		"player_card_count_per_change": player_card_count_per_change,
		"trades": trades,
		"player_dice_rolls": player_dice_rolls
	}

	return result

def autolabel(ax, bar_plot, resource_values, isPrint=False, customModifier=0.75):
	for idx,rect in enumerate(bar_plot):
		height = rect.get_height()
		modifier = customModifier if height >= 0 else 1.20
		if isPrint: print("oiii height", height)
		if resource_values[idx] == 0: continue
		ax.text(rect.get_x() + rect.get_width()/2., modifier*height,
				resource_values[idx],
				ha='center', va='bottom')

def plot_players_until_turn(player_points_until_turn, player_points, index_to_player, folder_name, turn, skip_show):
	logging.debug(f"plot_players_until_turn({player_points_until_turn}, {player_points}, {folder_name}, {skip_show}")
	player_points_until_turn = list(player_points_until_turn.values())
	player_points_through_turns = list(zip(*player_points_until_turn))
	plt.figure(figsize=(12,10))
	for i,pptt in enumerate(player_points_through_turns):
		plt.scatter(range(1, len(pptt)+1), pptt, s=10)
		plt.plot(range(1, len(pptt)+1), pptt, label=f"{index_to_player(i)}")

	x_anno = turn + 1.5
	points_to_player_map = defaultdict(list)
	for i,y_anno in enumerate(player_points):
		points_to_player_map[(x_anno, y_anno)].append(index_to_player(i))
	for k,v in points_to_player_map.items():
		playerlist = "\n".join(v)
		plt.annotate(f"{k[1]}: {playerlist}", (*k,))

	plt.legend()
	plt.savefig(f"{folder_name}/points_stats_through_turns.png")
	plt.savefig(f"newest_result/points_stats_through_turns.png")
	if not skip_show: plt.show()


def plot_card_count_through_turns(player_card_count_through_turns, index_to_player, folder_name, turn, skip_show):
	logging.debug(f"plot_players_until_turn({player_card_count_through_turns}, {folder_name}, {skip_show}")
	player_card_count_through_turns = [[pcc[index_to_player(i)] for pcc in player_card_count_through_turns.values()] for i in range(4)]
	
	plt.figure(figsize=(11,11))

	max_cards = np.max(player_card_count_through_turns)
	subplots = 1
	for i,p in enumerate(player_card_count_through_turns):
		ax = plt.subplot(2,2,subplots)
		subplots += 1
		ax.set_ylim([0,max_cards+1])
		ax.set_title(f"{index_to_player(i)} card count")
		scatter_plot = ax.scatter(range(1, len(p)+1), p, s=10)
		line_plot = ax.plot(range(1, len(p)+1), p)


	plt.savefig(f"{folder_name}/player_card_count_through_turns.png")
	plt.savefig(f"newest_result/player_card_count_through_turns.png")
	if not skip_show: plt.show()

def plot_card_count_per_change(player_card_count_per_change, index_to_player, folder_name, turn, skip_show):
	logging.debug(f"plot_card_count_per_change({player_card_count_per_change}, {folder_name}, {skip_show}")
	plt.figure(figsize=(11,11))

	all = []
	for v in player_card_count_per_change.values(): all += list(v)
	max_cards = max(all)
	subplots = 1
	for player,cards in player_card_count_per_change.items():
		ax = plt.subplot(2,2,subplots)
		subplots += 1
		ax.set_ylim([0,max_cards+1])
		ax.set_title(f"{player} card count")
		scatter_plot = ax.scatter(range(1, len(cards)+1), cards, s=10)
		line_plot = ax.plot(range(1, len(cards)+1), cards)


	plt.savefig(f"{folder_name}/player_card_count_per_change.png")
	plt.savefig(f"newest_result/player_card_count_per_change.png")
	if not skip_show: plt.show()

def plot_rolls_through_turns(dices_until_turn, dices, folder_name, turn, skip_show):
	logging.debug(f"plot_rolls_through_turns({dices_until_turn}, {dices}, {folder_name}, {skip_show}")
	rolls_through_turns = list(zip(*dices_until_turn))
	plt.figure(figsize=(12,10))
	for i,rtt in enumerate(rolls_through_turns):
		plt.scatter(range(1, len(rtt)+1), rtt, s=10)
		plt.plot(range(1, len(rtt)+1), rtt, label=f"{i+2}")

	x_anno = turn + 1.5

	rolled_to_dice_map = defaultdict(list)
	for i,y_anno in enumerate(dices):
		rolled_to_dice_map[(x_anno, y_anno)].append(i+2)

	for k,v in rolled_to_dice_map.items():
		plt.annotate(f"{v}: {k[1]}", (*k,))

	plt.legend()
	plt.savefig(f"{folder_name}/dice_stats_through_turns.png")
	plt.savefig(f"newest_result/dice_stats_through_turns.png")
	if not skip_show: plt.show()

def plot_dice_resource_stats(dices_until_turn, dices, folder_name, skip_show):
	plt.figure(figsize=(11,11))
	turn_num = len(dices_until_turn)
	quarters = [int((turn_num - 1) * i) for i in (0.25, 0.50, 0.75, 1.00)]


	max_rolls = max(dices)
	ax = plt.gca()
	ax.set_xticks(range(2,13))
	colors = ["yellow", "gold", "orange", "red"]
	prev_q = [0]*11
	for i,q in enumerate(quarters):
		q_data = [x - y for x,y in zip(dices_until_turn[q], prev_q)]
		ax.set_ylim([0,max_rolls+1])
		bar = ax.bar(range(2,13), q_data, label=f"quarter {i+1}", color=colors[i], bottom=prev_q)

		ax.bar_label(bar, label_type='center', labels=[str(x) if x != 0 else "" for x in q_data])
		plt.legend()
		prev_q = dices_until_turn[q]

	

	plt.savefig(f"{folder_name}/dice_resources_stats.png")
	plt.savefig(f"newest_result/dice_resources_stats.png")
	if not skip_show: plt.show()

def plot_resources_per_players(resources_per_player, players, folder_name, skip_show):
	plt.figure(figsize=(11,11))
	max_resources = max(resources_per_player.values())
	subplots = 1
	for p in players.keys():
		resource_values = [resources_per_player[(p, r)] for r in possible_resources]
		ax = plt.subplot(2,2,subplots)
		subplots += 1
		ax.set_ylim([0,max_resources+3])
		ax.set_title(f"{p} ({sum(resource_values)})")
		bar_plot = ax.bar(possible_resources, resource_values, color=resource_colors)
		ax.bar_label(bar_plot, label_type="center")


	plt.savefig(f"{folder_name}/resources_players.png")
	plt.savefig(f"newest_result/resources_players.png")
	if not skip_show: plt.show()

def plot_player_dice_rolls(player_dice_rolls, folder_name, skip_show):
	plt.figure(figsize=(11,11))
	for subplot, (player, dices) in enumerate(player_dice_rolls.items()):
		ax = plt.subplot(2,2,subplot+1)
		ax.set_title(f"{player}")
		bar_plot = ax.bar(list(range(2,13)), dices)
		labels = [d if d > 0 else '' for d in dices]
		ax.bar_label(bar_plot, labels=labels, label_type="center")


	plt.savefig(f"{folder_name}/dices_players_rolled.png")
	plt.savefig(f"newest_result/dices_players_rolled.png")
	if not skip_show: plt.show()


def plot_trades_per_players(trades, players, folder_name, skip_show):
	plt.figure(figsize=(22,16))
	print(trades)

	max_graph = 35
	try:
		max_graph = int(max(
			np.max([[x+y for x,y in zip_longest(trades["p2p_received"][p], trades["p2b_received"][p], fillvalue=0)] for p in players.keys()]),
			np.max([[x+y for x,y in zip_longest(trades["p2p_given"][p], trades["p2b_given"][p], fillvalue=0)] for p in players.keys()])
			))
	except:
		pass
	print("maxgraph", max_graph)

	subplots = 1
	for p in players.keys():
		p2p_received = trades["p2p_received"][p]; p2p_received = [0,0,0,0,0] if len(p2p_received) == 0 else p2p_received
		p2b_received = trades["p2b_received"][p]; p2b_received = [0,0,0,0,0] if len(p2b_received) == 0 else p2b_received
		p2p_given = trades["p2p_given"][p]; p2p_given = [0,0,0,0,0] if len(p2p_given) == 0 else p2p_given
		p2b_given = trades["p2b_given"][p]; p2b_given = [0,0,0,0,0] if len(p2b_given) == 0 else p2b_given

		received_total = [x+y for x,y in zip(p2p_received, p2b_received)]
		given_total = [-(x+y) for x,y in zip(p2p_given, p2b_given)]

		p2p_given = [-x for x in p2p_given]
		p2b_given = [-x for x in p2b_given]

		ax = plt.subplot(1,4,subplots)
		subplots += 1
		ax.set_ylim([-max_graph-2, max_graph+2])
		ax.set_title(f"{p} received: {sum(received_total)}, gave: {-sum(given_total)}")
		bar_plot1 = ax.bar(possible_resources, p2p_received, color=resource_colors)
		bar_plot2 = ax.bar(possible_resources, p2b_received, color=resource_colors_alt, bottom=p2p_received)
		bar_plot3 = ax.bar(possible_resources, p2p_given, color=resource_colors)
		bar_plot4 = ax.bar(possible_resources, p2b_given, color=resource_colors_alt, bottom=p2p_given)
		ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)


		ax.bar_label(bar_plot1, label_type='center', padding=0, labels=[str(x) if x != 0 else "" for x in p2p_received])
		ax.bar_label(bar_plot2, label_type='center', padding=0, labels=[str(x) if x != 0 else "" for x in p2b_received])
		ax.bar_label(bar_plot3, label_type='center', padding=0, labels=[str(x) if x != 0 else "" for x in p2p_given])
		ax.bar_label(bar_plot4, label_type='center', padding=0, labels=[str(x) if x != 0 else "" for x in p2b_given])
	plt.savefig(f"{folder_name}/trades_players.png")
	plt.savefig(f"newest_result/trades_players.png")
	if not skip_show: plt.show()


def plot_resources_per_players_per_dices(resources_per_player_per_dice, players, folder_name, skip_show):
	max_calc = defaultdict(int)
	for (player, resource, dice), v in resources_per_player_per_dice.items():
		max_calc[(player, dice)] += v
	
	max_per_roll = max(max_calc.values())


	plt.figure(figsize=(15,15))
	plt.grid()
	subplots = 1
	for p in players:
		rp = {(resource, dice) : v for ((player, resource, dice), v) in resources_per_player_per_dice.items() if p == player}
		dice_to_value_per_resource = []
		for r in possible_resources:
			rd = {dice : v for ((resource, dice), v) in rp.items() if resource == r}

			dice_to_value = [0]*11
			for ((resource, dice), v) in rp.items():
				if (resource == r): dice_to_value[dice - 2] = v

			dice_to_value_per_resource.append(dice_to_value)
		ax = plt.subplot(2,2,subplots)
		subplots += 1
		ax.set_ylim([0,max_per_roll+1.5])
		ax.set_title(f"{p}")

		dice_to_value_per_resource = np.array(dice_to_value_per_resource)
		dices = np.arange(2,13)
		bar = ax.bar(dices, dice_to_value_per_resource[0], label=possible_resources[0], color=resource_colors[0])
		ax.bar_label(bar, label_type='center', labels=[str(x) if x != 0 else "" for x in dice_to_value_per_resource[0]])		
		for i, dice_to_value in enumerate(dice_to_value_per_resource[1:]):
			prev_sum = np.sum(dice_to_value_per_resource[0:i+1], axis=0)
			bar = ax.bar(dices, dice_to_value, label=possible_resources[i+1], color=resource_colors[i+1], bottom=prev_sum)
			ax.bar_label(bar, label_type='center', labels=[str(x) if x != 0 else "" for x in dice_to_value])

		
		ax.set_xticks(dices)
		ax.set_xticklabels(dices)
		plt.legend()

	plt.savefig(f"{folder_name}/dices_per_player_and_resource.png")
	plt.savefig(f"newest_result/dices_per_player_and_resource.png")
	if not skip_show: plt.show()
	

def plot_total_dice_stats(dices, skip_show):
	with open("dice_stats.txt", "r+") as file:
		line_to_write = " ".join(map(str, dices)) + "\n"
		lines = file.readlines()
		last_line = lines[-1] if len(lines) > 0 else ""
		if line_to_write != last_line:
			file.write(line_to_write)
			lines.append(line_to_write)

		res = [0]*11
		for l in lines:
			for i,r in enumerate(l.split()):
				res[i] += int(r)
		
		plt.figure(figsize=(11,11))
		plt.title(f"Total dice stats, games played: {len(lines)}")
		ax = plt.gca()

		bar_plot = plt.bar(range(2,13), res)
		autolabel(ax, bar_plot, res)

		plt.savefig(f"dice_stats.png")
		if not skip_show: plt.show()

# almost same as above (simple IF based on dices) TODO remove later
def only_plot_total_dice_stats(skip_show):
	with open("dice_stats.txt", "r") as file:
		lines = file.readlines()

		res = [0]*11
		for l in lines:
			for i,r in enumerate(l.split()):
				res[i] += int(r)
		
		plt.figure(figsize=(11,11))
		plt.title(f"Total dice stats, games played: {len(lines)}")
		ax = plt.gca()

		bar_plot = plt.bar(range(2,13), res)
		autolabel(ax, bar_plot, res)

		plt.savefig(f"dice_stats.png")
		if not skip_show: plt.show()

def plot_steal(steal_map, players, folder_name, skip_show):
	if not steal_map:
		print("steal map empty")
		return
	plt.figure(figsize=(22,11))
	max_resources = max(steal_map.values())
	subplots = 1
	for p in players.keys():
		colors = ["blue", "orange", "green", "red"]
		possible_players = list(players.keys())
		p_index = possible_players.index(p)

		del possible_players[p_index]
		del colors[p_index]

		resource_values = [steal_map[(p, r)] for r in possible_players]
		ax = plt.subplot(1,4,subplots)
		subplots += 1
		ax.set_ylim([0,max_resources+3])
		ax.set_title(f"{p} ({sum(resource_values)})")
		bar_plot = ax.bar(possible_players, resource_values, color=colors)

		autolabel(ax, bar_plot, resource_values)

		plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')

	plt.savefig(f"{folder_name}/stealings.png")
	plt.savefig(f"newest_result/stealings.png")
	if not skip_show: plt.show()




def do(file_name, skip_show, skip_dices, newestOnly = False):
	lines = read_and_filter_lines(file_name)
	if len(lines) == 0: return False
	
	file_name = file_name.replace("gamelogs/", "")
	folder_name = f"results/{file_name.split('.')[0]}" if not newestOnly else "newest_result"
	make_folder(folder_name)

	res = process_game(lines)
	dices, dices_until_turn, players, player_points, player_points_until_turn, resources_per_player, resources_per_player_per_dice, index_to_player, player_to_index, index_to_resource, turn, steal_map, winner, player_card_count_through_turns, player_card_count_per_change, trades, player_dice_rolls = res.values()

	if not newestOnly: update_rankings_file_directly(players, player_points, winner, file_name)

	plot_players_until_turn(player_points_until_turn, player_points, index_to_player, folder_name, turn, skip_show)
	# plot_card_count_through_turns(player_card_count_through_turns, index_to_player, folder_name, turn, skip_show)
	plot_card_count_per_change(player_card_count_per_change, index_to_player, folder_name, turn, skip_show)
	plot_rolls_through_turns(dices_until_turn, dices, folder_name, turn, skip_show)
	plot_dice_resource_stats(dices_until_turn, dices, folder_name, skip_show)
	plot_resources_per_players(resources_per_player, players, folder_name, skip_show)
	plot_resources_per_players_per_dices(resources_per_player_per_dice, players, folder_name, skip_show)
	plot_trades_per_players(trades, players, folder_name, skip_show)
	plot_player_dice_rolls(player_dice_rolls, folder_name, skip_show)
	if not skip_dices: plot_total_dice_stats(dices, skip_show)
	plot_steal(steal_map, players, folder_name, skip_show)

	return True


def main():
	file_name, skip_show = check_args()
	do(file_name, skip_show)


if __name__ == "__main__":
	main()

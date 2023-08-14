from catan2 import do
from sys import argv


def read_info_file():
    games_played = 0
    with open("info.txt", "r") as file:
        games_played = int(file.read())
        print(f"{games_played=}")
    return games_played+1

def update_info_file(games_played):
    with open("info.txt", "w") as file:
        file.write(f"{games_played}")

def check_if_exists(lines, previous_game_number):
    file_name = f"gamelogs/{previous_game_number}.txt"
    with open(file_name) as file:
        previous_lines = file.readlines()
        matched_num = sum(l in previous_lines for l in lines)
        print(matched_num / len(previous_lines))
        matched_rate = matched_num / len(previous_lines)
        if matched_rate > 0.95: return True
    return False

def handle_lines(lines, newestOnly):
    print("handle_lines", lines)
    next_game = read_info_file()
    if not newestOnly and check_if_exists(lines, next_game - 1):
        print("yooo already exists")
        exit()

    file_name = f"gamelogs/{next_game}.txt" if not newestOnly else "temp.txt"

    with open(file_name, "w") as file:
        file.writelines(lines)

    result = do(file_name, True, False, newestOnly)
    if not newestOnly and result: update_info_file(next_game)

def handle_input(newestOnly):
    line = ""
    lines = []
    while "won the game" not in line:
        line = input()
        print(f"read: {line=}")
        lines.append(line + "\n")
    
    handle_lines(lines, newestOnly)


def test_newest_only(file_name):
    do(file_name, True, True, True)


def main():
    if len(argv) < 2:
        handle_input(False)
    elif argv[1] == "-newest":
        handle_input(True)
    else:
        file_name = argv[1]
        test_newest_only(file_name)

if __name__ == "__main__":
    main()
from bs4 import BeautifulSoup
from game_entry import handle_lines
from count_cards import count_cards
from discord_webhook import DiscordWebhook, DiscordEmbed

from flask import Flask
from flask import request
from flask_cors import CORS

import json

webhookUrl = None
with open('discordWebhookUrl.txt') as f:
    webhookUrl = f.readline().strip()

print(f'{webhookUrl=}')
webhook = DiscordWebhook(url='webhookUrl', content='')

ignoredList = [
    "Thank you for playing",
    "List of Commands",
    "Learn how to play",
    "Karma System",
    "<hr/>",
    "Chat now disabled"
]


def processMessages(messages):
    res = []
    for m in messages:
        messageString = str(m)
        shouldIgnore = any([ign in messageString for ign in ignoredList])
        if shouldIgnore: continue

        contents = m.contents
        new_contents = []
        for c in contents:
            if c.name == 'span':
                    spanContents = c.contents
                    for sc in spanContents:
                        if sc.name == 'img':
                            new_contents.append(sc.get('alt'))
                        elif sc.name in ['a']:
                            for content in sc.contents:
                                if content.name == 'img':
                                    new_contents.append(content.get('alt'))
                                else:
                                    new_contents.append(str(content))
                        elif sc.name in ['span', 'strong']:
                            new_contents.append(' '.join(map(str, sc.contents)))
                        else:
                            new_contents.append(str(sc))
            else:
                new_contents.append(c.get('alt'))
        line = "".join(new_contents)
        res.append(f"{line}\n")
    for r in res: print(r.strip())
    return res


def parse(source):
    soup = BeautifulSoup(source, 'html.parser')

    messages = soup.find_all("div", {"class" : "message-post"})
    result = processMessages(messages)

    return result
    

def upload_to_discord():
    folder = "C:\\Users\\petar\\Desktop\\catan\\newest_result\\"
    files = [
        "dice_resources_stats.png",
        "dice_stats_through_turns.png",
        "dices_per_player_and_resource.png",
        "dices_players_rolled.png",
        "points_stats_through_turns.png",
        "resources_players.png",
        "resources_through_turns.png",
        "stealings.png",
        "trades_players.png",
    ]

    for f in files:
        with open(f"{folder}{f}", "rb") as file:
            webhook.add_file(file=file.read(), filename=f)
    response = webhook.execute()



app = Flask(__name__)
CORS(app)

@app.route("/", methods=['GET'])
def yo():
    return "yo", 200


@app.route("/analizeGame", methods=['POST'])
def analize_game_request():
    req = json.loads(request.data)
    messages = req["messages"]
    sendToDiscord = req["sendToDiscord"]

    result = parse(messages)

    if len(result) == 0: return "incorrect format", 400

    handle_lines(result, False)
    if sendToDiscord: upload_to_discord()
    return 'OK', 200


@app.route("/countCards", methods=['POST'])
def count_cards_request():
    req = json.loads(request.data)
    messages = req["messages"]

    result = parse(messages)
    if len(result) == 0: return "incorrect format", 400

    countedCards = count_cards(result)
    result = ""
    for c in countedCards: result += str(c) + "\n"
    print('countedCards', result)

    return result, 200

def main():
    app.run(host="0.0.0.0", port=5009, debug=True)


if __name__ == "__main__":
    main()
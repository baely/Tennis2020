import csv
import math
import os.path
import pandas as pd
import re
import time


elo = {}
games = {}
wins = []
accuracies = []
last_match = {}
player_list = {}

P = 0


def accuracy() -> None:
    acc = sum(wins) / len(wins)
    print(f"Accuracy: {acc}%")


def analyse(matches: pd.DataFrame) -> None:
    print(f"{matches.shape[0]} matches counted.")
    print("Loading players...")
    for player in pd.concat([matches['winner_id'], matches['loser_id']], axis=0, ignore_index=True).drop_duplicates():
        elo[player] = 1500
        games[player] = 0
    print(f"{len(elo)} players counted.")
    print("Doing the math...")
    s = time.time()
    for index, match in matches.iterrows():
        winner_id = match['winner_id']
        loser_id = match['loser_id']
        last_match[winner_id] = match['tourney_date']
        last_match[loser_id] = match['tourney_date']
        if winner_id == 199999 or loser_id == 199999:
            continue
        p = do_match(winner_id, loser_id, 1)[0]
        if abs(p - 0.5) + 0.5 > P:
            wins.append(1 if p > 0.5 else 0)
        accuracies.append(p)
    print(f"Math took {time.time() - s}s")
    # best(matches)
    # accuracy()

    global player_list
    player_list = {x: get_player(matches, x) for x in elo}
    player_list = {k: str(v) for k, v in sorted(player_list.items(), key=lambda x: last_match[x[0]], reverse=True)}


def analyse_matches() -> None:
    hist = pd.read_excel("results.xlsx")
    win = 0
    loss = 0
    for i, match in hist.iterrows():
        try:
            actual = int(match["Actual"])
        except ValueError:
            actual = 0
        try:
            me = int(match["Me"])
        except ValueError:
            me = 0
        print([actual, me, actual > 0, me > 0, actual > 0 and me > 0, actual == me])
        if actual > 0 and me > 0:
            if actual == me:
                win += 1
            else:
                loss += 1

    print([win, loss, win/(win+loss)])


def best(matches: pd.DataFrame) -> None:
    sorted_ranks = sorted(elo.items(), key=lambda x: x[1])
    print("Top scorers:")
    for player in sorted_ranks[-15:]:
        print(f"{get_player(matches, player[0])}: {player[1]}")


def do_aus_open(matches: pd.DataFrame, aus_open: pd.DataFrame) -> None:
    open_player_list = {}
    for i, game in aus_open.iterrows():
        # print(game)
        for player in [game[1], game[2]]:
            if player not in open_player_list.keys() and player not in ['-']:
                open_player_list[player] = search_by_name_parts(player[0], player[3:])

        if "-" in [game[1], game[2]]:
            continue

        p1 = open_player_list[game[1]]
        p2 = open_player_list[game[2]]

        if game["Actual"] in [1, 2]:
            do_match(p1, p2, game["Actual"])

        if game["Me"] not in [1, 2] and game["Actual"] not in [1, 2]:
            p = predict(p1, p2)
            m = 1 if p > 0.5 else 2 if p < 0.5 else 0.5
            w = game[1] if m == 1 else game[2] if m == 2 else ""
            print(f"I predict for the game {game[1]} vs {game[2]} that {w} will win. {p}")


def get_player(matches: pd.DataFrame, player_id: int) -> str:
    try:
        player = matches.loc[matches['winner_id'] == player_id]['winner_name'].unique()[0]
    except IndexError:
        try:
            player = matches.loc[matches['loser_id'] == player_id]['loser_name'].unique()[0]
        except IndexError:
            print(["Player not found", player_id])
            player = ""
    return player


def load() -> pd.DataFrame:
    data = pd.read_csv("all_matches.csv", low_memory=False)
    # for year in range(1968, 2021):
    #     try:
    #         if year == 2020:
    #             data = data.append(pd.read_csv(f"tennis_atp/atp_matches_{year}.csv")
    #                                .rename(columns={"loser_id": "fake_loser_id", "winner_rank": "loser_id"}), sort=False)
    #         else:
    #             data = data.append(pd.read_csv(f"tennis_atp/atp_matches_{year}.csv"), sort=False)
    #         print(f"Loading data from {year}...")
    #     except FileNotFoundError:
    #         print(f"No data found for {year}.")
    # data.to_csv("all_matches.csv")

    return data


def load_aus_open() -> pd.DataFrame:
    aus_open = pd.read_excel("results_test.xlsx", nrows=127)
    return aus_open


def main() -> None:
    matches = load()
    analyse(matches)
    # verse(matches)
    #
    # predict_players(matches)
    aus_open2020 = load_aus_open()
    do_aus_open(matches, aus_open2020)
    # search(matches)
    # analyse_matches()


def do_match(p1: int, p2: int, winner: int) -> list:
    c1 = predict(p1, p2)
    c2 = predict(p2, p1)
    if p1 != 0:
        games[p1] += 1
        update(p1, c1, 1 if winner == 1 else 0)
    if p2 != 0:
        games[p2] += 1
        update(p2, c2, 1 if winner == 2 else 0)
    return [c1, c2]


def predict(player1: int, player2: int) -> float:
    s1 = elo[player1] if player1 != 0 else 1500
    s2 = elo[player2] if player2 != 0 else 1500
    p = 1.0 / (1.0 + math.pow(10, ((s2 - s1) / 400)))
    return p


def predict_players(matches: pd.DataFrame):
    players = []
    results = [["p1", "p2", "p1_confidence"]]
    with open('players.csv', newline='') as f:
        for row in csv.reader(f):
            players.append(int(row[0]))
    for winner in players:
        for loser in players:
            p = predict(winner, loser)
            results.append([get_player(matches, winner), get_player(matches, loser), p])
    with open('ausopen.csv', 'w', newline='') as f:
        wr = csv.writer(f)
        wr.writerows(results)


def search(matches: pd.DataFrame) -> None:
    while True:
        query = input("Name:")
        search_results = [[x, player_list[x], last_match[x]]
                          for x in player_list
                          if player_list[x].lower().find(query.lower()) > -1]
        if len(search_results) > 0:
            for player in search_results[:5]:
                print(f"{player[0]}:{player[1]} ({player[2]})")
        else:
            print("No player found.")


def search_by_name_parts(initial: str, surname: str) -> [str, str]:
    search_names = re.findall(r"[\w]+", surname)
    search_results = [x
                      for x in player_list
                      if not all(s == -1 for s in [player_list[x].lower().find(f.lower()) for f in search_names])
                      and player_list[x].lower()[0] == initial.lower()]
    return search_results[0] if len(search_results) > 0 else 0


def search_players(prompt: str) -> [str, str]:
    query = input(prompt)
    search_results = [[x, player_list[x], last_match[x]]
                      for x in player_list
                      if player_list[x].lower().find(query.lower()) > -1]
    if len(search_results) > 0:
        for player in search_results[:5]:
            print(f"{player[0]}:{player[1]} ({player[2]}): {elo[player[0]]}")
        player = [search_results[0][0], search_results[0][1]]
    else:
        print("No player found.")
        player = search_players(prompt)
    return player


def update(player: int, expected: float, actual: int) -> None:
    if player == 0:
        return
    c = 250
    o = 5
    s = 0.4
    k = c / math.pow((games[player] + o), s)
    elo[player] = elo[player] + k * (actual - expected)


def verse() -> None:
    while True:
        player1 = search_players("Player 1: ")
        player2 = search_players("Player 2: ")
        p = predict(player1[0], player2[0])
        print(f"{player1[1]} vs {player2[1]}: {p} (1:{1/p})")


if __name__ == '__main__':
    main()

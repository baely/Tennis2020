import csv
import math
import pandas as pd
import time


elo = {}
games = {}
wins = []
accuracies = []
last_match = {}

P = 0.85


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
        p1 = predict(winner_id, loser_id)
        p2 = predict(loser_id, winner_id)
        games[winner_id] += 1
        games[loser_id] += 1
        update(winner_id, p1, 1)
        update(loser_id, p2, 0)
        if abs(p1 - 0.5) + 0.5 > P:
            wins.append(1 if p1 > 0.5 else 0)
        accuracies.append(p1)
    print(f"Math took {time.time() - s}s")
    best(matches)
    accuracy()


def best(matches: pd.DataFrame) -> None:
    sorted_ranks = sorted(elo.items(), key=lambda x: x[1])
    print("Top scorers:")
    for player in sorted_ranks[-15:]:
        print(f"{get_player(matches, player[0])}: {player[1]}")


def get_player(matches: pd.DataFrame, player_id: int) -> str:
    try:
        player = matches.loc[matches['winner_id'] == player_id]['winner_name'].unique()[0]
    except IndexError:
        player = matches.loc[matches['loser_id'] == player_id]['loser_name'].unique()[0]
    return player


def load() -> pd.DataFrame:
    data = pd.DataFrame()
    for year in range(1968, 2020):
        try:
            data = data.append(pd.read_csv(f"tennis_atp/atp_matches_{year}.csv"), sort=False)
            print(f"Loading data from {year}...")
        except FileNotFoundError:
            print(f"No data found for {year}.")
    return data


def main() -> None:
    matches = load()
    analyse(matches)
    verse(matches)
    # search(matches)
    # predict_players(matches)


def predict(player1: int, player2: int) -> float:
    s1 = elo[player1]
    s2 = elo[player2]
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
    player_list = {x: get_player(matches, x) for x in elo}
    player_list = {k: v for k, v in sorted(player_list.items(), key=lambda x: last_match[x[0]], reverse=True)}
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


def search_players(prompt: str, player_list: dict) -> [str, str]:
    query = input(prompt)
    search_results = [[x, player_list[x], last_match[x]]
                      for x in player_list
                      if player_list[x].lower().find(query.lower()) > -1]
    if len(search_results) > 0:
        for player in search_results[:5]:
            print(f"{player[0]}:{player[1]} ({player[2]})")
        player = [search_results[0][0], search_results[0][1]]
    else:
        print("No player found.")
        player = search_players(prompt, player_list)
    return player


def update(player: int, expected: float, actual: int) -> None:
    c = 250
    o = 5
    s = 0.4
    k = c / math.pow((games[player] + o), s)
    elo[player] = elo[player] + k * (actual - expected)
    pass


def verse(matches: pd.DataFrame) -> None:
    player_list = {x: get_player(matches, x) for x in elo}
    player_list = {k: v for k, v in sorted(player_list.items(), key=lambda x: last_match[x[0]], reverse=True)}
    player1 = search_players("Player 1: ", player_list)
    player2 = search_players("Player 2: ", player_list)
    print(f"{player1[1]} vs {player2[1]}: {predict(player1[0], player2[0])}")


if __name__ == '__main__':
    main()

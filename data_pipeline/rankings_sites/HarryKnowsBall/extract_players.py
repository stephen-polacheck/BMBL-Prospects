import json
import requests
from bs4 import BeautifulSoup

URL = "https://harryknowsball.com/rankings?prospects=true"


def fetch():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    next_data = soup.find("script", id="__NEXT_DATA__")

    if next_data is None:
        raise RuntimeError("Could not locate __NEXT_DATA__ on the rankings page.")

    return json.loads(next_data.string)


def extract_players(raw):
    return raw["props"]["pageProps"]["players"]


def normalize(players):
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "team": p["team"],
            "positions": p["positions"],
            "rank": p["rank"],
            "value": p["value"],
            "age": p["age"],
            "source": "harryknowsball",
            "prospect": p["prospect"],
            "level": p["level"]
        }
        for p in players
    ]


def main():
    raw = fetch()
    players = extract_players(raw)
    normalized = normalize(players)

    with open("data/hkb_players.json", "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2)

    print(f"Saved {len(normalized)} players")


if __name__ == "__main__":
    main()
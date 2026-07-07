import requests
import json

URL = "https://harryknowsball.com/_next/data/v1Nr6fX1t8K6kJjkbPFlY/rankings.json?prospects=true"


def fetch():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    return r.json()


def extract_players(raw):
    return raw["pageProps"]["players"]


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

    with open("data/hkb_players.json", "w") as f:
        json.dump(normalized, f, indent=2)

    print(f"Saved {len(normalized)} players")


if __name__ == "__main__":
    main()
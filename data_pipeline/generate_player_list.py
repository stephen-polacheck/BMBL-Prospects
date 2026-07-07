import json
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent

DATA = BASE / "data"

OUTPUT_DIR = DATA / "public"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_json(filename):
    with open(DATA / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def main():

    hkb_players = load_json("hkb_players.json")
    registry = load_json("player_registry.json")
    players = load_json("players.json")
    fantasy_teams = load_json("teams.json")
    mlb_teams = load_json("mlb_teams.json")


    # -------------------------
    # Build lookup tables
    # -------------------------

    registry_by_hkb = {}

    for universal_id, record in registry.items():

        for hkb_id in record.get("hkb_ids", []):

            registry_by_hkb.setdefault(
                hkb_id,
                []
            ).append(record)


    players_by_id = {
        p["player_id"]: p
        for p in players
    }


    teams_by_id = {
        t["team_id"]: t
        for t in fantasy_teams
    }


    mlb_by_abbrev = {
        t["abbrev"]: t
        for t in mlb_teams
    }


    # -------------------------
    # Build prospect display
    # -------------------------

    output = []


    for hkb in hkb_players:

        hkb_id = hkb["id"]

        matches = registry_by_hkb.get(
            hkb_id,
            []
        )


        # Keep unmatched HKB players.
        # They simply have no internal enrichment.

        if not matches:

            output.append(
                build_record(
                    hkb,
                    None,
                    None,
                    None,
                    mlb_by_abbrev
                )
            )

            continue


        for registry_player in matches:

            internal_ids = registry_player.get(
                "internal_ids",
                []
            )


            # A registry entry should normally
            # have one internal id, but preserve
            # multiple just in case

            if not internal_ids:

                output.append(
                    build_record(
                        hkb,
                        registry_player,
                        None,
                        None,
                        mlb_by_abbrev
                    )
                )

                continue


            for internal_id in internal_ids:

                internal_player = players_by_id.get(
                    internal_id
                )


                fantasy_team = None

                if internal_player:

                    fantasy_team = teams_by_id.get(
                        internal_player["team_id"]
                    )


                output.append(
                    build_record(
                        hkb,
                        registry_player,
                        internal_player,
                        fantasy_team,
                        mlb_by_abbrev
                    )
                )


    output_file = OUTPUT_DIR / "prospect_list.json"


    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2
        )


    print(
        f"Created {output_file}"
    )

    print(
        f"Records generated: {len(output)}"
    )



def build_record(
    hkb,
    registry,
    internal_player,
    fantasy_team,
    mlb_lookup
):

    mlb = mlb_lookup.get(
        hkb.get("team")
    )


    return {

        "hkb_id": hkb["id"],

        "universal_id":
            registry["universal_id"]
            if registry else None,


        "name": hkb["name"],

        "team": hkb["team"],

        "positions":
            hkb.get("positions", []),

        "rank":
            hkb.get("rank"),

        "value":
            hkb.get("value"),

        "age":
            hkb.get("age"),

        "prospect":
            hkb.get("prospect"),

        "level":
            hkb.get("level"),


        "fantasy": {

            "player_id":
                internal_player["player_id"]
                if internal_player else None,

            "team_id":
                internal_player["team_id"]
                if internal_player else None,

            "team_name":
                fantasy_team["name"]
                if fantasy_team else None
        },


        "mlb": {

            "abbrev":
                mlb["abbrev"]
                if mlb else hkb.get("team"),

            "name":
                mlb["name"]
                if mlb else None,

            "city":
                mlb["city"]
                if mlb else None,

            "primary":
                mlb["primary"]
                if mlb else None,

            "secondary":
                mlb["secondary"]
                if mlb else None,

            "logo":
                mlb["logourl"]
                if mlb else None
        }
    }



if __name__ == "__main__":
    main()
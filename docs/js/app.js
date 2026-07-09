async function loadPlayers() {

    const isGithubPages =
        window.location.hostname.includes("github.io");


    const isSubPage =
    window.location.pathname.includes("/pages/");


    const jsonPath = isSubPage
        ? "../data/public/prospect_list.json"
        : "data/public/prospect_list.json";


    console.log("Page:", window.location.pathname);
    console.log("Loading JSON:", jsonPath);


    const response = await fetch(jsonPath);


    if (!response.ok) {

        throw new Error(
            `Unable to load ${jsonPath}: ${response.status}`
        );

    }


    let players = await response.json();


    // Remove draft picks from every page
    players = filterDraftPicks(players);


    const isProspectsPage =
        window.location.pathname.includes("prospects.html");


    // Sort all players by value
    players = players.sort(
        (a, b) => b.value - a.value
    );


    // Apply value-based ranking
    players = applyValueRanking(players);
    players = applyTeamRanking(players);

    if (isProspectsPage) {

        // Only show prospects
        players = players.filter(
            player => player.prospect === true
        );


        // Re-rank prospects after filtering
        players = applyValueRanking(players);

        players = applyTeamRanking(players);

    }


    renderTable(players);

}

function filterDraftPicks(players) {

    return players.filter(player => {

        if (!player.name) {
            return false;
        }

        // Remove draft pick placeholders
        return !player.name.trim().startsWith("2");

    });

}

function applyValueRanking(players) {

    let currentRank = 0;
    let previousValue = null;


    players.forEach((player, index) => {

        if (player.value !== previousValue) {

            currentRank = index + 1;

        }


        player.displayRank = currentRank;

        previousValue = player.value;

    });


    return players;

}

function renderTable(players) {


    const table =
        document.getElementById("playerTable");


    table.innerHTML = "";


    const columns =
        [...document.querySelectorAll("#player-table th")]
        .map(th => th.dataset.column);



    players.forEach(player => {


        const row = document.createElement("tr");

        applyRowClasses(row, player);


        row.innerHTML =
            columns.map(column => {


                return `

                <td data-column="${column}">
                    ${
                        columnRenderers[column]
                        ? columnRenderers[column](player)
                        : ""
                    }
                </td>

                `;


            }).join("");



        table.appendChild(row);


    });

}

function applyTeamRanking(players) {

    const teams = {};


    // Group players by fantasy team
    players.forEach(player => {

        const team =
            player.fantasy?.team_id ?? "unrostered";


        if (!teams[team]) {
            teams[team] = [];
        }


        teams[team].push(player);

    });


    // Rank each team separately
    Object.values(teams).forEach(teamPlayers => {


        teamPlayers.sort(
            (a, b) => b.value - a.value
        );


        let currentRank = 0;
        let previousValue = null;


        teamPlayers.forEach((player, index) => {


            if (player.value !== previousValue) {

                currentRank = index + 1;

            }


            player.teamRank = currentRank;

            previousValue = player.value;

        });


    });


    return players;

}

function assignOverallRanks(players){

    const ranked = players
        .filter(player => !isDraftPick(player))
        .sort((a,b)=>{

            if (b.value !== a.value) {
                return b.value - a.value;
            }

            return a.name.localeCompare(b.name);

        });


    ranked.forEach((player,index)=>{

        player.overall_rank = index + 1;

    });


    return ranked;

}

function assignProspectRanks(players){

    const ranked = players
        .filter(player =>
            player.prospect === true &&
            !isDraftPick(player)
        )
        .sort((a,b)=>{

            if (b.value !== a.value) {
                return b.value - a.value;
            }

            return a.name.localeCompare(b.name);

        });


    ranked.forEach((player,index)=>{

        player.prospect_rank = index + 1;

    });


    return ranked;

}

function getRankableProspects(players){

    return players.filter(player => {

        return (
            player.prospect === true &&
            !isDraftPick(player)
        );

    });

}

function isDraftPick(player){

    return (
        player.name &&
        /^[0-9]{4}/.test(player.name)
    );

}

function renderLevel(level) {

    switch (level) {

        case "MLB":
            return `
                <img
                    src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Major_League_Baseball_logo.svg/250px-Major_League_Baseball_logo.svg.png"
                    class="level-logo"
                    alt="MLB"
                >
            `;

        case "AAA":
            return "AAA";

        case "AA":
            return "AA";

        case "HIGH_A":
            return "A+";

        case "LOW_A":
            return "A";

        case "ROOKIE_BALL":
            return "ROK";

        default:
            return level ?? "";

    }

}

function renderFantasyTeam(team) {

    if (!team || team.team_id == null) {
        return `
            <div class="available-team">
                Available
            </div>
        `;
    }

    const teamPage =
        window.location.pathname.includes("/pages/")
            ? "team_roster.html"
            : "pages/team_roster.html";

    return `
        <a
            href="${teamPage}?team_id=${team.team_id}"
            class="fantasy-team-link">

            <div class="fantasy-team">

                <div
                    class="team-name"
                    style="
                        background:${team.primary_color};
                        color:${team.secondary_color};
                    ">
                    ${team.nickname}
                </div>

                <div
                    class="team-stripe stripe-one"
                    style="background:${team.secondary_color};">
                </div>

                <div
                    class="team-stripe stripe-two"
                    style="background:${team.primary_color};">
                </div>

            </div>

        </a>
    `;
}

function renderMLBTeam(mlb) {

    if (!mlb?.logo) {
        return "";
    }

    return `
        <img
            src="${mlb.logo}"
            class="mlb-logo"
            alt="${mlb.abbrev ?? ""}"
        >
    `;

}

function hasFantasyTeam(player) {
    return player.fantasy && player.fantasy.team_id != null;
}

function applyRowClasses(row, player) {
    
    if (!hasFantasyTeam(player)) {
        row.classList.add("available-row");
        return;
    }

    if (player.prospect) {
        row.classList.add("prospect-row");
    }

}

const columnRenderers = {

    rank(player) {

        return player.displayRank ?? "";

    },


    team_rank(player) {

        if (!hasFantasyTeam(player)) {
            return "";
        }

        return player.teamRank ?? "";

    },


    name(player) {

        return player.name ?? "";

    },


    mlb(player) {
        return renderMLBTeam(player.mlb);
    },


    position(player) {

        return player.positions?.join(", ") ?? "";

    },


    age(player) {

        return player.age !== null &&
               player.age !== undefined
            ? Number(player.age).toFixed(1)
            : "";

    },


    level(player) {

        return renderLevel(player.level);

    },


    value(player) {

        return player.value ?? "";

    },


    "fantasy-team"(player) {
        return renderFantasyTeam(player.fantasy);
    }

};

loadPlayers();
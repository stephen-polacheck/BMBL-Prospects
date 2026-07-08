async function loadPlayers() {

    const isGithubPages =
        window.location.hostname.includes("github.io");


    const jsonPath = isGithubPages
        ? "../data/public/prospect_list.json"
        : "../../data/public/prospect_list.json";


    console.log("Loading JSON from:", jsonPath);


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


    if (isProspectsPage) {

        // Only show prospects
        players = players.filter(
            player => player.prospect === true
        );


        // Re-rank prospects after filtering
        players = applyValueRanking(players);

    }


    renderTable(players, isProspectsPage);

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

function renderTable(players, isProspectsPage = false) {


    const table =
        document.getElementById(
            "playerTable"
        );


    table.innerHTML = "";


    players.forEach(player => {


        const row =
            document.createElement("tr");


        const age =
            player.age !== null &&
            player.age !== undefined
            ? Number(player.age).toFixed(1)
            : "";


        const fantasyTeam =
            player.fantasy?.nickname;


        const fantasyBadge =
            fantasyTeam
            ?
            `
            <div
                class="fantasy-team"
                style="
                    --primary:${player.fantasy.primary_color};
                    --secondary:${player.fantasy.secondary_color};
                "
            >
                <span class="team-name">
                    ${fantasyTeam}
                </span>

                <span class="team-stripe stripe-one"></span>
                <span class="team-stripe stripe-two"></span>


            </div>
            `
            :
            "Available";


        const mlbLogo =
            player.mlb?.logo
            ?
            `
            <img 
                src="${player.mlb.logo}"
                class="mlb-logo"
                alt="${player.mlb.nickname ?? ''}"
            >
            `
            :
            "";


        row.innerHTML = `

            <td>
                ${player.displayRank ?? ""}
            </td>


            <td>
                ${player.name ?? ""}
            </td>


            <td>
                ${mlbLogo}
            </td>


            <td>
                ${
                    player.positions
                    ?.join(", ")
                    ?? ""
                }
            </td>


            <td>
                ${age}
            </td>


            <td>
                ${player.level ?? ""}
            </td>


            <td>
                ${player.value ?? ""}
            </td>


            <td>
                ${fantasyBadge}
            </td>

        `;


        table.appendChild(row);


    });

}



loadPlayers();
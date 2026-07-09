async function loadSystemRanks() {

    const response = await fetch("../data/public/prospect_list.json");

    const players = await response.json();


    // Weighted scoring buckets
    const overallBuckets = [
        { limit: 20, weight: 15 },
        { limit: 40, weight: 12 },
        { limit: 60, weight: 10 },
        { limit: 80, weight: 8 },
        { limit: 100, weight: 6 },
        { limit: 120, weight: 5 },
        { limit: 140, weight: 4 },
        { limit: 160, weight: 3 },
        { limit: 180, weight: 2 },
        { limit: 200, weight: 1 },
        { limit: 220, weight: 1 }
    ];


    const positionBuckets = [
        { limit: 10, weight: 15 },
        { limit: 20, weight: 12 },
        { limit: 30, weight: 10 },
        { limit: 40, weight: 8 },
        { limit: 50, weight: 6 },
        { limit: 60, weight: 5 },
        { limit: 70, weight: 4 },
        { limit: 80, weight: 3 },
        { limit: 90, weight: 2 },
        { limit: 100, weight: 1 }
    ];



    // Only include true prospects with assigned fantasy teams
    const prospects = players.filter(player => {

        return (
            player.prospect === true &&
            player.fantasy &&
            player.fantasy.team_id &&
            player.fantasy.nickname !== "Available"
        );

    });



    // Split into batters and pitchers
    const pitchers = prospects.filter(player => {

        return player.positions.some(position =>
            position.includes("P")
        );

    });


    const batters = prospects.filter(player => {

        return !player.positions.some(position =>
            position.includes("P")
        );

    });



    // Apply independent rankings
    const rankedProspects = assignRanks(prospects);
    const rankedBatters = assignRanks(batters);
    const rankedPitchers = assignRanks(pitchers);



    // Generate rankings
    const overallRankings = calculateSystemRanks(
        rankedProspects,
        overallBuckets
    );


    const batterRankings = calculateSystemRanks(
        rankedBatters,
        positionBuckets
    );


    const pitcherRankings = calculateSystemRanks(
        rankedPitchers,
        positionBuckets
    );



    // Create headers
    renderSystemHeader(
        "overall-header",
        overallBuckets
    );


    renderSystemHeader(
        "batter-header",
        positionBuckets
    );


    renderSystemHeader(
        "pitcher-header",
        positionBuckets
    );



    // Render tables
    renderSystemRanks(
        overallRankings,
        "overall-ranks-body",
        overallBuckets
    );


    renderSystemRanks(
        batterRankings,
        "batter-ranks-body",
        positionBuckets
    );


    renderSystemRanks(
        pitcherRankings,
        "pitcher-ranks-body",
        positionBuckets
    );

}

function calculateSystemRanks(players, buckets){


    const teams = {};


    players.forEach(player=>{


        const teamId = player.fantasy.team_id;


        if(!teams[teamId]){

            teams[teamId] = {

                team_id: teamId,

                nickname: player.fantasy.nickname,

                primary_color: player.fantasy.primary_color,

                secondary_color: player.fantasy.secondary_color,

                players: []

            };

        }


        teams[teamId].players.push(player);


    });



    const rankings = Object.values(teams)
        .map(team=>{


            let total = 0;


            const result = {
                ...team
            };


            buckets.forEach(bucket=>{


                const count = team.players.filter(player=>{

                    return player.rank_position <= bucket.limit;

                }).length;



                result[`top_${bucket.limit}`] = count;


                total += count * bucket.weight;


            });



            result.total = total;


            return result;


        })
        .sort((a,b)=>b.total-a.total);



    return rankings;


}

function assignRanks(players){


    const ranked = [...players]
        .sort((a,b)=>a.rank-b.rank);



    ranked.forEach((player,index)=>{

        player.rank_position = index + 1;

    });


    return ranked;

}

function isPitcher(player){

    return player.positions.some(position =>
        position.includes("P")
    );

}



function isBatter(player){

    return !isPitcher(player);

}

function renderSystemRanks(teams, targetId, thresholds){


    const tbody =
        document.getElementById(targetId);


    teams.forEach((team,index)=>{


        let row = `

        <td data-column="rank">
            ${index+1}
        </td>

        <td data-column="team">
            ${renderFantasyTeam(team)}
        </td>

        <td data-column="total" class="system-total">
            <strong>${team.total}</strong>
        </td>

        `;


        thresholds.forEach(bucket=>{

            row += `
            <td data-column="tier">
                ${team[`top_${bucket.limit}`]}
            </td>
            `;

        });


        const tr=document.createElement("tr");

        tr.innerHTML=row;

        tbody.appendChild(tr);


    });


}

function renderSystemHeader(targetId, thresholds){

    const thead = document.getElementById(targetId);


    thead.innerHTML = `

    <tr>

    <th>Rank</th>
    <th>Team</th>
    <th>Total</th>

    ${
    thresholds.map(bucket => `
    <th>
    Top ${bucket.limit}
    </th>
    `).join("")
    }

    </tr>

    `;

}

function renderFantasyTeam(team){

    return `

    <a 
    href="team_roster.html?team_id=${team.team_id}"
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
            style="
            background:${team.secondary_color};
            ">
            </div>

            <div 
            class="team-stripe stripe-two"
            style="
            background:${team.primary_color};
            ">
            </div>

        </div>

    </a>

    `;

}



loadSystemRanks();
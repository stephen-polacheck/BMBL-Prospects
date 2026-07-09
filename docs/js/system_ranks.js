async function loadSystemRanks() {


    const response =
        await fetch("../data/public/prospect_list.json");


    const players =
        await response.json();



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



    /*
        Remove draft picks only.
        Keep Available players.
        Keep all roster statuses.
    */

    const prospects =
        players.filter(player =>
            player.prospect === true &&
            !player.name.startsWith("202")
        );



    /*
        OVERALL RANKING
        Batter + Pitcher together
    */

    const rankedOverall =
        assignValueRanks(
            prospects,
            "overall_rank"
        );



    /*
        POSITION RANKINGS
    */


    const pitchers =
        prospects.filter(isPitcher);


    const batters =
        prospects.filter(player => !isPitcher(player));



    const rankedBatters =
        assignValueRanks(
            batters,
            "batter_rank_position"
        );


    const rankedPitchers =
        assignValueRanks(
            pitchers,
            "pitcher_rank_position"
        );



    const overallRankings =
        calculateSystemRanks(
            rankedOverall,
            overallBuckets,
            "overall_rank"
        );


    const batterRankings =
        calculateSystemRanks(
            rankedBatters,
            positionBuckets,
            "batter_rank_position"
        );


    const pitcherRankings =
        calculateSystemRanks(
            rankedPitchers,
            positionBuckets,
            "pitcher_rank_position"
        );



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





function assignValueRanks(players, field){


    const ranked =
        [...players]
        .sort(
            (a,b)=>b.value-a.value
        );


    ranked.forEach(
        (player,index)=>{

            player[field] = index + 1;

        }
    );


    return ranked;

}





function calculateSystemRanks(players, buckets, rankField){


    const teams = {};


    players.forEach(player=>{


        if(
            !player.fantasy ||
            player.fantasy.team_id == null
        ){
            return;
        }



        const id =
            player.fantasy.team_id;



        if(!teams[id]){


            teams[id]={

                team_id:id,

                nickname:
                    player.fantasy.nickname,

                primary_color:
                    player.fantasy.primary_color,

                secondary_color:
                    player.fantasy.secondary_color,

                players:[]

            };


        }



        teams[id].players.push(player);


    });



    return Object.values(teams)

    .map(team=>{


        const result={
            ...team
        };


        let total=0;



        buckets.forEach(bucket=>{


            const count =
                team.players.filter(
                    player =>
                    player[rankField] <= bucket.limit
                ).length;



            result[`top_${bucket.limit}`]=count;


            total +=
                count * bucket.weight;


        });



        result.total=total;

        return result;


    })


    .sort(
        (a,b)=>b.total-a.total
    );

    

}





function isPitcher(player){

    return player.positions?.some(
        position =>
        position.includes("P")
    );

}





function renderSystemRanks(teams,targetId,thresholds){


    const tbody =
        document.getElementById(targetId);


    tbody.innerHTML="";


    teams.forEach((team,index)=>{


        const tr =
            document.createElement("tr");



        let html=`

        <td>
            ${index+1}
        </td>

        <td>
            ${renderFantasyTeam(team)}
        </td>

        <td class="system-total">
            ${team.total}
        </td>

        `;



        thresholds.forEach(bucket=>{


            html += `

            <td>
                ${team[`top_${bucket.limit}`]}
            </td>

            `;


        });



        tr.innerHTML=html;


        tbody.appendChild(tr);


    });


}





function renderSystemHeader(targetId,thresholds){


    const thead =
        document.getElementById(targetId);



    thead.innerHTML=`

    <tr>

        <th>Rank</th>

        <th>Team</th>

        <th>Total</th>

        ${
            thresholds.map(bucket=>
                `<th>Top ${bucket.limit}</th>`
            ).join("")
        }

    </tr>

    `;

}





loadSystemRanks();
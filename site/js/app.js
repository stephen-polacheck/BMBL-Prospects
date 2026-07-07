let players = [];


async function loadPlayers(){

    const response = await fetch(
        "../data/public/prospect_list.json"
    );


    players = await response.json();


    renderTable(players);

}



function renderTable(data){


    const table = document.getElementById(
        "playerTable"
    );


    table.innerHTML = "";


    data.forEach(player => {


        const row = document.createElement(
            "tr"
        );


        row.innerHTML = `

            <td>
                ${player.rank ?? ""}
            </td>


            <td>
                ${player.name}
            </td>


            <td>
                ${player.team ?? ""}
            </td>


            <td>
                ${
                    player.positions
                    ?.join(", ")
                    ?? ""
                }
            </td>


            <td>
                ${player.age ?? ""}
            </td>


            <td>
                ${player.level ?? ""}
            </td>


            <td>
                ${player.value ?? ""}
            </td>


            <td>
                ${
                    player.fantasy.team_name
                    ?? "Available"
                }
            </td>

        `;


        table.appendChild(row);


    });

}



function filterPlayers(){


    const search =
        document
        .getElementById("search")
        .value
        .toLowerCase();



    const level =
        document
        .getElementById("levelFilter")
        .value;



    const filtered =
        players.filter(player => {


            const matchesName =
                player.name
                .toLowerCase()
                .includes(search);


            const matchesLevel =
                !level ||
                player.level === level;


            return matchesName &&
                   matchesLevel;

        });


    renderTable(filtered);

}



document
    .getElementById("search")
    .addEventListener(
        "input",
        filterPlayers
    );


document
    .getElementById("levelFilter")
    .addEventListener(
        "change",
        filterPlayers
    );



loadPlayers();
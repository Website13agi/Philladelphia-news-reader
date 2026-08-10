/* =========================================================
   PHILLIES DAILY
   GAMES DATA ENGINE

   Data:
   MLB Stats API

   Features:
   - Today's Phillies game
   - Last 3 completed Phillies games
   - NL East standings
   - NL Wild Card standings
   - Automatic refresh every 5 minutes
========================================================= */

"use strict";


/* =========================================================
   CONFIG
========================================================= */

const MLB_API =
    "https://statsapi.mlb.com/api/v1";

const PHILLIES_ID =
    143;

const NATIONAL_LEAGUE_ID =
    104;

const AMERICAN_LEAGUE_ID =
    103;

const REFRESH_INTERVAL =
    5 * 60 * 1000;


/* =========================================================
   HELPERS
========================================================= */

function apiUrl(path, params = {}) {

    const url =
        new URL(
            MLB_API + path
        );

    Object.entries(params).forEach(
        ([key, value]) => {

            if (
                value !== undefined &&
                value !== null &&
                value !== ""
            ) {

                url.searchParams.set(
                    key,
                    value
                );

            }

        }
    );

    return url.toString();

}


async function fetchJSON(url) {

    const response =
        await fetch(
            url,
            {
                cache: "no-store"
            }
        );

    if (
        !response.ok
    ) {

        throw new Error(
            `MLB API error: ${response.status}`
        );

    }

    return response.json();

}


function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }

    return String(value)
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}


/* =========================================================
   DATE HELPERS
========================================================= */

/*
   MLBの試合日基準。

   サイトを見る場所が日本でも、
   Philliesの試合ページなので
   Philadelphia時間を基準にする。
*/

function philadelphiaDate() {

    const formatter =
        new Intl.DateTimeFormat(
            "en-CA",
            {
                timeZone:
                    "America/New_York",

                year: "numeric",
                month: "2-digit",
                day: "2-digit"
            }
        );

    return formatter.format(
        new Date()
    );

}


function formatGameDate(
    dateString
) {

    if (
        !dateString
    ) {

        return "—";

    }

    const date =
        new Date(
            dateString
        );

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "—";

    }

    return new Intl.DateTimeFormat(
        "en-US",
        {
            month: "short",
            day: "numeric"
        }
    ).format(
        date
    );

}


function formatGameTime(
    dateString
) {

    if (
        !dateString
    ) {

        return "";

    }

    const date =
        new Date(
            dateString
        );

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "";

    }

    return new Intl.DateTimeFormat(
        "en-US",
        {
            hour: "numeric",
            minute: "2-digit",
            timeZone:
                "America/New_York"
        }
    ).format(
        date
    ) + " ET";

}


/* =========================================================
   TODAY
========================================================= */

async function loadTodayGame() {

    const container =
        document.getElementById(
            "today-game"
        );

    if (
        !container
    ) {

        return;

    }

    const date =
        philadelphiaDate();

    const dateLabel =
        document.getElementById(
            "today-date"
        );

    if (
        dateLabel
    ) {

        dateLabel.textContent =
            formatSimpleDate(
                date
            );

    }


    try {

        const data =
            await fetchJSON(
                apiUrl(
                    "/schedule",
                    {
                        sportId: 1,
                        teamId:
                            PHILLIES_ID,
                        date: date,
                        hydrate:
                            "linescore,decisions,probablePitcher"
                    }
                )
            );


        const games =
            (
                data.dates &&
                data.dates[0] &&
                data.dates[0].games
            )
                ? data.dates[0].games
                : [];


        if (
            games.length === 0
        ) {

            renderNoTodayGame(
                container
            );

            return;

        }


        /*
           Doubleheaderの場合でも
           今日のゲームを表示できるよう
           最初の試合を表示。
        */

        renderTodayGame(
            container,
            games[0]
        );

    }

    catch (
        error
    ) {

        console.error(
            error
        );

        renderError(
            container,
            "Today's game could not be loaded."
        );

    }

}


/* =========================================================
   TODAY GAME RENDER
========================================================= */

function renderTodayGame(
    container,
    game
) {

    const away =
        game.teams.away;

    const home =
        game.teams.home;

    const awayTeam =
        away.team;

    const homeTeam =
        home.team;

    const status =
        game.status || {};

    const abstractState =
        status.abstractGameState ||
        "";

    const detailedState =
        status.detailedState ||
        "";

    const awayScore =
        away.score !== undefined
            ? away.score
            : null;

    const homeScore =
        home.score !== undefined
            ? home.score
            : null;


    let middleHTML =
        `<div class="vs">VS</div>`;


    if (
        abstractState ===
            "Final" ||
        abstractState ===
            "Live"
    ) {

        middleHTML = `

            <div
                class="today-score"
                style="
                    color:var(--navy-dark);
                    font-size:28px;
                    font-weight:900;
                    white-space:nowrap;
                "
            >

                ${
                    awayScore !== null
                        ? escapeHTML(
                            awayScore
                        )
                        : "—"
                }

                <span
                    style="
                        color:var(--gray-400);
                        padding:0 6px;
                    "
                >
                    -
                </span>

                ${
                    homeScore !== null
                        ? escapeHTML(
                            homeScore
                        )
                        : "—"
                }

            </div>

        `;

    }


    const statusText =
        getGameStatusText(
            game
        );


    container.innerHTML = `

        <div class="today-label">

            ${escapeHTML(
                statusText
            )}

        </div>


        <div class="matchup">


            <div class="team">

                <div class="team-name">

                    ${escapeHTML(
                        awayTeam.name
                    )}

                </div>

                <div class="team-record">

                    ${
                        away.isWinner
                            ? "WIN"
                            : ""
                    }

                </div>

            </div>


            ${middleHTML}


            <div class="team">

                <div class="team-name">

                    ${escapeHTML(
                        homeTeam.name
                    )}

                </div>

                <div class="team-record">

                    ${
                        home.isWinner
                            ? "WIN"
                            : ""
                    }

                </div>

            </div>


        </div>


        <div class="game-info">


            <div class="game-info-item">

                ${escapeHTML(
                    formatGameTime(
                        game.gameDate
                    )
                )}

            </div>


            <div class="game-info-item">

                ${escapeHTML(
                    game.venue?.name ||
                    ""
                )}

            </div>


            <div class="game-info-item">

                ${escapeHTML(
                    detailedState
                )}

            </div>


        </div>

    `;

}


/* =========================================================
   GAME STATUS
========================================================= */

function getGameStatusText(
    game
) {

    const status =
        game.status || {};

    const abstractState =
        status.abstractGameState;

    if (
        abstractState ===
        "Final"
    ) {

        return "FINAL";

    }

    if (
        abstractState ===
        "Live"
    ) {

        return (
            status.detailedState ||
            "LIVE"
        ).toUpperCase();

    }

    if (
        abstractState ===
        "Preview"
    ) {

        return "UPCOMING";

    }

    return (
        status.detailedState ||
        "TODAY"
    ).toUpperCase();

}


/* =========================================================
   NO GAME
========================================================= */

function renderNoTodayGame(
    container
) {

    container.innerHTML = `

        <div class="empty">

            <div class="empty-icon">
                ⚾
            </div>

            <h2 class="empty-title">
                No Phillies Game Today
            </h2>

            <p class="empty-description">
                There is no scheduled Phillies game today.
            </p>

        </div>

    `;

}


/* =========================================================
   RECENT 3 GAMES
========================================================= */

async function loadRecentGames() {

    const container =
        document.getElementById(
            "recent-games"
        );

    if (
        !container
    ) {

        return;

    }


    try {

        const today =
            philadelphiaDate();

        const start =
            getDateDaysAgo(
                14
            );


        const data =
            await fetchJSON(
                apiUrl(
                    "/schedule",
                    {
                        sportId: 1,
                        teamId:
                            PHILLIES_ID,
                        startDate:
                            start,
                        endDate:
                            today,
                        hydrate:
                            "linescore"
                    }
                )
            );


        let games = [];


        if (
            Array.isArray(
                data.dates
            )
        ) {

            data.dates.forEach(
                dateEntry => {

                    if (
                        Array.isArray(
                            dateEntry.games
                        )
                    ) {

                        games =
                            games.concat(
                                dateEntry.games
                            );

                    }

                }
            );

        }


        games =
            games
                .filter(
                    game =>
                        game.status &&
                        game.status.abstractGameState ===
                            "Final"
                )
                .sort(
                    (a, b) =>
                        new Date(
                            b.gameDate
                        ) -
                        new Date(
                            a.gameDate
                        )
                )
                .slice(
                    0,
                    3
                );


        if (
            games.length === 0
        ) {

            container.innerHTML = `

                <div class="empty">

                    <div class="empty-description">
                        No completed games found.
                    </div>

                </div>

            `;

            return;

        }


        container.innerHTML =
            games
                .map(
                    renderRecentGame
                )
                .join("");

    }

    catch (
        error
    ) {

        console.error(
            error
        );

        renderError(
            container,
            "Recent games could not be loaded."
        );

    }

}


/* =========================================================
   RECENT GAME CARD
========================================================= */

function renderRecentGame(
    game
) {

    const away =
        game.teams.away;

    const home =
        game.teams.home;

    const philliesIsHome =
        home.team.id ===
        PHILLIES_ID;

    const opponent =
        philliesIsHome
            ? away.team
            : home.team;

    const philliesScore =
        philliesIsHome
            ? home.score
            : away.score;

    const opponentScore =
        philliesIsHome
            ? away.score
            : home.score;

    const philliesWon =
        philliesScore >
        opponentScore;

    const resultClass =
        philliesWon
            ? "win"
            : "loss";

    const resultText =
        philliesWon
            ? "W"
            : "L";


    return `

        <article class="game-card">


            <div class="game-date">

                ${escapeHTML(
                    formatGameDate(
                        game.gameDate
                    )
                )}

            </div>


            <div>

                <div class="game-opponent">

                    ${
                        philliesIsHome
                            ? "vs"
                            : "@"
                    }

                    ${escapeHTML(
                        opponent.name
                    )}

                </div>


                <div class="game-detail">

                    Final

                </div>

            </div>


            <div class="game-result ${resultClass}">

                ${resultText}

                ${escapeHTML(
                    philliesScore
                )}

                -

                ${escapeHTML(
                    opponentScore
                )}

            </div>


        </article>

    `;

}


/* =========================================================
   NL EAST STANDINGS
========================================================= */

async function loadNLEastStandings() {

    const container =
        document.getElementById(
            "nl-east-standings"
        );

    if (
        !container
    ) {

        return;

    }


    try {

        const data =
            await fetchJSON(
                apiUrl(
                    "/standings",
                    {
                        leagueId:
                            NATIONAL_LEAGUE_ID,
                        standingsTypes:
                            "regularSeason",
                        season:
                            new Date()
                                .getFullYear(),
                        hydrate:
                            "team(division)"
                    }
                )
            );


        const records =
            extractStandingsRecords(
                data
            );


        const nlEast =
            records
                .filter(
                    record =>
                        record.team?.division?.id ===
                        204
                )
                .sort(
                    compareStandings
                );


        /*
           MLB APIのdivision IDが
           将来的に変わる可能性に備えて、
           取得したdivision.nameでも判定。
        */

        const fallback =
            records
                .filter(
                    record =>
                        record.team?.division?.name ===
                        "National League East"
                )
                .sort(
                    compareStandings
                );


        const finalRecords =
            nlEast.length
                ? nlEast
                : fallback;


        renderStandingsTable(
            container,
            finalRecords
        );

    }

    catch (
        error
    ) {

        console.error(
            error
        );

        renderTableError(
            container,
            5
        );

    }

}


/* =========================================================
   NL WILD CARD
========================================================= */

async function loadWildCardStandings() {

    const container =
        document.getElementById(
            "wild-card-standings"
        );

    if (
        !container
    ) {

        return;

    }


    try {

        const data =
            await fetchJSON(
                apiUrl(
                    "/standings",
                    {
                        leagueId:
                            NATIONAL_LEAGUE_ID,
                        standingsTypes:
                            "regularSeason",
                        season:
                            new Date()
                                .getFullYear(),
                        hydrate:
                            "team(division)"
                    }
                )
            );


        const records =
            extractStandingsRecords(
                data
            );


        const divisionLeaders =
            new Set();


        records.forEach(
            record => {

                if (
                    Number(
                        record.divisionRank
                    ) === 1
                ) {

                    divisionLeaders.add(
                        record.team.id
                    );

                }

            }
        );


        /*
           Wild Cardは
           各地区1位を除いたNLチームを
           勝率順に並べる。
        */

        const wildCard =
            records
                .filter(
                    record =>
                        !divisionLeaders.has(
                            record.team.id
                        )
                )
                .sort(
                    compareStandings
                )
                .slice(
                    0,
                    3
                );


        renderWildCardTable(
            container,
            wildCard
        );

    }

    catch (
        error
    ) {

        console.error(
            error
        );

        renderTableError(
            container,
            4
        );

    }

}


/* =========================================================
   STANDINGS HELPERS
========================================================= */

function extractStandingsRecords(
    data
) {

    const output = [];


    if (
        !data ||
        !Array.isArray(
            data.records
        )
    ) {

        return output;

    }


    data.records.forEach(
        divisionRecord => {

            if (
                Array.isArray(
                    divisionRecord.teamRecords
                )
            ) {

                divisionRecord.teamRecords.forEach(
                    record => {

                        output.push(
                            record
                        );

                    }
                );

            }

        }
    );


    return output;

}


function compareStandings(
    a,
    b
) {

    const aPct =
        Number(
            a.winningPercentage
        );

    const bPct =
        Number(
            b.winningPercentage
        );


    if (
        bPct !== aPct
    ) {

        return bPct - aPct;

    }


    const aWins =
        Number(
            a.wins || 0
        );

    const bWins =
        Number(
            b.wins || 0
        );


    return bWins - aWins;

}


/* =========================================================
   NL EAST TABLE
========================================================= */

function renderStandingsTable(
    container,
    records
) {

    if (
        !records.length
    ) {

        container.innerHTML = `

            <tr>

                <td colspan="5">
                    No standings data.
                </td>

            </tr>

        `;

        return;

    }


    container.innerHTML =
        records
            .map(
                record => {

                    const team =
                        record.team || {};

                    const isPhillies =
                        team.id ===
                        PHILLIES_ID;

                    const pct =
                        formatPercentage(
                            record.winningPercentage
                        );


                    return `

                        <tr
                            class="${
                                isPhillies
                                    ? "phillies"
                                    : ""
                            }"
                        >

                            <td>

                                ${escapeHTML(
                                    team.abbreviation ||
                                    team.name ||
                                    "—"
                                )}

                            </td>

                            <td>
                                ${escapeHTML(
                                    record.wins
                                )}
                            </td>

                            <td>
                                ${escapeHTML(
                                    record.losses
                                )}
                            </td>

                            <td>
                                ${escapeHTML(
                                    pct
                                )}
                            </td>

                            <td>
                                ${escapeHTML(
                                    formatGamesBack(
                                        record.gamesBack
                                    )
                                )}
                            </td>

                        </tr>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   WILD CARD TABLE
========================================================= */

function renderWildCardTable(
    container,
    records
) {

    if (
        !records.length
    ) {

        container.innerHTML = `

            <tr>

                <td colspan="4">
                    No standings data.
                </td>

            </tr>

        `;

        return;

    }


    container.innerHTML =
        records
            .map(
                (record, index) => {

                    const team =
                        record.team || {};

                    const isPhillies =
                        team.id ===
                        PHILLIES_ID;


                    return `

                        <tr
                            class="${
                                isPhillies
                                    ? "phillies"
                                    : ""
                            }"
                        >

                            <td>

                                ${
                                    index + 1
                                }.

                                ${escapeHTML(
                                    team.abbreviation ||
                                    team.name ||
                                    "—"
                                )}

                            </td>

                            <td>
                                ${escapeHTML(
                                    record.wins
                                )}
                            </td>

                            <td>
                                ${escapeHTML(
                                    record.losses
                                )}
                            </td>

                            <td>
                                ${escapeHTML(
                                    formatGamesBack(
                                        record.gamesBack
                                    )
                                )}
                            </td>

                        </tr>

                    `;

                }
            )
            .join("");

}


/* =========================================================
   PHILLIES SUMMARY
========================================================= */

async function loadPhilliesSummary() {

    const container =
        document.getElementById(
            "phillies-summary"
        );

    if (
        !container
    ) {

        return;

    }


    try {

        const data =
            await fetchJSON(
                apiUrl(
                    "/standings",
                    {
                        leagueId:
                            NATIONAL_LEAGUE_ID,
                        standingsTypes:
                            "regularSeason",
                        season:
                            new Date()
                                .getFullYear()
                    }
                )
            );


        const records =
            extractStandingsRecords(
                data
            );


        const phillies =
            records.find(
                record =>
                    record.team?.id ===
                    PHILLIES_ID
            );


        if (
            !phillies
        ) {

            container.textContent =
                "Phillies standings unavailable.";

            return;

        }


        container.innerHTML = `

            <div
                style="
                    display:grid;
                    grid-template-columns:
                        repeat(3,1fr);
                    gap:8px;
                    text-align:center;
                "
            >

                <div>

                    <div
                        style="
                            color:var(--navy-dark);
                            font-size:20px;
                            font-weight:900;
                        "
                    >
                        ${escapeHTML(
                            phillies.wins
                        )}
                    </div>

                    <div
                        style="
                            color:var(--gray-500);
                            font-size:8px;
                            font-weight:800;
                            text-transform:uppercase;
                        "
                    >
                        Wins
                    </div>

                </div>


                <div>

                    <div
                        style="
                            color:var(--navy-dark);
                            font-size:20px;
                            font-weight:900;
                        "
                    >
                        ${escapeHTML(
                            phillies.losses
                        )}
                    </div>

                    <div
                        style="
                            color:var(--gray-500);
                            font-size:8px;
                            font-weight:800;
                            text-transform:uppercase;
                        "
                    >
                        Losses
                    </div>

                </div>


                <div>

                    <div
                        style="
                            color:var(--navy-dark);
                            font-size:20px;
                            font-weight:900;
                        "
                    >
                        ${escapeHTML(
                            formatPercentage(
                                phillies.winningPercentage
                            )
                        )}
                    </div>

                    <div
                        style="
                            color:var(--gray-500);
                            font-size:8px;
                            font-weight:800;
                            text-transform:uppercase;
                        "
                    >
                        PCT
                    </div>

                </div>

            </div>

        `;

    }

    catch (
        error
    ) {

        console.error(
            error
        );

        container.textContent =
            "Phillies summary unavailable.";

    }

}


/* =========================================================
   FORMATTERS
========================================================= */

function formatPercentage(
    value
) {

    const number =
        Number(
            value
        );

    if (
        Number.isNaN(
            number
        )
    ) {

        return "—";

    }


    return number.toFixed(3)
        .replace(
            /^0/,
            ""
        );

}


function formatGamesBack(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "—";

    }

    const number =
        Number(
            value
        );

    if (
        Number.isNaN(
            number
        )
    ) {

        return String(
            value
        );

    }

    if (
        number === 0
    ) {

        return "—";

    }

    return number.toFixed(1);

}


function formatSimpleDate(
    dateString
) {

    if (
        !dateString
    ) {

        return "";

    }

    const parts =
        dateString.split(
            "-"
        );

    if (
        parts.length !== 3
    ) {

        return dateString;

    }

    const year =
        Number(parts[0]);

    const month =
        Number(parts[1]);

    const day =
        Number(parts[2]);


    const date =
        new Date(
            year,
            month - 1,
            day
        );


    return new Intl.DateTimeFormat(
        "en-US",
        {
            month: "short",
            day: "numeric",
            year: "numeric"
        }
    ).format(
        date
    );

}


function getDateDaysAgo(
    days
) {

    const date =
        new Date();

    date.setDate(
        date.getDate() - days
    );


    const formatter =
        new Intl.DateTimeFormat(
            "en-CA",
            {
                timeZone:
                    "America/New_York",

                year: "numeric",
                month: "2-digit",
                day: "2-digit"
            }
        );


    return formatter.format(
        date
    );

}


/* =========================================================
   ERROR DISPLAY
========================================================= */

function renderError(
    container,
    message
) {

    container.innerHTML = `

        <div class="empty">

            <div class="empty-icon">
                ⚠
            </div>

            <h2 class="empty-title">
                Unable to load
            </h2>

            <p class="empty-description">
                ${escapeHTML(
                    message
                )}
            </p>

        </div>

    `;

}


function renderTableError(
    container,
    colspan
) {

    container.innerHTML = `

        <tr>

            <td
                colspan="${colspan}"
                style="
                    padding:20px;
                    text-align:center;
                    color:var(--gray-500);
                "
            >
                Unable to load standings.
            </td>

        </tr>

    `;

}


/* =========================================================
   LOAD EVERYTHING
========================================================= */

async function loadGamesPage() {

    console.log(
        "[Phillies Daily] Updating game data..."
    );


    /*
       各データを独立して取得。

       1つ失敗しても他の表示は残す。
    */

    await Promise.allSettled(
        [
            loadTodayGame(),
            loadRecentGames(),
            loadNLEastStandings(),
            loadWildCardStandings(),
            loadPhilliesSummary()
        ]
    );


    console.log(
        "[Phillies Daily] Game data updated."
    );

}


/* =========================================================
   AUTOMATIC REFRESH
========================================================= */

function startAutoRefresh() {

    setInterval(
        function() {

            loadGamesPage();

        },
        REFRESH_INTERVAL
    );

}


/* =========================================================
   INITIALIZE
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        loadGamesPage();

        startAutoRefresh();

    }
);

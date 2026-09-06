function runSimulation() {

    const scenario =
        document.getElementById("scenario").value;


    let after = 10000000;
    let loss = 0;
    let risk = 32;
    let message = "";


    if (scenario === "crash") {

        after = 8750000;
        loss = 12.5;
        risk = 72;

        message =
            "Market crash detected. " +
            "Risk threshold breached. " +
            "System recommends reducing equity exposure " +
            "and increasing defensive assets.";

    }


    else if (scenario === "interest") {

        after = 9400000;
        loss = 6;
        risk = 55;

        message =
            "Interest rate increase detected. " +
            "Bond and liquidity exposure should be reviewed.";

    }


    else if (scenario === "liquidity") {

        after = 9200000;
        loss = 8;
        risk = 68;

        message =
            "Liquidity crisis detected. " +
            "System recommends increasing cash reserves.";

    }


    else if (scenario === "equity") {

        after = 9000000;
        loss = 10;
        risk = 65;

        message =
            "Equity market shock detected. " +
            "System recommends portfolio rebalancing.";

    }


    document.getElementById("afterValue").textContent =
        "₹" + after.toLocaleString("en-IN");


    document.getElementById("lossValue").textContent =
        "-" + loss + "%";


    document.getElementById("simulationRisk").textContent =
        risk + " / 100";


    document.getElementById("simulationMessage").innerHTML = `

        <h2>🤖 System Response</h2>

        <p>${message}</p>

        <br>

        <strong>
            Recommended Action:
        </strong>

        <p>
            Review allocation and execute
            portfolio rebalancing.
        </p>

    `;

}
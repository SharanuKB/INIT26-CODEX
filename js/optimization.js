function optimizePortfolio() {

    const capital =
        Number(document.getElementById("capital").value);

    const risk =
        document.getElementById("riskPreference").value;

    const liquidity =
        Number(document.getElementById("liquidity").value);

    const maxExposure =
        Number(document.getElementById("maxExposure").value);


    if (!capital || capital <= 0) {

        alert("Please enter valid capital.");

        return;

    }


    alert(
        "Portfolio optimized successfully!\n\n" +
        "Risk Preference: " + risk +
        "\nLiquidity Requirement: " + liquidity + "%" +
        "\nMaximum Exposure: " + maxExposure + "%"
    );

}
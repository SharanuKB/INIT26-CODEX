// ==========================================
// CAPITALGUARD - RISK MONITOR
// ==========================================

// Demo risk data
const riskData = {
    overallRisk: 32,
    marketRisk: 28,
    liquidityRisk: 18,
    concentrationRisk: 35,
    drawdown: 6,
    equityExposure: 35,
    liquidity: 24,
    volatility: 18
};


// Check whether risk values are within limits
function checkRiskStatus() {

    const equityLimit = 40;
    const liquidityLimit = 20;
    const volatilityLimit = 20;
    const drawdownLimit = 10;

    console.log("Risk Monitoring Started");

    if (riskData.equityExposure > equityLimit) {
        console.log("🚨 Equity exposure limit breached");
    } else {
        console.log("✓ Equity exposure is safe");
    }

    if (riskData.liquidity < liquidityLimit) {
        console.log("🚨 Liquidity requirement breached");
    } else {
        console.log("✓ Liquidity requirement satisfied");
    }

    if (riskData.volatility >= volatilityLimit) {
        console.log("⚠️ Volatility threshold reached");
    } else {
        console.log("✓ Volatility is within limit");
    }

    if (riskData.drawdown >= drawdownLimit) {
        console.log("🚨 Drawdown limit breached");
    } else {
        console.log("✓ Drawdown is within limit");
    }
}


// Calculate overall risk status
function getRiskStatus(score) {

    if (score < 40) {
        return {
            status: "SAFE",
            message: "Portfolio is within safe limits."
        };
    }

    if (score < 70) {
        return {
            status: "WARNING",
            message: "Portfolio risk is increasing. Monitoring required."
        };
    }

    return {
        status: "CRITICAL",
        message: "Critical risk detected. Rebalancing required."
    };
}


// Run risk monitoring
checkRiskStatus();


// Display result in browser console
const result = getRiskStatus(riskData.overallRisk);

console.log("Overall Risk:", riskData.overallRisk);
console.log("Status:", result.status);
console.log(result.message);
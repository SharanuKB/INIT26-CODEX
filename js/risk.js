async function checkRiskStatus() {
    try {
        const response = await fetch('/api/risk');
        const data = await response.json();
        
        document.getElementById("risk-score").textContent = Math.round(data.overall_risk);
        
        const badge = document.getElementById("risk-status-badge");
        badge.textContent = `● ${data.status}`;
        badge.className = `badge ${data.status === 'SAFE' ? 'safe-badge' : 'warning-badge'}`;
        
        document.getElementById("risk-message-title").textContent = data.message;
        document.getElementById("risk-message-desc").textContent = 
            data.status === 'SAFE' ? "No critical risk threshold has been breached. Continue monitoring market volatility." : 
            "Risk thresholds have been breached. System recommends rebalancing.";

        const updateMetric = (idPrefix, val) => {
            const elVal = document.getElementById(`${idPrefix}-val`);
            const elBar = document.getElementById(`${idPrefix}-bar`);
            if (elVal) elVal.textContent = `${Math.round(val)}%`;
            if (elBar) elBar.style.width = `${Math.round(val)}%`;
        };
        
        updateMetric("risk-market", data.market_risk);
        updateMetric("risk-liquidity", data.liquidity_risk);
        updateMetric("risk-concentration", data.concentration_risk);
        updateMetric("risk-drawdown", data.drawdown);
        
        const tbody = document.getElementById("risk-thresholds-body");
        if (tbody) {
            tbody.innerHTML = data.thresholds.map(t => `
                <tr>
                    <td>${t.metric}</td>
                    <td>${t.current_pct.toFixed(2)}%</td>
                    <td>${t.limit_pct}%</td>
                    <td><span class="${t.status === 'SAFE' ? 'table-safe' : 'table-warning'}">${t.status}</span></td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error("Risk fetch failed", e);
    }
}

document.addEventListener("DOMContentLoaded", checkRiskStatus);
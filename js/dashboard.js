const allocationCanvas = document.getElementById("allocationChart");
let chartInstance = null;

async function loadDashboard() {
    try {
        const response = await fetch('/api/portfolio');
        const data = await response.json();
        
        // Update Chart
        if (allocationCanvas) {
            const labels = ["Equity", "Bonds", "Gold", "Corporate Bonds", "Cash"];
            const chartData = labels.map(l => data.weights_pct[l] || 0);
            
            if (chartInstance) chartInstance.destroy();
            
            chartInstance = new Chart(allocationCanvas, {
                type: "doughnut",
                data: {
                    labels: labels,
                    datasets: [{ data: chartData }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: "bottom" } }
                }
            });
        }
        
        // Update KPIs
        const totalCapital = data.allocations["Equity"] / (data.weights["Equity"] || 1); // approx or just hardcode 1Cr
        const cap = Object.values(data.allocations).reduce((a,b)=>a+b, 0);
        document.getElementById("kpi-portfolio").textContent = `₹${(cap/10000000).toFixed(2)} Cr`;
        document.getElementById("kpi-portfolio-sub").textContent = `↑ ${(data.expected_return*100).toFixed(2)}% expected return`;
        
        document.getElementById("kpi-risk").innerHTML = `${Math.round(data.risk.overall_risk)}<span class="small-text">/100</span>`;
        document.getElementById("kpi-risk-status").textContent = `● ${data.risk.status}`;
        document.getElementById("kpi-risk-status").className = data.risk.status === "SAFE" ? "safe" : (data.risk.status === "WARNING" ? "warning" : "critical");
        
        document.getElementById("kpi-liquidity").textContent = `${data.liquidity_ratio.toFixed(2)}%`;
        document.getElementById("kpi-liquidity-status").textContent = data.liquidity_ratio >= 20 ? "● Healthy" : "● Low";
        
        document.getElementById("kpi-return").textContent = `${(data.expected_return*100).toFixed(2)}%`;
        
        // Update Risk Overview (assuming there are elements with these IDs in risk overview panel, if not they'll just silently fail or we need to add them)
        const roScore = document.getElementById("ro-score");
        if (roScore) roScore.textContent = Math.round(data.risk.overall_risk);
        const mRisk = document.getElementById("ro-market");
        if (mRisk) mRisk.style.width = `${data.risk.market_risk}%`;
        const lRisk = document.getElementById("ro-liquidity");
        if (lRisk) lRisk.style.width = `${data.risk.liquidity_risk}%`;
        const cRisk = document.getElementById("ro-concentration");
        if (cRisk) cRisk.style.width = `${data.risk.concentration_risk}%`;
        
        // Update alerts
        const alertsList = document.getElementById("risk-alerts-list");
        if (alertsList) {
            alertsList.innerHTML = "";
            data.risk.thresholds.forEach(t => {
                const isSafe = t.status === "SAFE";
                alertsList.innerHTML += `
                    <div class="alert-item">
                        <div class="alert-icon ${isSafe ? 'safe-icon' : 'warning-icon'}">${isSafe ? '✓' : '⚠️'}</div>
                        <div class="alert-content">
                            <strong>${t.metric}</strong>
                            <p>${t.current_pct.toFixed(1)}% (Limit: ${t.limit_pct}%)</p>
                        </div>
                    </div>
                `;
            });
        }
        
    } catch (e) {
        console.error("Failed to load dashboard data", e);
    }
}

document.addEventListener("DOMContentLoaded", loadDashboard);
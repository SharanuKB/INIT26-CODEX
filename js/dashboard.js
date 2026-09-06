const allocationCanvas = document.getElementById("allocationChart");
let chartInstance = null;
let ws = null;

const ASSETS = ["Equity", "Bonds", "Gold", "Corporate Bonds", "Cash"];

function renderChart(weights) {
    if (!allocationCanvas) return;
    const chartData = ASSETS.map(l => (weights[l] || 0) * 100);
    
    if (chartInstance) {
        chartInstance.data.datasets[0].data = chartData;
        chartInstance.update();
    } else {
        chartInstance = new Chart(allocationCanvas, {
            type: "doughnut",
            data: {
                labels: ASSETS,
                datasets: [{ data: chartData }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: "bottom" } }
            }
        });
    }
}

async function loadDashboard() {
    try {
        // Init HTTP Fetch
        const pf = await fetch('/api/portfolio').then(r => r.json());
        renderChart(pf.weights);
        
        const risk = await fetch('/api/risk-status').then(r => r.json());
        updateRiskPanel(risk);
        
        const alerts = await fetch('/api/alerts').then(r => r.json());
        updateAlerts(alerts);
        
        // Connect WebSocket
        ws = new WebSocket(`ws://${location.host}/ws/alerts`);
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === "portfolio_update") {
                renderChart(msg.portfolio.weights);
                // re-fetch risk silently
                fetch('/api/risk-status').then(r => r.json()).then(updateRiskPanel);
            } else if (msg.type === "alerts") {
                // prepend new alerts
                msg.data.forEach(a => {
                    const html = `
                    <div class="alert warning">
                        <div class="alert-icon">⚠️</div>
                        <div>
                            <strong>${a.metric} Breach</strong>
                            <p>Val: ${a.value.toFixed(2)} | Limit: ${a.threshold}</p>
                            <small>${new Date(a.timestamp).toLocaleTimeString()}</small>
                        </div>
                    </div>`;
                    const list = document.getElementById("risk-alerts-list");
                    if (list) list.insertAdjacentHTML('afterbegin', html);
                });
            }
        };
    } catch (e) {
        console.error("Failed to load dashboard data", e);
    }
}

function updateRiskPanel(risk) {
    const sElement = document.getElementById("kpi-risk-status");
    if (sElement) {
        sElement.textContent = risk.breached ? "● BREACHED" : "● SAFE";
        sElement.className = risk.breached ? "critical" : "safe";
    }
    const cVal = risk.metrics.concentration.max_val;
    const cBreach = risk.metrics.concentration.breached;
    document.getElementById("risk-conc-val").textContent = (cVal * 100).toFixed(1) + "%";
    document.getElementById("risk-conc-status").textContent = cBreach ? "Breached" : "Safe";
    document.getElementById("risk-conc-status").style.color = cBreach ? "#d64545" : "#28a745";

    const vVal = risk.metrics.volatility_spike.max_val;
    const vBreach = risk.metrics.volatility_spike.breached;
    document.getElementById("risk-vol-val").textContent = vVal.toFixed(2) + "x";
    document.getElementById("risk-vol-status").textContent = vBreach ? "Breached" : "Safe";
    document.getElementById("risk-vol-status").style.color = vBreach ? "#d64545" : "#28a745";
}

function updateAlerts(alerts) {
    const list = document.getElementById("risk-alerts-list");
    if (!list) return;
    list.innerHTML = "";
    alerts.forEach(a => {
        list.innerHTML += `
        <div class="alert warning">
            <div class="alert-icon">⚠️</div>
            <div>
                <strong>${a.metric} Breach</strong>
                <p>Val: ${a.value.toFixed(2)} | Limit: ${a.threshold}</p>
                <small>${new Date(a.timestamp).toLocaleTimeString()}</small>
            </div>
        </div>`;
    });
}

async function simulateShock() {
    const asset = document.getElementById("shock-asset").value;
    const mult = parseFloat(document.getElementById("shock-multiplier").value);
    await fetch('/api/simulate-shock', {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({asset, multiplier: mult})
    });
    alert(`Shock initiated for ${asset} at ${mult}x volatility.`);
}

async function runScenario() {
    const asset = document.getElementById("scenario-asset").value;
    const mult = parseFloat(document.getElementById("scenario-multiplier").value);
    const res = await fetch('/api/scenario', {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({asset, multiplier: mult})
    }).then(r => r.json());
    
    document.getElementById("scenario-result").innerHTML = `
        <p><strong>Breach:</strong> ${res.risk_breached}</p>
        <p><strong>Alerts:</strong> ${res.alerts_generated}</p>
        <p><strong>Hypothetical Weight for ${asset}:</strong> ${(res.hypothetical_weights[asset]*100).toFixed(1)}%</p>
    `;
}

document.addEventListener("DOMContentLoaded", loadDashboard);
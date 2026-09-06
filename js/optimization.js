async function optimizePortfolio() {
    const capital = Number(document.getElementById("capital").value);
    const risk = document.getElementById("riskPreference").value;
    const liquidity = Number(document.getElementById("liquidity").value);
    const maxExposure = Number(document.getElementById("maxExposure").value);

    if (!capital || capital <= 0) {
        alert("Please enter valid capital.");
        return;
    }

    try {
        const response = await fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                capital: capital,
                riskPreference: risk,
                liquidity: liquidity,
                maxExposure: maxExposure
            })
        });
        
        const data = await response.json();
        
        const resultsContainer = document.getElementById("optimizationResult");
        if (resultsContainer) {
            let html = ``;
            for (const [asset, pct] of Object.entries(data.weights_pct)) {
                html += `
                    <div class="allocation-row">
                        <span>${asset}</span>
                        <strong>${pct.toFixed(2)}%</strong>
                    </div>
                    <div class="allocation-bar">
                        <div style="width:${pct}%"></div>
                    </div>
                `;
            }
            resultsContainer.innerHTML = html;
        }

        const kpiReturn = document.getElementById("opt-return");
        const kpiRisk = document.getElementById("opt-risk");
        if (kpiReturn) kpiReturn.textContent = `${(data.expected_return * 100).toFixed(2)}%`;
        if (kpiRisk) kpiRisk.textContent = `${Math.round(data.risk.overall_risk)}/100`;

    } catch (e) {
        console.error("Optimization failed", e);
        alert("Optimization failed");
    }
}
async function runSimulation() {
    const scenario = document.getElementById("scenario").value;

    try {
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                scenario: scenario,
                capital: 10000000
            })
        });
        
        const data = await response.json();
        
        document.getElementById("afterValue").textContent = `₹${data.portfolio_after.toLocaleString("en-IN", {maximumFractionDigits:0})}`;
        document.getElementById("lossValue").textContent = `${data.loss_pct < 0 ? '+' : '-'}${Math.abs(data.loss_pct).toFixed(2)}%`;
        document.getElementById("simulationRisk").textContent = `${Math.round(data.risk_score_after)} / 100`;
        
        // Build recommended allocation HTML
        let allocHtml = `
            <div style="margin-top: 15px; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                <h4 style="margin-bottom: 10px; font-size: 14px;">Recommended Target Allocation</h4>
                <div style="display: grid; gap: 8px;">
        `;
        
        for (const [asset, pct] of Object.entries(data.recommended_allocation.weights_pct)) {
            if (pct > 0) {
                allocHtml += `
                    <div style="display: flex; justify-content: space-between; font-size: 13px;">
                        <span>${asset}</span>
                        <strong>${pct.toFixed(1)}%</strong>
                    </div>
                `;
            }
        }
        allocHtml += `</div></div>`;
        
        document.getElementById("simulationMessage").innerHTML = `
            <h2>🤖 System Response</h2>
            <p>${data.message}</p>
            <br>
            <strong>Recommended Action:</strong>
            <p>Review allocation and execute portfolio rebalancing.</p>
            ${allocHtml}
        `;
        
    } catch (e) {
        console.error("Simulation failed", e);
        document.getElementById("simulationMessage").innerHTML = `
            <h2>❌ System Error</h2>
            <p>Failed to run simulation. Check backend connection.</p>
        `;
    }
}
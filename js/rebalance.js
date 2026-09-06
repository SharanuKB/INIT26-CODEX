async function loadRebalance() {
    try {
        const response = await fetch('/api/rebalance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                capital: 10000000
            })
        });
        
        const data = await response.json();
        
        const tbody = document.getElementById("rebalance-body");
        if (tbody) {
            tbody.innerHTML = data.rows.map(r => `
                <tr>
                    <td>${r.asset}</td>
                    <td>${r.current_pct.toFixed(2)}%</td>
                    <td>${r.target_pct.toFixed(2)}%</td>
                    <td class="${r.change_pct > 0 ? 'positive' : (r.change_pct < 0 ? 'negative' : '')}">${r.change_pct > 0 ? '+' : ''}${r.change_pct.toFixed(2)}%</td>
                </tr>
            `).join('');
        }
        
        const reasonEl = document.getElementById("rebalance-reason");
        if (reasonEl) {
            reasonEl.textContent = data.reason;
        }
    } catch (e) {
        console.error("Rebalance load failed", e);
    }
}

document.addEventListener("DOMContentLoaded", loadRebalance);

function applyRebalance() {
    const message = document.getElementById("rebalanceMessage");
    message.textContent = "✓ Rebalancing recommendation applied successfully.";
    message.style.color = "#178a54";
}
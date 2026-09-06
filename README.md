# CapitalGuard
**FinTech Asset & Capital Management / Portfolio Optimization Platform**

CapitalGuard is an automated capital management and optimization tool designed to help financial institutions balance asset allocation while strictly enforcing institutional risk controls. It provides a real-time dashboard for risk managers to monitor exposure, run market shock simulations, and dynamically rebalance portfolios.

## How to Set Up and Run

1. **Install Dependencies:**
   Ensure you have Python 3.8+ installed. Run the following command to install the required backend packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Application:**
   Run the FastAPI server via Uvicorn:
   ```bash
   python app.py
   ```

3. **Access the Application:**
   - **Dashboard**: Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)
   - **Interactive API Docs (Swagger UI)**: Test endpoints at [http://localhost:5000/docs](http://localhost:5000/docs)

## The Financial Model

CapitalGuard uses a dual-engine optimization approach:
- **Markowitz Mean-Variance Optimization (QP):** Solved via `scipy.optimize.minimize` (SLSQP). This is the primary engine. The objective function maximizes Risk-Adjusted Return: `Expected Return - λ * Volatility`, where `λ` is the risk aversion parameter.
- **Linear-Programming Fallback (LP):** Solved via `scipy.optimize.linprog` (HiGHS). Used if the non-linear solver fails to converge.

**Constraints enforced automatically:**
- Total Allocation = 100%
- Minimum Cash Buffer >= 10%
- Minimum Liquidity Coverage >= 20%
- Asset-specific minimums and regulatory maximum exposure bounds
- No short-selling (all weights >= 0)

## The Asset Universe

Our baseline hackathon simulation uses a 5-asset universe:

| Asset | Expected Return | Risk | Max Allocation | Min Allocation | Liquid? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Equity** | 12% | High | 40% | 0% | No |
| **Bonds** | 7% | Low | 50% | 0% | Yes |
| **Gold** | 8% | Medium | 30% | 0% | No |
| **Corporate Bonds** | 9% | Medium | 35% | 0% | No |
| **Cash** | 4% | Very Low | 30% | 10% | Yes |

## Stress-Test Scenarios

The platform includes a robust simulation engine for 5 hypothetical market shocks:
1. **Equity Crash:** Equities fall sharply (-5% return) and equity volatility surges by 50%.
2. **Liquidity Crisis:** Market liquidity dries up. Required liquidity buffer is raised to 35%, and the cash minimum is increased to 20%.
3. **Stagflation:** High inflation and stagnant growth. Gold yields rise to 14%, while Equities drop to 5% and Corporate Bonds to 6%.
4. **Rate Hike:** Central bank raises interest rates. Cash yield jumps to 6.5%, driving Bond yields down to 3.5%.
5. **Market Crash:** A broad sell-off across both equities (-8%) and corporate credit (-2%), gold acts as a safe haven (+3%), and systemic volatility spikes across the entire covariance matrix (1.6x multiplier).

## Design Trade-offs

- **Mean-Variance vs. Linear:** Mean-variance realistically models correlations (e.g., Equity vs. Bonds), capturing diversification benefits better than linear sum-of-parts risk.
- **SLSQP with LP Fallback:** SLSQP is powerful for quadratic constraints but sensitive to initial conditions. The LP fallback ensures the system always returns a safe, compliant allocation even under extreme numerical stress.
- **Risk Score Normalization:** For the UI, raw portfolio volatility (typically 0.05 - 0.20) is scaled to a human-readable 0-100 score (`volatility / 0.30 * 100`).
- **FastAPI Migration:** The backend was migrated from Flask to FastAPI to provide out-of-the-box async readiness, automatic strict request validation using Pydantic (throwing 422s for bad inputs instead of 500s), and auto-generated OpenAPI documentation accessible at `/docs`.

## API Reference

| Method | Endpoint | Description | Example Response |
| :--- | :--- | :--- | :--- |
| **GET** | `/api/assets` | Returns the configured asset universe. | `[{"name": "Equity", "expected_return": 0.12...}]` |
| **GET** | `/api/portfolio` | Fetches the optimal allocation based on URL params (`capital`, `risk`). | `{"weights": {"Equity": 0.40...}, "risk": {...}}` |
| **GET** | `/api/risk` | Returns risk KPIs and threshold status. | `{"overall_risk": 32, "status": "SAFE"...}` |
| **POST** | `/api/optimize` | Generates a new portfolio with custom constraints. | `{"weights_pct": {"Equity": 35.0...}}` |
| **POST** | `/api/simulate` | Evaluates impact of a specific market shock. | `{"loss_pct": 12.5, "recommended_allocation": {...}}` |
| **POST** | `/api/rebalance`| Calculates drift between current vs optimal target. | `{"needs_rebalance": true, "rows": [...]}` |

## Known Limitations

- **In-Memory Only:** No database persistence. Refreshing resets state.
- **Simulated Data:** The system does not currently connect to a live market data feed (e.g., Bloomberg or Yahoo Finance API). Returns and covariances are static estimations.
- **Demo Auth:** The login screen (`admin` / `admin`) is a frontend mockup for hackathon presentation purposes.
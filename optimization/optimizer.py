"""
Core Portfolio Optimization Engine.
Maximizes risk-adjusted return subject to regulatory and liquidity safeguards.
"""

import sys
import os

# Ensure package root is in sys.path when executed directly
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy.optimize import linprog, minimize

from optimization.assets import Asset, RiskCategory, get_default_assets
from optimization.constraints import PortfolioConstraints
from optimization.risk import (
    build_default_covariance_matrix,
    get_asset_risk_score,
    portfolio_expected_return,
    portfolio_linear_risk,
    portfolio_volatility,
    portfolio_variance,
    calculate_risk_adjusted_score,
    portfolio_sharpe_ratio,
)


def get_currency_symbol() -> str:
    """Returns currency symbol, falling back to 'INR ' if terminal does not support unicode."""
    try:
        encoding = sys.stdout.encoding or "utf-8"
        "\u20b9".encode(encoding)
        return "\u20b9"
    except Exception:
        return "INR "


def format_inr(amount: float) -> str:
    """Formats a monetary amount into the Indian Rupee numbering format (Lakhs, Crores)."""
    sym = get_currency_symbol()
    if amount < 0:
        return f"-{sym}{format_inr(-amount)[len(sym):]}"

    s = f"{amount:.2f}"
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = parts[1]

    if len(integer_part) <= 3:
        return f"{sym}{integer_part}.{decimal_part}"

    last_three = integer_part[-3:]
    remaining = integer_part[:-3]

    groups = []
    while len(remaining) > 2:
        groups.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        groups.insert(0, remaining)

    formatted_int = ",".join(groups) + "," + last_three
    return f"{sym}{formatted_int}.{decimal_part}"


@dataclass
class OptimizationResult:
    """
    Standardized result of portfolio optimization.
    """
    capital: float
    weights: Dict[str, float]
    allocations: Dict[str, float]
    expected_return: float
    expected_return_amount: float
    portfolio_risk: float
    risk_adjusted_score: float
    sharpe_ratio: float
    cash_ratio: float
    liquidity_ratio: float
    method: str
    risk_aversion: float
    status: str
    is_valid: bool
    validation_details: Dict[str, Any]
    assets: List[Asset]

    def summary(self) -> str:
        """Generates a presentation-ready summary table."""
        sym = get_currency_symbol()
        lines = []
        lines.append("=" * 72)
        cap_fmt = format_inr(self.capital)
        lines.append(f"PORTFOLIO CAPITAL ALLOCATION (Total Capital: {cap_fmt})")
        method_name = "Mean-Variance (Markowitz QP)" if self.method == "mean_variance" else "Risk-Adjusted Linear Program (LP)"
        lines.append(f"Risk Aversion (lambda): {self.risk_aversion:.2f} | Engine: {method_name}")
        lines.append("=" * 72)
        alloc_col_title = f"Allocation ({sym.strip()})"
        lines.append(f"{'Asset':<18} {'Weight':>10} {alloc_col_title:>20} {'Exp Return':>12} {'Risk':>10}")
        lines.append("-" * 72)

        asset_map = {a.name: a for a in self.assets}
        total_weight = sum(self.weights.values())
        total_amount = sum(self.allocations.values())

        for name, weight in self.weights.items():
            amt = self.allocations[name]
            asset = asset_map[name]
            ret_str = f"{asset.expected_return * 100:.1f}%"
            risk_str = asset.risk_category.value
            lines.append(f"{name:<18} {weight * 100:>9.2f}% {format_inr(amt):>20} {ret_str:>12} {risk_str:>10}")

        lines.append("-" * 72)
        lines.append(f"{'Total':<18} {total_weight * 100:>9.2f}% {format_inr(total_amount):>20}")
        lines.append("=" * 72)
        lines.append("KEY METRICS & SAFEGUARDS:")
        ret_amt_fmt = format_inr(self.expected_return_amount)
        lines.append(f"  * Expected Annual Return : {self.expected_return * 100:.2f}% ({ret_amt_fmt} / yr)")
        lines.append(f"  * Portfolio Risk Metric  : {self.portfolio_risk * 100:.2f}%")
        lines.append(f"  * Risk-Adjusted Score    : {self.risk_adjusted_score:.4f} (E[R] - lambda * Risk)")
        lines.append(f"  * Sharpe Ratio           : {self.sharpe_ratio:.2f}")

        cash_pass = "[PASS]" if self.validation_details.get("checks", {}).get("cash_minimum", False) else "[FAIL]"
        liq_pass = "[PASS]" if self.validation_details.get("checks", {}).get("liquidity_requirement", False) else "[FAIL]"
        bounds_pass = "[PASS]" if self.validation_details.get("checks", {}).get("asset_bounds", False) else "[FAIL]"

        lines.append(f"  * Cash Allocation        : {self.cash_ratio * 100:.2f}% {cash_pass} (min 10%)")
        lines.append(f"  * Liquidity Ratio        : {self.liquidity_ratio * 100:.2f}% {liq_pass} (min 20%)")
        lines.append(f"  * Asset Exposure Limits  : {bounds_pass} (all within regulatory caps)")
        lines.append(f"  * Optimization Status    : {self.status} (Valid: {self.is_valid})")
        lines.append("=" * 72)

        return "\n".join(lines)


class PortfolioOptimizer:
    """
    Automated Capital Allocation and Safeguard Optimization Engine.

    Solves:
        Maximize Score = Expected Return - lambda * Risk
        Subject to:
            sum(w_i) = 1.0 (Total allocation = 100%)
            0 <= min_i <= w_i <= max_i (Max exposure bounds)
            w_cash >= 10% (Minimum cash buffer)
            sum(liquid_w) >= 20% (Liquidity coverage requirement)
    """

    def __init__(
        self,
        assets: Optional[List[Asset]] = None,
        constraints: Optional[PortfolioConstraints] = None,
        covariance_matrix: Optional[np.ndarray] = None
    ):
        self.assets = assets if assets is not None else get_default_assets()
        self.constraints = constraints if constraints is not None else PortfolioConstraints()

        # Build numerical vectors
        self.names = [a.name for a in self.assets]
        self.returns = np.array([a.expected_return for a in self.assets], dtype=float)
        self.risk_scores = np.array([get_asset_risk_score(a) for a in self.assets], dtype=float)
        self.cov_matrix = (
            covariance_matrix
            if covariance_matrix is not None
            else build_default_covariance_matrix(self.assets)
        )

    def optimize(
        self,
        capital: float = 10_000_000.0,  # 1 Crore (100 Lakhs = 10,000,000)
        risk_aversion: float = 0.50,
        method: str = "mean_variance",
    ) -> OptimizationResult:
        """
        Executes portfolio optimization for given capital and risk aversion parameter.

        Args:
            capital: Total capital to allocate in Rupees (default: 1 Crore = 10,000,000).
            risk_aversion: Penalty factor lambda for risk.
                           0.0 = Pure return seeker,
                           0.5 = Balanced / Moderate (default),
                           1.5+ = Conservative / Capital preservation.
            method: 'mean_variance' (Markowitz QP) or 'linear' (Linear Programming with Risk Scores).
        """
        if method == "linear":
            weights, status = self._solve_linear(risk_aversion)
        elif method == "mean_variance":
            weights, status = self._solve_mean_variance(risk_aversion)
        else:
            raise ValueError(f"Unknown optimization method: '{method}'. Choose 'mean_variance' or 'linear'.")

        # Validate resulting weights against constraints
        val_report = self.constraints.validate(weights, self.assets)

        # Calculate portfolio metrics
        exp_return = portfolio_expected_return(weights, self.returns)
        exp_return_amt = exp_return * capital

        if method == "mean_variance":
            port_risk = portfolio_volatility(weights, self.cov_matrix)
        else:
            port_risk = portfolio_linear_risk(weights, self.risk_scores)

        score = calculate_risk_adjusted_score(exp_return, port_risk, risk_aversion)
        vol = portfolio_volatility(weights, self.cov_matrix)
        sharpe = portfolio_sharpe_ratio(exp_return, vol)

        # Find cash and liquidity metrics
        cash_ratio = val_report["metrics"]["cash_weight"]
        liq_ratio = val_report["metrics"]["liquidity_ratio"]

        weight_dict = {name: float(weights[i]) for i, name in enumerate(self.names)}
        alloc_dict = {name: float(weights[i] * capital) for i, name in enumerate(self.names)}

        return OptimizationResult(
            capital=capital,
            weights=weight_dict,
            allocations=alloc_dict,
            expected_return=exp_return,
            expected_return_amount=exp_return_amt,
            portfolio_risk=port_risk,
            risk_adjusted_score=score,
            sharpe_ratio=sharpe,
            cash_ratio=cash_ratio,
            liquidity_ratio=liq_ratio,
            method=method,
            risk_aversion=risk_aversion,
            status=status,
            is_valid=val_report["is_valid"],
            validation_details=val_report,
            assets=self.assets,
        )

    def _solve_linear(self, risk_aversion: float) -> Tuple[np.ndarray, str]:
        """
        Solves via Linear Programming (LP):
            Maximize sum(w_i * (expected_return_i - lambda * risk_score_i))
            Equivalent to:
            Minimize c^T w where c_i = -(expected_return_i - lambda * risk_score_i)
        """
        n = len(self.assets)
        # Objective coefficients for minimization
        c = -(self.returns - (risk_aversion * self.risk_scores))

        # Equality constraint: sum(w_i) = 1.0
        A_eq = np.ones((1, n))
        b_eq = np.array([self.constraints.total_allocation])

        # Inequality constraints:
        # Liquidity constraint: sum(w_i * liq_factor_i) >= min_liquidity
        # => - sum(w_i * liq_factor_i) <= -min_liquidity
        A_ub = []
        b_ub = []
        if self.constraints.enforce_liquidity:
            liq_weights = self.constraints.get_liquidity_weights(self.assets)
            A_ub.append(-liq_weights)
            b_ub.append(-self.constraints.min_liquidity)

        A_ub_mat = np.array(A_ub) if A_ub else None
        b_ub_vec = np.array(b_ub) if b_ub else None

        # Individual asset bounds
        bounds = self.constraints.get_bounds(self.assets)

        res = linprog(
            c,
            A_ub=A_ub_mat,
            b_ub=b_ub_vec,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method="highs",
        )

        if not res.success:
            return np.zeros(n), f"Failed: {res.message}"

        # Clean numerical noise
        w = np.clip(res.x, 0.0, 1.0)
        w = w / np.sum(w)
        return w, "Optimal (Solved via HiGHS LP)"

    def _solve_mean_variance(self, risk_aversion: float) -> Tuple[np.ndarray, str]:
        """
        Solves Quadratic / Non-linear Mean-Variance Optimization (SLSQP):
            Minimize - ( expected_return - lambda * portfolio_volatility )
            subject to all constraints.
        """
        n = len(self.assets)
        bounds = self.constraints.get_bounds(self.assets)

        def objective(w: np.ndarray) -> float:
            ret = float(np.dot(w, self.returns))
            vol = float(np.sqrt(max(np.dot(w.T, np.dot(self.cov_matrix, w)), 0.0)))
            # Maximize (ret - lambda * vol) => Minimize - (ret - lambda * vol)
            return -(ret - (risk_aversion * vol))

        # Constraints for scipy.optimize.minimize
        scipy_constraints = [
            # Total sum = 1.0
            {
                "type": "eq",
                "fun": lambda w: np.sum(w) - self.constraints.total_allocation,
            }
        ]

        if self.constraints.enforce_liquidity:
            liq_weights = self.constraints.get_liquidity_weights(self.assets)
            scipy_constraints.append({
                "type": "ineq",
                "fun": lambda w: np.dot(w, liq_weights) - self.constraints.min_liquidity,
            })

        # Initial guess: uniform allocation within bounds
        w0 = np.array([(low + high) / 2.0 for low, high in bounds])
        w0 = w0 / np.sum(w0)

        res = minimize(
            objective,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=scipy_constraints,
            options={"maxiter": 1000, "ftol": 1e-9},
        )

        if not res.success:
            # Fallback to linear if SLSQP fails
            w_lin, stat_lin = self._solve_linear(risk_aversion)
            return w_lin, f"SLSQP Fallback ({res.message}) -> {stat_lin}"

        w = np.clip(res.x, 0.0, 1.0)
        w = w / np.sum(w)
        return w, "Optimal (Solved via SLSQP Quadratic Programming)"

    def stress_test(
        self,
        scenario: str,
        capital: float = 10_000_000.0,
        risk_aversion: float = 0.50
    ) -> OptimizationResult:
        """
        Simulates hypothetical market shocks and rebalances capital.

        Scenarios:
            - 'equity_crash': Equities fall sharply (-5% return, volatility surges)
            - 'liquidity_crisis': Liquidity requirement raised to 35%, cash min to 20%
            - 'stagflation': Gold surges to 14%, Equity drops to 5%
            - 'rate_hike': Cash yield rises to 6.5%, Bond yields drop to 3.5%
        """
        import copy
        assets_copy = copy.deepcopy(self.assets)
        constraints_copy = copy.deepcopy(self.constraints)
        cov_copy = np.copy(self.cov_matrix)

        if scenario == "equity_crash":
            for a in assets_copy:
                if a.name == "Equity":
                    a.expected_return = -0.05
                    a.risk_score = 0.35
            # Scale equity variance in cov_matrix
            eq_idx = self.names.index("Equity") if "Equity" in self.names else -1
            if eq_idx >= 0:
                cov_copy[eq_idx, :] *= 1.5
                cov_copy[:, eq_idx] *= 1.5

        elif scenario == "liquidity_crisis":
            constraints_copy.min_liquidity = 0.35
            constraints_copy.min_cash = 0.20

        elif scenario == "stagflation":
            for a in assets_copy:
                if a.name == "Gold":
                    a.expected_return = 0.14
                elif a.name == "Equity":
                    a.expected_return = 0.05
                elif a.name == "Corporate Bonds":
                    a.expected_return = 0.06

        elif scenario == "rate_hike":
            for a in assets_copy:
                if a.name == "Cash":
                    a.expected_return = 0.065
                elif a.name == "Bonds":
                    a.expected_return = 0.035

        else:
            raise ValueError(f"Unknown stress test scenario: '{scenario}'")

        stressed_optimizer = PortfolioOptimizer(
            assets=assets_copy,
            constraints=constraints_copy,
            covariance_matrix=cov_copy,
        )
        return stressed_optimizer.optimize(
            capital=capital,
            risk_aversion=risk_aversion,
            method="mean_variance"
        )


def run_demo():
    """Demonstrates optimizer addressing the hackathon prompt with 1 Crore capital."""
    sym = get_currency_symbol()
    print("\n" + "#" * 72)
    print("FINTECH ASSET & CAPITAL MANAGEMENT OPTIMIZATION ENGINE")
    print(f"Problem Statement: Optimal allocation for {sym}1 Crore with Risk Controls")
    print("#" * 72)

    optimizer = PortfolioOptimizer()

    # 1. Standard 1 Crore allocation with balanced risk aversion (lambda = 0.50)
    res_balanced = optimizer.optimize(capital=10_000_000.0, risk_aversion=0.50, method="mean_variance")
    print(res_balanced.summary())

    # 2. Conservative / Capital Preservation profile (lambda = 1.20)
    print("\n" + "=" * 72)
    print("SCENARIO A: HIGH RISK AVERSION (lambda = 1.20 - Capital Preservation Profile)")
    print("=" * 72)
    res_conservative = optimizer.optimize(capital=10_000_000.0, risk_aversion=1.20, method="mean_variance")
    print(res_conservative.summary())

    # 3. Market Stress Test: Equity Crash
    print("\n" + "=" * 72)
    print("SCENARIO B: STRESS TEST - EQUITY CRASH & VOLATILITY SURGE")
    print("=" * 72)
    res_stress = optimizer.stress_test("equity_crash", capital=10_000_000.0, risk_aversion=0.50)
    print(res_stress.summary())


if __name__ == "__main__":
    run_demo()

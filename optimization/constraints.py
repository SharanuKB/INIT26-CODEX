"""
Portfolio constraints modeling, boundary calculations, and compliance validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from optimization.assets import Asset


@dataclass
class PortfolioConstraints:
    """
    Portfolio-level constraints enforcement and configuration.

    Default constraints per hackathon specification:
    - Total allocation = 100% (sum of weights = 1.0)
    - Cash >= 10% (0.10)
    - Liquidity requirement >= 20% (0.20)
    - Asset exposure limits (e.g., Equity <= 40%, Gold <= 30%, Corporate Bonds <= 35%, Bonds <= 50%)
    - No short-selling (w_i >= 0)
    """
    total_allocation: float = 1.0
    min_cash: float = 0.10
    min_liquidity: float = 0.20
    max_individual_exposure: Optional[float] = None
    custom_bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    enforce_liquidity: bool = True
    tolerance: float = 1e-4

    def get_bounds(self, assets: List[Asset]) -> List[Tuple[float, float]]:
        """
        Computes (lower_bound, upper_bound) for each asset in the portfolio.
        Integrates individual asset bounds with portfolio-wide minimums (e.g., Cash min).
        """
        bounds = []
        for asset in assets:
            lower = asset.min_allocation
            upper = asset.max_allocation

            # Enforce portfolio-level cash minimum constraint
            if asset.name.lower() == "cash":
                lower = max(lower, self.min_cash)

            # Apply global exposure cap if defined
            if self.max_individual_exposure is not None:
                upper = min(upper, self.max_individual_exposure)

            # Check if custom override exists
            if asset.name in self.custom_bounds:
                c_min, c_max = self.custom_bounds[asset.name]
                lower = max(lower, c_min)
                upper = min(upper, c_max)

            if lower > upper:
                raise ValueError(
                    f"Infeasible bounds for asset '{asset.name}': lower ({lower}) > upper ({upper})"
                )

            bounds.append((float(lower), float(upper)))
        return bounds

    def get_liquidity_weights(self, assets: List[Asset]) -> np.ndarray:
        """
        Returns a vector of liquidity discount factors for each asset.
        Assets marked liquid have weight >= 1.0 (or custom liquidity_weight).
        """
        return np.array([
            asset.liquidity_weight if asset.is_liquid else 0.0
            for asset in assets
        ], dtype=float)

    def validate(
        self,
        weights: np.ndarray,
        assets: List[Asset]
    ) -> Dict[str, Any]:
        """
        Validates whether an allocation vector satisfies all institutional constraints.

        Returns a dictionary containing:
        - 'is_valid': bool indicating compliance
        - 'violations': list of descriptive violation strings
        - 'checks': detailed boolean status per constraint
        - 'metrics': computed values (total_sum, cash_weight, liquidity_weight)
        """
        violations: List[str] = []
        checks: Dict[str, bool] = {}

        weights = np.asarray(weights, dtype=float)
        bounds = self.get_bounds(assets)

        # 1. Total allocation constraint: sum(w) == 1.0
        total_sum = float(np.sum(weights))
        sum_valid = abs(total_sum - self.total_allocation) <= self.tolerance
        checks["total_allocation_100%"] = sum_valid
        if not sum_valid:
            violations.append(
                f"Total allocation is {total_sum * 100:.2f}%, expected {self.total_allocation * 100:.1f}%."
            )

        # 2. Asset boundary constraints: min <= w_i <= max
        bounds_valid = True
        for i, (asset, (low, high)) in enumerate(zip(assets, bounds)):
            w = weights[i]
            if w < low - self.tolerance:
                bounds_valid = False
                violations.append(
                    f"Asset '{asset.name}' allocation {w * 100:.2f}% is below minimum {low * 100:.2f}%."
                )
            if w > high + self.tolerance:
                bounds_valid = False
                violations.append(
                    f"Asset '{asset.name}' allocation {w * 100:.2f}% exceeds maximum allowed {high * 100:.2f}%."
                )
        checks["asset_bounds"] = bounds_valid

        # 3. Cash minimum constraint: w_cash >= min_cash
        cash_weight = 0.0
        for i, asset in enumerate(assets):
            if asset.name.lower() == "cash":
                cash_weight = weights[i]
                break

        cash_valid = cash_weight >= (self.min_cash - self.tolerance)
        checks["cash_minimum"] = cash_valid
        if not cash_valid:
            violations.append(
                f"Cash allocation {cash_weight * 100:.2f}% is below required minimum of {self.min_cash * 100:.1f}%."
            )

        # 4. Liquidity constraint: sum(liquid_w) >= min_liquidity
        liq_factors = self.get_liquidity_weights(assets)
        portfolio_liquidity = float(np.dot(weights, liq_factors))
        liq_valid = True
        if self.enforce_liquidity:
            liq_valid = portfolio_liquidity >= (self.min_liquidity - self.tolerance)
            if not liq_valid:
                violations.append(
                    f"Portfolio liquidity {portfolio_liquidity * 100:.2f}% is below required minimum of {self.min_liquidity * 100:.1f}%."
                )
        checks["liquidity_requirement"] = liq_valid

        is_valid = len(violations) == 0

        return {
            "is_valid": is_valid,
            "violations": violations,
            "checks": checks,
            "metrics": {
                "total_allocation": total_sum,
                "cash_weight": cash_weight,
                "liquidity_ratio": portfolio_liquidity,
            }
        }

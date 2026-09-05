"""
Optimization & Financial Control Logic Engine.
Member 2 - FinTech Asset & Capital Management / Optimization Controls Hackathon Solution.
"""

from optimization.assets import Asset, RiskCategory, get_default_assets
from optimization.constraints import PortfolioConstraints
from optimization.risk import (
    get_asset_risk_score,
    build_default_covariance_matrix,
    portfolio_expected_return,
    portfolio_linear_risk,
    portfolio_volatility,
    portfolio_variance,
    calculate_risk_adjusted_score,
    portfolio_sharpe_ratio,
)

__all__ = [
    "Asset",
    "RiskCategory",
    "get_default_assets",
    "PortfolioConstraints",
    "get_asset_risk_score",
    "build_default_covariance_matrix",
    "portfolio_expected_return",
    "portfolio_linear_risk",
    "portfolio_volatility",
    "portfolio_variance",
    "calculate_risk_adjusted_score",
    "portfolio_sharpe_ratio",
    "PortfolioOptimizer",
    "OptimizationResult",
    "format_inr",
    "run_demo",
]


def __getattr__(name: str):
    if name in ("PortfolioOptimizer", "OptimizationResult", "format_inr", "run_demo"):
        from optimization import optimizer
        return getattr(optimizer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

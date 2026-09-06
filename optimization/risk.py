"""
Risk models, risk metrics, and scoring functions for portfolio optimization.
"""

from typing import Dict, List, Optional
import numpy as np

from optimization.assets import Asset, RiskCategory

# Standard numerical mapping for qualitative risk tiers (volatility proxy)
DEFAULT_RISK_WEIGHTS: Dict[RiskCategory, float] = {
    RiskCategory.VERY_LOW: 0.02,
    RiskCategory.LOW: 0.06,
    RiskCategory.MEDIUM: 0.12,
    RiskCategory.HIGH: 0.20,
    RiskCategory.VERY_HIGH: 0.30,
}


def get_asset_risk_score(asset: Asset) -> float:
    """Returns numerical risk score for an asset."""
    if asset.risk_score is not None:
        return asset.risk_score
    return DEFAULT_RISK_WEIGHTS.get(asset.risk_category, 0.10)


def build_default_covariance_matrix(assets: List[Asset]) -> np.ndarray:
    """
    Constructs a realistic covariance matrix based on asset volatility
    and asset-class correlations.

    Correlations represent typical financial market interactions:
    - Cash has near-zero correlation with all assets.
    - Sovereign Bonds provide negative or low correlation with Equity.
    - Gold acts as a safe-haven non-correlated asset.
    - Corporate Bonds correlate moderately with both Bonds and Equity.
    """
    n = len(assets)
    # Estimated annual standard deviations (volatilities)
    vol_map = {
        RiskCategory.VERY_LOW: 0.015,
        RiskCategory.LOW: 0.060,
        RiskCategory.MEDIUM: 0.120,
        RiskCategory.HIGH: 0.180,
        RiskCategory.VERY_HIGH: 0.280,
    }

    volatilities = np.array([
        asset.risk_score if asset.risk_score is not None
        else vol_map.get(asset.risk_category, 0.10)
        for asset in assets
    ])

    # Base correlation matrix (identity)
    corr = np.eye(n)

    # Asset name lookup
    name_to_idx = {asset.name: i for i, asset in enumerate(assets)}

    def set_corr(a1: str, a2: str, val: float):
        if a1 in name_to_idx and a2 in name_to_idx:
            i, j = name_to_idx[a1], name_to_idx[a2]
            corr[i, j] = val
            corr[j, i] = val

    # Cross-asset correlations
    set_corr("Equity", "Bonds", -0.15)
    set_corr("Equity", "Gold", 0.05)
    set_corr("Equity", "Corporate Bonds", 0.40)
    set_corr("Equity", "Cash", 0.00)

    set_corr("Bonds", "Corporate Bonds", 0.65)
    set_corr("Bonds", "Gold", 0.12)
    set_corr("Bonds", "Cash", 0.00)

    set_corr("Corporate Bonds", "Gold", 0.10)
    set_corr("Corporate Bonds", "Cash", 0.00)

    set_corr("Gold", "Cash", 0.00)

    # Covariance = diag(vol) * Corr * diag(vol)
    cov = np.outer(volatilities, volatilities) * corr
    # Ensure positive semi-definiteness
    min_eig = np.min(np.real(np.linalg.eigvals(cov)))
    if min_eig < 1e-8:
        cov += (abs(min_eig) + 1e-6) * np.eye(n)

    return cov


def portfolio_expected_return(weights: np.ndarray, returns: np.ndarray) -> float:
    """Calculates portfolio expected return: w^T * r"""
    return float(np.dot(weights, returns))


def portfolio_linear_risk(weights: np.ndarray, risk_scores: np.ndarray) -> float:
    """Calculates weighted linear portfolio risk score: w^T * risk_scores"""
    return float(np.dot(weights, risk_scores))


def portfolio_variance(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Calculates portfolio variance: w^T * Sigma * w"""
    return float(np.dot(weights.T, np.dot(cov_matrix, weights)))


def portfolio_volatility(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """Calculates portfolio standard deviation (volatility): sqrt(w^T * Sigma * w)"""
    return float(np.sqrt(max(portfolio_variance(weights, cov_matrix), 0.0)))


def calculate_risk_adjusted_score(
    expected_return: float,
    risk: float,
    risk_aversion: float = 0.5
) -> float:
    """
    Computes risk-adjusted score:
    Score = Expected Return - lambda * Risk
    """
    return float(expected_return - (risk_aversion * risk))


def portfolio_sharpe_ratio(
    expected_return: float,
    volatility: float,
    risk_free_rate: float = 0.04
) -> float:
    """Computes Sharpe Ratio: (E[R] - Rf) / Volatility"""
    if volatility <= 1e-8:
        return 0.0
    return float((expected_return - risk_free_rate) / volatility)

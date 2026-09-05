"""
Asset definitions and default asset catalog for Portfolio Optimization.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class RiskCategory(str, Enum):
    """Qualitative risk categorization for assets."""
    VERY_LOW = "Very Low"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


@dataclass
class Asset:
    """
    Financial Asset representation with risk, return, and allocation parameters.

    Attributes:
        name: Name of the asset class (e.g., 'Equity', 'Bonds').
        expected_return: Expected annual return as a decimal (e.g., 0.12 for 12%).
        risk_category: Qualitative risk tier (VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH).
        max_allocation: Maximum allowable portfolio weight as a decimal (e.g., 0.40 for 40%).
        min_allocation: Minimum required portfolio weight as a decimal (default: 0.0, e.g., 0.10 for Cash).
        is_liquid: Whether the asset qualifies towards liquidity requirements.
        liquidity_weight: Liquidity discount factor (1.0 = fully liquid cash/sovereign bond).
        risk_score: Numerical risk score (if None, mapped from risk_category).
        description: Brief description or ticker/class note.
    """
    name: str
    expected_return: float
    risk_category: RiskCategory
    max_allocation: float
    min_allocation: float = 0.0
    is_liquid: bool = False
    liquidity_weight: float = 0.0
    risk_score: Optional[float] = None
    description: str = ""

    def __post_init__(self):
        if not (0.0 <= self.min_allocation <= self.max_allocation <= 1.0):
            raise ValueError(
                f"Invalid allocation bounds for {self.name}: "
                f"min={self.min_allocation}, max={self.max_allocation}"
            )
        if self.is_liquid and self.liquidity_weight == 0.0:
            self.liquidity_weight = 1.0


def get_default_assets() -> List[Asset]:
    """
    Returns the standard hackathon benchmark asset universe:

    Asset            Expected Return  Risk       Max Allocation  Min Allocation  Liquid?
    Equity           12% (0.12)       High       40% (0.40)      0%              No
    Bonds            7%  (0.07)       Low        50% (0.50)      0%              Yes
    Gold             8%  (0.08)       Medium     30% (0.30)      0%              No
    Cash             4%  (0.04)       Very Low   30% (0.30)      10% (0.10)      Yes
    Corporate Bonds  9%  (0.09)       Medium     35% (0.35)      0%              No
    """
    return [
        Asset(
            name="Equity",
            expected_return=0.12,
            risk_category=RiskCategory.HIGH,
            max_allocation=0.40,
            min_allocation=0.0,
            is_liquid=False,
            liquidity_weight=0.0,
            description="Large-cap & diversified equities"
        ),
        Asset(
            name="Bonds",
            expected_return=0.07,
            risk_category=RiskCategory.LOW,
            max_allocation=0.50,
            min_allocation=0.0,
            is_liquid=True,
            liquidity_weight=1.0,
            description="Sovereign / Government bonds (High Quality Liquid Asset)"
        ),
        Asset(
            name="Gold",
            expected_return=0.08,
            risk_category=RiskCategory.MEDIUM,
            max_allocation=0.30,
            min_allocation=0.0,
            is_liquid=False,
            liquidity_weight=0.0,
            description="Precious metal / inflation hedge"
        ),
        Asset(
            name="Cash",
            expected_return=0.04,
            risk_category=RiskCategory.VERY_LOW,
            max_allocation=0.30,
            min_allocation=0.10,  # Cash >= 10% constraint
            is_liquid=True,
            liquidity_weight=1.0,
            description="Cash & cash equivalents (immediate liquidity)"
        ),
        Asset(
            name="Corporate Bonds",
            expected_return=0.09,
            risk_category=RiskCategory.MEDIUM,
            max_allocation=0.35,
            min_allocation=0.0,
            is_liquid=False,
            liquidity_weight=0.0,
            description="Investment grade corporate credit"
        ),
    ]

"""
Unit test suite for Portfolio Optimization and Financial Control Logic.
"""

import sys
import os
import unittest

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import numpy as np

from optimization.assets import Asset, RiskCategory, get_default_assets
from optimization.constraints import PortfolioConstraints
from optimization.risk import (
    DEFAULT_RISK_WEIGHTS,
    build_default_covariance_matrix,
    portfolio_expected_return,
    portfolio_linear_risk,
    portfolio_volatility,
    calculate_risk_adjusted_score,
)
from optimization.optimizer import PortfolioOptimizer, format_inr


class TestAssetUniverse(unittest.TestCase):
    """Verifies default asset catalog specifications."""

    def setUp(self):
        self.assets = get_default_assets()
        self.asset_map = {a.name: a for a in self.assets}

    def test_default_assets_count_and_presence(self):
        expected_names = {"Equity", "Bonds", "Gold", "Cash", "Corporate Bonds"}
        self.assertEqual(set(self.asset_map.keys()), expected_names)

    def test_asset_parameters(self):
        # Equity: Return 12%, High Risk, Max 40%
        equity = self.asset_map["Equity"]
        self.assertAlmostEqual(equity.expected_return, 0.12)
        self.assertEqual(equity.risk_category, RiskCategory.HIGH)
        self.assertAlmostEqual(equity.max_allocation, 0.40)

        # Bonds: Return 7%, Low Risk, Max 50%, Liquid
        bonds = self.asset_map["Bonds"]
        self.assertAlmostEqual(bonds.expected_return, 0.07)
        self.assertEqual(bonds.risk_category, RiskCategory.LOW)
        self.assertAlmostEqual(bonds.max_allocation, 0.50)
        self.assertTrue(bonds.is_liquid)

        # Gold: Return 8%, Medium Risk, Max 30%
        gold = self.asset_map["Gold"]
        self.assertAlmostEqual(gold.expected_return, 0.08)
        self.assertEqual(gold.risk_category, RiskCategory.MEDIUM)
        self.assertAlmostEqual(gold.max_allocation, 0.30)

        # Cash: Return 4%, Very Low Risk, Max 30%, Min 10%, Liquid
        cash = self.asset_map["Cash"]
        self.assertAlmostEqual(cash.expected_return, 0.04)
        self.assertEqual(cash.risk_category, RiskCategory.VERY_LOW)
        self.assertAlmostEqual(cash.max_allocation, 0.30)
        self.assertAlmostEqual(cash.min_allocation, 0.10)
        self.assertTrue(cash.is_liquid)

        # Corporate Bonds: Return 9%, Medium Risk, Max 35%
        cb = self.asset_map["Corporate Bonds"]
        self.assertAlmostEqual(cb.expected_return, 0.09)
        self.assertEqual(cb.risk_category, RiskCategory.MEDIUM)
        self.assertAlmostEqual(cb.max_allocation, 0.35)


class TestConstraints(unittest.TestCase):
    """Verifies constraint enforcement and validation."""

    def setUp(self):
        self.assets = get_default_assets()
        self.constraints = PortfolioConstraints()

    def test_valid_portfolio_passes_validation(self):
        # Example valid weights: Equity 35%, Bonds 30%, Gold 15%, Corp Bonds 10%, Cash 10%
        weights = np.array([0.35, 0.30, 0.15, 0.10, 0.10])
        # Asset order in get_default_assets(): Equity, Bonds, Gold, Cash, Corporate Bonds
        # Re-map correctly
        order = [a.name for a in self.assets]
        sample_w = {
            "Equity": 0.35,
            "Bonds": 0.30,
            "Gold": 0.15,
            "Cash": 0.10,
            "Corporate Bonds": 0.10,
        }
        w_vec = np.array([sample_w[name] for name in order])

        res = self.constraints.validate(w_vec, self.assets)
        self.assertTrue(res["is_valid"])
        self.assertEqual(len(res["violations"]), 0)

    def test_breach_total_allocation(self):
        # Sum = 90% (underallocated)
        order = [a.name for a in self.assets]
        sample_w = {
            "Equity": 0.30,
            "Bonds": 0.30,
            "Gold": 0.10,
            "Cash": 0.10,
            "Corporate Bonds": 0.10,
        }
        w_vec = np.array([sample_w[name] for name in order])

        res = self.constraints.validate(w_vec, self.assets)
        self.assertFalse(res["is_valid"])
        self.assertIn("Total allocation", res["violations"][0])

    def test_breach_asset_cap(self):
        # Equity exceeds 40%
        order = [a.name for a in self.assets]
        sample_w = {
            "Equity": 0.50,  # Cap is 40%
            "Bonds": 0.20,
            "Gold": 0.10,
            "Cash": 0.10,
            "Corporate Bonds": 0.10,
        }
        w_vec = np.array([sample_w[name] for name in order])

        res = self.constraints.validate(w_vec, self.assets)
        self.assertFalse(res["is_valid"])
        self.assertFalse(res["checks"]["asset_bounds"])

    def test_breach_cash_minimum(self):
        # Cash is 5%, below 10% minimum
        order = [a.name for a in self.assets]
        sample_w = {
            "Equity": 0.35,
            "Bonds": 0.35,
            "Gold": 0.15,
            "Cash": 0.05,  # Violates 10%
            "Corporate Bonds": 0.10,
        }
        w_vec = np.array([sample_w[name] for name in order])

        res = self.constraints.validate(w_vec, self.assets)
        self.assertFalse(res["is_valid"])
        self.assertFalse(res["checks"]["cash_minimum"])

    def test_breach_liquidity_requirement(self):
        # Only Cash is liquid (10%), Bonds = 0%, Total Liquidity = 10% < 20%
        order = [a.name for a in self.assets]
        sample_w = {
            "Equity": 0.40,
            "Bonds": 0.00,  # Liquid asset = 0
            "Gold": 0.25,
            "Cash": 0.10,   # Liquid asset = 10%
            "Corporate Bonds": 0.25,
        }
        w_vec = np.array([sample_w[name] for name in order])

        res = self.constraints.validate(w_vec, self.assets)
        self.assertFalse(res["is_valid"])
        self.assertFalse(res["checks"]["liquidity_requirement"])


class TestOptimizerEngine(unittest.TestCase):
    """Verifies optimization engine results, bounds, capital math, and risk controls."""

    def setUp(self):
        self.optimizer = PortfolioOptimizer()
        self.capital = 10_000_000.0  # ₹1 Crore

    def test_mean_variance_optimization_validity(self):
        res = self.optimizer.optimize(capital=self.capital, risk_aversion=0.50, method="mean_variance")

        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(sum(res.weights.values()), 1.0, places=4)
        self.assertAlmostEqual(sum(res.allocations.values()), self.capital, places=2)

        # Check cash >= 10%
        self.assertGreaterEqual(res.weights["Cash"], 0.10 - 1e-4)

        # Check liquidity >= 20%
        liq_total = res.weights["Cash"] + res.weights["Bonds"]
        self.assertGreaterEqual(liq_total, 0.20 - 1e-4)

        # Check caps
        self.assertLessEqual(res.weights["Equity"], 0.40 + 1e-4)
        self.assertLessEqual(res.weights["Gold"], 0.30 + 1e-4)
        self.assertLessEqual(res.weights["Corporate Bonds"], 0.35 + 1e-4)
        self.assertLessEqual(res.weights["Bonds"], 0.50 + 1e-4)
        self.assertLessEqual(res.weights["Cash"], 0.30 + 1e-4)

    def test_linear_optimization_validity(self):
        res = self.optimizer.optimize(capital=self.capital, risk_aversion=0.50, method="linear")

        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(sum(res.weights.values()), 1.0, places=4)
        self.assertAlmostEqual(sum(res.allocations.values()), self.capital, places=2)
        self.assertGreaterEqual(res.weights["Cash"], 0.10 - 1e-4)
        liq_total = res.weights["Cash"] + res.weights["Bonds"]
        self.assertGreaterEqual(liq_total, 0.20 - 1e-4)

    def test_risk_aversion_behavior(self):
        # Higher risk aversion should lower portfolio risk
        res_growth = self.optimizer.optimize(capital=self.capital, risk_aversion=0.10, method="mean_variance")
        res_defense = self.optimizer.optimize(capital=self.capital, risk_aversion=1.50, method="mean_variance")

        self.assertGreater(res_growth.portfolio_risk, res_defense.portfolio_risk)
        # Defense should hold more safe assets (Cash or Bonds)
        safe_growth = res_growth.weights["Cash"] + res_growth.weights["Bonds"]
        safe_defense = res_defense.weights["Cash"] + res_defense.weights["Bonds"]
        self.assertGreaterEqual(safe_defense, safe_growth)

    def test_stress_test_equity_crash(self):
        res_stress = self.optimizer.stress_test("equity_crash", capital=self.capital, risk_aversion=0.50)
        self.assertTrue(res_stress.is_valid)
        # Under equity crash, equity weight should drop significantly (to near zero)
        self.assertLess(res_stress.weights["Equity"], 0.05)

    def test_currency_formatting(self):
        self.assertIn("1,00,00,000.00", format_inr(10_000_000.0))
        self.assertIn("35,00,000.00", format_inr(3_500_000.0))


if __name__ == "__main__":
    unittest.main()

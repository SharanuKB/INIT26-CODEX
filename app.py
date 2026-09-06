from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from optimization.optimizer import PortfolioOptimizer
from optimization.assets import get_default_assets
from optimization.constraints import PortfolioConstraints
import os

app = Flask(__name__, static_folder=".")
CORS(app)

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/frontend/<path:path>")
def serve_frontend(path):
    return send_from_directory("frontend", path)

@app.route("/css/<path:path>")
def serve_css(path):
    return send_from_directory("css", path)

@app.route("/js/<path:path>")
def serve_js(path):
    return send_from_directory("js", path)

@app.route("/api/assets", methods=["GET"])
def get_assets():
    assets = get_default_assets()
    return jsonify([
        {
            "name": a.name,
            "expected_return": a.expected_return,
            "risk_category": a.risk_category.value,
            "max_allocation": a.max_allocation,
            "min_allocation": a.min_allocation,
            "is_liquid": a.is_liquid,
            "description": a.description
        } for a in assets
    ])

def _get_risk_obj(capital, risk_pref):
    optimizer = PortfolioOptimizer()
    risk_aversion = 0.50
    if risk_pref.lower() == "conservative":
        risk_aversion = 1.20
    elif risk_pref.lower() == "aggressive":
        risk_aversion = 0.10
        
    res = optimizer.optimize(capital=capital, risk_aversion=risk_aversion, method="mean_variance")
    
    overall_risk = min(100.0, (res.portfolio_risk / 0.30) * 100)
    if overall_risk < 40:
        status = "SAFE"
        message = "Portfolio is within safe limits."
    elif overall_risk < 70:
        status = "WARNING"
        message = "Portfolio risk is increasing. Monitoring required."
    else:
        status = "CRITICAL"
        message = "Critical risk detected. Rebalancing required."
        
    equity_exposure = res.weights.get("Equity", 0) * 100
    liquidity = res.liquidity_ratio * 100
    volatility = res.portfolio_risk * 100
    cash_min = res.weights.get("Cash", 0) * 100
    
    thresholds = [
        {"metric": "Equity Exposure", "current_pct": equity_exposure, "limit_pct": 40.0, "status": "SAFE" if equity_exposure <= 40 else "WARNING"},
        {"metric": "Liquidity", "current_pct": liquidity, "limit_pct": 20.0, "status": "SAFE" if liquidity >= 20 else "WARNING"},
        {"metric": "Volatility", "current_pct": volatility, "limit_pct": 20.0, "status": "SAFE" if volatility <= 20 else "WARNING"},
        {"metric": "Cash Minimum", "current_pct": cash_min, "limit_pct": 10.0, "status": "SAFE" if cash_min >= 10 else "WARNING"},
    ]
    
    market_risk = min(100, volatility * 1.5)
    liquidity_risk = max(0, 100 - (liquidity * 2))
    concentration_risk = max([w * 100 for w in res.weights.values()]) * 1.2
    drawdown = overall_risk * 0.2
    
    return {
        "overall_risk": overall_risk,
        "status": status,
        "message": message,
        "market_risk": market_risk,
        "liquidity_risk": liquidity_risk,
        "concentration_risk": concentration_risk,
        "drawdown": drawdown,
        "thresholds": thresholds
    }, res

@app.route("/api/portfolio", methods=["GET"])
def get_portfolio():
    capital = float(request.args.get("capital", 10000000))
    risk_pref = request.args.get("risk", "balanced")
    
    risk_obj, res = _get_risk_obj(capital, risk_pref)
    
    return jsonify({
        "weights": res.weights,
        "weights_pct": {k: v * 100 for k, v in res.weights.items()},
        "allocations": res.allocations,
        "expected_return": res.expected_return,
        "portfolio_risk": res.portfolio_risk,
        "sharpe_ratio": res.sharpe_ratio,
        "cash_ratio": res.cash_ratio,
        "liquidity_ratio": res.liquidity_ratio,
        "status": res.status,
        "is_valid": res.is_valid,
        "validation_details": res.validation_details,
        "risk": risk_obj
    })

@app.route("/api/risk", methods=["GET"])
def get_risk():
    capital = float(request.args.get("capital", 10000000))
    risk_pref = request.args.get("risk", "balanced")
    risk_obj, _ = _get_risk_obj(capital, risk_pref)
    return jsonify(risk_obj)

@app.route("/api/optimize", methods=["POST"])
def optimize():
    data = request.json or {}
    capital = float(data.get("capital", 10000000))
    risk_pref = data.get("riskPreference", "Balanced")
    liquidity_pct = data.get("liquidity")
    max_exp_pct = data.get("maxExposure")
    method = data.get("method", "mean_variance")
    
    constraints = PortfolioConstraints()
    if liquidity_pct is not None:
        constraints.min_liquidity = float(liquidity_pct) / 100.0
    if max_exp_pct is not None:
        constraints.max_individual_exposure = float(max_exp_pct) / 100.0
        
    optimizer = PortfolioOptimizer(constraints=constraints)
    risk_aversion = 0.50
    if risk_pref.lower() == "conservative":
        risk_aversion = 1.20
    elif risk_pref.lower() == "aggressive":
        risk_aversion = 0.10
        
    res = optimizer.optimize(capital=capital, risk_aversion=risk_aversion, method=method)
    
    overall_risk = min(100.0, (res.portfolio_risk / 0.30) * 100)
    risk_obj = {
        "overall_risk": overall_risk,
        "status": "SAFE" if overall_risk < 40 else "WARNING" if overall_risk < 70 else "CRITICAL"
    }

    return jsonify({
        "weights": res.weights,
        "weights_pct": {k: v * 100 for k, v in res.weights.items()},
        "allocations": res.allocations,
        "expected_return": res.expected_return,
        "portfolio_risk": res.portfolio_risk,
        "sharpe_ratio": res.sharpe_ratio,
        "cash_ratio": res.cash_ratio,
        "liquidity_ratio": res.liquidity_ratio,
        "status": res.status,
        "is_valid": res.is_valid,
        "validation_details": res.validation_details,
        "risk": risk_obj
    })

@app.route("/api/simulate", methods=["POST"])
def simulate():
    data = request.json or {}
    scenario = data.get("scenario", "crash")
    capital = float(data.get("capital", 10000000))
    
    scenario_map = {
        "crash": ("market_crash", "Market Crash"),
        "interest": ("rate_hike", "Interest Rate Hike"),
        "liquidity": ("liquidity_crisis", "Liquidity Crisis"),
        "equity": ("equity_crash", "Equity Shock")
    }
    
    backend_scenario, label = scenario_map.get(scenario, ("equity_crash", "Unknown Shock"))
    
    optimizer = PortfolioOptimizer()
    res_before = optimizer.optimize(capital=capital, risk_aversion=0.50, method="mean_variance")
    res_after = optimizer.stress_test(scenario=backend_scenario, capital=capital, risk_aversion=0.50)
    
    import copy
    import numpy as np
    assets_shocked = copy.deepcopy(optimizer.assets)
    if backend_scenario == "market_crash":
        for a in assets_shocked:
            if a.name == "Equity": a.expected_return = -0.08
            elif a.name == "Corporate Bonds": a.expected_return = -0.02
            elif a.name == "Gold": a.expected_return = 0.03
    elif backend_scenario == "equity_crash":
        for a in assets_shocked:
            if a.name == "Equity": a.expected_return = -0.05
    elif backend_scenario == "stagflation":
        for a in assets_shocked:
            if a.name == "Gold": a.expected_return = 0.14
            elif a.name == "Equity": a.expected_return = 0.05
            elif a.name == "Corporate Bonds": a.expected_return = 0.06
    elif backend_scenario == "rate_hike":
        for a in assets_shocked:
            if a.name == "Cash": a.expected_return = 0.065
            elif a.name == "Bonds": a.expected_return = 0.035
            
    shocked_returns = np.array([a.expected_return for a in assets_shocked])
    original_weights = np.array([res_before.weights[a.name] for a in optimizer.assets])
    
    port_return = np.dot(original_weights, shocked_returns)
    port_value_after = capital * (1 + port_return)
    loss_pct = -port_return * 100
        
    risk_score_after = min(100.0, (res_after.portfolio_risk / 0.30) * 100)
    
    msg = f"{label} detected. Risk profile changed significantly. System recommends immediate portfolio rebalancing."
    
    return jsonify({
        "scenario": scenario,
        "scenario_label": label,
        "portfolio_before": capital,
        "portfolio_after": port_value_after,
        "loss_pct": loss_pct,
        "risk_score_after": risk_score_after,
        "message": msg,
        "recommended_allocation": {
            "weights_pct": {k: v * 100 for k, v in res_after.weights.items()},
            "allocations": res_after.allocations,
            "expected_return": res_after.expected_return,
            "portfolio_risk": res_after.portfolio_risk
        }
    })

@app.route("/api/rebalance", methods=["POST"])
def rebalance():
    data = request.json or {}
    capital = float(data.get("capital", 10000000))
    current_weights_pct = data.get("current_weights")
    if not current_weights_pct:
        current_weights_pct = {
            "Equity": 45,
            "Bonds": 25,
            "Gold": 15,
            "Corporate Bonds": 10,
            "Cash": 5
        }
        
    optimizer = PortfolioOptimizer()
    res = optimizer.optimize(capital=capital, risk_aversion=0.50, method="mean_variance")
    
    rows = []
    needs_rebalance = False
    for asset_name, current_pct in current_weights_pct.items():
        target_pct = res.weights.get(asset_name, 0) * 100
        change = target_pct - current_pct
        if abs(change) > 1.0:
            needs_rebalance = True
        rows.append({
            "asset": asset_name,
            "current_pct": current_pct,
            "target_pct": target_pct,
            "change_pct": change
        })
        
    reason = "Significant drift detected." if needs_rebalance else "Portfolio is close to optimal target."
    if current_weights_pct.get("Cash", 0) < 10:
        reason += " Cash balance is below 10% minimum threshold."
        needs_rebalance = True
        
    return jsonify({
        "rows": rows,
        "needs_rebalance": needs_rebalance,
        "reason": reason,
        "target_portfolio": {
            "weights_pct": {k: v * 100 for k, v in res.weights.items()},
            "allocations": res.allocations
        }
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)

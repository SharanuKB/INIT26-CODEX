from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict
import uvicorn
import copy
import numpy as np
import sqlite3
import asyncio
import random
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from optimization.optimizer import PortfolioOptimizer
from optimization.assets import get_default_assets
from optimization.constraints import PortfolioConstraints

app = FastAPI(title="CapitalGuard API")

# 1. Permissive CORS (for Hackathon Demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Pydantic Request Models (Automatic Validation & Clean 422s)
class OptimizeRequest(BaseModel):
    capital: float = Field(10_000_000, gt=0)
    riskPreference: str = "Balanced"
    liquidity: Optional[float] = None
    maxExposure: Optional[float] = None
    method: Optional[str] = "mean_variance"

class SimulateRequest(BaseModel):
    scenario: str
    capital: float = Field(10_000_000, gt=0)

class RebalanceRequest(BaseModel):
    current_weights: Optional[Dict[str, float]] = None
    capital: float = Field(10_000_000, gt=0)


# 3. Static Files Mounting
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")


# 4. API Routes (with original business logic & matching return dicts)
@app.get("/api/assets")
def get_assets():
    assets = get_default_assets()
    return [
        {
            "name": a.name,
            "expected_return": a.expected_return,
            "risk_category": a.risk_category.value,
            "max_allocation": a.max_allocation,
            "min_allocation": a.min_allocation,
            "is_liquid": a.is_liquid,
            "description": a.description
        } for a in assets
    ]


def _get_risk_obj(capital: float, risk_pref: str):
    optimizer = PortfolioOptimizer()
    risk_aversion = 0.50
    if risk_pref.lower() == "conservative":
        risk_aversion = 1.20
    elif risk_pref.lower() == "aggressive":
        risk_aversion = 0.10
        
    try:
        res = optimizer.optimize(capital=capital, risk_aversion=risk_aversion, method="mean_variance")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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


@app.get("/api/risk")
def get_risk(capital: float = Query(10_000_000, gt=0), risk: str = "balanced"):
    risk_obj, _ = _get_risk_obj(capital, risk)
    return risk_obj


@app.post("/api/optimize")
def optimize(req: OptimizeRequest):
    constraints = PortfolioConstraints()
    if req.liquidity is not None:
        constraints.min_liquidity = req.liquidity / 100.0
    if req.maxExposure is not None:
        constraints.max_individual_exposure = req.maxExposure / 100.0
        
    optimizer = PortfolioOptimizer(constraints=constraints)
    risk_aversion = 0.50
    if req.riskPreference.lower() == "conservative":
        risk_aversion = 1.20
    elif req.riskPreference.lower() == "aggressive":
        risk_aversion = 0.10
        
    try:
        res = optimizer.optimize(capital=req.capital, risk_aversion=risk_aversion, method=req.method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    overall_risk = min(100.0, (res.portfolio_risk / 0.30) * 100)
    risk_obj = {
        "overall_risk": overall_risk,
        "status": "SAFE" if overall_risk < 40 else "WARNING" if overall_risk < 70 else "CRITICAL"
    }

    val_details = copy.deepcopy(res.validation_details)
    val_details["checks"] = {k: bool(v) for k, v in val_details["checks"].items()}

    return {
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
        "validation_details": val_details,
        "risk": risk_obj
    }


@app.post("/api/simulate")
def simulate(req: SimulateRequest):
    scenario_map = {
        "crash": ("market_crash", "Market Crash"),
        "interest": ("rate_hike", "Interest Rate Hike"),
        "liquidity": ("liquidity_crisis", "Liquidity Crisis"),
        "equity": ("equity_crash", "Equity Shock")
    }
    
    backend_scenario, label = scenario_map.get(req.scenario, ("equity_crash", "Unknown Shock"))
    optimizer = PortfolioOptimizer()
    
    try:
        res_before = optimizer.optimize(capital=req.capital, risk_aversion=0.50, method="mean_variance")
        res_after = optimizer.stress_test(scenario=backend_scenario, capital=req.capital, risk_aversion=0.50)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
    original_weights = np.array([res_before.weights.get(a.name, 0.0) for a in optimizer.assets])
    
    port_return = np.dot(original_weights, shocked_returns)
    port_value_after = req.capital * (1 + port_return)
    loss_pct = -port_return * 100
        
    risk_score_after = min(100.0, (res_after.portfolio_risk / 0.30) * 100)
    msg = f"{label} detected. Risk profile changed significantly. System recommends immediate portfolio rebalancing."
    
    return {
        "scenario": req.scenario,
        "scenario_label": label,
        "portfolio_before": req.capital,
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
    }


@app.post("/api/rebalance")
def rebalance(req: RebalanceRequest):
    current_weights_pct = req.current_weights
    if not current_weights_pct:
        current_weights_pct = {
            "Equity": 45,
            "Bonds": 25,
            "Gold": 15,
            "Corporate Bonds": 10,
            "Cash": 5
        }
        
    optimizer = PortfolioOptimizer()
    try:
        res = optimizer.optimize(capital=req.capital, risk_aversion=0.50, method="mean_variance")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
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
        
    return {
        "rows": rows,
        "needs_rebalance": needs_rebalance,
        "reason": reason,
        "target_portfolio": {
            "weights_pct": {k: v * 100 for k, v in res.weights.items()},
            "allocations": res.allocations
        }
    }


# ==========================================

# LIVE FINTECH ENGINE (Synthetic Market)

# ==========================================


ASSETS_META = {
    "Equity": {"start": 150.0, "vol": 0.20},
    "Bonds": {"start": 100.0, "vol": 0.05},
    "Gold": {"start": 2000.0, "vol": 0.15},
    "Corporate Bonds": {"start": 100.0, "vol": 0.10},
    "Cash": {"start": 1.0, "vol": 0.01}
}
ASSET_NAMES = list(ASSETS_META.keys())

conn = sqlite3.connect("capitalguard.db", check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")

def init_db():
    conn.execute('''
    CREATE TABLE IF NOT EXISTS portfolio (
        asset TEXT PRIMARY KEY,
        current_weight REAL,
        target_weight REAL,
        last_price REAL,
        updated_at TIMESTAMP
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset TEXT,
        timestamp TIMESTAMP,
        price REAL
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP,
        metric TEXT,
        value REAL,
        threshold REAL,
        resulting_allocation_json TEXT
    )
    ''')
    
    cnt = conn.execute("SELECT COUNT(*) FROM portfolio").fetchone()[0]
    if cnt == 0:
        now = datetime.now()
        for a, meta in ASSETS_META.items():
            conn.execute("INSERT INTO portfolio (asset, current_weight, target_weight, last_price, updated_at) VALUES (?, ?, ?, ?, ?)",
                         (a, 0.20, 0.20, meta["start"], now))
            for i in range(20):
                p = meta["start"] * (1 + random.gauss(0, meta["vol"]*0.05))
                conn.execute("INSERT INTO price_history (asset, timestamp, price) VALUES (?, ?, ?)", (a, now, p))
        conn.commit()

init_db()

SHOCK_STATE = {a: {"multiplier": 1.0, "ticks": 0} for a in ASSET_NAMES}

def compute_target_weights(lookback=20, cap=0.30, temp_shock=None):
    vols = {}
    for asset in ASSET_NAMES:
        rows = conn.execute("SELECT price FROM price_history WHERE asset=? ORDER BY timestamp DESC LIMIT ?", (asset, lookback+1)).fetchall()
        prices = [r[0] for r in rows][::-1]
        
        if len(prices) < 2:
            vol = 0.001
        else:
            returns = [prices[i]/prices[i-1] - 1 for i in range(1, len(prices))]
            vol = float(np.std(returns)) if len(returns) > 0 else 0.001
            
        vol = max(vol, 0.0001)
        if temp_shock and temp_shock.get("asset") == asset:
            vol *= temp_shock.get("multiplier", 1.0)
            
        vols[asset] = vol
        
    inv_vols = {a: 1.0/v for a, v in vols.items()}
    total_inv = sum(inv_vols.values())
    weights = {a: v/total_inv for a, v in inv_vols.items()}
    
    while any(w > cap for w in weights.values()):
        excess = 0
        uncapped = []
        for k, w in weights.items():
            if w > cap:
                excess += w - cap
                weights[k] = cap
            elif w < cap:
                uncapped.append(k)
        if not uncapped: break
        for k in uncapped:
            weights[k] += excess / len(uncapped)
            
    return weights

def needs_rebalance(current, target, band=0.05):
    for a in ASSET_NAMES:
        if abs(current.get(a,0) - target.get(a,0)) > band:
            return True
    return False

def check_risk_metrics(current_w, lookback=20, temp_shock=None):
    breached = False
    metrics = {"concentration": {"breached": False, "max_val": 0, "asset": ""},
               "volatility_spike": {"breached": False, "max_val": 0, "asset": ""}}
    alerts = []
    now = datetime.now()
    
    for a, w in current_w.items():
        if w > metrics["concentration"]["max_val"]:
            metrics["concentration"]["max_val"] = w
            metrics["concentration"]["asset"] = a
        if w > 0.30:
            breached = True
            metrics["concentration"]["breached"] = True
            alerts.append((now, "Concentration", w, 0.30))
            
    for asset in ASSET_NAMES:
        rows = conn.execute("SELECT price FROM price_history WHERE asset=? ORDER BY timestamp DESC LIMIT ?", (asset, lookback+1)).fetchall()
        prices = [r[0] for r in rows][::-1]
        if len(prices) >= 6:
            returns = [prices[i]/prices[i-1] - 1 for i in range(1, len(prices))]
            long_vol = float(np.std(returns))
            short_vol = float(np.std(returns[-5:]))
            if temp_shock and temp_shock.get("asset") == asset:
                short_vol *= temp_shock.get("multiplier", 1.0)
            if long_vol > 0.0001:
                ratio = short_vol / long_vol
                if ratio > metrics["volatility_spike"]["max_val"]:
                    metrics["volatility_spike"]["max_val"] = ratio
                    metrics["volatility_spike"]["asset"] = asset
                if ratio > 2.0:
                    breached = True
                    metrics["volatility_spike"]["breached"] = True
                    alerts.append((now, "Volatility Spike", ratio, 2.0))
                    
    return breached, metrics, alerts

class WSManager:
    def __init__(self):
        self.connections = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
    async def broadcast(self, data: dict):
        for c in self.connections:
            try:
                await c.send_json(data)
            except:
                pass
ws_manager = WSManager()

async def market_simulation_loop():
    while True:
        await asyncio.sleep(5)
        now = datetime.now()
        
        for a in ASSET_NAMES:
            if SHOCK_STATE[a]["ticks"] > 0:
                SHOCK_STATE[a]["ticks"] -= 1
            else:
                SHOCK_STATE[a]["multiplier"] = 1.0
                
            meta = ASSETS_META[a]
            vol = meta["vol"] * SHOCK_STATE[a]["multiplier"]
            last_p = conn.execute("SELECT last_price FROM portfolio WHERE asset=?", (a,)).fetchone()[0]
            new_p = last_p * (1 + random.gauss(0, vol * 0.05))
            
            conn.execute("INSERT INTO price_history (asset, timestamp, price) VALUES (?, ?, ?)", (a, now, new_p))
            conn.execute("UPDATE portfolio SET last_price=?, updated_at=? WHERE asset=?", (new_p, now, a))
        conn.commit()
        
        rows = conn.execute("SELECT asset, current_weight FROM portfolio").fetchall()
        current_w = {r[0]: r[1] for r in rows}
        target_w = compute_target_weights()
        
        breached, metrics, new_alerts = check_risk_metrics(current_w)
        should_rebalance = breached or needs_rebalance(current_w, target_w)
        
        if should_rebalance:
            for a, w in target_w.items():
                conn.execute("UPDATE portfolio SET current_weight=?, target_weight=?, updated_at=? WHERE asset=?", (w, w, now, a))
            for alt in new_alerts:
                conn.execute("INSERT INTO alerts (timestamp, metric, value, threshold, resulting_allocation_json) VALUES (?, ?, ?, ?, ?)",
                             (alt[0], alt[1], alt[2], alt[3], json.dumps(target_w)))
            conn.commit()
            if new_alerts:
                alerts_data = [{"timestamp": str(a[0]), "metric": a[1], "value": a[2], "threshold": a[3], "resulting_allocation": target_w} for a in new_alerts]
                await ws_manager.broadcast({"type": "alerts", "data": alerts_data})
                
        # Broadcast portfolio update
        pr_rows = conn.execute("SELECT asset, last_price FROM portfolio").fetchall()
        lp = {r[0]: r[1] for r in pr_rows}
        await ws_manager.broadcast({
            "type": "portfolio_update", 
            "portfolio": {"weights": (target_w if should_rebalance else current_w), "last_prices": lp}
        })

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(market_simulation_loop())

class ShockRequest(BaseModel):
    asset: str
    multiplier: float

@app.get("/api/portfolio")
def get_portfolio():
    rows = conn.execute("SELECT asset, current_weight, last_price FROM portfolio").fetchall()
    return {
        "weights": {r[0]: r[1] for r in rows},
        "last_prices": {r[0]: r[2] for r in rows}
    }

@app.get("/api/risk-status")
def get_risk_status():
    rows = conn.execute("SELECT asset, current_weight FROM portfolio").fetchall()
    current_w = {r[0]: r[1] for r in rows}
    breached, metrics, _ = check_risk_metrics(current_w)
    return {"breached": breached, "metrics": metrics}

@app.get("/api/alerts")
def get_alerts():
    rows = conn.execute("SELECT id, timestamp, metric, value, threshold, resulting_allocation_json FROM alerts ORDER BY id DESC LIMIT 50").fetchall()
    return [{"id": r[0], "timestamp": r[1], "metric": r[2], "value": r[3], "threshold": r[4], "resulting_allocation": json.loads(r[5])} for r in rows]

@app.post("/api/simulate-shock")
def simulate_shock(req: ShockRequest):
    if req.asset in SHOCK_STATE:
        SHOCK_STATE[req.asset]["multiplier"] = req.multiplier
        SHOCK_STATE[req.asset]["ticks"] = 10
        return {"status": "success", "message": f"Shock applied to {req.asset}"}
    raise HTTPException(status_code=400, detail="Invalid asset")

@app.post("/api/scenario")
def api_scenario(req: ShockRequest):
    rows = conn.execute("SELECT asset, current_weight FROM portfolio").fetchall()
    current_w = {r[0]: r[1] for r in rows}
    temp_shock = {"asset": req.asset, "multiplier": req.multiplier}
    breached, metrics, alerts = check_risk_metrics(current_w, temp_shock=temp_shock)
    target_w = compute_target_weights(temp_shock=temp_shock)
    return {
        "hypothetical_weights": target_w,
        "risk_breached": breached,
        "risk_metrics": metrics,
        "alerts_generated": len(alerts)
    }

@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)



app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000)

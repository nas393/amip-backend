from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_DURATION = 600

cache = {
    "fx": None,
    "fx_prev": None,
    "commodities": None,
    "timestamp": 0
}

# ------------------ FX ------------------

def fetch_usd_aoa():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        r = requests.get(url, timeout=10).json()

        if r.get("result") != "success":
            return None

        return round(r["rates"].get("AOA"), 2)

    except:
        return None


# ------------------ Commodities ------------------
# Using free stooq.com API (no key)

def fetch_commodity(symbol):
    try:
        url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
        r = requests.get(url, timeout=10).text.split(",")
        return float(r[6])
    except:
        return None


def fetch_commodities():
    return {
        "Wheat": fetch_commodity("zw.f"),
        "Sugar": fetch_commodity("sb.f"),
        "Rice": fetch_commodity("zr.f"),
        "Maize": fetch_commodity("zc.f"),
        "Flour": fetch_commodity("zw.f"),  # proxy wheat
        "Margarine": None  # no direct public feed, placeholder
    }


# ------------------ Risk Model ------------------

def calculate_risk(fx, fx_prev, commodities):
    fx_volatility = 0
    if fx_prev:
        fx_volatility = abs((fx - fx_prev) / fx_prev) * 100

    commodity_pressure = 0
    valid_prices = [v for v in commodities.values() if v]
    if valid_prices:
        commodity_pressure = sum(valid_prices) / len(valid_prices)

    risk_score = (
        fx_volatility * 3 +
        (commodity_pressure / 100) * 20
    )

    return round(min(risk_score, 100), 2)


# ------------------ API ENDPOINTS ------------------

@app.get("/")
def home():
    return {"message": "Intelligence Engine Active"}


@app.get("/fx")
def fx():
    current_time = time.time()

    if cache["fx"] and current_time - cache["timestamp"] < CACHE_DURATION:
        return {"USD/AOA": cache["fx"], "cached": True}

    fx_value = fetch_usd_aoa()

    if fx_value:
        cache["fx_prev"] = cache["fx"]
        cache["fx"] = fx_value
        cache["timestamp"] = current_time
        return {"USD/AOA": fx_value, "cached": False}

    return {"error": "FX unavailable"}


@app.get("/commodities")
def commodities():
    current_time = time.time()

    if cache["commodities"] and current_time - cache["timestamp"] < CACHE_DURATION:
        return cache["commodities"]

    data = fetch_commodities()

    if data:
        cache["commodities"] = data
        cache["timestamp"] = current_time
        return data

    return {"error": "Commodity data unavailable"}


@app.get("/risk")
def risk():
    if not cache["fx"]:
        return {"risk": "insufficient data"}

    commodities_data = cache["commodities"] or {}
    risk_score = calculate_risk(
        cache["fx"],
        cache["fx_prev"],
        commodities_data
    )

    return {"Angola Risk Score": risk_score}

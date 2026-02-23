from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import random

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


# ------------------ Stable Commodity Model ------------------

def fetch_commodities():
    # Temporary realistic model
    # Replace later with live feeds
    return {
        "Wheat": 250 + random.uniform(-5, 5),
        "Sugar": 22 + random.uniform(-1, 1),
        "Rice": 310 + random.uniform(-5, 5),
        "Maize": 210 + random.uniform(-4, 4),
        "Flour": 260 + random.uniform(-5, 5),
        "Margarine": 180 + random.uniform(-3, 3),
    }


# ------------------ Risk Model ------------------

def calculate_risk(fx, fx_prev, commodities):
    fx_volatility = 0
    if fx_prev:
        fx_volatility = abs((fx - fx_prev) / fx_prev) * 100

    commodity_pressure = sum(commodities.values()) / len(commodities)

    risk_score = (
        fx_volatility * 4 +
        (commodity_pressure / 10)
    )

    return round(min(risk_score, 100), 2)


# ------------------ API ------------------

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
    cache["commodities"] = data
    cache["timestamp"] = current_time

    return data


@app.get("/risk")
def risk():
    if not cache["fx"]:
        return {"risk": "insufficient data"}

    commodities_data = cache["commodities"] or fetch_commodities()

    risk_score = calculate_risk(
        cache["fx"],
        cache["fx_prev"],
        commodities_data
    )

    return {"Angola Risk Score": risk_score}

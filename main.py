from fastapi import FastAPI
import requests
import os
import time

app = FastAPI()

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")

# ---- CACHE SETTINGS ----
CACHE_DURATION = 600  # 10 minutes
fx_cache = {
    "data": None,
    "timestamp": 0
}


@app.get("/")
def home():
    return {"message": "Angola Market Intelligence API is running"}


@app.get("/debug")
def debug():
    return {
        "api_key_loaded": ALPHA_KEY is not None,
        "cache_active": fx_cache["data"] is not None
    }


def fetch_fx_from_api(from_currency="USD"):
    url = (
        "https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={from_currency}"
        f"&to_currency=AOA"
        f"&apikey={ALPHA_KEY}"
    )

    response = requests.get(url, timeout=10)
    data = response.json()

    if "Realtime Currency Exchange Rate" not in data:
        return None

    return float(
        data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
    )


def get_cached_fx():
    current_time = time.time()

    # If cache exists and not expired
    if (
        fx_cache["data"] is not None and
        current_time - fx_cache["timestamp"] < CACHE_DURATION
    ):
        return fx_cache["data"]

    # Otherwise fetch fresh data
    usd = fetch_fx_from_api("USD")
    eur = fetch_fx_from_api("EUR")

    if usd and eur:
        fx_cache["data"] = {
            "USD/AOA": usd,
            "EUR/AOA": eur,
            "cached": False
        }
        fx_cache["timestamp"] = current_time
        return fx_cache["data"]

    # If API fails but cache exists, serve old cache
    if fx_cache["data"]:
        return {
            **fx_cache["data"],
            "cached": True
        }

    return {"error": "Unable to fetch FX data"}


@app.get("/fx")
def fx():
    return get_cached_fx()


@app.get("/risk")
def risk():
    fx_vol = 50
    commodity_vol = 40
    news_score = 30
    weather_score = 20

    risk_score = (
        fx_vol * 0.30 +
        commodity_vol * 0.30 +
        news_score * 0.25 +
        weather_score * 0.15
    )

    return {"Angola Risk Score": round(risk_score, 2)}

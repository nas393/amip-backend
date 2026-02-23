from fastapi import FastAPI
import requests
import time

app = FastAPI()

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
        "cache_active": fx_cache["data"] is not None
    }


def fetch_fx_from_api():
    url = "https://api.exchangerate.host/latest?base=USD&symbols=AOA"
    response = requests.get(url, timeout=10)
    data = response.json()

    if "rates" not in data or "AOA" not in data["rates"]:
        return None

    usd_to_aoa = data["rates"]["AOA"]

    # Now fetch EUR
    url_eur = "https://api.exchangerate.host/latest?base=EUR&symbols=AOA"
    response_eur = requests.get(url_eur, timeout=10)
    data_eur = response_eur.json()

    if "rates" not in data_eur or "AOA" not in data_eur["rates"]:
        return None

    eur_to_aoa = data_eur["rates"]["AOA"]

    return {
        "USD/AOA": round(usd_to_aoa, 2),
        "EUR/AOA": round(eur_to_aoa, 2)
    }


def get_cached_fx():
    current_time = time.time()

    if (
        fx_cache["data"] is not None and
        current_time - fx_cache["timestamp"] < CACHE_DURATION
    ):
        return {
            **fx_cache["data"],
            "cached": True
        }

    fresh_data = fetch_fx_from_api()

    if fresh_data:
        fx_cache["data"] = fresh_data
        fx_cache["timestamp"] = current_time
        return {
            **fresh_data,
            "cached": False
        }

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

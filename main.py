from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

app = FastAPI()

# ---- ENABLE CORS (Allows Vercel frontend to call this API) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For now allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- CACHE SETTINGS ----
CACHE_DURATION = 600  # 10 minutes
fx_cache = {
    "rate": None,
    "timestamp": 0
}


@app.get("/")
def home():
    return {"message": "Angola Market Intelligence API is running"}


@app.get("/debug")
def debug():
    return {
        "cache_active": fx_cache["rate"] is not None
    }


def fetch_usd_aoa():
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("result") != "success":
            return None

        usd_to_aoa = data["rates"].get("AOA")

        if not usd_to_aoa:
            return None

        return round(usd_to_aoa, 2)

    except Exception:
        return None


def get_cached_fx():
    current_time = time.time()

    # If cache valid, return it
    if (
        fx_cache["rate"] is not None and
        current_time - fx_cache["timestamp"] < CACHE_DURATION
    ):
        return {
            "USD/AOA": fx_cache["rate"],
            "cached": True
        }

    # Otherwise fetch fresh data
    fresh_rate = fetch_usd_aoa()

    if fresh_rate:
        fx_cache["rate"] = fresh_rate
        fx_cache["timestamp"] = current_time
        return {
            "USD/AOA": fresh_rate,
            "cached": False
        }

    # If API fails but we have old cache, serve old cache
    if fx_cache["rate"]:
        return {
            "USD/AOA": fx_cache["rate"],
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

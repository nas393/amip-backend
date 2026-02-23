from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time
import random
import xml.etree.ElementTree as ET

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
    "regulations": None,
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


# ------------------ Commodity Model ------------------

def fetch_commodities():
    return {
        "Wheat": 250 + random.uniform(-5, 5),
        "Sugar": 22 + random.uniform(-1, 1),
        "Rice": 310 + random.uniform(-5, 5),
        "Maize": 210 + random.uniform(-4, 4),
        "Flour": 260 + random.uniform(-5, 5),
        "Margarine": 180 + random.uniform(-3, 3),
    }


# ------------------ Regulation Intelligence ------------------

KEYWORDS = [
    "import",
    "tariff",
    "tax",
    "regulation",
    "customs",
    "currency",
    "inflation",
    "subsidy",
    "food",
    "price"
]

def fetch_regulations():
    try:
        # Angola News RSS (Google aggregated)
        url = "https://news.google.com/rss/search?q=Angola+economy+law+regulation"
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)

        items = root.findall(".//item")[:5]

        headlines = []
        risk_score = 0

        for item in items:
            title = item.find("title").text.lower()

            keyword_hit = any(k in title for k in KEYWORDS)

            if keyword_hit:
                risk_score += 10

            headlines.append({
                "title": item.find("title").text,
                "risk_flag": keyword_hit
            })

        return {
            "headlines": headlines,
            "regulation_risk": min(risk_score, 100)
        }

    except:
        return {
            "headlines": [],
            "regulation_risk": 0
        }


# ------------------ Risk Model ------------------

def calculate_risk(fx, fx_prev, commodities, regulation_risk):
    fx_volatility = 0
    if fx_prev:
        fx_volatility = abs((fx - fx_prev) / fx_prev) * 100

    commodity_pressure = sum(commodities.values()) / len(commodities)

    total_risk = (
        fx_volatility * 4 +
        (commodity_pressure / 10) +
        regulation_risk
    )

    return round(min(total_risk, 100), 2)


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
    data = fetch_commodities()
    cache["commodities"] = data
    return data


@app.get("/regulations")
def regulations():
    data = fetch_regulations()
    cache["regulations"] = data
    return data


@app.get("/risk")
def risk():
    if not cache["fx"]:
        return {"risk": "insufficient data"}

    commodities_data = cache["commodities"] or fetch_commodities()
    regulation_data = cache["regulations"] or fetch_regulations()

    risk_score = calculate_risk(
        cache["fx"],
        cache["fx_prev"],
        commodities_data,
        regulation_data["regulation_risk"]
    )

    return {
        "Angola Risk Score": risk_score,
        "Regulation Risk": regulation_data["regulation_risk"]
    }

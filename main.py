from fastapi import FastAPI
import requests
import os

app = FastAPI()

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")


@app.get("/")
def home():
    return {"message": "Angola Market Intelligence API is running"}


@app.get("/debug")
def debug():
    return {
        "api_key_loaded": ALPHA_KEY is not None,
        "api_key_preview": ALPHA_KEY[:4] + "..." if ALPHA_KEY else None
    }


def fetch_fx(from_currency="USD"):
    if not ALPHA_KEY:
        return {"error": "API key not loaded"}

    url = (
        "https://www.alphavantage.co/query"
        f"?function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={from_currency}"
        f"&to_currency=AOA"
        f"&apikey={ALPHA_KEY}"
    )

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        # If structure is not what we expect, return full response for diagnosis
        if "Realtime Currency Exchange Rate" not in data:
            return {
                "error": "Unexpected API response",
                "raw_response": data
            }

        rate = float(
            data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
        )

        return {"rate": rate}

    except Exception as e:
        return {"error": str(e)}


@app.get("/fx")
def fx():
    usd = fetch_fx("USD")
    eur = fetch_fx("EUR")

    return {
        "USD/AOA": usd,
        "EUR/AOA": eur
    }


@app.get("/risk")
def risk():
    # Temporary simulated inputs
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

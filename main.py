from fastapi import FastAPI
import requests
import os

app = FastAPI()

ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")

def get_fx_rate(from_currency="USD"):
    url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={from_currency}&to_currency=AOA&apikey={ALPHA_KEY}"
    r = requests.get(url)
    data = r.json()
    try:
        return float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
    except:
        return None

@app.get("/")
def home():
    return {"message": "Angola Market Intelligence API is running"}

@app.get("/fx")
def fx():
    usd = get_fx_rate("USD")
    eur = get_fx_rate("EUR")
    return {
        "USD/AOA": usd,
        "EUR/AOA": eur
    }

@app.get("/risk")
def risk():
    # Temporary static logic
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

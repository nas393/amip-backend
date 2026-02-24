from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import requests
import sqlite3
import time
import hashlib
import secrets
import xml.etree.ElementTree as ET
from datetime import datetime

app = FastAPI()

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("intelligence.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password_hash TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fx_history (
    timestamp TEXT,
    value REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS commodity_history (
    timestamp TEXT,
    wheat REAL,
    sugar REAL,
    rice REAL,
    maize REAL,
    flour REAL,
    margarine REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS regulation_history (
    timestamp TEXT,
    risk_score INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS risk_history (
    timestamp TEXT,
    fx_risk REAL,
    commodity_risk REAL,
    regulation_risk REAL,
    total_risk REAL
)
""")

conn.commit()

# ---------------- INITIAL USERS ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?)",
                       (username, hash_password(password)))
        conn.commit()
    except:
        pass

create_user("Nassim", "101112")
create_user("user", "qwerty1")

# ---------------- AUTH ----------------
tokens = {}

@app.post("/login")
def login(data: dict):
    username = data.get("username")
    password = data.get("password")

    cursor.execute("SELECT password_hash FROM users WHERE username=?",
                   (username,))
    result = cursor.fetchone()

    if not result or result[0] != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(16)
    tokens[token] = username
    return {"token": token}

def authenticate(authorization: str = Header(None)):
    if not authorization or authorization not in tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ---------------- FX ----------------
def fetch_usd_aoa():
    url = "https://open.er-api.com/v6/latest/USD"
    r = requests.get(url, timeout=10).json()
    return r["rates"]["AOA"]

# ---------------- COMMODITIES ----------------
import random

def fetch_commodities():
    return {
        "wheat": 250 + random.uniform(-5, 5),
        "sugar": 22 + random.uniform(-1, 1),
        "rice": 310 + random.uniform(-5, 5),
        "maize": 210 + random.uniform(-4, 4),
        "flour": 260 + random.uniform(-5, 5),
        "margarine": 180 + random.uniform(-3, 3),
    }

# ---------------- REGULATIONS ----------------
KEYWORDS = ["import", "tariff", "tax", "customs", "ban", "regulation"]

def fetch_regulation_risk():
    url = "https://news.google.com/rss/search?q=Angola+law+economy"
    response = requests.get(url, timeout=10)
    root = ET.fromstring(response.content)
    items = root.findall(".//item")[:5]

    risk_score = 0

    for item in items:
        title = item.find("title").text.lower()
        if any(k in title for k in KEYWORDS):
            risk_score += 15

    return min(risk_score, 100)

# ---------------- RISK ENGINE ----------------
def calculate_risk(fx_value, commodities, regulation_risk):
    fx_risk = abs(fx_value - 900) / 10
    commodity_risk = sum(commodities.values()) / 50
    total = fx_risk + commodity_risk + regulation_risk
    return fx_risk, commodity_risk, regulation_risk, min(total, 100)

# ---------------- API ENDPOINTS ----------------
@app.get("/fx")
def fx(user=Depends(authenticate)):
    value = fetch_usd_aoa()
    timestamp = datetime.utcnow().isoformat()

    cursor.execute("INSERT INTO fx_history VALUES (?, ?)",
                   (timestamp, value))
    conn.commit()

    return {"USD/AOA": round(value, 2)}

@app.get("/commodities")
def commodities(user=Depends(authenticate)):
    data = fetch_commodities()
    timestamp = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO commodity_history VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        data["wheat"],
        data["sugar"],
        data["rice"],
        data["maize"],
        data["flour"],
        data["margarine"],
    ))
    conn.commit()

    return data

@app.get("/regulations")
def regulations(user=Depends(authenticate)):
    risk_score = fetch_regulation_risk()
    timestamp = datetime.utcnow().isoformat()

    cursor.execute("INSERT INTO regulation_history VALUES (?, ?)",
                   (timestamp, risk_score))
    conn.commit()

    return {"regulation_risk": risk_score}

@app.get("/risk")
def risk(user=Depends(authenticate)):
    fx_value = fetch_usd_aoa()
    commodities = fetch_commodities()
    regulation_risk = fetch_regulation_risk()

    fx_risk, commodity_risk, reg_risk, total = calculate_risk(
        fx_value, commodities, regulation_risk
    )

    timestamp = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO risk_history VALUES (?, ?, ?, ?, ?)
    """, (
        timestamp,
        fx_risk,
        commodity_risk,
        reg_risk,
        total
    ))
    conn.commit()

    return {
        "fx_risk": round(fx_risk, 2),
        "commodity_risk": round(commodity_risk, 2),
        "regulation_risk": reg_risk,
        "total_risk": round(total, 2)
    }

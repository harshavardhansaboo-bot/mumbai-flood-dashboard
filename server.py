from flask import Flask, jsonify, send_file
from flask_cors import CORS
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

API_KEY = "043512ab78328aaab96c4457fe65b060"
HISTORY_FILE = "history.json"

WARDS = {
    "A":   (18.9322, 72.8264),
    "B":   (18.9543, 72.8196),
    "C":   (18.9647, 72.8258),
    "D":   (18.9553, 72.8074),
    "E":   (18.9635, 72.8362),
    "F/S": (19.0176, 72.8490),
    "F/N": (19.0761, 72.8553),
    "G/S": (19.0178, 72.8397),
    "G/N": (19.0590, 72.8370),
    "H/E": (19.0544, 72.8402),
    "H/W": (19.0607, 72.8355),
    "K/E": (19.1136, 72.8697),
    "K/W": (19.1136, 72.8364),
    "L":   (19.1726, 72.9325),
    "M/E": (19.0437, 72.9125),
    "M/W": (19.0437, 72.8574),
    "N":   (19.1095, 72.9007),
    "P/N": (19.1628, 72.8494),
    "P/S": (19.1215, 72.8544),
    "R/C": (19.1543, 72.9032),
    "R/N": (19.2437, 72.8561),
    "R/S": (19.1976, 72.9625),
    "S":   (19.0728, 72.9009),
    "T":   (19.2183, 72.9781),
}

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {ward: [] for ward in WARDS}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def prune_history(history):
    cutoff = datetime.utcnow() - timedelta(hours=24)
    for ward in history:
        history[ward] = [
            entry for entry in history[ward]
            if datetime.fromisoformat(entry["time"]) > cutoff
        ]
    return history

def get_rainfall(lat, lon):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        res = requests.get(url, timeout=10)
        data = res.json()
        return data.get("rain", {}).get("1h", 0)
    except:
        return 0

def rainfall_to_risk(mm):
    if mm > 20:   return "high"
    elif mm > 5:  return "medium"
    else:         return "low"

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/BMC_admin_wards.geojson")
def geojson():
    return send_file("BMC_admin_wards.geojson")

@app.route("/risk")
def risk():
    history = load_history()
    history = prune_history(history)
    result = {}
    now = datetime.utcnow().isoformat()

    for ward, (lat, lon) in WARDS.items():
        mm = get_rainfall(lat, lon)
        result[ward] = {
            "risk": rainfall_to_risk(mm),
            "rainfall_mm": mm
        }
        if ward not in history:
            history[ward] = []
        history[ward].append({ "time": now, "mm": mm })

    save_history(history)
    return jsonify(result)

@app.route("/history/<ward>")
def ward_history(ward):
    ward = ward.replace("_", "/")
    history = load_history()
    return jsonify(history.get(ward, []))

if __name__ == "__main__":
    app.run(port=5001, debug=True)
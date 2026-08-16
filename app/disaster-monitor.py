import json
import time
import csv
import os
from datetime import datetime, timezone

import requests

LATITUDE = 28.6139   
LONGITUDE = 77.2090
t = 60
log  = "old_data.csv"

rain_danger= 64.5         
max_river = 1500  
max_aqi = 300
max_wind = 50


def get_data():
    weather = requests.get("https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": LATITUDE, "longitude": LONGITUDE,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
            "timezone": "auto",
        },
        timeout=15,
    ).json()["current"]

    air_quality = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality",
        params={"latitude": LATITUDE, "longitude": LONGITUDE, "current": "us_aqi"},
        timeout=15,
    ).json()["current"]

    flood = requests.get("https://flood-api.open-meteo.com/v1/flood",
        params={"latitude": LATITUDE, "longitude": LONGITUDE, "daily": "river_discharge", "past_days": 1},
        timeout=15,
    ).json()["daily"]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rainfall_mm": weather.get("precipitation", 0.0),
        "river_discharge_m3s": flood["river_discharge"][-1],
        "air_quality_index": air_quality.get("us_aqi", 0),
        "temperature_c": weather.get("temperature_2m", 0.0),
        "humidity_pct": weather.get("relative_humidity_2m", 0.0),
        "wind_speed_kmph": round(weather.get("wind_speed_10m", 0.0) * 3.6, 1),
    }


def check_thresholds(data):
    issues = []
    if data["rainfall_mm"] > rain_danger:
        issues.append("Heavy rainfall")

    if data["river_discharge_m3s"] > max_river:
        issues.append("flood alert")

    if data["air_quality_index"] > max_aqi:
        issues.append("Dangerous air quality")

    if data["wind_speed_kmph"] > max_wind:
        issues.append("High wind alert")

    return issues


while True:
    try:
        data = get_data()
        print(f"[READING] {json.dumps(data)}")

        breaches = check_thresholds(data)
        if breaches:
            print("Disaster detected")
            for b in breaches:
                print(b)
            print("[EMAIL ALERT] Would notify: officer@example.gov, control-room@example.gov")
            print("[SMS ALERT] Would notify registered phone numbers")
        else:
            print("no disaster found")
        file_exists = os.path.isfile(log)
        with open(log, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as exc:
        print(f"{exc}")

    time.sleep(t)



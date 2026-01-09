import pandas as pd
import requests
from datetime import datetime
import sqlite3
import random
import json
import os
from templates.flask_app import app

LOG_PATH = "log.txt"

def write_log(info):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {info}\n")

defaults = {
    "lat": 54.323,
    "lon": 10.122,
    "start_date": "2026-01-02",
    "end_date": "2026-01-06"
}

def get_date_input(tvoje):
    while True:
        ucet = input(tvoje)  
        try:
            date_obj = datetime.strptime(ucet, "%d.%m.%Y")
            return date_obj.strftime("%Y-%m-%d")  
        except ValueError:
            print("Neplatný formát! Zadej datum ve tvaru DD.MM.RRRR, jen čísla.")

def get_lat_input(moje):
    hodnota = input(moje).lower().strip()
    if hodnota == "nahodne":
        return random.uniform(-90, 90)
    try:
        return float(hodnota)
    except ValueError:
        print("Špatný formát! Zkus to znovu.")
        return get_lat_input(moje)
   
write_log("Program funguje")

print("Vyber možnost:")
print("1 = Použít defaultní hodnoty")
print("2 = Ručně zadat vše")
print("3 = data z json")

volba = input("Tvoje volba: ").strip()

match volba:
    case "1":
        config = defaults.copy()
        print("Používám defaultní hodnoty.")
        write_log("Používám defaultní hodnoty")

    case "2":
        print("Ručně zadáváš hodnoty:")
        config = {
            "start_date": get_date_input("Zadej start datum (DD.MM.RRRR): "),
            "end_date": get_date_input("Zadej end datum (DD.MM.RRRR): "),
            "lat": get_lat_input("Zadej LAT nebo 'nahodne': "),
            "lon": get_lat_input("Zadej LON nebo 'nahodne': ")
        }
        write_log(f"pouzivas radnom info{config}")



    case "3":
        with open("vystup_daily.json", "r", encoding="utf-8") as f:
            dataabc = json.load(f)
            config = defaults.copy()
            for cfg in dataabc:
                config["lat"] = cfg["lat"]
                config["lon"] = cfg["lon"]
                config["start_date"] = cfg["start_date"]  
                config["end_date"] = cfg["end_date"]
    case _:
        print("spatne hodnoty si zadal")
        write_log("tady si zadal neco spatne")
        exit()
        
       

url = (
    "https://marine-api.open-meteo.com/v1/marine"
    f"?latitude={config['lat']}"
    f"&longitude={config['lon']}"
    f"&hourly=wave_height,sea_surface_temperature,wave_direction"
    f"&start_date={config['start_date']}"
    f"&end_date={config['end_date']}"
)


response = requests.get(url)
print("Status code:", response.status_code)
data = response.json()
print(data)
write_log("api funguje v poradku")

if "hourly" not in data:
    print("Data nebyla načtena správně:", data)
    exit()


conn = sqlite3.connect("weather.db")
cur = conn.cursor()


times = data["hourly"].get("time", [])
waves = data["hourly"].get("wave_height", [])
temps = data["hourly"].get("sea_surface_temperature", [])
dirs = data["hourly"].get("wave_direction", [])

cur.execute("""
CREATE TABLE IF NOT EXISTS marine_weather (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,
    wave_height REAL,
    sea_temp REAL,
    wave_direction REAL
)
""")

# cur.execute("DELETE FROM marine_weather")

for t, w, temp, d in zip(times, waves, temps, dirs):
    cur.execute(
        "INSERT INTO marine_weather (time, wave_height, sea_temp, wave_direction) VALUES (?, ?, ?, ?)",
        (t, w, temp, d)
    )

conn.commit()
conn.close()
print("Data byla úspěšně uložena do")


# download_weather.py
import requests
import pandas as pd
from datetime import datetime, timedelta

def download_weather():
    lat, lon = 58.966, 57.683
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "precipitation"],
        "forecast_days": 3,
        "timezone": "Europe/Moscow"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        hourly = data['hourly']
        df = pd.DataFrame({
            'ds': pd.to_datetime(hourly['time']),
            'temp_air': hourly['temperature_2m'],
            'precip': hourly['precipitation']
        })
        df.to_csv('weather_historical.csv', index=False)
        print(f"Скачано {len(df)} записей погоды, сохранено в weather_historical.csv")
    except Exception as e:
        print(f"Ошибка скачивания: {e}")

if __name__ == "__main__":
    download_weather()
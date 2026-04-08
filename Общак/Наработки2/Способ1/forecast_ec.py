#!/usr/bin/env python3
"""
Прогноз EC с помощью Prophet + реальные метеоданные (Open-Meteo)
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
import requests
import warnings
warnings.filterwarnings('ignore')

class ECProphet:
    def __init__(self, scenario='moderate'):
        self.model = None
        self.scenario = scenario
        self.factor = {'moderate':1.0, 'pessimistic':1.2, 'optimistic':0.9}[scenario]

    def load_ec_data(self, csv_path):
        df = pd.read_csv(csv_path)
        df['ds'] = pd.to_datetime(df['timestamp'])
        df['y'] = df['ec_microsiemens']
        df = df[['ds','y']].dropna()
        print(f"📊 Загружено {len(df)} записей EC: {df['y'].min():.0f}–{df['y'].max():.0f} мкСм/см")
        return df

    def get_weather(self, lat=58.966, lon=57.683, hours=72):
        """Реальный прогноз погоды с Open-Meteo"""
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat, "longitude": lon,
                "hourly": ["temperature_2m", "precipitation"],
                "forecast_days": 3, "timezone": "Europe/Moscow"
            }
            r = requests.get(url, params=params, timeout=8)
            r.raise_for_status()
            data = r.json()
            hourly = data['hourly']
            df_weather = pd.DataFrame({
                'ds': pd.to_datetime(hourly['time']),
                'temp_air': hourly['temperature_2m'],
                'precip': hourly['precipitation']
            }).head(hours)
            print("🌦️ Реальный прогноз погоды загружен")
            return df_weather
        except Exception as e:
            print(f"⚠️ Ошибка погоды: {e}. Использую средние климатические значения.")
            return None

    def train(self, hist_df, weather_df=None):
        self.model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.2,
            seasonality_prior_scale=10.0,
            interval_width=0.95
        )
        self.model.add_regressor('temp_air')
        self.model.add_regressor('precip')
        train = hist_df.copy()
        if weather_df is not None:
            merged = pd.merge(train, weather_df, on='ds', how='left')
            train['temp_air'] = merged['temp_air'].fillna(5.0)
            train['precip'] = merged['precip'].fillna(1.0)
        else:
            # fallback – средние апрельские значения
            train['temp_air'] = 5.0
            train['precip'] = 2.0
        self.model.fit(train)
        print("✅ Модель Prophet обучена")

    def predict(self, hours=72, weather_df=None):
        last = self.model.history['ds'].max()
        future = pd.DataFrame({'ds': pd.date_range(last + timedelta(hours=1), periods=hours, freq='h')})
        if weather_df is not None:
            merged = pd.merge(future, weather_df, on='ds', how='left')
            future['temp_air'] = merged['temp_air'].fillna(5.0)
            future['precip'] = merged['precip'].fillna(1.0)
        else:
            future['temp_air'] = 5.0
            future['precip'] = 2.0
        fcst = self.model.predict(future)
        result = pd.DataFrame({
            'timestamp': fcst['ds'],
            'ec_microsiemens': fcst['yhat'] * self.factor,
            'ec_lower': fcst['yhat_lower'] * self.factor,
            'ec_upper': fcst['yhat_upper'] * self.factor,
            'temp_air_c': future['temp_air'],
            'precip_mm': future['precip']
        })
        return result

def main():
    import matplotlib.pyplot as plt
    model = ECProphet(scenario='pessimistic')
    hist = model.load_ec_data('kiyazevo_iot_realistic.csv')
    weather = model.get_weather()
    model.train(hist, weather)
    forecast = model.predict(72, weather)
    forecast.to_csv('ec_forecast_72h.csv', index=False)
    print("💾 Прогноз EC сохранён в ec_forecast_72h.csv")

    plt.figure(figsize=(12,5))
    plt.plot(forecast['timestamp'], forecast['ec_microsiemens'], 'r-', label='Прогноз EC')
    plt.fill_between(forecast['timestamp'], forecast['ec_lower'], forecast['ec_upper'], alpha=0.2, color='red')
    plt.axhline(4000, color='orange', linestyle='--', label='Опасный порог')
    plt.title('Прогноз электропроводности (EC) на 72 часа\nр. Косьва, пост Кияево')
    plt.ylabel('мкСм/см')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('ec_forecast_plot.png', dpi=150)
    plt.show()

if __name__ == "__main__":
    main()
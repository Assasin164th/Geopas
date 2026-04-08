#!/usr/bin/env python3
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime, timedelta
import warnings
import requests
warnings.filterwarnings('ignore')

class WaterECForecastModel:
    def __init__(self, climate_scenario='moderate'):
        self.model = None
        self.climate_scenario = climate_scenario
        self.climate_factors = {
            'moderate': 1.0,
            'pessimistic': 1.2,
            'optimistic': 0.9
        }

    def load_historical_ec(self, csv_path):
        df = pd.read_csv(csv_path)
        time_col = 'timestamp' if 'timestamp' in df.columns else df.columns[0]
        ec_col = 'ec_microsiemens' if 'ec_microsiemens' in df.columns else df.columns[1]
        df_prophet = pd.DataFrame()
        df_prophet['ds'] = pd.to_datetime(df[time_col])
        df_prophet['y'] = pd.to_numeric(df[ec_col], errors='coerce')
        df_prophet = df_prophet.dropna()
        print(f"📊 Загружено {len(df_prophet)} записей EC: {df_prophet['y'].min():.0f} - {df_prophet['y'].max():.0f} мкСм/см")
        return df_prophet

    def get_real_weather_forecast(self, lat=58.966, lon=57.683, hours=72):
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat, "longitude": lon,
                "hourly": ["temperature_2m", "precipitation"],
                "forecast_days": 3, "timezone": "Europe/Moscow"
            }
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            hourly = data['hourly']
            df = pd.DataFrame({
                'ds': pd.to_datetime(hourly['time']),
                'temp_air': hourly['temperature_2m'],
                'precip': hourly['precipitation']
            }).head(hours)
            print("🌦️ Реальный прогноз погоды загружен")
            return df
        except Exception as e:
            print(f"⚠️ Реальная погода не загружена: {e}. Используем улучшенную стохастическую модель.")
            return self._generate_realistic_weather(lat, lon, hours)

    def _generate_realistic_weather(self, lat, lon, hours):
        """Генерирует более реалистичную погоду с трендом и шумом, без идеальной синусоиды."""
        start = datetime.now()
        dates = [start + timedelta(hours=i) for i in range(hours)]
        # Базовые сезонные значения для апреля
        base_temp = 5.0  # средняя температура апреля
        base_precip = 1.5  # мм/час
        
        temps = []
        precip = []
        for i, d in enumerate(dates):
            # Суточные колебания (более резкие)
            diurnal = 6 * np.sin(2 * np.pi * (d.hour - 14) / 24)
            # Случайные колебания (авторегрессия)
            if i == 0:
                noise_temp = np.random.normal(0, 1)
            else:
                noise_temp = 0.7 * temps[-1] + np.random.normal(0, 1.5)
            # Тренд на потепление в апреле
            trend = 0.05 * i / 24
            temp = base_temp + diurnal + noise_temp + trend
            temps.append(temp)
            
            # Осадки: логнормальное распределение с редкими сильными осадками
            if np.random.random() < 0.3:
                p = np.random.lognormal(0, 1.2)
            else:
                p = 0
            precip.append(min(p, 8))
        
        return pd.DataFrame({'ds': dates, 'temp_air': temps, 'precip': precip})

    def train(self, df_hist, weather_df=None):
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=True,
            changepoint_prior_scale=0.2,
            interval_width=0.95
        )
        self.model.add_regressor('temp_air')
        self.model.add_regressor('precip')
        
        train_df = df_hist.copy()
        if weather_df is not None:
            merged = pd.merge(train_df, weather_df, on='ds', how='left')
            train_df['temp_air'] = merged['temp_air'].fillna(0)
            train_df['precip'] = merged['precip'].fillna(0)
        else:
            # fallback
            train_df['temp_air'] = 5.0
            train_df['precip'] = 1.0
        
        self.model.fit(train_df)
        print("✅ Модель Prophet обучена")
        return self.model

    def predict(self, hours=72, weather_df=None):
        if self.model is None:
            raise ValueError("Модель не обучена")
        last_date = self.model.history['ds'].max()
        future_dates = pd.date_range(start=last_date + timedelta(hours=1), periods=hours, freq='h')
        future = pd.DataFrame({'ds': future_dates})
        if weather_df is not None:
            merged = pd.merge(future, weather_df, on='ds', how='left')
            future['temp_air'] = merged['temp_air'].fillna(0)
            future['precip'] = merged['precip'].fillna(0)
        else:
            future['temp_air'] = 5.0
            future['precip'] = 1.0
        
        forecast = self.model.predict(future)
        results = []
        for i, row in forecast.iterrows():
            results.append({
                'timestamp': row['ds'],
                'ec_microsiemens': row['yhat'],
                'ec_lower': row['yhat_lower'],
                'ec_upper': row['yhat_upper'],
                'temp_air_c': future.loc[i, 'temp_air'],
                'precip_mm': future.loc[i, 'precip']
            })
        return pd.DataFrame(results)

    def apply_climate_correction(self, forecast_df):
        factor = self.climate_factors[self.climate_scenario]
        forecast_df['ec_microsiemens'] *= factor
        forecast_df['ec_lower'] *= factor
        forecast_df['ec_upper'] *= factor
        print(f"🌡️ Коррекция EC: {self.climate_scenario} (x{factor})")
        return forecast_df

def main():
    import matplotlib.pyplot as plt
    model = WaterECForecastModel('pessimistic')
    hist = model.load_historical_ec('kiyazevo_iot_realistic.csv')
    weather = model.get_real_weather_forecast()
    model.train(hist, weather)
    forecast = model.predict(72, weather)
    forecast = model.apply_climate_correction(forecast)
    forecast.to_csv('ec_forecast_72h.csv', index=False)
    
    plt.figure(figsize=(12,6))
    plt.plot(forecast['timestamp'], forecast['ec_microsiemens'], 'r-', label='Прогноз EC')
    plt.fill_between(forecast['timestamp'], forecast['ec_lower'], forecast['ec_upper'], alpha=0.2, color='red')
    plt.axhline(y=4000, color='orange', linestyle='--', label='Опасный порог (4000)')
    plt.xlabel('Дата')
    plt.ylabel('EC (мкСм/см)')
    plt.title('Прогноз электропроводности воды (EC) на 72 часа\nр. Косьва, пост Кияево')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('ec_forecast_plot.png', dpi=150)
    plt.show()
    print("💾 Сохранено: ec_forecast_72h.csv, ec_forecast_plot.png")

if __name__ == "__main__":
    main()
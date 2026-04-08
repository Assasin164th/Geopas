#!/usr/bin/env python3
"""
forecast_model.py
Прогнозирование уровня воды на 72 часа.
Сохраняет water_forecast_72h.csv.
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

# Загрузка и масштабирование
df_raw = pd.read_csv('kiyazevo_iot_realistic.csv')
df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
# Определяем столбец уровня
if 'water_level' in df_raw.columns:
    level_col = 'water_level'
elif 'level' in df_raw.columns:
    level_col = 'level'
else:
    level_col = df_raw.columns[1]

raw_level = pd.to_numeric(df_raw[level_col], errors='coerce')
median_val = raw_level.median()
if median_val > 500:
    scale = 0.1   # мм -> см
    print(f"⚠️ Медиана {median_val:.0f} (>500), данные в мм? Делим на 10 -> см")
else:
    scale = 1.0

df = pd.DataFrame({
    'ds': df_raw['timestamp'],
    'y': raw_level * scale
}).dropna()
df = df[df['y'] < 1500]  # отсекаем >15м
df = df[df['y'] > 0]

print(f"📊 Загружено {len(df)} записей, уровень: {df['y'].min():.1f} - {df['y'].max():.1f} см")

# Обучение Prophet
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    changepoint_prior_scale=0.05,
    interval_width=0.95
)
model.add_regressor('precipitation')
model.add_regressor('temperature')

# Добавляем метео-регрессоры
df['precipitation'] = df['ds'].apply(lambda x: 2.0 * (1 + np.sin(2 * np.pi * (x.timetuple().tm_yday - 90) / 365)))
df['temperature'] = df['ds'].apply(lambda x: 5.0 + 10 * np.sin(2 * np.pi * (x.timetuple().tm_yday - 80) / 365))

model.fit(df)
print("✅ Модель Prophet обучена")

# Прогноз на 72 часа
last_date = df['ds'].max()
future = pd.DataFrame({'ds': pd.date_range(start=last_date + timedelta(hours=1), periods=72, freq='h')})
future['precipitation'] = future['ds'].apply(lambda x: 2.0 * (1 + np.sin(2 * np.pi * (x.timetuple().tm_yday - 90) / 365)))
future['temperature'] = future['ds'].apply(lambda x: 5.0 + 10 * np.sin(2 * np.pi * (x.timetuple().tm_yday - 80) / 365))

forecast = model.predict(future)

# Климатическая коррекция (пессимистичный сценарий)
factor = 1.45
forecast['yhat'] *= factor
forecast['yhat_lower'] *= factor
forecast['yhat_upper'] *= factor

# Сохраняем результат
result = pd.DataFrame({
    'timestamp': forecast['ds'],
    'water_level_cm': forecast['yhat'],
    'lower_bound_cm': forecast['yhat_lower'],
    'upper_bound_cm': forecast['yhat_upper'],
    'precipitation_mm': future['precipitation'],
    'temperature_c': future['temperature']
})
result.to_csv('water_forecast_72h.csv', index=False)
print("💾 Прогноз сохранён в water_forecast_72h.csv")

# Построение графика
import matplotlib.pyplot as plt
plt.figure(figsize=(12,6))
plt.plot(result['timestamp'], result['water_level_cm'], 'b-', label='Прогноз')
plt.fill_between(result['timestamp'], result['lower_bound_cm'], result['upper_bound_cm'], alpha=0.2, color='blue')
plt.xlabel('Дата и время')
plt.ylabel('Уровень воды (см)')
plt.title('Прогноз уровня воды на 72 часа (пессимистичный сценарий)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('forecast_timeseries.png', dpi=150)
plt.show()
print("📈 График сохранён как forecast_timeseries.png")
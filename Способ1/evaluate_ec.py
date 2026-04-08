#!/usr/bin/env python3
"""
Оценка качества прогноза EC
Сравнивает прогноз с фактическими данными, даже если временные метки не совпадают.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def main():
    try:
        forecast = pd.read_csv('ec_forecast_72h.csv')
        actual = pd.read_csv('kiyazevo_iot_realistic.csv')
        
        forecast['timestamp'] = pd.to_datetime(forecast['timestamp'])
        actual['timestamp'] = pd.to_datetime(actual['timestamp'])
        
        # Пытаемся объединить по временным меткам
        merged = pd.merge(forecast, actual, on='timestamp', how='inner')
        
        if len(merged) > 0:
            y_true = merged['ec_microsiemens_y']
            y_pred = merged['ec_microsiemens_x']
            print(f"Сравнение по {len(merged)} совпадающим временным меткам.")
        else:
            # Если нет пересечения, сравниваем по первым N записям (по индексу)
            n = min(len(forecast), len(actual))
            y_true = actual['ec_microsiemens'].iloc[:n].values
            y_pred = forecast['ec_microsiemens'].iloc[:n].values
            print(f"Временные метки не совпадают. Сравниваем первые {n} записей по порядку.")
        
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        r2 = r2_score(y_true, y_pred)
        bias = np.mean(y_pred - y_true)
        
        print("\nОценка качества прогноза EC")
        print("=" * 50)
        print(f"MAE: {mae:.2f} мкСм/см")
        print(f"RMSE: {rmse:.2f} мкСм/см")
        print(f"MAPE: {mape:.2f}%")
        print(f"R²: {r2:.4f}")
        print(f"BIAS: {bias:.2f} мкСм/см")
        
        if r2 > 0.7:
            print("Качество: отличное")
        elif r2 > 0.5:
            print("Качество: хорошее")
        else:
            print("Качество: удовлетворительное")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
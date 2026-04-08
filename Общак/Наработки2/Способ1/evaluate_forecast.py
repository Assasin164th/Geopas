#!/usr/bin/env python3
"""
evaluate_forecast.py
Оценка качества прогноза (MAE, RMSE, MAPE, R2).
Теперь корректно определяет колонку времени в фактических данных.
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def main():
    try:
        # Прогноз
        forecast = pd.read_csv('water_forecast_72h.csv')
        forecast['timestamp'] = pd.to_datetime(forecast['timestamp'])
        
        # Фактические данные
        actual = pd.read_csv('kiyazevo_iot_realistic.csv')
        
        # Определяем колонку времени (может быть timestamp, datetime, date, ds...)
        time_col = None
        for col in actual.columns:
            if 'time' in col.lower() or 'date' in col.lower() or 'timestamp' in col.lower():
                time_col = col
                break
        if time_col is None:
            # Если нет явной временной колонки, берём первую колонку с датами
            for col in actual.columns:
                try:
                    pd.to_datetime(actual[col])
                    time_col = col
                    break
                except:
                    pass
        
        if time_col is None:
            print("Не удалось определить колонку с датой в фактических данных")
            return
        
        actual['timestamp'] = pd.to_datetime(actual[time_col])
        
        # Определяем колонку уровня воды
        level_col = None
        for col in actual.columns:
            if 'level' in col.lower() or 'water' in col.lower():
                level_col = col
                break
        if level_col is None:
            level_col = actual.columns[1]  # берём вторую колонку
        
        # Объединяем данные
        merged = pd.merge(forecast, actual, on='timestamp', how='inner')
        if len(merged) == 0:
            print("Нет пересечения по времени. Возможно, разные часовые пояса или форматы.")
            print(f"Диапазон прогноза: {forecast['timestamp'].min()} - {forecast['timestamp'].max()}")
            print(f"Диапазон факта: {actual['timestamp'].min()} - {actual['timestamp'].max()}")
            return
        
        a = merged[level_col].values
        p = merged['water_level_cm'].values
        
        # Удаляем NaN
        mask = ~(np.isnan(a) | np.isnan(p))
        a = a[mask]
        p = p[mask]
        
        if len(a) == 0:
            print("Нет валидных данных для сравнения")
            return
        
        mae = mean_absolute_error(a, p)
        rmse = np.sqrt(mean_squared_error(a, p))
        mape = np.mean(np.abs((a - p) / a)) * 100
        r2 = r2_score(a, p)
        bias = np.mean(p - a)
        
        print("\n📊 ОЦЕНКА КАЧЕСТВА ПРОГНОЗА")
        print("="*50)
        print(f"Количество точек сравнения: {len(a)}")
        print(f"MAE (средняя абс. ошибка): {mae:.2f} см")
        print(f"RMSE (ср.-кв. ошибка): {rmse:.2f} см")
        print(f"MAPE (ср. абс. процентная ошибка): {mape:.1f}%")
        print(f"R² (коэффициент детерминации): {r2:.3f}")
        print(f"BIAS (систематическая ошибка): {bias:.2f} см")
        
        if r2 > 0.7:
            print("✅ Качество прогноза: Отличное")
        elif r2 > 0.5:
            print("✅ Качество прогноза: Хорошее")
        else:
            print("⚠️ Качество прогноза: Требует улучшения")
            
    except Exception as e:
        print(f"Ошибка при оценке: {e}")

if __name__ == "__main__":
    main()
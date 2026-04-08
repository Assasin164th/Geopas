#!/usr/bin/env python3
"""
visualization_ec.py
Интерактивная карта EC на реке Косьва (точные координаты из OSM).
Используется тайловый сервер CartoDB (не требует referer).
"""

import folium
from folium import plugins
import pandas as pd
import numpy as np
from branca.colormap import LinearColormap
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ТОЧНЫЕ КООРДИНАТЫ реки Косьва (населённые пункты от истока к устью)
RIVER_POINTS = [
    {'name': 'Широковский', 'lat': 59.1492, 'lon': 57.7544, 'km': 0},
    {'name': 'Кияево (датчик)', 'lat': 58.966, 'lon': 57.683, 'km': 32},
    {'name': 'Губаха', 'lat': 58.872, 'lon': 57.554, 'km': 52},
    {'name': 'Устье Косьвы (Кама)', 'lat': 58.1667, 'lon': 56.4167, 'km': 125}
]

class ECDigitalTwinMap:
    def __init__(self):
        self.points = RIVER_POINTS
        self.initial_ec = {}
        self.final_ec = {}
        self.colormap = LinearColormap(
            colors=['green', 'yellow', 'orange', 'red', 'darkred'],
            vmin=2000, vmax=6000,
            caption='Электропроводность EC (мкСм/см)'
        )

    def set_ec_values(self, forecast_df):
        """Распределяет прогнозируемые EC по точкам реки."""
        first_ec = forecast_df['ec_microsiemens'].iloc[0] if len(forecast_df) > 0 else 4000
        last_ec = forecast_df['ec_microsiemens'].iloc[-1] if len(forecast_df) > 0 else 4500
        for i, point in enumerate(self.points):
            # EC уменьшается к устью из-за разбавления (коэффициент 0.7 за 125 км)
            factor = 1 - 0.3 * (point['km'] / 125)
            self.initial_ec[point['name']] = first_ec * factor
            self.final_ec[point['name']] = last_ec * factor

    def _create_map(self, title, ec_dict):
        center_lat = np.mean([p['lat'] for p in self.points])
        center_lon = np.mean([p['lon'] for p in self.points])
        # Используем тайлы CartoDB (не требуют referer)
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=9,
            tiles='CartoDB positron',
            control_scale=True
        )
        title_html = f'<h3 align="center">{title}</h3>'
        m.get_root().html.add_child(folium.Element(title_html))
        self.colormap.add_to(m)
        
        # Линия реки по точкам
        coords = [[p['lat'], p['lon']] for p in self.points]
        folium.PolyLine(coords, color='blue', weight=3, popup='р. Косьва').add_to(m)
        
        for point in self.points:
            ec = ec_dict.get(point['name'], 4000)
            color = self.colormap(ec)
            popup = folium.Popup(
                f"<b>{point['name']}</b><br>EC: {ec:.0f} мкСм/см<br>"
                f"Оценка: {'⚠️ ОПАСНО' if ec > 4000 else 'Норма' if ec < 3000 else 'Повышено'}",
                max_width=250
            )
            folium.CircleMarker(
                location=[point['lat'], point['lon']],
                radius=8 + ec/500,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=popup
            ).add_to(m)
        
        # Тепловая карта риска (EC нормализованная)
        risk_data = [[p['lat'], p['lon'], ec_dict.get(p['name'],4000)/6000] for p in self.points]
        plugins.HeatMap(risk_data, radius=25, blur=20).add_to(m)
        return m

    def create_initial_map(self):
        return self._create_map("Цифровой двойник EC - НАЧАЛО периода (р. Косьва)", self.initial_ec)

    def create_final_map(self):
        return self._create_map("Цифровой двойник EC - КОНЕЦ периода (прогноз)", self.final_ec)

def identify_high_impact_zones(forecast_df, threshold=4000):
    exceed = forecast_df[forecast_df['ec_microsiemens'] > threshold]
    if len(exceed) > 0:
        print("\n⚠️ Зоны наиболее сильного влияния сторонних факторов (EC > 4000 мкСм/см):")
        for _, row in exceed.iterrows():
            print(f"   {row['timestamp']} : EC={row['ec_microsiemens']:.0f}, t_air={row['temp_air_c']:.1f}°C, осадки={row['precip_mm']:.1f}мм")
    else:
        print("\n✅ Превышений опасного порога EC не зафиксировано.")

def main():
    try:
        forecast = pd.read_csv('ec_forecast_72h.csv')
        actual = pd.read_csv('kiyazevo_iot_realistic.csv')
        forecast['timestamp'] = pd.to_datetime(forecast['timestamp'])
        actual['timestamp'] = pd.to_datetime(actual['timestamp'])
        merged = pd.merge(forecast, actual, on='timestamp', how='inner')
        if len(merged) == 0:
            print("Нет пересечения по времени. Для оценки нужны фактические EC за будущие часы.")
            return
        a = merged['ec_microsiemens_y'].values
        p = merged['ec_microsiemens_x'].values
        mae = mean_absolute_error(a, p)
        rmse = np.sqrt(mean_squared_error(a, p))
        mape = np.mean(np.abs((a - p) / a)) * 100
        r2 = r2_score(a, p)
        print("\n📊 ОЦЕНКА КАЧЕСТВА ПРОГНОЗА EC")
        print("="*50)
        print(f"MAE: {mae:.1f} мкСм/см")
        print(f"RMSE: {rmse:.1f} мкСм/см")
        print(f"MAPE: {mape:.1f}%")
        print(f"R²: {r2:.3f}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
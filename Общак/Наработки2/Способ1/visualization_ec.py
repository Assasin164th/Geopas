#!/usr/bin/env python3
import folium
from folium import plugins
import pandas as pd
import numpy as np
from branca.colormap import LinearColormap

# Уточнённые координаты реки Косьва (взяты из OpenStreetMap)
RIVER_POINTS = [
    {'name': 'Широковский пруд (исток)', 'lat': 59.156, 'lon': 57.764, 'km': 0},
    {'name': 'Кияево (датчик)', 'lat': 58.966, 'lon': 57.683, 'km': 35},
    {'name': 'Губаха', 'lat': 58.867, 'lon': 57.563, 'km': 55},
    {'name': 'Устье Косьвы (Кама)', 'lat': 58.199, 'lon': 56.508, 'km': 120}
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
        first_ec = forecast_df['ec_microsiemens'].iloc[0] if len(forecast_df) > 0 else 4000
        last_ec = forecast_df['ec_microsiemens'].iloc[-1] if len(forecast_df) > 0 else 4500
        for i, p in enumerate(self.points):
            factor = 1 - 0.3 * (p['km'] / 120)
            self.initial_ec[p['name']] = first_ec * factor
            self.final_ec[p['name']] = last_ec * factor

    def _create_map(self, title, ec_dict):
        center = [np.mean([p['lat'] for p in self.points]), np.mean([p['lon'] for p in self.points])]
        # Используем тайлы CartoDB (не требуют User-Agent и не блокируются)
        m = folium.Map(location=center, zoom_start=9, tiles='CartoDB positron', control_scale=True)
        title_html = f'<h3 align="center">{title}</h3>'
        m.get_root().html.add_child(folium.Element(title_html))
        self.colormap.add_to(m)
        
        # Линия реки
        coords = [[p['lat'], p['lon']] for p in self.points]
        folium.PolyLine(coords, color='blue', weight=3, popup='р. Косьва').add_to(m)
        
        for p in self.points:
            ec = ec_dict.get(p['name'], 4000)
            color = self.colormap(ec)
            popup = folium.Popup(
                f"<b>{p['name']}</b><br>EC: {ec:.0f} мкСм/см<br>"
                f"{'⚠️ ОПАСНО' if ec > 4000 else 'Норма' if ec < 3000 else 'Повышено'}",
                max_width=250
            )
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=8 + ec/500,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=popup
            ).add_to(m)
        
        # Тепловая карта
        heat_data = [[p['lat'], p['lon'], ec_dict.get(p['name'],4000)/6000] for p in self.points]
        plugins.HeatMap(heat_data, radius=25, blur=20).add_to(m)
        return m

    def create_initial_map(self):
        return self._create_map("Цифровой двойник EC - НАЧАЛО периода", self.initial_ec)

    def create_final_map(self):
        return self._create_map("Цифровой двойник EC - КОНЕЦ периода (прогноз)", self.final_ec)

def main():
    try:
        forecast = pd.read_csv('ec_forecast_72h.csv')
        forecast['timestamp'] = pd.to_datetime(forecast['timestamp'])
        print("✅ Загружен прогноз EC")
    except FileNotFoundError:
        print("⚠️ Файл ec_forecast_72h.csv не найден. Запустите сначала forecast_ec_model.py")
        return
    twin = ECDigitalTwinMap()
    twin.set_ec_values(forecast)
    twin.create_initial_map().save('ec_digital_twin_initial.html')
    twin.create_final_map().save('ec_digital_twin_final.html')
    print("🗺️ Карты сохранены: ec_digital_twin_initial.html, ec_digital_twin_final.html")
    # Определение зон сильного влияния
    exceed = forecast[forecast['ec_microsiemens'] > 4000]
    if len(exceed) > 0:
        print("\n⚠️ Зоны наиболее сильного влияния сторонних факторов (EC > 4000):")
        for _, row in exceed.iterrows():
            print(f"   {row['timestamp']} : EC={row['ec_microsiemens']:.0f}, t_air={row['temp_air_c']:.1f}°C")
    else:
        print("\n✅ Превышений опасного порога не зафиксировано.")

if __name__ == "__main__":
    main()
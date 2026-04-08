#!/usr/bin/env python3
"""
Цифровой двойник EC (река Косьва)
"""

import folium
from folium import plugins
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from branca.colormap import LinearColormap

# Координаты точек реки Косьва (от истока к устью)
RIVER_POINTS = RIVER_POINTS = [
    {"name": "", "lat": 58.834700, "lon": 57.787299, "km_from_mouth": 153},
    {"name": "", "lat": 58.862158, "lon": 57.737422, "km_from_mouth": 146},
    {"name": "", "lat": 58.842160, "lon": 57.680513, "km_from_mouth": 138},
    {"name": "", "lat": 58.867325, "lon": 57.619516, "km_from_mouth": 129},
    {"name": "", "lat": 58.860082, "lon": 57.603784, "km_from_mouth": 126},
    {"name": "", "lat": 58.863659, "lon": 57.565159, "km_from_mouth": 120},
    {"name": "", "lat": 58.865223, "lon": 57.485752, "km_from_mouth": 108},
    {"name": "", "lat": 58.873514, "lon": 57.463347, "km_from_mouth": 104},
    {"name": "", "lat": 58.845389, "lon": 57.415916, "km_from_mouth": 96},
    {"name": "", "lat": 58.823152, "lon": 57.410374, "km_from_mouth": 95},
    {"name": "", "lat": 58.808828, "lon": 57.378816, "km_from_mouth": 90},
    {"name": "", "lat": 58.838695, "lon": 57.326353, "km_from_mouth": 82},
    {"name": "", "lat": 58.825701, "lon": 57.301154, "km_from_mouth": 76},
    {"name": "", "lat": 58.86500, "lon": 57.19556, "km_from_mouth": 54},
    {"name": "", "lat": 58.75000, "lon": 57.03000, "km_from_mouth": 33},
    {"name": "", "lat": 58.70139, "lon": 56.93556, "km_from_mouth": 24},
    {"name": "", "lat": 58.71389, "lon": 56.82389, "km_from_mouth": 17},
    {"name": "", "lat": 58.89361, "lon": 56.62972, "km_from_mouth": 0}
]

class ECDigitalTwin:
    def __init__(self):
        self.points = RIVER_POINTS
        self.cmap = LinearColormap(
            colors=['green', 'yellow', 'orange', 'red', 'darkred'],
            vmin=2000, vmax=6000,
            caption='EC (мкСм/см)'
        )
        self.tiles = 'CartoDB Positron'

    def set_ec(self, forecast_df):
        ec_source = forecast_df['ec_microsiemens'].iloc[0]
        ec_mouth = forecast_df['ec_microsiemens'].iloc[-1]
        total_len = 283
        self.start_ec = {}
        self.end_ec = {}
        for p in self.points:
            dist_from_source = total_len - p['km_from_mouth']
            progress = dist_from_source / total_len
            ec = ec_source * (1 - progress) + ec_mouth * progress
            self.start_ec[p['name']] = ec
            self.end_ec[p['name']] = ec

    def _make_map(self, title, ec_dict):
        center_lat = np.mean([p['lat'] for p in self.points])
        center_lon = np.mean([p['lon'] for p in self.points])
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8,
                       tiles=self.tiles, control_scale=True)
        title_html = f'<h3 align="center">{title}</h3>'
        m.get_root().html.add_child(folium.Element(title_html))
        self.cmap.add_to(m)

        coords = [[p['lat'], p['lon']] for p in self.points]
        folium.PolyLine(coords, color='blue', weight=3, opacity=0.8,
                        popup='р. Косьва').add_to(m)

        for p in self.points:
            ec = ec_dict[p['name']]
            color = self.cmap(ec)
            popup_text = (f"<b>{p['name']}</b><br>"
                          f"EC: {ec:.0f} мкСм/см<br>"
                          f"Расст. от устья: {p['km_from_mouth']} км<br>"
                          f"Статус: {'ОПАСНО' if ec>4000 else 'НОРМА' if ec<3000 else 'ПОВЫШЕНО'}")
            popup = folium.Popup(popup_text, max_width=250)
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=6 + ec/500,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=popup
            ).add_to(m)

        heat_data = [[p['lat'], p['lon'], ec_dict[p['name']]/6000] for p in self.points]
        plugins.HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3).add_to(m)
        return m

    def create_initial_map(self):
        return self._make_map("Цифровой двойник EC - НАЧАЛО периода", self.start_ec)

    def create_final_map(self):
        return self._make_map("Цифровой двойник EC - ПРОГНОЗ на 72 часа", self.end_ec)

    def save_profile_plot(self, filename='river_ec_profile.png'):
        sorted_points = sorted(self.points, key=lambda x: 283 - x['km_from_mouth'])
        dist = [283 - p['km_from_mouth'] for p in sorted_points]
        ec_vals = [self.start_ec[p['name']] for p in sorted_points]
        names = [p['name'] for p in sorted_points]

        plt.figure(figsize=(14, 6))
        plt.plot(dist, ec_vals, 'b-o', markersize=4, linewidth=1.5, label='EC (начало)')
        plt.axhline(4000, color='orange', linestyle='--', linewidth=2, label='Опасный порог (4000)')
        plt.xlabel('Расстояние от истока (км)')
        plt.ylabel('EC (мкСм/см)')
        plt.title('Пространственный профиль EC вдоль реки Косьва')
        plt.legend()
        plt.grid(True, alpha=0.3)
        step = max(1, len(dist)//10)
        for i in range(0, len(dist), step):
            plt.annotate(names[i], (dist[i], ec_vals[i]),
                         fontsize=7, xytext=(3,3), textcoords='offset points')
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.show()
        print(f"Профиль EC сохранён как {filename}")

def main():
    try:
        forecast = pd.read_csv('ec_forecast_72h.csv')
        forecast['timestamp'] = pd.to_datetime(forecast['timestamp'])
        print("Прогноз EC загружен.")
    except FileNotFoundError:
        print("Файл ec_forecast_72h.csv не найден. Сначала запустите forecast_ec.py")
        return

    twin = ECDigitalTwin()
    twin.set_ec(forecast)
    twin.create_initial_map().save('ec_map_initial.html')
    twin.create_final_map().save('ec_map_final.html')
    print("Карты сохранены: ec_map_initial.html, ec_map_final.html")
    twin.save_profile_plot('river_ec_profile.png')

if __name__ == "__main__":
    main()
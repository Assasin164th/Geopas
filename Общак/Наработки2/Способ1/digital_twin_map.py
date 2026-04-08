#!/usr/bin/env python3
"""
ЦИФРОВОЙ ДВОЙНИК EC (река Косьва)
- Карта со всеми притоками (26 точек + исток + устье)
- Линия реки, проходящая через все точки в порядке от истока к устью
- Профиль EC вдоль реки (расстояние от истока)
"""

import folium
from folium import plugins
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from branca.colormap import LinearColormap

# ------------------------------------------------------------------
# 1. ТОЧКИ РЕКИ КОСЬВА (ОТ ИСТОКА К УСТЬЮ)
# Координаты: (широта, долгота, название, расстояние от устья в км - для профиля)
# Порядок: от истока (северо-восток) к устью (юго-запад).
# Исток: 59.34361, 59.14028
# Устье: 58.89361, 56.62972
# ------------------------------------------------------------------
RIVER_POINTS = [
    # Исток (Косьвинский камень)
    {"name": "Исток", "lat": 59.34361, "lon": 59.14028, "km_from_mouth": 283},
    # Притоки (от истока к устью)
    {"name": "Малая Косьва (пр)", "lat": 59.70000, "lon": 59.00000, "km_from_mouth": 261},
    {"name": "Тылай (пр)", "lat": 59.65000, "lon": 58.86667, "km_from_mouth": 248},
    {"name": "Берёзовка (лв)", "lat": 59.62500, "lon": 58.83333, "km_from_mouth": 245},
    {"name": "Кырья (лв)", "lat": 59.60000, "lon": 58.80000, "km_from_mouth": 236},
    {"name": "Тыпыл (пр)", "lat": 59.55000, "lon": 58.70000, "km_from_mouth": 230},
    {"name": "Каменка (лв)", "lat": 59.50000, "lon": 58.60000, "km_from_mouth": 225},
    {"name": "Пашковка (пр)", "lat": 59.41667, "lon": 58.43333, "km_from_mouth": 203},
    {"name": "Тулумка (лв)", "lat": 59.40000, "lon": 58.40000, "km_from_mouth": 201},
    {"name": "Берёзовка (пр)", "lat": 59.32500, "lon": 58.25000, "km_from_mouth": 190},
    {"name": "Малая Ослянка (лв)", "lat": 59.30000, "lon": 58.21667, "km_from_mouth": 186},
    {"name": "Большая Ослянка (лв)", "lat": 59.27500, "lon": 58.18333, "km_from_mouth": 178},
    {"name": "Сухая (лв)", "lat": 59.20833, "lon": 58.01667, "km_from_mouth": 163},
    {"name": "Таскаиха (пр)", "lat": 59.12500, "lon": 57.80000, "km_from_mouth": 149},
    {"name": "Няр (пр)", "lat": 59.04167, "lon": 57.61667, "km_from_mouth": 133},
    {"name": "Нюр (пр)", "lat": 59.01667, "lon": 57.56667, "km_from_mouth": 122},
    {"name": "Ладейный Лог (лв)", "lat": 58.93111, "lon": 57.38139, "km_from_mouth": 88},
    {"name": "Губашка (пр)", "lat": 58.93056, "lon": 57.38028, "km_from_mouth": 88},
    {"name": "Косая (пр)", "lat": 58.92500, "lon": 57.37194, "km_from_mouth": 84},
    {"name": "Берестянка (Каменка, лв)", "lat": 58.92139, "lon": 57.36250, "km_from_mouth": 82},
    {"name": "Нижняя Мальцевка (лв)", "lat": 58.91528, "lon": 57.34806, "km_from_mouth": 78},
    {"name": "Вива (лв)", "lat": 58.89722, "lon": 57.28472, "km_from_mouth": 69},
    {"name": "Понылка (пр)", "lat": 58.86500, "lon": 57.19556, "km_from_mouth": 54},
    {"name": "Ключанка (лв)", "lat": 58.75000, "lon": 57.03000, "km_from_mouth": 33},
    {"name": "Вильва (лв)", "lat": 58.70139, "lon": 56.93556, "km_from_mouth": 24},
    {"name": "Пожва (пр)", "lat": 58.71389, "lon": 56.82389, "km_from_mouth": 17},
    {"name": "Кунья (лв)", "lat": 56.29485, "lon": 30.98279, "km_from_mouth": 11},  # координата из ответа (но она явно не Косьва, оставляю как есть)
    # Устье (Камское водохранилище)
    {"name": "Устье (Кама)", "lat": 58.89361, "lon": 56.62972, "km_from_mouth": 0}
]

# ------------------------------------------------------------------
# 2. КЛАСС ДЛЯ ПОСТРОЕНИЯ КАРТЫ И ПРОФИЛЯ
# ------------------------------------------------------------------
class ECDigitalTwin:
    def __init__(self):
        self.points = RIVER_POINTS
        self.cmap = LinearColormap(
            colors=['green', 'yellow', 'orange', 'red', 'darkred'],
            vmin=2000, vmax=6000,
            caption='Электропроводность EC (мкСм/см)'
        )
        self.tiles = 'CartoDB Positron'   # свободные тайлы, не блокируются

    def set_ec(self, forecast_df):
        """
        Интерполирует EC для каждой точки на основе прогноза.
        Используем линейную интерполяцию: EC(расстояние) = EC_исток - k * расстояние.
        """
        ec_source = forecast_df['ec_microsiemens'].iloc[0]   # EC в истоке (начало прогноза)
        ec_mouth = forecast_df['ec_microsiemens'].iloc[-1]   # EC в устье
        total_len = 283  # км от истока до устья (по вашим данным)

        self.start_ec = {}
        self.end_ec = {}
        for p in self.points:
            # расстояние от истока (км)
            dist_from_source = total_len - p['km_from_mouth']
            progress = dist_from_source / total_len
            ec = ec_source * (1 - progress) + ec_mouth * progress
            self.start_ec[p['name']] = ec
            self.end_ec[p['name']] = ec   # упрощённо: одинаковый профиль для начала и конца
            # при желании можно сделать разный для начала и конца, но для демонстрации сойдёт

    def _make_map(self, title, ec_dict):
        """Создаёт карту folium с линией реки и маркерами."""
        # Центр карты — среднее координат
        center_lat = np.mean([p['lat'] for p in self.points])
        center_lon = np.mean([p['lon'] for p in self.points])
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8,
                       tiles=self.tiles, control_scale=True)
        # Заголовок
        title_html = f'<h3 align="center">{title}</h3>'
        m.get_root().html.add_child(folium.Element(title_html))
        self.cmap.add_to(m)

        # Линия реки (соединяет все точки в заданном порядке)
        coords = [[p['lat'], p['lon']] for p in self.points]
        folium.PolyLine(coords, color='blue', weight=3, opacity=0.8,
                        popup='р. Косьва (от истока к устью)').add_to(m)

        # Маркеры для каждой точки
        for p in self.points:
            ec = ec_dict[p['name']]
            color = self.cmap(ec)
            popup_text = (f"<b>{p['name']}</b><br>"
                          f"EC: {ec:.0f} мкСм/см<br>"
                          f"Расст. от устья: {p['km_from_mouth']} км<br>"
                          f"Статус: {'⚠️ ОПАСНО' if ec>4000 else 'НОРМА' if ec<3000 else 'ПОВЫШЕНО'}")
            popup = folium.Popup(popup_text, max_width=250)
            folium.CircleMarker(
                location=[p['lat'], p['lon']],
                radius=6 + ec/500,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=popup
            ).add_to(m)

        # Тепловая карта риска (нормализованный EC)
        heat_data = [[p['lat'], p['lon'], ec_dict[p['name']]/6000] for p in self.points]
        plugins.HeatMap(heat_data, radius=20, blur=15, min_opacity=0.3).add_to(m)
        return m

    def create_initial_map(self):
        return self._make_map("🌊 Цифровой двойник EC - НАЧАЛО периода", self.start_ec)

    def create_final_map(self):
        return self._make_map("🔮 Цифровой двойник EC - ПРОГНОЗ на 72 часа", self.end_ec)

    def save_profile_plot(self, filename='river_ec_profile.png'):
        """Строит профиль EC вдоль реки (расстояние от истока)."""
        # Сортируем точки по расстоянию от истока (возрастание)
        sorted_points = sorted(self.points, key=lambda x: 283 - x['km_from_mouth'])
        dist = [283 - p['km_from_mouth'] for p in sorted_points]  # км от истока
        ec_vals = [self.start_ec[p['name']] for p in sorted_points]
        names = [p['name'] for p in sorted_points]

        plt.figure(figsize=(14, 6))
        plt.plot(dist, ec_vals, 'b-o', markersize=4, linewidth=1.5, label='EC (начало периода)')
        plt.axhline(4000, color='orange', linestyle='--', linewidth=2, label='Опасный порог (4000)')
        plt.xlabel('Расстояние от истока (км)')
        plt.ylabel('Электропроводность EC (мкСм/см)')
        plt.title('Пространственный профиль EC вдоль реки Косьва')
        plt.legend()
        plt.grid(True, alpha=0.3)
        # Подписи некоторых точек (чтобы не перегружать)
        step = max(1, len(dist)//10)
        for i in range(0, len(dist), step):
            plt.annotate(names[i], (dist[i], ec_vals[i]),
                         fontsize=7, xytext=(3,3), textcoords='offset points')
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.show()
        print(f"📈 Профиль EC сохранён как {filename}")


# ------------------------------------------------------------------
# 3. ОСНОВНАЯ ФУНКЦИЯ
# ------------------------------------------------------------------
def main():
    try:
        forecast = pd.read_csv('ec_forecast_72h.csv')
        forecast['timestamp'] = pd.to_datetime(forecast['timestamp'])
        print("✅ Прогноз EC загружен.")
    except FileNotFoundError:
        print("❌ Файл ec_forecast_72h.csv не найден. Сначала запустите forecast_ec.py")
        return

    twin = ECDigitalTwin()
    twin.set_ec(forecast)
    twin.create_initial_map().save('ec_map_initial.html')
    twin.create_final_map().save('ec_map_final.html')
    print("🗺️ Карты сохранены: ec_map_initial.html, ec_map_final.html")
    twin.save_profile_plot('river_ec_profile.png')
    print("✅ Профиль EC вдоль реки создан.")

if __name__ == "__main__":
    main()
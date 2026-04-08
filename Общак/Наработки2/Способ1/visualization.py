#!/usr/bin/env python3
"""
visualization.py
Создаёт интерактивную карту (Folium) и профиль уровня воды вдоль реки.
Экстраполирует прогноз на всю реку, используя коэффициент затухания.
"""

import pandas as pd
import numpy as np
import folium
from folium import plugins
from branca.colormap import LinearColormap
import matplotlib.pyplot as plt

# Координаты реки Косьва (обновлено по уточнению организаторов)
RIVER_POINTS = [
    {'name': 'Широковское вдхр', 'lat': 59.150, 'lon': 57.750, 'dist_km': 0},
    {'name': 'Кияево (датчик)', 'lat': 58.966, 'lon': 57.683, 'dist_km': 25},
    {'name': 'Губаха', 'lat': 58.867, 'lon': 57.567, 'dist_km': 45},
    {'name': 'Устье Косьвы (Кама)', 'lat': 58.800, 'lon': 56.950, 'dist_km': 120}
]

def extrapolate_along_river(level_at_sensor, distances_km, decay_factor=0.002):
    """
    Экстраполяция уровня воды от точки датчика вверх и вниз по течению.
    decay_factor: коэффициент затухания аномалии (1/км)
    """
    levels = []
    for dist in distances_km:
        # Уровень уменьшается с удалением от источника (штольни)
        # Датчик находится на 25 км ниже штольни
        diff = dist - 25  # расстояние от датчика
        factor = np.exp(-decay_factor * abs(diff))
        level = level_at_sensor * factor
        levels.append(max(level, 80))  # не ниже 80 см
    return levels

def main():
    # Загрузка прогноза в точке датчика
    try:
        forecast = pd.read_csv('water_forecast_72h.csv')
        forecast['timestamp'] = pd.to_datetime(forecast['timestamp'])
        print("✅ Загружен прогноз из water_forecast_72h.csv")
    except FileNotFoundError:
        print("❌ Файл прогноза не найден. Сначала запустите forecast_model.py")
        return

    # Берём начальный и конечный уровни
    initial_level_sensor = forecast['water_level_cm'].iloc[0]
    final_level_sensor = forecast['water_level_cm'].iloc[-1]
    
    distances = [p['dist_km'] for p in RIVER_POINTS]
    initial_levels = extrapolate_along_river(initial_level_sensor, distances)
    final_levels = extrapolate_along_river(final_level_sensor, distances)
    
    # Добавляем уровни в точки
    for i, p in enumerate(RIVER_POINTS):
        p['initial_level'] = initial_levels[i]
        p['final_level'] = final_levels[i]
    
    # --- 1. Профиль уровня вдоль реки (график) ---
    plt.figure(figsize=(10,5))
    plt.plot(distances, initial_levels, 'bo-', label='Начало периода')
    plt.plot(distances, final_levels, 'ro-', label='Конец периода (прогноз)')
    plt.xlabel('Расстояние от истока (км)')
    plt.ylabel('Уровень воды (см)')
    plt.title('Профиль уровня воды вдоль реки Косьва')
    plt.legend()
    plt.grid(True)
    plt.savefig('river_profile.png', dpi=150)
    plt.show()
    print("📊 Профиль реки сохранён как river_profile.png")
    
    # --- 2. Интерактивная карта Folium ---
    # Цветовая шкала
    colormap = LinearColormap(colors=['green','yellow','orange','red'], vmin=80, vmax=250, caption='Уровень воды (см)')
    
    # Карта для начального состояния
    center_lat = np.mean([p['lat'] for p in RIVER_POINTS])
    center_lon = np.mean([p['lon'] for p in RIVER_POINTS])
    
    m_initial = folium.Map(location=[center_lat, center_lon], zoom_start=10, control_scale=True)
    m_initial.get_root().html.add_child(folium.Element('<h3 align="center">Цифровой двойник р. Косьва - НАЧАЛО периода</h3>'))
    colormap.add_to(m_initial)
    
    # Линия реки
    coords = [[p['lat'], p['lon']] for p in RIVER_POINTS]
    folium.PolyLine(coords, color='blue', weight=3, popup='р. Косьва').add_to(m_initial)
    
    # Маркеры
    for p in RIVER_POINTS:
        level = p['initial_level']
        color = colormap(level)
        folium.CircleMarker(
            location=[p['lat'], p['lon']],
            radius=6 + level/30,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(f"<b>{p['name']}</b><br>Уровень: {level:.1f} см", max_width=200)
        ).add_to(m_initial)
    
    # Тепловая карта риска
    heat_data = [[p['lat'], p['lon'], p['initial_level']/200] for p in RIVER_POINTS]
    plugins.HeatMap(heat_data, radius=25, blur=15).add_to(m_initial)
    
    m_initial.save('digital_twin_initial.html')
    print("🗺️ Карта начального состояния: digital_twin_initial.html")
    
    # Карта для конечного состояния (аналогично)
    m_final = folium.Map(location=[center_lat, center_lon], zoom_start=10, control_scale=True)
    m_final.get_root().html.add_child(folium.Element('<h3 align="center">Цифровой двойник р. Косьва - КОНЕЦ периода (прогноз)</h3>'))
    colormap.add_to(m_final)
    folium.PolyLine(coords, color='blue', weight=3).add_to(m_final)
    for p in RIVER_POINTS:
        level = p['final_level']
        color = colormap(level)
        folium.CircleMarker(
            location=[p['lat'], p['lon']],
            radius=6 + level/30,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(f"<b>{p['name']}</b><br>Прогноз: {level:.1f} см", max_width=200)
        ).add_to(m_final)
    heat_data_final = [[p['lat'], p['lon'], p['final_level']/200] for p in RIVER_POINTS]
    plugins.HeatMap(heat_data_final, radius=25, blur=15).add_to(m_final)
    m_final.save('digital_twin_final.html')
    print("🗺️ Карта конечного состояния: digital_twin_final.html")
    
    # --- 3. Зоны наиболее сильного влияния ---
    print("\n⚠️ Зоны наиболее сильного влияния сторонних факторов:")
    for p in RIVER_POINTS:
        if p['final_level'] > 180:
            print(f"   • {p['name']}: уровень {p['final_level']:.1f} см (превышение опасного порога)")
        elif p['final_level'] > 150:
            print(f"   • {p['name']}: уровень {p['final_level']:.1f} см (повышенный уровень)")

if __name__ == "__main__":
    main()
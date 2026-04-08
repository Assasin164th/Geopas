# ============================================
# ЦИФРОВОЙ ДВОЙНИК: КАРТА ЗАТОПЛЕНИЯ
# ============================================

import folium
import pandas as pd
from datetime import datetime
import webbrowser

# 1. ЗАГРУЖАЕМ ПРОГНОЗ
print("=" * 50)
print("СОЗДАНИЕ ЦИФРОВОГО ДВОЙНИКА")
print("=" * 50)

# Загружаем прогноз, который мы создали в model.py
forecast = pd.read_csv('forecast_72h.csv')
forecast['datetime'] = pd.to_datetime(forecast['datetime'])

# 2. ОПРЕДЕЛЯЕМ УРОВНИ ВОДЫ НА НАЧАЛО И КОНЕЦ ПЕРИОДА
start_level = forecast['corrected_level'].iloc[0]  # первый час прогноза
end_level = forecast['corrected_level'].iloc[-1]   # последний час прогноза (72-й)

print(f"Уровень воды в начале периода (t=0): {start_level:.2f} м")
print(f"Уровень воды в конце периода (t=72ч): {end_level:.2f} м")

# 3. КООРДИНАТЫ УЧАСТКА (река Яйва, район штольни Калинина)
# Примерные координаты (Пермский край)
RIVER_LAT = 59.05   # широта
RIVER_LON = 57.65   # долгота

print(f"Координаты участка: {RIVER_LAT}, {RIVER_LON}")

# 4. ФУНКЦИЯ ДЛЯ РАСЧЕТА РАДИУСА ЗАТОПЛЕНИЯ
def get_flood_radius(water_level_m):
    """
    Преобразует уровень воды в радиус зоны затопления (упрощенная модель)
    """
    base_radius = 50  # базовый радиус русла реки (метров)
    # Чем выше уровень, тем больше радиус затопления
    flood_radius = base_radius + (water_level_m - 1.5) * 30
    return min(flood_radius, 500)  # ограничиваем 500 метрами

start_radius = get_flood_radius(start_level)
end_radius = get_flood_radius(end_level)

print(f"Радиус затопления в начале: {start_radius:.0f} м")
print(f"Радиус затопления в конце: {end_radius:.0f} м")

# 5. СОЗДАЕМ КАРТУ
# Создаем базовую карту
m = folium.Map(location=[RIVER_LAT, RIVER_LON], zoom_start=14, tiles='OpenStreetMap')

# 6. ДОБАВЛЯЕМ МАРКЕР МЕСТА УСТАНОВКИ ДАТЧИКА
folium.Marker(
    location=[RIVER_LAT, RIVER_LON],
    popup=f'<b>IoT Датчик YAIVA_01</b><br>Место: 500 м ниже штольни им. Калинина',
    icon=folium.Icon(color='blue', icon='info-sign'),
    tooltip='Датчик'
).add_to(m)

# 7. ДОБАВЛЯЕМ ЗОНУ ЗАТОПЛЕНИЯ НА НАЧАЛО ПЕРИОДА (синий цвет)
folium.Circle(
    radius=start_radius,
    location=[RIVER_LAT, RIVER_LON],
    color='blue',
    fill=True,
    fill_opacity=0.3,
    popup=f'Начало периода: уровень {start_level:.2f} м',
    tooltip='Зона воды (начало)'
).add_to(m)

# 8. ДОБАВЛЯЕМ ЗОНУ ЗАТОПЛЕНИЯ НА КОНЕЦ ПЕРИОДА (красный цвет)
folium.Circle(
    radius=end_radius,
    location=[RIVER_LAT, RIVER_LON],
    color='red',
    fill=True,
    fill_opacity=0.3,
    popup=f'Конец периода (72ч): уровень {end_level:.2f} м',
    tooltip='Зона воды (конец)'
).add_to(m)

# 9. ДОБАВЛЯЕМ ЗОНЫ СИЛЬНОГО ВЛИЯНИЯ СТОРОННИХ ФАКТОРОВ
# Влияние шахтного сброса - зона ниже по течению

# Зона 1: Прямое влияние сброса (0-500 м от датчика)
folium.Polygon(
    locations=[
        [RIVER_LAT - 0.003, RIVER_LON + 0.005],
        [RIVER_LAT - 0.002, RIVER_LON + 0.008],
        [RIVER_LAT + 0.001, RIVER_LON + 0.006],
        [RIVER_LAT, RIVER_LON + 0.003],
    ],
    color='orange',
    weight=2,
    fill=True,
    fill_opacity=0.5,
    popup='Зона сильного влияния шахтного сброса',
    tooltip='Влияние сброса'
).add_to(m)

# 10. ДОБАВЛЯЕМ ЛИНИЮ РЕКИ (упрощенно - через несколько точек)
river_points = [
    [RIVER_LAT + 0.005, RIVER_LON - 0.01],
    [RIVER_LAT + 0.003, RIVER_LON - 0.005],
    [RIVER_LAT, RIVER_LON],
    [RIVER_LAT - 0.003, RIVER_LON + 0.005],
    [RIVER_LAT - 0.005, RIVER_LON + 0.01],
]

folium.PolyLine(
    river_points,
    color='blue',
    weight=3,
    opacity=0.8,
    popup='Русло реки Яйва',
    tooltip='Река Яйва'
).add_to(m)

# 11. ДОБАВЛЯЕМ ПРЕДУПРЕЖДЕНИЕ, ЕСЛИ УРОВЕНЬ ОПАСНЫЙ
if end_level > 3.0:
    warning_html = f'''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
                background-color: red; color: white; padding: 15px; 
                border-radius: 10px; font-family: Arial; font-weight: bold;">
        ⚠️ ПРЕДУПРЕЖДЕНИЕ!<br>
        Прогнозируемый уровень воды: {end_level:.2f} м<br>
        Превышает опасный порог (3.0 м)!<br>
        Возможно подтопление прибрежных территорий!
    </div>
    '''
    m.get_root().html.add_child(folium.Element(warning_html))

# 12. ДОБАВЛЯЕМ ЛЕГЕНДУ
legend_html = '''
<div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; 
            background-color: white; padding: 10px; border: 2px solid black; 
            border-radius: 5px; font-family: Arial; font-size: 12px;">
    <b>Легенда:</b><br>
    <span style="color: blue;">●</span> Синяя зона: уровень в начале<br>
    <span style="color: red;">●</span> Красная зона: уровень через 72 часа<br>
    <span style="color: orange;">■</span> Зона влияния шахтного сброса<br>
    <span style="color: blue;">━━</span> Русло реки
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

# 13. СОХРАНЯЕМ КАРТУ
m.save('digital_twin_map.html')
print("\n✅ Карта сохранена в файл: digital_twin_map.html")

# 14. АВТОМАТИЧЕСКИ ОТКРЫВАЕМ КАРТУ В БРАУЗЕРЕ
webbrowser.open('digital_twin_map.html')
print("Карта открыта в браузере!")

# 15. ВЫВОДИМ ИНФОРМАЦИЮ О ЗОНАХ ВЛИЯНИЯ
print("\n" + "=" * 50)
print("ЗОНЫ НАИБОЛЕЕ СИЛЬНОГО ВЛИЯНИЯ СТОРОННИХ ФАКТОРОВ")
print("=" * 50)

print("""
1. ЗОНА ШАХТНОГО СБРОСА (0-500 м ниже штольни)
   - Фактор: Техногенный сброс шахтных вод
   - Влияние: Повышение электропроводности в 1.5-2 раза
   - Эффект: Увеличение уровня воды на 0.3-0.5 м

2. ЗОНА ВЛИЯНИЯ ТЕМПЕРАТУРЫ (вся река)
   - Фактор: Суточные колебания температуры
   - Влияние: Изменение электропроводности на 10-15%
   - Эффект: Суточная вариация уровня ±0.1 м

3. ЗОНА ПОЛОВОДЬЯ (пойма реки)
   - Фактор: Таяние снега и весеннее половодье
   - Влияние: Подъем уровня на 20-30% от нормы
   - Эффект: Выход воды на пойму шириной 50-200 м
""")

print(f"\n📊 ИТОГОВАЯ ОЦЕНКА:")
print(f"   - Зона затопления в начале: {start_radius:.0f} м от русла")
print(f"   - Зона затопления в конце: {end_radius:.0f} м от русла")
print(f"   - Расширение зоны затопления: {end_radius - start_radius:.0f} м")
print(f"   - Дополнительная площадь затопления: {(end_radius**2 - start_radius**2) * 3.14 / 10000:.1f} га")
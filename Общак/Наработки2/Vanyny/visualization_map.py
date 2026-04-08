import folium
import pandas as pd
import numpy as np
from branca.colormap import linear

# Координаты точки наблюдения (Яйва, ниже штольни Калинина)
lat, lon = 59.3, 56.7  # приблизительные координаты

# Данные на начало и конец периода
df_hist = pd.read_csv("kiyazevo_iot_realistic.csv", parse_dates=["timestamp"])
start_value = df_hist.iloc[0]["ec_microsiemens"]
forecast = pd.read_csv("water_forecast_72h.csv", parse_dates=["timestamp"])
end_value = forecast.iloc[-1]["ec_forecast_microsiemens"]

# Карта
m = folium.Map(location=[lat, lon], zoom_start=12)

# Цветовая шкала
colormap = linear.YlOrRd_09.scale(3000, 5500)

# Начальное состояние
folium.CircleMarker(
    location=[lat, lon],
    radius=15,
    popup=f"Start EC: {start_value:.1f} µS/cm",
    color=colormap(start_value),
    fill=True,
    fill_color=colormap(start_value),
    fill_opacity=0.7
).add_to(m)

# Конечное состояние
folium.CircleMarker(
    location=[lat + 0.01, lon + 0.01],
    radius=15,
    popup=f"End EC (72h forecast): {end_value:.1f} µS/cm",
    color=colormap(end_value),
    fill=True,
    fill_color=colormap(end_value),
    fill_opacity=0.7
).add_to(m)

# Зоны влияния сторонних факторов (имитация: участки реки выше/ниже)
for offset, factor in [(-0.02, "Above mine"), (0.02, "Below discharge")]:
    folium.Circle(
        location=[lat + offset, lon],
        radius=200,
        popup=f"High impact zone: {factor}",
        color="red",
        fill=True,
        fill_opacity=0.2
    ).add_to(m)

colormap.add_to(m)
m.save("digital_twin_map.html")
print("Карта сохранена как digital_twin_map.html")
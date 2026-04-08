import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Загрузка данных
df = pd.read_csv("kiyazevo_iot_realistic.csv", parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)

# Используем электропроводность как основной индикатор состояния воды
# Прогноз на 72 часа (3 дня) с шагом 1 час
last_time = df.index[-1]
future_times = pd.date_range(start=last_time + pd.Timedelta(hours=1), periods=72, freq='H')

# Простая модель: тренд + сезонность (суточные колебания)
X = np.arange(len(df)).reshape(-1, 1)
y = df["ec_microsiemens"].values
model = LinearRegression()
model.fit(X, y)

# Базовый прогноз
X_future = np.arange(len(df), len(df) + 72).reshape(-1, 1)
base_forecast = model.predict(X_future)

# Климатическая коррекция (имитация данных Росгидромета: половодье)
# Весеннее половодье на р. Яйва начинается в апреле, разбавление воды снижает EC
climatic_factor = np.linspace(1.0, 0.85, 72)  # снижение на 15% из-за талых вод
corrected_forecast = base_forecast * climatic_factor

# Добавляем суточные колебания (амплитуда ~200)
hour_of_day = future_times.hour
daily_cycle = 100 * np.sin(2 * np.pi * hour_of_day / 24)
final_forecast = corrected_forecast + daily_cycle

# Оценка качества на последних 24 часах данных
train = df.iloc[:-24]
test = df.iloc[-24:]

X_train = np.arange(len(train)).reshape(-1, 1)
y_train = train["ec_microsiemens"]
model_val = LinearRegression().fit(X_train, y_train)

y_pred = model_val.predict(np.arange(len(train), len(df)).reshape(-1, 1))
mae = mean_absolute_error(test["ec_microsiemens"], y_pred)
rmse = np.sqrt(mean_squared_error(test["ec_microsiemens"], y_pred))

print(f"MAE: {mae:.2f} µS/cm")
print(f"RMSE: {rmse:.2f} µS/cm")

# Сохраняем прогноз
forecast_df = pd.DataFrame({
    "timestamp": future_times,
    "ec_forecast_microsiemens": final_forecast,
    "climatic_correction_factor": climatic_factor
})
forecast_df.to_csv("water_forecast_72h.csv", index=False)
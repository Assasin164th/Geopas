import pandas as pd
import paho.mqtt.client as mqtt
import json
import time

# Загружаем реальные данные
df = pd.read_csv("kiyazevo_iot_realistic.csv", parse_dates=["timestamp"])

# Настройки MQTT брокера (локальная эмуляция)
BROKER = "test.mosquitto.org"
TOPIC = "water/yaiva/iot"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)

# Эмуляция потоковой передачи
for _, row in df.iterrows():
    payload = {
        "timestamp": row["timestamp"].isoformat(),
        "ec_microsiemens": row["ec_microsiemens"],
        "temperature_celsius": row["temperature_celsius"],
        "sensor_id": row["sensor_id"],
        "location": row["location"]
    }
    client.publish(TOPIC, json.dumps(payload))
    print(f"Sent: {payload}")
    time.sleep(0.1)  # имитация реального времени

client.disconnect()
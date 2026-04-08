#!/usr/bin/env python3
import json
import time
import random
import pandas as pd
from datetime import datetime
import paho.mqtt.client as mqtt
import argparse
import numpy as np

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "water/yaiva/level"
MQTT_CLIENT_ID = "yaiva_sensor_01"

class WaterLevelSensor:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.data = None
        self.current_index = 0
        self.load_data()

    def load_data(self):
        try:
            self.data = pd.read_csv(self.csv_path)
            if 'timestamp' in self.data.columns:
                time_col = 'timestamp'
            elif 'datetime' in self.data.columns:
                time_col = 'datetime'
            else:
                time_col = self.data.columns[0]

            if 'water_level' in self.data.columns:
                level_col = 'water_level'
            elif 'level' in self.data.columns:
                level_col = 'level'
            else:
                level_col = self.data.columns[1]

            self.data['timestamp'] = pd.to_datetime(self.data[time_col])
            self.data['water_level'] = pd.to_numeric(self.data[level_col], errors='coerce')
            self.data = self.data.dropna(subset=['water_level'])
            print(f"✅ Загружено {len(self.data)} записей из {self.csv_path}")
        except Exception as e:
            print(f"⚠️ Не удалось загрузить {self.csv_path}: {e}. Генерируем синтетику.")
            self._generate_synthetic_data(168)

    def _generate_synthetic_data(self, n=168):
        start = datetime.now() - pd.Timedelta(hours=n)
        timestamps = [start + pd.Timedelta(hours=i) for i in range(n)]
        levels = [100 + 50 * np.sin(2*np.pi*i/24) + np.random.normal(0, 5) for i in range(n)]
        self.data = pd.DataFrame({'timestamp': timestamps, 'water_level': levels})

    def read_measurement(self):
        if self.current_index >= len(self.data):
            self.current_index = 0
        row = self.data.iloc[self.current_index]
        measurement = {
            'device_id': MQTT_CLIENT_ID,
            'timestamp': row['timestamp'].isoformat(),
            'water_level_cm': float(row['water_level']),
            'water_temperature_c': 5.0 + random.gauss(0, 1),
            'battery_voltage': 3.7 + random.gauss(0, 0.05),
            'signal_strength': random.randint(60, 99)
        }
        self.current_index += 1
        return measurement

# Исправленный callback для новой версии paho-mqtt
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ IoT-устройство подключено к MQTT брокеру")
    else:
        print(f"❌ Ошибка подключения, код {reason_code}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='kiyazevo_iot_realistic.csv')
    parser.add_argument('--interval', type=float, default=60, help='Интервал в секундах (0.1 для быстрого теста)')
    parser.add_argument('--once', action='store_true', help='Выдать все данные один раз')
    parser.add_argument('--broker', default=MQTT_BROKER)
    args = parser.parse_args()

    sensor = WaterLevelSensor(args.csv)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.connect(args.broker, MQTT_PORT, 60)
    client.loop_start()

    if args.once:
        print(f"📡 Однократная выдача {len(sensor.data)} записей...")
        for _ in range(len(sensor.data)):
            msg = sensor.read_measurement()
            payload = json.dumps(msg, ensure_ascii=False)
            client.publish(MQTT_TOPIC, payload, qos=1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Уровень: {msg['water_level_cm']:.1f} см")
        print("✅ Отправлено. Завершаем.")
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
        return

    print(f"📡 Передача с интервалом {args.interval} сек")
    try:
        while True:
            msg = sensor.read_measurement()
            payload = json.dumps(msg, ensure_ascii=False)
            client.publish(MQTT_TOPIC, payload, qos=1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Уровень: {msg['water_level_cm']:.1f} см")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Остановка")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
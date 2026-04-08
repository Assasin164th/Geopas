#!/usr/bin/env python3
"""
Симулятор IoT-датчика электропроводности (EC).
Читает реальные данные из CSV и публикует в MQTT.
"""

import json
import time
import pandas as pd
from datetime import datetime
import paho.mqtt.client as mqtt
import argparse

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC = "water/kosva/ec"
MQTT_CLIENT_ID = "kosva_sensor_01"

class ECSensor:
    def __init__(self, csv_path):
        self.data = pd.read_csv(csv_path)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.ec_col = 'ec_microsiemens'
        self.temp_col = 'temperature_celsius'
        self.idx = 0

    def read(self):
        if self.idx >= len(self.data):
            self.idx = 0  # цикл
        row = self.data.iloc[self.idx]
        msg = {
            'device_id': MQTT_CLIENT_ID,
            'timestamp': row['timestamp'].isoformat(),
            'ec_microsiemens': float(row[self.ec_col]),
            'water_temperature_c': float(row[self.temp_col]),
            'battery_v': 3.7,
            'signal': 85
        }
        self.idx += 1
        return msg

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Подключено к MQTT брокеру")
    else:
        print(f"❌ Ошибка {rc}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='kiyazevo_iot_realistic.csv')
    parser.add_argument('--interval', type=float, default=5.0, help='сек (0.5 для быстрого теста)')
    parser.add_argument('--once', action='store_true', help='выдать все данные и выйти')
    args = parser.parse_args()

    sensor = ECSensor(args.csv)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    if args.once:
        print(f"📡 Однократная отправка {len(sensor.data)} записей...")
        for _ in range(len(sensor.data)):
            msg = sensor.read()
            client.publish(MQTT_TOPIC, json.dumps(msg), qos=1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] EC={msg['ec_microsiemens']:.0f} мкСм/см")
        client.loop_stop()
        client.disconnect()
        return

    print(f"📡 Передача каждые {args.interval} сек. Прерывание Ctrl+C")
    try:
        while True:
            msg = sensor.read()
            client.publish(MQTT_TOPIC, json.dumps(msg), qos=1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] EC={msg['ec_microsiemens']:.0f} мкСм/см")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Остановка по запросу")
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
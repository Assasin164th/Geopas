#!/usr/bin/env python3
"""
Симулятор IoT-датчика EC с автоматическим выбором MQTT брокера
и возможностью работы без MQTT (просто вывод в консоль).
"""

import json
import time
import pandas as pd
from datetime import datetime
import argparse

# Список публичных MQTT брокеров (пробуем по порядку)
BROKERS = [
    ("mqtt.eclipseprojects.io", 1883),
    ("broker.emqx.io", 1883),
    ("test.mosquitto.org", 1883),
    ("broker.hivemq.com", 1883)
]

MQTT_TOPIC = "water/kosva/ec"
MQTT_CLIENT_ID = "kosva_sensor_01"

class ECSensor:
    def __init__(self, csv_path):
        self.data = pd.read_csv(csv_path)
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        self.idx = 0

    def read(self):
        if self.idx >= len(self.data):
            self.idx = 0
        row = self.data.iloc[self.idx]
        msg = {
            'device_id': MQTT_CLIENT_ID,
            'timestamp': row['timestamp'].isoformat(),
            'ec_microsiemens': float(row['ec_microsiemens']),
            'water_temperature_c': float(row['temperature_celsius']),
            'battery_v': 3.7,
            'signal': 85
        }
        self.idx += 1
        return msg

def try_connect_mqtt():
    """Пробует подключиться к одному из брокеров."""
    for broker, port in BROKERS:
        try:
            import paho.mqtt.client as mqtt
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, MQTT_CLIENT_ID)
            client.connect(broker, port, timeout=5)
            print(f"Подключено к MQTT брокеру {broker}:{port}")
            return client
        except Exception as e:
            print(f"Не удалось подключиться к {broker}: {e}")
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default='kiyazevo_iot_realistic.csv')
    parser.add_argument('--interval', type=float, default=2.0, help='Интервал в секундах')
    parser.add_argument('--once', action='store_true', help='Однократная отправка всех данных')
    parser.add_argument('--no-mqtt', action='store_true', help='Только вывод в консоль, без MQTT')
    args = parser.parse_args()

    sensor = ECSensor(args.csv)
    client = None
    
    if not args.no_mqtt:
        client = try_connect_mqtt()
        if client:
            client.loop_start()
        else:
            print("MQTT не работает. Переключаемся в режим только консольного вывода.")
            args.no_mqtt = True

    if args.once:
        print(f"Однократная отправка {len(sensor.data)} записей...")
        for _ in range(len(sensor.data)):
            msg = sensor.read()
            if client:
                client.publish(MQTT_TOPIC, json.dumps(msg), qos=1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] EC={msg['ec_microsiemens']:.0f} мкСм/см")
        if client:
            client.loop_stop()
            client.disconnect()
        return

    print(f"Передача каждые {args.interval} сек. Ctrl+C для остановки.")
    try:
        while True:
            msg = sensor.read()
            if client:
                client.publish(MQTT_TOPIC, json.dumps(msg), qos=1)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] EC={msg['ec_microsiemens']:.0f} мкСм/см")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nОстановка.")
        if client:
            client.loop_stop()
            client.disconnect()

if __name__ == "__main__":
    main()
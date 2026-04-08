#!/usr/bin/env python3
"""
mqtt_subscriber.py
Подписчик MQTT, сохраняет полученные данные в CSV.
"""
import json
import pandas as pd
import paho.mqtt.client as mqtt
import argparse
from datetime import datetime

MQTT_TOPIC = "water/yaiva/level"

class DataCollector:
    def __init__(self):
        self.data = []
    def add(self, msg):
        self.data.append(msg)
    def to_df(self):
        return pd.DataFrame(self.data)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    userdata['collector'].add(payload)
    print(f"Получено: уровень {payload['water_level_cm']:.1f} см")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--broker', default='test.mosquitto.org')
    parser.add_argument('--output', default='received_data.csv')
    args = parser.parse_args()

    collector = DataCollector()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.user_data_set({'collector': collector})
    client.on_message = on_message
    client.connect(args.broker, 1883, 60)
    client.subscribe(MQTT_TOPIC)
    print(f"Подписан на {MQTT_TOPIC}, сохраняем в {args.output}")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        df = collector.to_df()
        df.to_csv(args.output, index=False)
        print(f"Сохранено {len(df)} записей")
        client.disconnect()

if __name__ == "__main__":
    main()
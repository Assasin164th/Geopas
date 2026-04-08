# ============================================
# ЦИФРОВОЙ ДВОЙНИК: ПОДПИСЧИК ДАННЫХ IoT
# ============================================
# Задача: Получение данных от датчика через MQTT
# Роль: Модель прогноза / База данных / GIS система

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

print("=" * 60)
print("ЦИФРОВОЙ ДВОЙНИК - ПОДПИСЧИК ДАННЫХ IoT")
print("=" * 60)

# Настройки (должны совпадать с публикатором)
BROKER_HOST = "broker.emqx.io"
BROKER_PORT = 1883
TOPIC = "geopas/kiyazevo/water/sensor1"

print(f"\n📡 НАСТРОЙКИ:")
print(f"   Брокер: {BROKER_HOST}:{BROKER_PORT}")
print(f"   Топик: {TOPIC}")

# Счетчики
received_count = 0
data_buffer = []

def on_connect(client, userdata, flags, reason_code, properties):
    """Подключение к брокеру"""
    if reason_code == 0:
        print(f"\n✅ ПОДКЛЮЧЕНО к брокеру")
        # Подписываемся на топик
        client.subscribe(TOPIC, qos=1)
        print(f"📡 Подписались на топик: {TOPIC}")
    else:
        print(f"\n❌ Ошибка подключения: {reason_code}")

def on_message(client, userdata, msg):
    """Обработка входящего сообщения от датчика"""
    global received_count, data_buffer
    
    try:
        # Декодируем JSON
        payload = json.loads(msg.payload.decode('utf-8'))
        received_count += 1
        
        # Извлекаем данные
        timestamp = payload['timestamp']
        ec = payload['measurements']['ec_microsiemens']
        temp = payload['measurements']['temperature_celsius']
        sensor_id = payload['sensor_id']
        
        # Выводим информацию
        print(f"\n📥 [{received_count}] {timestamp}")
        print(f"   Датчик: {sensor_id}")
        print(f"   EC: {ec:.1f} µS/cm")
        print(f"   Температура: {temp:.1f}°C")
        
        # Сохраняем в буфер (можно сохранять в базу данных)
        data_buffer.append({
            'timestamp': timestamp,
            'ec': ec,
            'temperature': temp
        })
        
        # Здесь можно вызывать модель прогноза
        # forecast_model.update(ec, temp)
        
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка декодирования JSON: {e}")
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    """Отключение от брокера"""
    print(f"\n🔌 Отключено от брокера")

# Создаем клиента
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Назначаем обработчики
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Подключаемся
print("\n🔄 ПОДКЛЮЧЕНИЕ...")
try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever()  # Бесконечный цикл приема сообщений
except KeyboardInterrupt:
    print("\n\n⏹️ Остановка подписчика...")
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
finally:
    print(f"\n📊 ИТОГО ПОЛУЧЕНО: {received_count} сообщений")
    client.disconnect()
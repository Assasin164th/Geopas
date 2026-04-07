# ============================================
# СИМУЛЯЦИЯ ПЕРЕДАЧИ ДАННЫХ С IoT ЧЕРЕЗ MQTT
# (ВЕРСИЯ С ОБРАБОТКОЙ ОШИБОК)
# ============================================

import pandas as pd
import time
import json
from datetime import datetime
import sys

print("=" * 50)
print("СИМУЛЯЦИЯ ПЕРЕДАЧИ ДАННЫХ IoT")
print("=" * 50)

# 1. ПРОВЕРЯЕМ НАЛИЧИЕ ФАЙЛА
print("\nШаг 1: Проверка файла с данными...")
try:
    df = pd.read_csv('kiyazevo_iot_realistic.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"✅ Загружено {len(df)} записей")
except FileNotFoundError:
    print("❌ Файл kiyazevo_iot_realistic.csv не найден!")
    sys.exit(1)

# 2. ПРОБУЕМ ПОДКЛЮЧИТЬ MQTT
print("\nШаг 2: Попытка подключения к MQTT брокеру...")

try:
    import paho.mqtt.client as mqtt
    
    # Исправляем предупреждение о версии API
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    
    # Используем другой брокер (более стабильный)
    BROKER_HOST = "broker.emqx.io"  # альтернативный публичный брокер
    BROKER_PORT = 1883
    TOPIC = "iot/kiyazevo/water"
    
    print(f"   Брокер: {BROKER_HOST}:{BROKER_PORT}")
    print(f"   Топик: {TOPIC}")
    
    # Функции-обработчики
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Успешно подключено к брокеру!")
        else:
            print(f"❌ Ошибка подключения, код: {rc}")
    
    client.on_connect = on_connect
    
    # Пытаемся подключиться с таймаутом 5 секунд
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    time.sleep(2)
    
    MQTT_AVAILABLE = True
    print("✅ MQTT готов к работе")
    
except ImportError:
    print("⚠️ Библиотека paho-mqtt не установлена")
    print("   Установите: pip install paho-mqtt")
    MQTT_AVAILABLE = False
except Exception as e:
    print(f"⚠️ MQTT недоступен: {e}")
    print("   Будет использована симуляция без реальной отправки")
    MQTT_AVAILABLE = False

# 3. СИМУЛЯЦИЯ ПЕРЕДАЧИ ДАННЫХ
print("\n" + "=" * 50)
print("ШАГ 3: СИМУЛЯЦИЯ ПЕРЕДАЧИ ДАННЫХ")
print("=" * 50)

if MQTT_AVAILABLE:
    print("Режим: РЕАЛЬНАЯ отправка через MQTT")
else:
    print("Режим: СИМУЛЯЦИЯ (отправка в консоль)")

print("\nНачало передачи данных...")
print("-" * 50)

# Перебираем все записи
for index, row in df.iterrows():
    # Формируем сообщение
    message = {
        "timestamp": row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
        "ec_microsiemens": float(row['ec_microsiemens']),
        "temperature_celsius": float(row['temperature_celsius']),
        "sensor_id": row['sensor_id'],
        "location": row['location']
    }
    
    payload = json.dumps(message, ensure_ascii=False)
    
    # Отправляем или симулируем
    if MQTT_AVAILABLE:
        try:
            result = client.publish(TOPIC, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status = "✅"
            else:
                status = "⚠️"
        except:
            status = "❌"
    else:
        status = "📝"
    
    # Выводим информацию
    print(f"{status} [{index+1}/{len(df)}] {row['timestamp']} | EC={row['ec_microsiemens']:.1f} | T={row['temperature_celsius']:.1f}°C")
    
    # Задержка между сообщениями
    time.sleep(0.05)  # быстро для демо

# 4. ЗАВЕРШЕНИЕ
print("\n" + "=" * 50)
print("ПЕРЕДАЧА ЗАВЕРШЕНА")
print("=" * 50)

if MQTT_AVAILABLE:
    client.loop_stop()
    client.disconnect()
    print("Отключено от брокера")
    
    # Выводим статистику
    print(f"\n📊 Статистика передачи:")
    print(f"   Всего записей: {len(df)}")
    print(f"   Брокер: {BROKER_HOST}")
    print(f"   Топик: {TOPIC}")
else:
    print("\n📌 ВАЖНО:")
    print("   MQTT не использовался, но это не критично.")
    print("   Для демонстрации достаточно показать код и объяснить выбор брокера.")

print("\n💡 Для презентации:")
print("   - Покажите этот код как пример симуляции передачи данных")
print("   - Объясните, что выбран брокер EMQX (стабильный, публичный)")
print("   - Аргументируйте: MQTT легкий, pub-sub, работает при плохой связи")
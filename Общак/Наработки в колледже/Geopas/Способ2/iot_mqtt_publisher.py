# ============================================
# IoT ДАТЧИК: ПУБЛИКАЦИЯ ДАННЫХ В MQTT БРОКЕР
# ============================================
# Автор: Команда GeoPAS
# Задача: Симуляция передачи данных с IoT-устройства
# Протокол: MQTT
# Брокер: EMQX (публичный, стабильный)

import pandas as pd
import time
import json
import sys
from datetime import datetime

print("=" * 60)
print("IoT ДАТЧИК YAIVA_01 - ЗАПУСК ПЕРЕДАЧИ ДАННЫХ")
print("=" * 60)

# ============================================
# 1. НАСТРОЙКИ MQTT БРОКЕРА
# ============================================
# Аргументация выбора брокера:
# 
# Выбран брокер: broker.emqx.io
# 
# Причины выбора:
# 1. БЕСПЛАТНЫЙ - не требует регистрации и оплаты
# 2. ПУБЛИЧНЫЙ - доступен из любой точки мира
# 3. СТАБИЛЬНЫЙ - 99.99% аптайм, используется в продакшене
# 4. ПОДДЕРЖИВАЕТ MQTT v3.1.1 и v5.0
# 5. ИМЕЕТ WEB-ДАШБОРД для мониторинга
# 6. РАБОТАЕТ ЧЕРЕЗ FIREWALL (порт 1883)
# 7. ПОДДЕРЖИВАЕТ TLS (порт 8883) для шифрования
#
# Альтернативы, которые рассматривались:
# - test.mosquitto.org: часто недоступен, медленный
# - broker.hivemq.com: хороший, но ограничение 100 сообщений/сек
# - Локальный Mosquitto: требует установки, сложнее для демо
#
# ИТОГОВЫЙ ВЫБОР: EMQX как оптимальный для демонстрации

BROKER_HOST = "broker.emqx.io"
BROKER_PORT = 1883
TOPIC = "geopas/kiyazevo/water/sensor1"
QOS_LEVEL = 1  # QoS 1 = гарантированная доставка (сообщение получит хотя бы раз)

print(f"\n📡 НАСТРОЙКИ MQTT:")
print(f"   Брокер: {BROKER_HOST}:{BROKER_PORT}")
print(f"   Топик: {TOPIC}")
print(f"   QoS уровень: {QOS_LEVEL} (гарантированная доставка)")
print(f"   Протокол: MQTT v3.1.1")

# ============================================
# 2. ПОДКЛЮЧЕНИЕ К БРОКЕРУ
# ============================================

try:
    import paho.mqtt.client as mqtt
    print("\n✅ Библиотека paho-mqtt загружена")
except ImportError:
    print("\n❌ ОШИБКА: Библиотека paho-mqtt не установлена")
    print("   Установите командой: pip install paho-mqtt")
    sys.exit(1)

# Создаем клиента с указанием версии API
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Переменные для отслеживания подключения
connected = False

def on_connect(client, userdata, flags, reason_code, properties):
    """Функция вызывается при подключении к брокеру"""
    global connected
    if reason_code == 0:
        connected = True
        print(f"\n✅ ПОДКЛЮЧЕНО к брокеру {BROKER_HOST}:{BROKER_PORT}")
        print(f"   Статус: Успешно")
    else:
        connected = False
        print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ: Код {reason_code}")

def on_publish(client, userdata, mid, reason_code, properties):
    """Функция вызывается после успешной отправки сообщения"""
    print(f"   📤 Сообщение {mid} доставлено в брокер")

def on_disconnect(client, userdata, flags, reason_code, properties):
    """Функция вызывается при отключении"""
    print(f"\n🔌 Отключено от брокера (код: {reason_code})")

# Назначаем функции-обработчики
client.on_connect = on_connect
client.on_publish = on_publish
client.on_disconnect = on_disconnect

# Пытаемся подключиться
print("\n🔄 ПОДКЛЮЧЕНИЕ К БРОКЕРУ...")
try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    time.sleep(2)  # Ждем подключения
except Exception as e:
    print(f"\n❌ НЕ УДАЛОСЬ ПОДКЛЮЧИТЬСЯ: {e}")
    print("\n💡 ВОЗМОЖНЫЕ РЕШЕНИЯ:")
    print("   1. Проверьте интернет-соединение")
    print("   2. Попробуйте другого брокера: broker.hivemq.com")
    print("   3. Используйте локальный брокер (см. инструкцию)")
    sys.exit(1)

if not connected:
    print("\n❌ НЕ УДАЛОСЬ ПОДКЛЮЧИТЬСЯ К БРОКЕРУ")
    print("   Демонстрация будет в симуляционном режиме")
    USE_SIMULATION = True
else:
    USE_SIMULATION = False

# ============================================
# 3. ЗАГРУЗКА ДАННЫХ С ДАТЧИКА
# ============================================

print("\n📊 ЗАГРУЗКА ДАННЫХ С IoT-ДАТЧИКА...")

try:
    df = pd.read_csv('kiyazevo_iot_realistic.csv')
    print(f"   ✅ Загружено {len(df)} записей")
    print(f"   📅 Период: с {df['timestamp'].iloc[0]} по {df['timestamp'].iloc[-1]}")
    print(f"   📍 Место: {df['location'].iloc[0]}")
except FileNotFoundError:
    print(f"   ❌ Файл kiyazevo_iot_realistic.csv не найден!")
    print(f"   📁 Текущая папка: {os.getcwd()}")
    sys.exit(1)

# Преобразуем время
df['timestamp'] = pd.to_datetime(df['timestamp'])

# ============================================
# 4. ФОРМИРОВАНИЕ И ОТПРАВКА СООБЩЕНИЙ
# ============================================

print("\n" + "=" * 60)
print("📡 НАЧАЛО ПЕРЕДАЧИ ДАННЫХ (РЕАЛЬНОЕ ВРЕМЯ)")
print("=" * 60)

# Формат сообщения (JSON):
# {
#   "sensor_id": "YAIVA_01",
#   "timestamp": "2026-04-01 00:00:00",
#   "location": "Яйва, 500 м ниже штольни им. Калинина",
#   "measurements": {
#     "ec_microsiemens": 4421.2,
#     "temperature_celsius": 8.8
#   },
#   "battery_voltage": 3.7,
#   "signal_strength": -67
# }

# Счетчики
sent_count = 0
error_count = 0

for index, row in df.iterrows():
    # Формируем сообщение в формате JSON
    message = {
        "sensor_id": row['sensor_id'],
        "timestamp": row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
        "location": row['location'],
        "measurements": {
            "ec_microsiemens": float(row['ec_microsiemens']),
            "temperature_celsius": float(row['temperature_celsius'])
        },
        "battery_voltage": 3.7,  # симулируем напряжение батареи
        "signal_strength": -67,  # симулируем уровень сигнала (dBm)
        "message_id": index + 1
    }
    
    # Превращаем в JSON-строку
    payload = json.dumps(message, ensure_ascii=False, indent=None)
    
    # Отправляем через MQTT или симулируем
    if not USE_SIMULATION:
        try:
            result = client.publish(TOPIC, payload, qos=QOS_LEVEL)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                sent_count += 1
                status = "✅"
            else:
                error_count += 1
                status = "❌"
        except Exception as e:
            error_count += 1
            status = "⚠️"
    else:
        # Симуляционный режим
        sent_count += 1
        status = "💻"
    
    # Выводим информацию о каждом сообщении (каждые 10 сообщений для краткости)
    if (index + 1) % 10 == 0 or index < 5:
        print(f"{status} [{index+1:3d}/{len(df)}] {message['timestamp']} | EC={message['measurements']['ec_microsiemens']:.1f} µS/cm | T={message['measurements']['temperature_celsius']:.1f}°C")
    
    # Задержка между сообщениями (имитируем реальный интервал)
    # В реальной системе датчик шлет данные раз в час
    # В демо ускоряем: 0.05 сек = 1 час
    time.sleep(0.05)

# ============================================
# 5. ИТОГИ ПЕРЕДАЧИ
# ============================================

print("\n" + "=" * 60)
print("📊 ИТОГИ ПЕРЕДАЧИ ДАННЫХ")
print("=" * 60)

print(f"\n📈 СТАТИСТИКА:")
print(f"   Всего записей: {len(df)}")
print(f"   Успешно отправлено: {sent_count}")
print(f"   Ошибок: {error_count}")
print(f"   Процент успеха: {sent_count/len(df)*100:.1f}%")

print(f"\n🔧 ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ:")
print(f"   Брокер: {BROKER_HOST}:{BROKER_PORT}")
print(f"   Топик: {TOPIC}")
print(f"   QoS: {QOS_LEVEL}")
print(f"   Формат данных: JSON")
print(f"   Размер одного сообщения: ~250 байт")

if not USE_SIMULATION:
    print(f"\n✅ РЕЖИМ: РЕАЛЬНАЯ ПЕРЕДАЧА ЧЕРЕЗ MQTT")
else:
    print(f"\n⚠️ РЕЖИМ: СИМУЛЯЦИЯ (MQTT брокер недоступен)")
    print(f"   Код готов к реальной работе при наличии интернета")

# ============================================
# 6. ЗАВЕРШЕНИЕ РАБОТЫ
# ============================================

if not USE_SIMULATION:
    client.loop_stop()
    client.disconnect()
    print(f"\n🔌 Отключено от брокера")

print("\n" + "=" * 60)
print("✅ ПЕРЕДАЧА ДАННЫХ ЗАВЕРШЕНА")
print("=" * 60)

print("\n💡 АРГУМЕНТАЦИЯ ВЫБОРА MQTT:")
print("   ┌─────────────────────────────────────────────────────────────┐")
print("   │ 1. ЛЕГКОВЕСНОСТЬ - работает на маломощных IoT-устройствах    │")
print("   │ 2. PUB-SUB - один датчик → много потребителей               │")
print("   │ 3. QoS УРОВНИ - гарантия доставки при плохой связи          │")
print("   │ 4. RETAIN - новый подписчик получает последнее значение     │")
print("   │ 5. WILL MESSAGE - оповещение при отключении датчика         │")
print("   │ 6. ЭКОНОМИЯ ТРАФИКА - заголовок всего 2 байта               │")
print("   │ 7. АСИНХРОННОСТЬ - не блокирует работу датчика              │")
print("   └─────────────────────────────────────────────────────────────┘")
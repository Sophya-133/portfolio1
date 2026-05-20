import paho.mqtt.client as mqtt
import csv
import time
from datetime import datetime
import random

# --- Конфигурация ---
MQTT_BROKER = "broker.hivemq.com"  # Публичный MQTT-брокер
MQTT_PORT = 1883
MQTT_TOPIC = "home/sensor/dht11"   # Топик для данных датчика
CSV_FILE = "dht11_readings.csv"

# Функция: запись данных в CSV
def log_to_csv(temperature, humidity, timestamp):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Записываем заголовок, если файл пуст
        if file.tell() == 0:
            writer.writerow(["Timestamp", "Temperature (°C)", "Humidity (%)"])
        writer.writerow([timestamp, temperature, humidity])
    print(f"[LOG] Записано: {timestamp} | {temperature}°C | {humidity}%")

# Функция: обработка приходящего сообщения
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        temp, hum = map(float, payload.split(","))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_to_csv(temp, hum, timestamp)
    except Exception as e:
        print(f"[ERROR] Неверный формат данных: {message.payload}, ошибка: {e}")

# Функция: подключение к MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[INFO] Успешное подключение к MQTT-брокеру")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[ERROR] Ошибка подключения: {rc}")

# Создаем клиент MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Подключаемся
print(f"[INFO] Подключение к MQTT-брокеру {MQTT_BROKER}...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Запускаем цикл обработки сообщений в фоне
client.loop_start()

print("[INFO] Ожидание данных от датчика DHT11... (нажмите Ctrl+C для остановки)")

# Основной цикл — можно использовать для отправки симулированных данных
# (в реальности данные приходят от датчика, здесь мы просто ждём)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[INFO] Остановка клиента...")
    client.loop_stop()
    client.disconnect()
    print("[INFO] Соединение закрыто.")

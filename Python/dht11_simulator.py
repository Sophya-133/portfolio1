import paho.mqtt.client as mqtt
import time
import random

MQTT_BROKER = "broker.hivemq.com"
MQTT_TOPIC = "home/sensor/dht11"

client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)

print("[SIMULATOR] Запущен симулятор DHT11...")

while True:
    temp = round(20 + random.random() * 10, 1)   # 20–30°C
    hum = round(40 + random.random() * 30, 1)    # 40–70%
    payload = f"{temp},{hum}"
    client.publish(MQTT_TOPIC, payload)
    print(f"[SEND] {payload}")
    time.sleep(10)

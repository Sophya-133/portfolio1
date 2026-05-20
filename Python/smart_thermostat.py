import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from datetime import datetime

# --- Конфигурация ---
TARGET_MIN = 18    # Минимальная комфортная температура
TARGET_MAX = 24    # Максимальная комфортная температура
READ_INTERVAL = 5  # Интервал чтения датчика (сек)

# --- Глобальные состояния ---
current_temp = 22.0
heater_on = False
log_file = "thermostat_log.txt"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- Симуляция датчика температуры ---
def read_temperature():
    """Симулирует чтение температуры с датчика (с небольшой случайной вариацией)"""
    global current_temp
    variation = random.uniform(-0.5, 0.5)
    current_temp += variation
    # Ограничиваем температуру в разумных пределах
    current_temp = max(10, min(35, current_temp))
    return round(current_temp, 1)

# --- Управление обогревателем ---
def control_heater():
    global heater_on
    temp = read_temperature()
    if temp < TARGET_MIN and not heater_on:
        heater_on = True
        logging.info(f"🌡️ Обогреватель ВКЛЮЧЕН. Температура: {temp}°C")
    elif temp > TARGET_MAX and heater_on:
        heater_on = False
        logging.info(f"🌡️ Обогреватель ВЫКЛЮЧЕН. Температура: {temp}°C")

# --- Фоновый цикл чтения и управления ---
def thermostat_loop():
    while True:
        control_heater()
        time.sleep(READ_INTERVAL)

# --- HTTP-сервер для получения статуса ---
class ThermostatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "temperature": current_temp,
                "heater_on": heater_on,
                "target_min": TARGET_MIN,
                "target_max": TARGET_MAX
            }
            self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def start_http_server():
    server = HTTPServer(('localhost', 5000), ThermostatHandler)
    print("🌐 HTTP-сервер запущен на http://localhost:5000/status")
    server.serve_forever()

# --- Запуск ---
if __name__ == "__main__":
    print("🚀 Запуск умного термостата IoT...")
    
    # Запускаем фоновый цикл термостата
    thermostat_thread = threading.Thread(target=thermostat_loop, daemon=True)
    thermostat_thread.start()
    
    # Запускаем HTTP-сервер
    start_http_server()

import time
import random
import threading
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import urllib.parse

# ==================== КОНФИГУРАЦИЯ ====================
TARGET_MIN_DEFAULT = 18
TARGET_MAX_DEFAULT = 24
SIMULATION_INTERVAL = 5  # секунд
WEATHER_API = "https://wttr.in/?format=%t"
WEATHER_FALLBACK = 15  # °C — значение по умолчанию, если погода недоступна
LOG_FILE = "smart_thermostat_log.txt"

# Глобальные переменные состояния
room_temperature = 21.0
heater_on = False
target_min = TARGET_MIN_DEFAULT
target_max = TARGET_MAX_DEFAULT
is_energy_saving_mode = True  # включено по умолчанию

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ==================== HTML-Интерфейс  ====================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Умный термостат</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        .status { font-size: 1.2em; margin: 15px 0; }
        .btn { padding: 12px 20px; margin: 5px; border: none; border-radius: 6px; cursor: pointer; font-size: 1em; }
        .btn-on { background: #4CAF50; color: white; }
        .btn-off { background: #f44336; color: white; }
        .btn-toggle { background: #2196F3; color: white; }
        .weather { font-weight: bold; color: #d35400; }
        .tariff { font-weight: bold; color: #8e44ad; }
        .log { margin-top: 30px; font-size: 0.9em; color: #666; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🌡️ Умный термостат</h1>

        <div class="status">
            <strong>Температура в комнате:</strong> <span id="room-temp">--</span>°C
        </div>
        <div class="status">
            <strong>Внешняя температура:</strong> <span id="outdoor-temp" class="weather">--</span>
        </div>
        <div class="status">
            <strong>Цель:</strong> <span id="target-range">--</span>°C
        </div>
        <div class="status">
            <strong>Обогреватель:</strong> <span id="heater-status">--</span>
        </div>
        <div class="status">
            <strong>Тариф:</strong> <span id="tariff-status" class="tariff">--</span>
        </div>
        <div class="status">
            <strong>Режим энергосбережения:</strong> <span id="saving-status">--</span>
        </div>

        <div>
            <button id="btn-heater" class="btn">ВКЛ/ВЫКЛ обогрев</button>
            <button id="btn-saving" class="btn btn-toggle">Переключить энергосбережение</button>
        </div>

        <div>
          <button id="btn-cooler" 
        </div>

        <div class="log">
            <h3>Логи</h3>
            <pre id="log-output" style="height: 150px; overflow-y: scroll; background: #eee; padding: 10px; border-radius: 5px;"></pre>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/status')
                .then(r => {
                    if (!r.ok) throw new Error('HTTP ' + r.status);
                    return r.json();
                })
                .then(data => {
                    document.getElementById('room-temp').textContent = data.room_temperature;
                    document.getElementById('outdoor-temp').textContent = data.outdoor_temperature !== null ? data.outdoor_temperature + '°C' : '<span class="error">Погода недоступна</span>';
                    document.getElementById('target-range').textContent = data.target_min + '–' + data.target_max;
                    document.getElementById('heater-status').textContent = data.heater_on ? '✅ ВКЛЮЧЕН' : '❌ ВЫКЛЮЧЕН';
                    document.getElementById('heater-status').style.color = data.heater_on ? '#4CAF50' : '#f44336';
                    document.getElementById('tariff-status').textContent = data.is_low_tariff ? '💰 Дешёвый' : '💸 Дорогой';
                    document.getElementById('saving-status').textContent = data.energy_saving_mode ? '✅ ВКЛЮЧЕН' : '❌ ВЫКЛЮЧЕН';

                    // Кнопка обогрева
                    const btn = document.getElementById('btn-heater');
                    btn.textContent = data.heater_on ? '❌ ВЫКЛЮЧИТЬ обогрев' : '✅ ВКЛЮЧИТЬ обогрев';
                    btn.className = 'btn ' + (data.heater_on ? 'btn-off' : 'btn-on');

                    // Лог
                    const log = document.getElementById('log-output');
                    log.textContent = 'Обновлено: ' + new Date().toLocaleTimeString() + '\\n' + log.textContent;
                })
                .catch(err => {
                    console.error('Ошибка:', err);
                    document.getElementById('room-temp').textContent = 'Ошибка';
                    document.getElementById('outdoor-temp').innerHTML = '<span class="error">Ошибка сети</span>';
                });
        }

        // Кнопки
        document.getElementById('btn-heater').addEventListener('click', () => {
            fetch('/control?action=' + (document.getElementById('heater-status').textContent.includes('ВКЛЮЧЕН') ? 'off' : 'on'))
                .then(() => updateStatus());
        });

        document.getElementById('btn-saving').addEventListener('click', () => {
            fetch('/control?action=toggle_saving')
                .then(() => updateStatus());
        });

        // Автообновление каждые 5 сек
        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
"""

# ==================== ФУНКЦИИ ====================

def get_outdoor_temperature():
    """Получает температуру с wttr.in, с fallback на значение по умолчанию"""
    try:
        response = requests.get(WEATHER_API, timeout=5)
        if response.status_code == 200:
            temp_str = response.text.strip().replace('°C', '').replace('+', '')
            return float(temp_str)
        else:
            logging.warning(f"⚠️ wttr.in вернул код {response.status_code}, используем fallback")
    except requests.exceptions.Timeout:
        logging.warning("❌ Таймаут при запросе погоды (wttr.in)")
    except requests.exceptions.RequestException as e:
        logging.warning(f"❌ Ошибка запроса погоды: {e}")
    except ValueError:
        logging.warning("❌ Невозможно распарсить температуру с wttr.in")

    # Если всё сломалось — возвращаем fallback
    logging.info(f"🌤️ Используем запасную температуру: {WEATHER_FALLBACK}°C")
    return WEATHER_FALLBACK

def adjust_target_by_weather():
    global target_min, target_max
    outdoor_temp = get_outdoor_temperature()
    logging.info(f"🌡️ Внешняя температура: {outdoor_temp}°C")

    if outdoor_temp <= 0:
        target_min = TARGET_MIN_DEFAULT + 1
        target_max = TARGET_MAX_DEFAULT + 1
        logging.info("❄️ Холодно на улице — цель повышена до {}–{}°C".format(target_min, target_max))
    elif outdoor_temp >= 25:
        target_min = TARGET_MIN_DEFAULT - 1
        target_max = TARGET_MAX_DEFAULT - 1
        logging.info("☀️ Тепло на улице — цель снижена до {}–{}°C".format(target_min, target_max))
    else:
        target_min = TARGET_MIN_DEFAULT
        target_max = TARGET_MAX_DEFAULT
        logging.info("🌤️ Нормальная погода — цель: {}–{}°C".format(target_min, target_max))

def simulate_temperature():
    global room_temperature, heater_on
    while True:
        time.sleep(SIMULATION_INTERVAL)
        delta = random.uniform(-0.3, 0.3)
        room_temperature += delta
        if heater_on:
            room_temperature += 0.2
        room_temperature = max(10, min(35, room_temperature))
        status = "ВКЛЮЧЕН" if heater_on else "ВЫКЛЮЧЕН"
        logging.info(f"🌡️ Комнатная температура: {room_temperature:.1f}°C | Обогреватель: {status}")

def control_heater():
    global heater_on
    while True:
        time.sleep(2)
        current_hour = datetime.now().hour
        is_low_tariff = (current_hour >= 22) or (current_hour < 6)
        should_turn_on = room_temperature < target_min and (not is_energy_saving_mode or is_low_tariff)
        should_turn_off = room_temperature > target_max

        if should_turn_on and not heater_on:
            heater_on = True
            tariff_status = "дешёвый" if is_low_tariff else "дорогой"
            logging.info(f"🔥 Обогреватель ВКЛЮЧЕН (температура: {room_temperature:.1f}°C, тариф: {tariff_status})")
        elif should_turn_off and heater_on:
            heater_on = False
            logging.info(f"❄️ Обогреватель ВЫКЛЮЧЕН (температура: {room_temperature:.1f}°C)")

def update_weather_periodically():
    while True:
        time.sleep(15 * 60)
        adjust_target_by_weather()

# ==================== HTTP-СЕРВЕР ====================

class ThermostatHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global heater_on, is_energy_saving_mode

        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "room_temperature": round(room_temperature, 1),
                "heater_on": heater_on,
                "target_min": target_min,
                "target_max": target_max,
                "outdoor_temperature": get_outdoor_temperature(),  # Безопасно — с fallback
                "is_low_tariff": (datetime.now().hour >= 22 or datetime.now().hour < 6),
                "energy_saving_mode": is_energy_saving_mode
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode("utf-8"))
        elif self.path.startswith("/control?"):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            action = params.get("action", [""])[0]

            if action == "on":
                heater_on = True
                logging.info("🔌 Обогреватель ВКЛЮЧЕН через веб-интерфейс")
            elif action == "off":
                heater_on = False
                logging.info("🔌 Обогреватель ВЫКЛЮЧЕН через веб-интерфейс")
            elif action == "toggle_saving":
                is_energy_saving_mode = not is_energy_saving_mode
                logging.info(f"⚡ Энергосбережение {'ВКЛЮЧЕНО' if is_energy_saving_mode else 'ВЫКЛЮЧЕНО'} через веб-интерфейс")

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "action": action}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    print("🚀 Запуск умного термостата IoT с веб-интерфейсом...")
    print("🌐 Откройте в браузере: http://localhost:5000")

    # Запускаем фоновые потоки
    threading.Thread(target=simulate_temperature, daemon=True).start()
    threading.Thread(target=control_heater, daemon=True).start()
    threading.Thread(target=update_weather_periodically, daemon=True).start()

    # Сразу обновим погоду при запуске
    adjust_target_by_weather()

    # Запускаем HTTP-сервер
    server = HTTPServer(('localhost', 5000), ThermostatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Остановка термостата...")
        server.shutdown()

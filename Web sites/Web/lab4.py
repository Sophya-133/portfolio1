from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import datetime
import json

# ==============================================================================
# 1. МНОГОСТРОЧНЫЕ СТРОКИ (Весь сайт внутри Python)
# ==============================================================================

# --- HTML (Скелет страницы умного дома) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Умный дом "Нейро-Дом"</title>
    <style>{css}</style>
</head>
<body>
    <header>
        <div class="logo">Нейро-Дом</div>
        <div class="status-indicator" id="status-indicator">● Система онлайн</div>
    </header>

    <main>
        <section class="dashboard">
            
            <!-- Виджет освещения -->
            <div class="card">
                <h2>Освещение</h2>
                <div class="toggle-group">
                    <button class="toggle-btn" data-room="living" onclick="toggleLight('living')">Зал</button>
                    <button class="toggle-btn" data-room="kitchen" onclick="toggleLight('kitchen')">Кухня</button>
                    <button class="toggle-btn" data-room="bedroom" onclick="toggleLight('bedroom')">Спальня</button>
                </div>
                <div class="brightness-slider">
                    <label>Яркость: <span id="brightness-val">80</span>%</label>
                    <input type="range" min="0" max="100" value="80" id="brightness-range" oninput="updateBrightness()">
                </div>
            </div>

            <!-- Виджет климата -->
            <div class="card">
                <h2>Климат</h2>
                <div class="temp-display">
                    <span id="temp-val">22</span>°C
                </div>
                <div class="temp-controls">
                    <button onclick="changeTemp(-1)">−</button>
                    <button onclick="changeTemp(1)">+</button>
                </div>
                <div class="mode-selector">
                    <button class="mode-btn active" data-mode="auto" onclick="setMode('auto')">Авто</button>
                    <button class="mode-btn" data-mode="heat" onclick="setMode('heat')">Обогрев</button>
                    <button class="mode-btn" data-mode="cool" onclick="setMode('cool')">Охлаждение</button>
                </div>
            </div>

            <!-- Виджет безопасности -->
            <div class="card security-card">
                <h2>Безопасность</h2>
                <div class="security-grid">
                    <div class="sec-item">
                        <h4>Камеры</h4>
                        <label class="switch">
                            <input type="checkbox" id="cam-toggle" onchange="toggleSecurity('cameras')">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="sec-item">
                        <h4>Датчики движения</h4>
                        <label class="switch">
                            <input type="checkbox" id="motion-toggle" onchange="toggleSecurity('motion')">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="sec-item">
                        <h4>Охрана</h4>
                        <button class="alarm-btn" id="alarm-btn" onclick="toggleAlarm()">Снять с охраны</button>
                    </div>
                </div>
            </div>

            <!-- Виджет автоматизации -->
            <div class="card">
                <h2>Сценарии</h2>
                <div class="scene-buttons">
                    <button class="scene-btn" onclick="runScene('morning')">Доброе утро</button>
                    <button class="scene-btn" onclick="runScene('away')">Я ушел</button>
                    <button class="scene-btn" onclick="runScene('movie')">Кино</button>
                    <button class="scene-btn" onclick="runScene('night')">Спокойной ночи</button>
                </div>
            </div>

        </section>
    </main>

    <footer>
        <p>Система "Нейро-Дом" v2.0 &copy; {year}</p>
    </footer>

    <script>{js}</script>
</body>
</html>
"""

# --- CSS (Стиль: глассморфизм, неон, панель управления) ---
CSS_CODE = """
:root { --bg: #0f121a; --card-bg: rgba(255, 255, 255, 0.05); --glass: rgba(255, 255, 255, 0.1); --accent: #00d5ff; --warning: #ff4757; --success: #2ed573; }
* { box-sizing: border-box; }
body { font-family: 'Roboto', sans-serif; background: var(--bg); color: #e0e0e0; margin: 0; padding: 0; }
header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 3%; background: rgba(15, 18, 26, 0.9); backdrop-filter: blur(10px); border-bottom: 1px solid var(--accent); }
.logo { font-size: 1.5rem; font-weight: bold; color: var(--accent); }
.status-indicator { font-size: 0.8rem; color: var(--success); }
.status-indicator.offline { color: var(--warning); }
main { padding: 2rem 3%; min-height: calc(100vh - 120px); }
.dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
.card { background: var(--card-bg); backdrop-filter: blur(10px); border-radius: 15px; padding: 1.5rem; border: 1px solid var(--glass); position: relative; overflow: hidden; }
.card::before { content: ''; position: absolute; top: -50%; right: -50%; width: 200%; height: 200%; background: conic-gradient(from 180deg at 50% 50%, transparent, var(--accent), transparent); animation: rotate 4s linear infinite; opacity: 0.05; z-index: 0; }
.card * { position: relative; z-index: 1; }
h2 { margin-bottom: 1rem; color: #fff; }
.toggle-group { display: flex; gap: 10px; margin-bottom: 1rem; flex-wrap: wrap; }
.toggle-btn { padding: 8px 16px; border: 1px solid #444; background: #1a1a1a; color: #aaa; border-radius: 5px; cursor: pointer; flex: 1; }
.toggle-btn.active { background: var(--accent); color: #000; box-shadow: 0 0 10px var(--accent); }
.brightness-slider { margin-top: 1rem; }
.brightness-slider input { width: 100%; margin-top: 5px; }
.temp-display { font-size: 4rem; font-weight: bold; text-align: center; margin: 1rem 0; color: var(--accent); }
.temp-controls { display: flex; justify-content: center; gap: 20px; margin-bottom: 1rem; }
.temp-controls button { width: 50px; height: 50px; font-size: 1.5rem; border: 1px solid var(--accent); background: transparent; color: var(--accent); border-radius: 50%; cursor: pointer; transition: 0.3s; }
.temp-controls button:hover { background: var(--accent); color: #000; }
.mode-selector { display: flex; justify-content: center; gap: 10px; }
.mode-btn { padding: 8px 12px; border: 1px solid #444; background: #1a1a1a; color: #aaa; border-radius: 20px; cursor: pointer; }
.mode-btn.active { background: var(--accent); color: #000; }
.security-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; align-items: center; }
.sec-item { display: flex; flex-direction: column; align-items: center; }
.alarm-btn { width: 100%; padding: 12px; background: var(--warning); color: #fff; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
.armed { background: var(--warning) !important; color: #000 !important; animation: blink 1s infinite; }
.scene-buttons { display: flex; flex-direction: column; gap: 10px; }
.scene-btn { padding: 12px; background: #2d3436; color: #fff; border: 1px solid #636e72; border-radius: 5px; cursor: pointer; transition: 0.3s; }
.scene-btn:hover { background: #353b3d; }

/* Кастомные чекбоксы (Switch) */
.switch { position: relative; display: inline-block; width: 50px; height: 28px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #444; transition: .4s; border-radius: 34px; }
.slider:before { position: absolute; content: ""; height: 22px; width: 22px; left: 4px; bottom: 3px; background: #aaa; transition: .4s; border-radius: 50%; }
input:checked + .slider { background: var(--accent); }
input:checked + .slider:before { transform: translateX(22px); }

/* Анимации */
@keyframes rotate { 100% { transform: rotate(360deg); } }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
footer { text-align: center; padding: 2rem; color: #777; }
"""

# --- JS (Логика: клики, изменения, имитация API) ---
JS_CODE = """
// Состояние системы
let lights = { living: true, kitchen: false, bedroom: false };
let brightness = 80;
let temperature = 22;
let mode = 'auto';
let security = { cameras: false, motion: false, alarm: false };

// Обновление статуса (имитация пинга)
function updateStatus() {
    const indicator = document.getElementById('status-indicator');
    // Случайно меняем статус для красоты
    if (Math.random() > 0.95) {
        indicator.classList.toggle('offline');
        indicator.textContent = indicator.classList.contains('offline') ? '● Ошибка связи' : '● Система онлайн';
    }
}

// ОСВЕЩЕНИЕ
function toggleLight(room) {
    lights[room] = !lights[room];
    const btn = document.querySelector(`.toggle-btn[data-room="${room}"]`);
    btn.classList.toggle('active', lights[room]);
    console.log(`Свет в ${room}: ${lights[room] ? 'Включен' : 'Выключен'}`);
}

function updateBrightness() {
    const range = document.getElementById('brightness-range');
    const val = document.getElementById('brightness-val');
    brightness = range.value;
    val.textContent = brightness;
    console.log(`Яркость: ${brightness}%`);
}

// КЛИМАТ
function changeTemp(delta) {
    temperature += delta;
    if (temperature > 30) temperature = 30;
    if (temperature < 16) temperature = 16;
    document.getElementById('temp-val').textContent = temperature;
    console.log(`Температура: ${temperature}°C`);
}

function setMode(newMode) {
    mode = newMode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    console.log(`Режим климата: ${mode}`);
}

// БЕЗОПАСНОСТЬ
function toggleSecurity(type) {
    const isChecked = event.target.checked;
    security[type] = isChecked;
    console.log(`${type}: ${isChecked ? 'Включено' : 'Выключено'}`);
}

function toggleAlarm() {
    const btn = document.getElementById('alarm-btn');
    security.alarm = !security.alarm;
    if (security.armed) {
        btn.textContent = 'Снять с охраны';
        btn.classList.remove('armed');
        console.log('Система охраны: СНЯТО');
    } else {
        btn.textContent = 'ОХРАНА АКТИВНА';
        btn.classList.add('armed');
        console.log('Система охраны: АКТИВНА');
    }
}

// СЦЕНАРИИ
function runScene(scene) {
    console.log(`Запуск сценария: ${scene}`);
    switch(scene) {
        case 'morning':
            lights = { living: true, kitchen: true, bedroom: false };
            brightness = 90; temperature = 22; mode = 'heat';
            break;
        case 'away':
            lights = { living: false, kitchen: false, bedroom: false };
            security.cameras = true; security.motion = true; 
            if(!security.alarm) toggleAlarm();
            break;
        case 'movie':
            lights = { living: true, kitchen: false, bedroom: false };
            brightness = 20; temperature = 21;
            break;
        case 'night':
            lights = { living: false, kitchen: false, bedroom: true };
            brightness = 10; temperature = 19; mode = 'cool';
            break;
    }
    applyState();
}

// Применение состояния к DOM
function applyState() {
    // Свет
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        const room = btn.dataset.room;
        btn.classList.toggle('active', lights[room]);
    });
    // Яркость
    document.getElementById('brightness-range').value = brightness;
    document.getElementById('brightness-val').textContent = brightness;
    // Климат
    document.getElementById('temp-val').textContent = temperature;
    document.querySelector(`.mode-btn[data-mode="${mode}"]`).classList.add('active');
    // Охрана
    document.getElementById('cam-toggle').checked = security.cameras;
    document.getElementById('motion-toggle').checked = security.motion;
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    applyState();
    setInterval(updateStatus, 2000); // Проверка статуса каждые 2 сек
});
"""

# ==============================================================================
# 2. ЛОГИКА СЕРВЕРА
# ==============================================================================

class SiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == "/":
            self.send_html()
        else:
            self.send_error(404)

    def send_html(self):
        current_year = datetime.datetime.now().year
        full_html = HTML_TEMPLATE.format(
            css=CSS_CODE,
            js=JS_CODE,
            year=current_year
        )
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(full_html.encode('utf-8'))

# ==============================================================================
# 3. ЗАПУСК
# ==============================================================================
if __name__ == "__main__":
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, SiteHandler)
    print("="*50)
    print('Умный дом "Нейро-Дом" запущен на http://localhost:8080')
    print("Нажмите Ctrl+C для остановки")
    print("="*50)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        httpd.server_close()
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import datetime

# ==============================================================================
# 1. ШАБЛОНЫ (HTML, CSS, JS)
# ==============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Умный Дом Pro</title>
    <style>{css}</style>
</head>
<body>

    <!-- МОДАЛЬНОЕ ОКНО (скрыто по умолчанию) -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <h3 id="modal-title">⚠️ Подтверждение</h3>
            <p id="modal-text">Вы уверены?</p>
            <div class="modal-actions">
                <button id="modal-cancel">Отмена</button>
                <button id="modal-confirm" class="btn-danger">Подтвердить</button>
            </div>
        </div>
    </div>

    <header>
        <h1>🏠 Neuro-Smart Pro</h1>
        <span id="clock"></span>
    </header>

    <main>
        <div class="dashboard">
            
            <!-- СВЕТ -->
            <div class="card">
                <h2>💡 Освещение</h2>
                <div class="light-group">
                    <div class="light-item">
                        <span>Гостиная</span>
                        <div>
                            <span id="icon-guest" class="light-icon">🔵</span>
                            <button class="light-btn" data-room="guest" onclick="toggleLight('guest')">Выкл</button>
                        </div>
                    </div>
                    <div class="light-item">
                        <span>Кухня</span>
                        <div>
                            <span id="icon-kitchen" class="light-icon">🔵</span>
                            <button class="light-btn" data-room="kitchen" onclick="toggleLight('kitchen')">Выкл</button>
                        </div>
                    </div>
                    <div class="light-item">
                        <span>Спальня</span>
                        <div>
                            <span id="icon-bed" class="light-icon">🔵</span>
                            <button class="light-btn" data-room="bed" onclick="toggleLight('bed')">Выкл</button>
                        </div>
                    </div>
                </div>
                <div class="brightness-control">
                    <label>Яркость: <span id="brightness-val">80</span>%</label>
                    <input type="range" id="brightness-range" min="0" max="100" value="80" oninput="updateBrightness()">
                </div>
                <button class="action-btn-wide" onclick="showModal('Выключить весь свет?', 'Это действие погасит свет во всем доме.', 'allOff')">🔌 Выключить всё</button>
            </div>

            <!-- КЛИМАТ -->
            <div class="card">
                <h2>🌡️ Климат</h2>
                <div class="climate-main">
                    <span id="temp-val">22</span>°C
                    <span id="mode-eco">ЭКО</span>
                </div>
                <div class="climate-controls">
                    <button onclick="changeTemp(-1)">−</button>
                    <button onclick="changeTemp(1)">+</button>
                </div>
                <div class="mode-selector">
                    <button class="mode-btn active" data-mode="eco" onclick="setMode('eco')">ЭКО</button>
                    <button class="mode-btn" data-mode="comfort" onclick="setMode('comfort')">Комфорт</button>
                </div>
            </div>

            <!-- БЕЗОПАСНОСТЬ -->
            <div class="card">
                <h2>🛡️ Безопасность</h2>
                <div class="sec-row">
                    <span>Датчик движения</span>
                    <span id="icon-motion" class="sec-icon">🔵</span>
                    <label class="switch"><input type="checkbox" id="sensor-motion" onchange="toggleSensor('motion')"><span></span></label>
                </div>
                <div class="sec-row">
                    <span>Датчик дыма</span>
                    <span id="icon-smoke" class="sec-icon">🔵</span>
                    <label class="switch"><input type="checkbox" id="sensor-smoke" onchange="toggleSensor('smoke')"><span></span></label>
                </div>
                <button class="action-btn-wide btn-danger" onclick="showModal('Вызвать тревогу?', 'Будет отправлено уведомление в охранную службу.', 'panic')">🚨 ТРЕВОГА</button>
            </div>

            <!-- АВТОМАТИЗАЦИЯ -->
            <div class="card">
                <h2>⚙️ Сценарии</h2>
                <div class="scene-grid">
                    <button class="scene-btn" onclick="runScene('morning')">☀️ Утро</button>
                    <button class="scene-btn" onclick="runScene('away')">🚪 Я ушел</button>
                    <button class="scene-btn" onclick="runScene('movie')">🎬 Кино</button>
                    <button class="scene-btn" onclick="runScene('night')">🌙 Ночь</button>
                </div>
            </div>

        </div>
    </main>

    <footer>
        <p>Система v2.1 | {year}</p>
    </footer>

    <script>{js}</script>
</body>
</html>
"""

CSS_CODE = """
:root { --bg: #0f121b; --panel: #1a202f; --card: #232b3d; --accent: #3b82f6; --danger: #ef4444; --text: #f1f5f9; }
* { box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 0 1rem; }
header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #334155; }
header h1 { font-size: 1.5rem; }
#clock { color: #94a3b8; }
main { padding: 1rem 0; min-height: calc(100vh - 140px); }
.dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; }
.card { background: var(--card); padding: 1.5rem; border-radius: 12px; border: 1px solid #334155; }
.card h2 { margin: 0 0 1rem 0; color: #fff; }

/* Свет */
.light-group { margin-bottom: 1rem; }
.light-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #334155; }
.light-item:last-child { border: none; }
.light-icon { font-size: 1.2rem; margin-right: 10px; }
.light-btn { padding: 6px 12px; border: 1px solid #4b5563; background: #334155; color: #fff; border-radius: 6px; cursor: pointer; }
.light-btn.active { background: var(--accent); color: #000; border-color: var(--accent); }
.brightness-control { margin-top: 1rem; }
.brightness-control label { display: block; margin-bottom: 5px; font-size: 0.9rem; color: #94a3b8; }
.brightness-control input { width: 100%; }

/* Климат */
.climate-main { display: flex; justify-content: space-between; align-items: center; font-size: 2.5rem; margin: 1rem 0; }
.climate-main span#mode-eco { font-size: 1rem; background: #10b981; color: #fff; padding: 4px 10px; border-radius: 20px; }
.climate-controls { display: flex; justify-content: center; gap: 30px; margin-bottom: 1rem; }
.climate-controls button { width: 50px; height: 50px; font-size: 1.5rem; border-radius: 50%; border: 1px solid var(--accent); background: transparent; color: var(--accent); cursor: pointer; }
.mode-selector { display: flex; justify-content: center; gap: 15px; }
.mode-btn { padding: 8px 16px; border: 1px solid #4b5563; background: #334155; border-radius: 9999px; cursor: pointer; }
.mode-btn.active { background: var(--accent); color: #000; }

/* Безопасность */
.sec-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid #334155; }
.sec-row:last-child { border: none; }
.sec-icon { font-size: 1.2rem; margin-right: 10px; }
.sec-icon.alert { color: var(--danger); }

/* Кнопки */
.action-btn-wide { width: 100%; padding: 14px; margin-top: 1rem; border: none; border-radius: 8px; font-size: 1rem; font-weight: bold; cursor: pointer; transition: 0.2s; }
.action-btn-wide:hover { transform: translateY(-2px); }
.btn-danger { background: var(--danger); color: #fff; }
.btn-danger:hover { background: #b91c1c; }

/* Сценарии */
.scene-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.scene-btn { padding: 15px; background: #334155; border-radius: 8px; cursor: pointer; border: 1px solid #4b5563; }
.scene-btn:hover { background: #4b5563; }

/* Модальное окно */
.modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); align-items: center; justify-content: center; z-index: 100; }
.modal-content { background: var(--card); padding: 2rem; border-radius: 12px; text-align: center; width: 90%; max-width: 400px; border: 1px solid #334155; animation: pop 0.3s; }
.modal-actions { display: flex; justify-content: center; gap: 15px; margin-top: 1.5rem; }
#modal-confirm { background: var(--danger); color: #fff; border: none; }
#modal-cancel { background: #4b5563; color: #fff; border: none; }
@keyframes pop { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }

/* Свитч */
.switch { position: relative; display: inline-block; width: 38px; height: 22px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; inset: 0; background: #4b5563; border-radius: 9999px; transition: .4s; }
.slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 2px; background: #fff; border-radius: 50%; transition: .4s; }
input:checked + .slider { background: var(--accent); }
input:checked + .slider:before { transform: translateX(16px); }

footer { text-align: center; padding: 2rem; color: #64748b; font-size: 0.8rem; }
"""

JS_CODE = """
// СОСТОЯНИЕ
let lights = { guest: false, kitchen: false, bed: false };
let sensors = { motion: false, smoke: false };
let brightness = 80;
let temperature = 22;
let mode = 'eco';

// МОДАЛЬНОЕ ОКНО
let pendingAction = null;

function showModal(title, text, action) {
    pendingAction = action;
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-text').textContent = text;
    document.getElementById('modal').style.display = 'flex';
}

document.getElementById('modal-cancel').addEventListener('click', () => {
    document.getElementById('modal').style.display = 'none';
    pendingAction = null;
});

document.getElementById('modal-confirm').addEventListener('click', () => {
    if (pendingAction === 'allOff') allLightsOff();
    if (pendingAction === 'panic') triggerPanic();
    document.getElementById('modal').style.display = 'none';
    pendingAction = null;
});

// УПРАВЛЕНИЕ
function toggleLight(room) {
    lights[room] = !lights[room];
    const btn = document.querySelector(`.light-btn[data-room='${room}']`);
    const icon = document.getElementById(`icon-${room}`);
    btn.classList.toggle('active', lights[room]);
    btn.textContent = lights[room] ? 'Вкл' : 'Выкл';
    icon.textContent = lights[room] ? '🔴' : '🔵';
    showToast(`Свет в ${room} ${lights[room] ? 'включен' : 'выключен'}`);
}

function allLightsOff() {
    for (let room in lights) { lights[room] = false; }
    updateLightUI();
    showToast('Все источники света выключены');
}

function updateLightUI() {
    for (let room in lights) {
        const btn = document.querySelector(`.light-btn[data-room='${room}']`);
        const icon = document.getElementById(`icon-${room}`);
        btn.classList.toggle('active', lights[room]);
        btn.textContent = lights[room] ? 'Вкл' : 'Выкл';
        icon.textContent = lights[room] ? '🔴' : '🔵';
    }
}

function updateBrightness() {
    brightness = document.getElementById('brightness-range').value;
    document.getElementById('brightness-val').textContent = brightness;
    showToast(`Яркость: ${brightness}%`);
}

function changeTemp(delta) {
    temperature += delta;
    if (temperature > 30) temperature = 30;
    if (temperature < 15) temperature = 15;
    document.getElementById('temp-val').textContent = temperature;
}

function setMode(m) {
    mode = m;
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('mode-eco').textContent = m === 'eco' ? 'ЭКО' : 'COMFORT';
    showToast(`Режим: ${m.toUpperCase()}`);
}

function toggleSensor(type) {
    sensors[type] = event.target.checked;
    const icon = document.getElementById(`icon-${type}`);
    icon.textContent = sensors[type] ? '🔴' : '🔵';
    icon.classList.toggle('alert', sensors[type] && type === 'smoke');
    showToast(`Датчик ${type} ${sensors[type] ? 'сработал' : 'в норме'}`);
}

function triggerPanic() {
    document.getElementById('icon-smoke').textContent = '🔴';
    document.getElementById('icon-smoke').classList.add('alert');
    showToast('🚨 ТРЕВОГА! ОХРАНА ВЫЗВАНА!', 'error');
}

function runScene(scene) {
    if (scene === 'morning') { lights.guest=true; lights.kitchen=true; temperature=23; mode='comfort'; }
    if (scene === 'away') { lights={guest:false, kitchen:false, bed:false}; sensors.motion=true; temperature=16; }
    if (scene === 'movie') { lights.guest=false; lights.bed=true; brightness=20; }
    if (scene === 'night') { lights={guest:false, kitchen:false, bed:true}; temperature=19; mode='eco'; }
    updateLightUI();
    document.getElementById('temp-val').textContent = temperature;
    document.getElementById('brightness-range').value = brightness;
    document.getElementById('brightness-val').textContent = brightness;
    setMode(mode);
    document.getElementById('sensor-motion').checked = sensors.motion;
    showToast(`Сценарий "${scene}" активирован`);
}

// УВЕДОМЛЕНИЯ
function showToast(msg, type="info") {
    const toast = document.createElement('div');
    toast.textContent = msg;
    toast.style.cssText = `position:fixed;top:15px;right:15px;padding:12px 20px;background:${type==='error'?'#dc2626':'#000'};color:#fff;border-radius:9999px;z-index:2000;animation:fade 0.3s;box-shadow:0 4px 15px rgba(0,0,0,0.3);`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
}
const style = document.createElement('style');
style.textContent = `@keyframes fade{from{transform:translateX(100%);opacity:0;}to{transform:translateX(0);opacity:1;}}`;
document.head.appendChild(style);

// ЧАСЫ
function updateClock() { document.getElementById('clock').textContent = new Date().toLocaleTimeString('ru-RU'); }
updateClock(); setInterval(updateClock, 1000);

// Инициализация
document.addEventListener('DOMContentLoaded', updateLightUI);
"""

# ==============================================================================
# 2. СЕРВЕР
# ==============================================================================

class SiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path == "/":
            self.send_html()
        else:
            self.send_error(404)

    def send_html(self):
        html = HTML_TEMPLATE.format(css=CSS_CODE, js=JS_CODE, year=datetime.datetime.now().year)
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

if __name__ == "__main__":
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, SiteHandler)
    print("🚀 Умный Дом Pro запущен на http://localhost:8080")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        httpd.server_close()
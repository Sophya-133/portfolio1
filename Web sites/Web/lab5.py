from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import datetime
import json

# --- Константы ---
VALID_PASSWORD = "12345" # Пароль теперь простой для удобства

# ==============================================================================
# 1. МНОГОСТРОЧНЫЕ СТРОКИ (HTML, CSS, JS)
# ==============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Умный Дом 4.0</title>
    <style>{css}</style>
</head>
<body>

    <!-- СЛОЙ 1: ЭКРАН БЛОКИРОВКИ -->
    <div id="lock-screen" class="lock-screen">
        <div class="lock-box">
            <h2>🔒 Умный Дом</h2>
            <p>Введите код доступа</p>
            <input type="password" id="unlock-code" placeholder="Код">
            <button id="unlock-btn">Разблокировать</button>
            <div id="lock-error" class="error-lock"></div>
        </div>
    </div>

    <!-- СЛОЙ 2: ОСНОВНАЯ ПАНЕЛЬ -->
    <div id="main-dashboard" style="display: none;">
        <header>
            <div class="logo">🏠 Neuro-Smart</div>
            <div class="header-right">
                <span id="date-time"></span>
                <span class="status-dot" id="net-status"></span>
            </div>
        </header>

        <main class="dashboard-grid">
            
            <!-- Виджет: Сводка -->
            <div class="card summary-card">
                <h3>📊 Сводка</h3>
                <div class="summary-item"><span>Свет:</span> <strong id="lights-count">0</strong> вкл.</div>
                <div class="summary-item"><span>Датчики:</span> <strong id="sensors-count">0</strong> акт.</div>
                <div class="summary-item"><span>Расход:</span> <strong>1.2</strong> кВт</div>
            </div>

            <!-- Виджет: Освещение -->
            <div class="card">
                <h3>💡 Свет</h3>
                <div class="device-row"><span>Люстра</span> <label class="switch"><input type="checkbox" id="light-main"><span></span></label></div>
                <div class="device-row"><span>Торшер</span> <label class="switch"><input type="checkbox" id="light-lamp"><span></span></label></div>
                <div class="device-row"><span>LED-лента</span> <label class="switch"><input type="checkbox" id="light-strip"><span></span></label></div>
                <div class="device-row"><span>Ночник</span> <label class="switch"><input type="checkbox" id="light-night"><span></span></label></div>
            </div>

            <!-- Виджет: Погода -->
            <div class="card weather-card">
                <h3>🌤️ Погода</h3>
                <div class="weather-main">
                    <span id="weather-icon">🌡️</span>
                    <div>
                        <span id="weather-temp">--</span>°C
                        <span id="weather-desc">Загрузка...</span>
                    </div>
                </div>
                <div class="weather-details">
                    <span>Влажность: <strong id="weather-hum">--</strong>%</span>
                    <span>Ветер: <strong id="weather-wind">--</strong> м/с</span>
                </div>
            </div>

            <!-- Виджет: Медиаплеер -->
            <div class="card media-card">
                <h3>🎵 Музыка</h3>
                <div class="track-info">
                    <span id="track-name">Умный Дом - Chill Mix</span>
                    <span id="track-time">02:15 / 04:30</span>
                </div>
                <div class="media-controls">
                    <button id="btn-prev">⏮️</button>
                    <button id="btn-play">▶️</button>
                    <button id="btn-next">⏭️</button>
                </div>
            </div>

            <!-- Виджет: Приводы -->
            <div class="card">
                <h3>🚪 Ворота и Шторы</h3>
                <div class="device-row"><span>Гараж</span> <button class="action-btn" id="garage-toggle">Открыть</button></div>
                <div class="device-row"><span>Шторы</span> <button class="action-btn" id="curtains-toggle">Закрыть</button></div>
            </div>

            <!-- Виджет: Безопасность -->
            <div class="card security-card">
                <h3>🛡️ Охрана</h3>
                <div class="device-row"><span>Камеры</span> <label class="switch"><input type="checkbox" id="sec-cam"><span></span></label></div>
                <div class="device-row"><span>Датчик дыма</span> <label class="switch"><input type="checkbox" id="sec-smoke"><span></span></label></div>
                <button id="panic-btn" class="btn-panic">🚨 ТРЕВОГА</button>
            </div>

        </main>
    </div>

    <script>{js}</script>
</body>
</html>
"""

CSS_CODE = """
:root { --bg: #0a0e17; --panel: #111622; --card: #161d2b; --text: #e2e8f0; --accent: #60a5fa; --red: #f87171; --green: #34d399; }
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh;}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(circle at 20% 30%, rgba(100,165,255,0.03) 0%, transparent 70%);z-index:-1;}

/* Экран блокировки */
.lock-screen{display:flex;align-items:center;justify-content:center;height:100vh;background:linear-gradient(135deg, #0a0e17 0%, #1a202e 100%);}
.lock-box{text-align:center;background:rgba(255,255,255,0.05);padding:2.5rem;border-radius:20px;border:1px solid rgba(255,255,255,0.1);backdrop-filter:blur(10px);}
.lock-box input{width:100%;padding:12px;margin:10px 0;background:#000;border:1px solid #333;color:#fff;border-radius:8px;}
.error-lock{color:#fca5a5;margin-top:10px;min-height:20px;}

/* Панель */
header{display:flex;justify-content:space-between;padding:1rem 2%;align-items:center;background:rgba(17,22,34,0.9);border-bottom:1px solid #1f2937;}
.logo{font-size:1.3rem;font-weight:bold;}
.status-dot{display:inline-block;width:10px;height:10px;background:#34d399;border-radius:50%;margin-left:8px;}
.status-dot.off{background:#fca5a5;}
.dashboard-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:1.5rem;padding:2rem;}

/* Карточки */
.card{background:var(--card);padding:1.5rem;border-radius:15px;border:1px solid #1f2937;position:relative;overflow:hidden;animation: fadeInUp 0.5s ease-out;}
.card h3{margin-bottom:1rem;color:#fff;display:flex;align-items:center;}
.device-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #1f2937;}
.device-row:last-child{border:none;}
.action-btn{padding:8px 12px;background:#1f2937;color:#fff;border:1px solid #4b5563;border-radius:9999px;cursor:pointer;transition:0.2s;}
.action-btn:hover{background:#374151;}

/* Switch */
.switch{position:relative;display:inline-block;width:40px;height:20px;}
.switch input{opacity:0;width:0;height:0;}
.switch span{position:absolute;cursor:pointer;inset:0;background:#4b5563;border-radius:20px;transition:.4s;}
.switch span:before{position:absolute;content:"";height:16px;width:16px;left:2px;bottom:2px;background:#fff;border-radius:50%;transition:.4s;}
input:checked + span{background:var(--accent);}
input:checked + span:before{transform:translateX(20px);}

/* Спец виджеты */
.summary-card .summary-item{display:flex;justify-content:space-between;padding:6px 0;color:#9ca3af;}
.weather-main{display:flex;align-items:center;justify-content:space-between;margin:1rem 0;}
.weather-main span{font-size:2rem;}
.weather-details{display:flex;justify-content:space-between;color:#9ca3af;font-size:0.9rem;}
.media-card .track-info{display:flex;flex-direction:column;margin-bottom:1rem;color:#9ca3af;}
.media-controls{display:flex;justify-content:space-around;}
.media-controls button{background:none;border:none;font-size:1.5rem;cursor:pointer;color:var(--accent);}
.btn-panic{width:100%;margin-top:1rem;padding:15px;background:var(--red);color:#fff;border:none;border-radius:8px;font-weight:bold;font-size:1.1rem;cursor:pointer;animation: pulse 2s infinite;}

/* Анимации */
@keyframes fadeInUp{from{opacity:0;transform:translateY(30px);}to{opacity:1;transform:translateY(0);}}
@keyframes pulse{0%,100%{transform:scale(1);}50%{transform:scale(1.05);}}
"""

JS_CODE = """
// СОСТОЯНИЕ
let isLocked = true;
let lights = {main: false, lamp: false, strip: false, night: false};
let security = {cam: false, smoke: false};
let media = {isPlaying: false, track: "Chill Mix", time: "02:15"};
let weather = {temp: 22, desc: "Солнечно", hum: 60, wind: 3, icon: "☀️"};

// === БЛОКИРОВКА ===
document.getElementById('unlock-btn').addEventListener('click', () => {
    const code = document.getElementById('unlock-code').value;
    if (code === "12345") {
        isLocked = false;
        document.getElementById('lock-screen').style.display = 'none';
        document.getElementById('main-dashboard').style.display = 'block';
        startDashboard();
    } else {
        document.getElementById('lock-error').textContent = "Неверный код доступа";
    }
});

// === ЗАПУСК ПАНЕЛИ ===
function startDashboard() {
    updateClock();
    updateWeather();
    updateSummary();
    setInterval(updateClock, 1000);
    // Имитация получения погоды каждые 10 сек
    setInterval(updateWeather, 10000); 
}

// === ФУНКЦИИ ОБНОВЛЕНИЯ ===
function updateClock() {
    const now = new Date();
    document.getElementById('date-time').textContent = now.toLocaleString('ru-RU', {hour:'2-digit', minute:'2-digit', weekday:'short', day:'numeric', month:'short'});
    document.getElementById('net-status').classList.toggle('off', Math.random() < 0.05); // Имитация обрыва сети
}

function updateWeather() {
    // Случайные данные для имитации API
    weather.temp = Math.floor(15 + Math.random() * 10);
    weather.hum = 40 + Math.floor(Math.random() * 40);
    weather.wind = (Math.random() * 5).toFixed(1);
    weather.icon = weather.temp > 25 ? "☀️" : "🌥️";
    
    document.getElementById('weather-icon').textContent = weather.icon;
    document.getElementById('weather-temp').textContent = weather.temp;
    document.getElementById('weather-desc').textContent = weather.desc;
    document.getElementById('weather-hum').textContent = weather.hum;
    document.getElementById('weather-wind').textContent = weather.wind;
}

function updateSummary() {
    const activeLights = Object.values(lights).filter(v => v).length;
    const activeSensors = Object.values(security).filter(v => v).length;
    document.getElementById('lights-count').textContent = activeLights;
    document.getElementById('sensors-count').textContent = activeSensors;
}

// === УПРАВЛЕНИЕ УСТРОЙСТВАМИ ===
function toggleDevice(stateObj, key, uiId) {
    stateObj[key] = !stateObj[key];
    document.getElementById(uiId).checked = stateObj[key];
    updateSummary();
    const status = stateObj[key] ? "включен" : "выключен";
    showToast(`${key} ${status}`);
}

// Привязка событий для света
['main', 'lamp', 'strip', 'night'].forEach(id => {
    document.getElementById(`light-${id}`).addEventListener('change', (e) => {
        lights[id] = e.target.checked;
        updateSummary();
    });
});

// Безопасность
['cam', 'smoke'].forEach(id => {
    document.getElementById(`sec-${id}`).addEventListener('change', (e) => {
        security[id] = e.target.checked;
        updateSummary();
    });
});

// Ворота
document.getElementById('garage-toggle').addEventListener('click', () => {
    const state = document.getElementById('garage-toggle').textContent;
    document.getElementById('garage-toggle').textContent = (state === "Открыть") ? "Закрыть" : "Открыть";
    showToast(`Гаражные ворота ${state === "Открыть" ? "открываются" : "закрываются"}...`);
});

// Шторы
document.getElementById('curtains-toggle').addEventListener('click', () => {
    const state = document.getElementById('curtains-toggle').textContent;
    document.getElementById('curtains-toggle').textContent = (state === "Закрыть") ? "Открыть" : "Закрыть";
    showToast(`Шторы ${state === "Закрыть" ? "закрываются" : "открываются"}`);
});

// Медиа
document.getElementById('btn-play').addEventListener('click', () => {
    media.isPlaying = !media.isPlaying;
    document.getElementById('btn-play').textContent = media.isPlaying ? "⏸️" : "▶️";
    showToast(media.isPlaying ? "Воспроизведение" : "Пауза");
});
document.getElementById('btn-next').addEventListener('click', () => showToast("Следующий трек"));
document.getElementById('btn-prev').addEventListener('click', () => showToast("Предыдущий трек"));

// Тревога
document.getElementById('panic-btn').addEventListener('click', () => {
    document.body.classList.add('alarm-active');
    showToast("🚨 ТРЕВОГА! ВЫЗВАНА ОХРАНА!", "error");
    setTimeout(() => document.body.classList.remove('alarm-active'), 1000);
});

// Уведомления
function showToast(msg, type = "info") {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = msg;
    if(type === "error") toast.style.borderLeft = "4px solid #f87171";
    document.getElementById('toast-container').appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}

// Анимация появления карточек
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, i) => {
        setTimeout(() => card.classList.add('show'), i * 100);
    });
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
        page = HTML_TEMPLATE.format(css=CSS_CODE, js=JS_CODE)
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))

# ==============================================================================
# 3. ЗАПУСК
# ==============================================================================
if __name__ == "__main__":
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, SiteHandler)
    print("🚀 Умный Дом 4.0 запущен на http://localhost:8080")
    print("Пароль для входа: 12345")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        httpd.server_close()
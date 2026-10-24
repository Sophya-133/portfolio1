#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой IoT-полив без внешних зависимостей.
  4 зоны, CSV-лог, UDP-широковещание, OTA-обновление.
  Python ≥ 3.7
"""

import socket, json, time, csv, os, datetime, random, urllib.request, threading

ZONES      = 4
SOIL_LOW   = 30          # %, ниже – полив
WATER_SEC  = 15           # секунд полива
CSV_FILE   = 'garden.csv'
UDP_BC     = ('255.255.255.255', 4040)
OTA_URL    = 'http://192.168.1.99:8000/poliv.py'
OTA_PERIOD = 5*60         # с
LOG_FMT    = '[%Y-%m-%d %H:%M:%S]'   # короткий формат

def log(msg):
    print(f'{datetime.datetime.now().strftime(LOG_FMT)}  {msg}')

# ---------- UDP (один сокет на всё время работы) ----------
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

def udp_send(obj):
    udp_sock.sendto(json.dumps(obj, separators=(',', ':')).encode(), UDP_BC)

# ---------- датчики (имитация) ----------
class Sensor:
    __slots__ = ('sid',)
    def __init__(self, sid): self.sid = sid
    def soil(self)     : return max(0, min(100, int(50 + random.gauss(0, 15))))
    def air_temp(self) : return round(20 + random.gauss(0, 3), 1)
    def air_hum(self)  : return round(60 + random.gauss(0, 10), 1)
    def rain(self)     : return random.random() < 0.1

# ---------- клапан ----------
class Valve:
    __slots__ = ('pin', 'state')
    def __init__(self, pin):
        self.pin   = pin
        self.state = False
    def set(self, on: bool):
        if self.state != on:
            self.state = on
            log(f'Клапан {self.pin}  {"ON" if on else "OFF"}')

# ---------- CSV ----------
def write_csv(row):
    exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='') as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(['time', 'zone', 'soil%', 'airT', 'airH%', 'rain', 'watered'])
        w.writerow(row)

# ---------- OTA ----------
_last_ota = 0
def ota_check():
    global _last_ota
    now = time.monotonic()
    if now - _last_ota < OTA_PERIOD: return
    _last_ota = now
    try:
        new = urllib.request.urlopen(OTA_URL, timeout=3).read()
        own = open(__file__, 'rb').read()
        if new != own:
            log('OTA: новая версия')
            open(__file__, 'wb').write(new)
            log('OTA: перезапуск')
            os.execv(__file__, ['python3', __file__])
    except Exception as e:
        log(f'OTA skip: {e}')

# ---------- основной цикл ----------
def irrigate_loop():
    sensors = [Sensor(i) for i in range(ZONES)]
    valves  = [Valve(i)  for i in range(ZONES)]
    last_rgb = [(None, None, None)] * ZONES
    log('Старт системы полива')
    while True:
        loop_start = time.monotonic()
        for z in range(ZONES):
            s    = sensors[z]
            soil = s.soil()
            temp = s.air_temp()
            hum  = s.air_hum()
            rain = s.rain()
            need = soil < SOIL_LOW and not rain

            rgb_new = (need, not need, rain)
            if rgb_new != last_rgb[z]:
                last_rgb[z] = rgb_new
                log(f'Z{z}  RGB={rgb_new}')

            if need:
                valves[z].set(True)
                time.sleep(WATER_SEC)
                valves[z].set(False)

            row = [datetime.datetime.now().replace(microsecond=0), z, soil, temp, hum, rain, need]
            write_csv(row)
            udp_send({'zone': z, 'soil': soil, 'temp': temp, 'hum': hum, 'rain': rain, 'watered': need})

        ota_check()
        elapsed = time.monotonic() - loop_start
        time.sleep(max(0, 60 - elapsed))

# ---------- запуск ----------
if __name__ == '__main__':
    # поток полива
    threading.Thread(target=irrigate_loop, daemon=True).start()
    # основной поток просто ждёт Ctrl-C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log('Выход по Ctrl-C')

 

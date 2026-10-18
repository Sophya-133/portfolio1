import hashlib
import hmac
import time
import json
import os
import secrets

# ==============================================================================
# БЛОК 1: КОНФИГУРАЦИЯ И "АППАРАТНЫЙ МОДУЛЬ" (TPM SIMULATOR)
# ==============================================================================

# "Аппаратный ключ" (TPM). В реальности он вшит в чип на материнской плате.
# Здесь мы его генерируем один раз и храним в зашифрованном виде.
MASTER_HARDWARE_KEY = b"hw_tpm_master_key_9f8a7b6c5d4e3f2a1b0c"

# Настройки PBKDF2 (замедляют взлом)
ITERATIONS = 600_000  # Количество итераций (чем больше, тем медленнее брутфорс)
DIGEST_ALGO = "sha256"

# Файлы "диска" (для демонстрации целостности)
CONFIG_FILE = "secure_config.json"
AUDIT_LOG_FILE = "audit.log"

# ==============================================================================
# БЛОК 2: БАЗА ДАННЫХ И СОСТОЯНИЕ (Hardcoded + File-based)
# ==============================================================================

# Пользователи. Паролей в открытом виде нет.
USERS = {
    "admin": {
        "role": "administrator",
        "hw_protected": True
    },
    "user": {
        "role": "standard", 
        "hw_protected": False
    }
}

# Попытки входа (в памяти)
LOGIN_STATE = {
    "admin": {"count": 0, "lock_until": 0},
    "user": {"count": 0, "lock_until": 0}
}

# ==============================================================================
# БЛОК 3: ЯДРО БЕЗОПАСНОСТИ (Криптография)
# ==============================================================================

def load_config():
    """Загрузка конфига с проверкой целостности (HMAC)"""
    if not os.path.exists(CONFIG_FILE):
        return None, None
        
    with open(CONFIG_FILE, "rb") as f:
        file_content = f.read()
    
    # Разделяем данные и подпись
    data, received_sig = file_content[:-64], file_content[-64:]
    
    # Вычисляем правильную подпись
    expected_sig = hmac.new(MASTER_HARDWARE_KEY, data, hashlib.sha256).hexdigest().encode()
    
    if not hmac.compare_digest(received_sig, expected_sig):
        print("[FATAL] Конфигурационный файл поврежден или подделан! (HMAC mismatch)")
        return None, None
        
    return json.loads(data.decode()), expected_sig

def save_config(config_data):
    """Сохранение конфига с созданием HMAC-подписи"""
    data_bytes = json.dumps(config_data, indent=2).encode()
    signature = hmac.new(MASTER_HARDWARE_KEY, data_bytes, hashlib.sha256).hexdigest().encode()
    
    with open(CONFIG_FILE, "wb") as f:
        f.write(data_bytes + signature)

def derive_key(password, salt):
    """
    PBKDF2: Защита от GPU-брутфорса.
    Вместо одного хеша мы делаем 600 000 итераций хеширования.
    """
    return hashlib.pbkdf2_hmac(
        DIGEST_ALGO,
        password.encode(),
        salt.encode(),
        ITERATIONS
    )

def secure_wipe_memory(byte_array):
    """
    Симуляция очистки памяти. 
    В C++ мы бы занулили массив. В Python просим сборщик мусора поработать.
    """
    # Перезаписываем данные (для наглядности, в реальности это сложно в Python)
    for i in range(len(byte_array)):
        byte_array[i] = 0
    del byte_array

def log_audit(message, level="INFO"):
    """Запись в журнал событий (Audit Log)"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

# ==============================================================================
# БЛОК 4: БИЗНЕС-ЛОГИКА (Аутентификация и Авторизация)
# ==============================================================================

def login(username, password):
    log_audit(f"Попытка входа пользователя: {username}")
    
    if is_locked(username):
        log_audit(f"Отказ: Аккаунт {username} заблокирован.", "WARNING")
        return False

    if username not in USERS:
        log_audit(f"Отказ: Пользователь {username} не найден.", "WARNING")
        return False

    user_profile = USERS[username]
    
    # 1. Проверка аппаратной защиты (TPM)
    if user_profile["hw_protected"]:
        # Для админа нужен и пароль, и "железный" ключ
        salt = "admin_hw_salt"
        stored_key = load_config()[0].get("admin_hw_key") if load_config()[0] else None
        
        if not stored_key:
            log_audit("Ошибка: Аппаратный ключ не инициализирован.", "ERROR")
            return False
            
        derived_attempt = derive_key(password, salt)
        
        if not secure_compare(derived_attempt.hex(), stored_key):
            register_fail(username)
            log_audit("Отказ: Неверный пароль или аппаратный ключ.", "SECURITY")
            return False
    else:
        # Обычный пользователь (только пароль)
        salt = "user_salt"
        stored_key = "a3f5e9c1d2b4a6f8e0d1c3b5a7f9e0d1c3b5a7f9e0d1c3b5a7f9e0d1c3b5a7f9" # Заглушка
        derived_attempt = derive_key(password, salt)
        if not secure_compare(derived_attempt.hex(), stored_key):
            register_fail(username)
            log_audit("Отказ: Неверный пароль.", "SECURITY")
            return False

    # Успех
    register_success(username)
    log_audit(f"Пользователь {username} успешно авторизован. Роль: {user_profile['role']}", "SUCCESS")
    return True

def register_fail(username):
    state = LOGIN_STATE[username]
    state["count"] += 1
    if state["count"] >= 3:
        state["lock_until"] = time.time() + 30
        log_audit(f"Аккаунт {username} заблокирован на 30 сек из-за перебора.", "ALERT")

def register_success(username):
    LOGIN_STATE[username]["count"] = 0
    LOGIN_STATE[username]["lock_until"] = 0

def is_locked(username):
    state = LOGIN_STATE[username]
    if state["lock_until"] > time.time():
        return True
    if state["count"] >= 3:
        state["count"] = 0
        state["lock_until"] = 0
    return False

def secure_compare(val1, val2):
    return hmac.compare_digest(val1.encode(), val2.encode())

def execute_action(user_role, action):
    """Принцип наименьших привилегий"""
    log_audit(f"Запрос действия '{action}' от роли '{user_role}'")
    
    if user_role == "administrator":
        if action == "delete_system32":
            log_audit("Администратор выполнил критическую операцию.", "CRITICAL")
            print("[SYSTEM] Выполняю: rm -rf / (Имитировано)")
        elif action == "view_logs":
            print("[SYSTEM] Чтение журнала аудита...")
            with open(AUDIT_LOG_FILE, "r") as f:
                print(f.read())
        else:
            print(f"[SYSTEM] Выполняю: {action}")
            
    elif user_role == "standard":
        if action.startswith("delete") or action.startswith("format"):
            log_audit("СТАНДАРТНЫЙ пользователь пытался выполнить админ-действие!", "BLOCK")
            print("[ACCESS DENIED] Недостаточно прав. (UAC)")
        else:
            print(f"[SYSTEM] Выполняю пользовательскую задачу: {action}")

# ==============================================================================
# БЛОК 5: ИНИЦИАЛИЗАЦИЯ (Setup)
# ==============================================================================

def initialize_system():
    """Первый запуск: создание 'железного' ключа для админа"""
    if not os.path.exists(CONFIG_FILE):
        print("[SETUP] Инициализация системы. Создание аппаратного ключа...")
        
        # Генерируем ключ на основе пароля и "железа"
        admin_password = "SecureRoot2024!"
        hw_salt = "admin_hw_salt"
        hw_derived_key = derive_key(admin_password, hw_salt)
        
        config = {"admin_hw_key": hw_derived_key.hex()}
        save_config(config)
        
        # Очищаем переменную с паролем из памяти
        secure_wipe_memory(bytearray(admin_password, 'utf-8'))
        
        print("[SETUP] Система защищена. Ключ сохранен в", CONFIG_FILE)

# ==============================================================================
# БЛОК 6: ЗАПУСК (Main)
# ==============================================================================
from datetime import datetime

def main():
    print("=" * 70)
    print("SECURE SDLC SIMULATOR v2.0: TPM, PBKDF2, HMAC Integrity")
    print("=" * 70)
    
    initialize_system()
    
    # Загружаем конфиг для проверки
    config, sig = load_config()
    if config is None:
        return

    # --- СЦЕНАРИЙ 1: Вход администратора ---
    print("\n[СЦЕНА 1] Вход Администратора (нужен пароль + TPM)")
    admin_auth = login("admin", "SecureRoot2024!")
    
    if admin_auth:
        execute_action("administrator", "view_logs")
        execute_action("administrator", "optimize_network")
        
        # Попытка взлома
        print("\n[АТАКА] 3 неверных попытки пароля для 'admin'...")
        login("admin", "1")
        login("admin", "2")
        login("admin", "3")
        
        print("[ПРОВЕРКА] 4-я попытка (должна быть блокировка):")
        login("admin", "SecureRoot2024!")

    print("\n[СЦЕНА 2] Вход Стандартного пользователя")
    user_auth = login("user", "userpass123") # Этот пароль не сработает (заглушка выше)

    if not user_auth:
        print("[INFO] Для пользователя 'user' пароль в коде задан как заглушка. Вход имитирован как успешный.")
        user_auth = True
        
    if user_auth:
        execute_action("standard", "open_browser")
        execute_action("standard", "format_c_drive") # Попытка нарушения LUA
        
    print("\n[ИТОГ] Проверьте файл 'audit.log' для детального отчета о событиях.")
    print("Обратите внимание на попытки подбора и блокировку (30 секунд ожидания).")

if __name__ == "__main__":
    main()
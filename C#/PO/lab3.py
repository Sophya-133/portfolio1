import hashlib
import time
import hmac
import os

# ==============================================================================
# БЛОК 1: НАСТРОЙКИ ДЛЯ WINDOWS-ПОЛЬЗОВАТЕЛЯ
# ==============================================================================

# Настройки безопасности (как в хорошем антивирусе)
MAX_PASSWORD_ATTEMPTS = 3
LOCKOUT_TIME_SECONDS = 10
SECRET_PEPPER = "win_user_local_pepper_2024" # Секрет, спрятанный внутри .exe файла

# Имитация файловой системы пользователя Windows
# В реальности это пути типа C:\Users\Имя\Documents
USER_FILES_DB = {
    "ivan": {
        "salt": "pc_salt_01",
        "pwd_hash": hashlib.sha256((SECRET_PEPPER + "pc_salt_01" + "IvanPC2024!").encode()).hexdigest(),
        "my_folder": "C:\\Users\\Ivan\\Documents",
        "secret_folder": "C:\\Users\\Ivan\\Documents\\Family_Secrets",
        "role": "owner"
    },
    "guest": {
        "salt": "pc_salt_02", 
        "pwd_hash": hashlib.sha256((SECRET_PEPPER + "pc_salt_02" + "guest123").encode()).hexdigest(),
        "my_folder": "C:\\Users\\Public", # Обычный пользователь не может лезть в профиль Ивана
        "secret_folder": None,            # Доступа к секретам нет
        "role": "guest"
    }
}

LOGIN_ATTEMPTS = {
    "ivan": {"count": 0, "lock_until": 0},
    "guest": {"count": 0, "lock_until": 0}
}

# ==============================================================================
# БЛОК 2: БИБЛИОТЕКА БЕЗОПАСНОСТИ (та же, что и в безопасной разработке)
# ==============================================================================

def secure_compare(val1, val2):
    return hmac.compare_digest(val1.encode(), val2.encode())

def hash_password(password, salt):
    peppered = SECRET_PEPPER + salt + password
    return hashlib.sha256(peppered.encode()).hexdigest()

def sanitize_path(user_path):
    """
    Защита от Path Traversal (атака ../).
    Обычный пользователь не должен иметь возможности выйти из своей папки.
    """
    # Разрешаем только буквы, цифры, дефис, подчеркивание и разделители путей
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_\\/:."
    safe_path = "".join([c for c in user_path if c in allowed_chars])
    
    # Запрещаем выходить выше корневой папки пользователя
    if ".." in safe_path:
        return None
        
    if len(safe_path) > 100: # Защита от слишком длинных строк
        return None
    return safe_path

def is_account_locked(username):
    current_time = time.time()
    state = LOGIN_ATTEMPTS.get(username)
    
    if not state:
        return False
        
    if state["lock_until"] > current_time:
        return True
        
    if state["count"] >= MAX_PASSWORD_ATTEMPTS:
        state["count"] = 0
        state["lock_until"] = 0
        
    return False

# ==============================================================================
# БЛОК 3: ФУНКЦИИ РАБОТЫ В WINDOWS (симуляция)
# ==============================================================================

def login(username, password):
    print(f"\n[*] Вход в Windows под пользователем: {username}")
    
    if is_account_locked(username):
        print("[БЛОКИРОВКА] Аккаунт временно заблокирован. Подождите 10 секунд.")
        return None

    safe_username = sanitize_input(username)
    if not safe_username or safe_username not in USER_FILES_DB:
        print("[ОШИБКА] Неверный логин или пароль.")
        return None

    user_record = USER_FILES_DB[safe_username]
    attempt_hash = hash_password(password, user_record["salt"])
    
    if secure_compare(attempt_hash, user_record["pwd_hash"]):
        print(f"[ДОСТУП РАЗРЕШЕН] Сессия открыта. Профиль: {user_record['my_folder']}")
        LOGIN_ATTEMPTS[safe_username]["count"] = 0
        return user_record
    else:
        LOGIN_ATTEMPTS[safe_username]["count"] += 1
        print(f"[ПРЕДУПРЕЖДЕНИЕ] Пароль неверный. Попытка {LOGIN_ATTEMPTS[safe_username]['count']}")
        
        if LOGIN_ATTEMPTS[safe_username]["count"] >= MAX_PASSWORD_ATTEMPTS:
            LOGIN_ATTEMPTS[safe_username]["lock_until"] = time.time() + LOCKOUT_TIME_SECONDS
            print("[ТРЕВОГА] Windows заблокировала учетную запись на 10 секунд.")
        return None

def open_folder(user_session, requested_path):
    """
    Принцип наименьших привилегий:
    Гость может открывать только Public.
    Владелец может открывать свои папки.
    """
    safe_path = sanitize_path(requested_path)
    if not safe_path:
        print("[ОШИБКА] Путь содержит запрещенные символы.")
        return

    # Проверка прав доступа
    if user_session["role"] == "guest":
        if "Ivan" in safe_path:
            print("[ОТКАЗ] У вас нет прав доступа к этой папке. (Ошибка доступа Windows)")
            return
    
    # Проверка существования папки в нашей "базе данных"
    if safe_path == user_session["my_folder"]:
        print(f"[OK] Открываю папку: {safe_path}")
        print("Содержимое: Фото_отпуск.jpg, Резюме.docx, Проект_дом.xlsx")
    elif safe_path == user_session["secret_folder"]:
        if user_session["role"] == "owner":
            print(f"[OK] Открываю защищенную папку: {safe_path}")
            print("Содержимое: Паспорта_скан.pdf, Пароли_к_банкингу.txt (ЗАШИФРОВАНО)")
        else:
            print("[ОТКАЗ] Папка не найдена или доступ запрещен.")
    else:
        print(f"[ОШИБКА] Папка '{safe_path}' не существует или вы не являетесь ее владельцем.")

def run_windows_command(user_session, command):
    """
    Симуляция CMD/PowerShell.
    Гость не может менять систему.
    Владелец может, но мы его предупреждаем.
    """
    safe_cmd = sanitize_input(command)
    if not safe_cmd:
        print("[ОШИБКА] Команда отклонена.")
        return

    dangerous_commands = ["format", "del /f /s /q c:\\", "rd /s /q", "mklink /d"]
    
    # Проверка на опасные команды (аналог SmartScreen или UAC)
    is_dangerous = any(danger in safe_cmd.lower() for danger in dangerous_commands)
    
    if user_session["role"] == "guest":
        print("[ОТКАЗ] У гостя нет прав на выполнение команд. (UAC: Запрос отклонен)")
        return
        
    if is_dangerous:
        print(f"[UAC] ВНИМАНИЕ: Попытка выполнить опасную команду: '{safe_cmd}'")
        print("-> Это может привести к удалению Windows. Действие заблокировано.")
        print("-> Совет: Используйте Корзину для удаления файлов.")
        return
        
    # Безопасные команды
    if "ipconfig" in safe_cmd.lower():
        print("[CMD] Выполнение: ipconfig")
        print("-> IPv4 Address. . . . . . . . . . . : 192.168.1.50")
    elif "explorer" in safe_cmd.lower():
        print("[CMD] Выполнение: explorer")
        print("-> Открывается окно 'Этот компьютер'")
    else:
        print(f"[CMD] Команда '{safe_cmd}' не распознана или требует прав Администратора.")

def sanitize_input(user_input):
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_\\/:. "
    sanitized = "".join([c for c in user_input if c in allowed_chars])
    if len(sanitized) > 50:
        return None
    return sanitized

# ==============================================================================
# БЛОК 4: СЦЕНАРИЙ ДЛЯ КУРСОВОЙ (Обычный день пользователя Windows)
# ==============================================================================

def main():
    print("=" * 60)
    print("SECURE WINDOWS ENVIRONMENT SIMULATOR")
    print("Тема: Разработка безопасных программ (LUA - Least Privilege)")
    print("=" * 60)

    # --- СЦЕНА 1: Иван работает на своем ПК ---
    print("\n[СЦЕНА 1] Владелец ПК (Иван) входит в систему.")
    ivan_session = login("ivan", "IvanPC2024!")
    
    if ivan_session:
        open_folder(ivan_session, "C:\\Users\\Ivan\\Documents")
        open_folder(ivan_session, "C:\\Users\\Ivan\\Documents\\Family_Secrets")
        
        print("\n[ДЕЙСТВИЕ] Иван хочет узнать свой IP-адрес через CMD.")
        run_windows_command(ivan_session, "ipconfig")
        
        print("\n[ДЕЙСТВИЕ] Иван случайно ввел опасную команду (защита срабатывает).")
        run_windows_command(ivan_session, "format c:")

    # --- СЦЕНА 2: Приходит гость ---
    print("\n" + "="*60)
    print("[СЦЕНА 2] К Ивану пришел друг (Гость) и просит воспользоваться ПК.")
    print("="*60)
    
    guest_session = login("guest", "guest123")
    
    if guest_session:
        # Гость пытается шпионить за Иваном
        print("\n[ДЕЙСТВИЕ] Гость пытается зайти в 'Мои документы' Ивана.")
        open_folder(guest_session, "C:\\Users\\Ivan\\Documents")
        
        # Гость пытается открыть свои (публичные) файлы
        print("\n[ДЕЙСТВИЕ] Гость заходит в общую папку.")
        open_folder(guest_session, "C:\\Users\\Public")
        
        # Гость пытается сломать систему
        print("\n[ДЕЙСТВИЕ] Гость пытается очистить диск C через CMD.")
        run_windows_command(guest_session, "del *.* /s")
        
        # Гость пытается запустить браузер
        print("\n[ДЕЙСТВИЕ] Гость запускает браузер.")
        run_windows_command(guest_session, "start chrome")

    # --- СЦЕНА 3: Защита от перебора (Brute Force) ---
    print("\n" + "="*60)
    print("[СЦЕНА 3] Злоумышленник пытается подобрать пароль Ивана.")
    print("="*60)
    
    wrong_passwords = ["12345", "qwerty", "password", "ivan123"]
    for pwd in wrong_passwords:
        login("ivan", pwd)
        time.sleep(0.5)
        
    print("\n[ПРОВЕРКА] Злоумышленник вводит ПРАВИЛЬНЫЙ пароль, но аккаунт заблокирован.")
    login("ivan", "IvanPC2024!")
    
    time.sleep(LOCKOUT_TIME_SECONDS + 1)
    print("[ПРОВЕРКА] Время блокировки вышло. Пробуем снова.")
    ivan_session_2 = login("ivan", "IvanPC2024!")
    
    if ivan_session_2:
        print("\n[ИТОГ] Иван снова в системе. Файлы в безопасности.")

if __name__ == "__main__":
    main()
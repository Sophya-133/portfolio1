import hashlib
import time
import os
import getpass

USER_DB_FILE = "user_db.txt"    
LOG_FILE = "auth_log.txt"
MAX_ATTEMPTS = 3
BLOCK_TIME_SECONDS = 600       
SALT = b'salt_for_auth_2024'

def hash_password(password: str) -> str:
    """Хеширует пароль с солью."""
    return hashlib.sha256(SALT + password.encode('utf-8')).hexdigest()

def get_current_time_str() -> str:
    """Возвращает текущее время в формате YYYY-MM-DD HH:MM:SS"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def load_users() -> dict:
    """
    Загружает всех пользователей из файла в виде словаря:
    {user_id: hashed_password}
    """
    users = {}
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|", 1)
                if len(parts) != 2:
                    continue
                user_id, hashed = parts
                users[user_id.strip()] = hashed.strip()
    return users

def save_user(user_id: str, password_hash: str):
    """Сохраняет пользователя."""
    with open(USER_DB_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id}|{password_hash}\n")

def load_blocked_until() -> float:
    """Проверяет время окончания блокировки."""
    if os.path.exists("auth_block.lock"):
        with open("auth_block.lock", "r") as f:
            try:
                return float(f.read().strip())
            except ValueError:
                pass
    return None

def is_blocked() -> bool:
    """Проверяет, заблокирован ли аккаунт."""
    blocked_until = load_blocked_until()
    if blocked_until is None:
        return False
    return time.time() < blocked_until

def save_blocked_until(expire_time: float):
    """Сохраняет время окончания блокировки."""
    with open("auth_block.lock", "w") as f:
        f.write(str(expire_time))

def log_event(message: str):
    """Логирует событие."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{get_current_time_str()} - {message}\n")

def register_user(users: dict):
    """Регистрация нового пользователя."""
    while True:
        user_id = input("Введите уникальный ID пользователя: ").strip()
        if user_id in users:
            print("Пользователь с таким ID уже существует. Попробуйте другой ID.")
            continue
        while True:
            password1 = getpass.getpass("Введите пароль (отображаются звездочки): ")
            password2 = getpass.getpass("Повторите пароль: ")
            if password1 == password2:
                break
            else:
                print("Пароли не совпадают. Повторите попытку.")
        password_hash = hash_password(password1)
        save_user(user_id, password_hash)
        log_event(f"Пользователь {user_id} зарегистрирован.")
        print(f"Пользователь {user_id} успешно зарегистрирован.")
        break

def authenticate_user(users: dict, user_id: str):
    """Аутентификация пользователя."""
    attempts = 0
    blocked_until = load_blocked_until()
    if blocked_until is not None and time.time() < blocked_until:
        log_event(f"Блокировка аккаунта {user_id}. Доступ доступен через {int(blocked_until - time.time())} сек.")
        print("Доступ к аккаунту заблокирован. Подождите 10 минут.")
        return False

    while attempts < MAX_ATTEMPTS:
        password = getpass.getpass("Введите пароль (звездочки будут отображаться): ")
        password_hash = hash_password(password)
        if users.get(user_id) == password_hash:
            log_event(f"Успешная аутентификация пользователя {user_id}.")
            print("Аутентификация успешна.")
            return True
        else:
            attempts += 1
            log_event(f"Неуспешная попытка аутентификации пользователя {user_id}. Попытка #{attempts}.")
            if attempts < MAX_ATTEMPTS:
                print(f"Неправильный пароль. Осталось {MAX_ATTEMPTS - attempts} попытки(-оки).")
            else:
                now = time.time()
                expire = now + BLOCK_TIME_SECONDS
                save_blocked_until(expire)
                log_event(f"Три неуспешные попытки. Аккаунт {user_id} заблокирован на 10 минут.")
                print(f"Три неуспешные попытки. Аккаунт заблокирован на 10 минут.")
                print(f"Блокировка истекает в: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expire))}")
                return False

def main():
    users = load_users()
    print("== Программа авторизации и регистрации ==")
    while True:
        choice = input("Выберите действие:\n1. Регистрация\n2. Авторизация\n3. Выход\n> ").strip()
        if choice == '1':
            register_user(users)
            # Обновить словарь пользователей после регистрации
            users = load_users()
        elif choice == '2':
            user_id = input("Введите ваш ID: ").strip()
            if user_id not in users:
                print(f"Пользователь с ID '{user_id}' не найден. Сначала зарегистрируйтесь.")
            else:
                if authenticate_user(users, user_id):
                    # После успешной авторизации можно добавить свой код
                    print("Вы успешно вошли в систему!")
                # else — уже обработано в authenticate_user
        elif choice == '3':
            print("Выход из программы.")
            break
        else:
            print("Некорректный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()

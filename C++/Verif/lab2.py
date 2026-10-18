def validate_email(email):
    """
    """
    if isinstance(email, str) and '@' in email:
        domain_part = email.split('@', 1)[1]
        if '.' in domain_part:
            return True, "Email валиден."
    return False, "Email невалиден. Требуется формат user@domain.ru"

def validate_password(password):
    """
    Пароль должен:
      - иметь минимум 8 символов
      - содержать хотя бы одну цифру
      - содержать хотя бы одну букву
    """
    if not isinstance(password, str) or len(password) < 8:
        return False, "Пароль слишком короткий. Минимум 8 символов."
    has_digit = any(c.isdigit() for c in password)
    has_letter = any(c.isalpha() for c in password)
    if not (has_digit and has_letter):
        if not has_digit:
            msg = "Пароль должен содержать хотя бы одну цифру."
        if not has_letter:
            msg = "Пароль должен содержать хотя бы одну букву."
        # Если обе проверки не прошли, можно объединить сообщение:
        if not (has_digit and has_letter):
            msg = "Пароль должен содержать хотя бы одну цифру и одну букву."
        return False, msg
    return True, "Пароль валиден."

def check_email_exists(emails_db, email):
    """
    Имитация проверки на уникальность email в базе данных (списке).
    """
    if email in emails_db:
        return False, "Email уже зарегистрирован."
    return True, "Email свободен."

def register_user(emails_db):
    email = input("Введите email: ").strip()
    password = input("Введите пароль: ").strip()
    confirm_password = input("Повторите пароль: ").strip()

    # Валидация email
    is_email_valid, email_msg = validate_email(email)
    print(f"[Валидация email] {email_msg}")
    if not is_email_valid:
        return

    # Валидация пароля
    is_password_valid, password_msg = validate_password(password)
    print(f"[Валидация пароля] {password_msg}")
    if not is_password_valid:
        return

    # Проверка совпадения паролей
    if password != confirm_password:
        print("[Ошибка] Пароли не совпадают.")
        return

    # Верификация уникальности email 
    is_unique, uniqueness_msg = check_email_exists(emails_db, email)
    print(f"[Верификация email] {uniqueness_msg}")
    if not is_unique:
        return

    # Если все ОК — "зарегистрирован"
    emails_db.append(email)
    print("[Успех] Пользователь успешно зарегистрирован!")

if __name__ == "__main__":
    # "База данных" — список зарегистрированных email
    users_db = ["alice@example.com", "bob@domain.ru"]
    print("=== Регистрация нового пользователя ===")
    register_user(users_db)

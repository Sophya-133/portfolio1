def validate_phone(phone):
    """Валидация телефонного номера (Простая проверка: 10 цифр)"""
    if isinstance(phone, str) and phone.isdigit() and len(phone) == 11 and phone.startswith('8') or phone.startswith('7'):
        return True, "Номер телефона валиден."
    return False, "Номер телефона невалиден. Он должен начинаться с 7 или 8 и содержать 11 цифр."

def validate_age(age):
    """Валидация возраста (от 0 до 120 лет)"""
    if isinstance(age, int) and 0 <= age <= 120:
        return True, "Возраст валиден."
    return False, "Возраст должен быть числом от 0 до 120."

def verify_adult(age):
    """Верификация: совершеннолетний ли человек? (с 18 лет)"""
    if age >= 18:
        return True, "Пользователь совершеннолетний."
    return False, "Пользователь не совершеннолетний."

def main():
    print("=== Простая система валидации и верификации ===")
    
    # Ввод данных
    phone_input = input("Введите номер телефона (например, +7 или 8): ").strip()
    age_input = input("Введите возраст: ").strip()
    
    # Попытка преобразовать возраст в число
    try:
        age = int(age_input)
    except ValueError:
        age = None

    # Валидация телефона
    is_phone_valid, phone_message = validate_phone(phone_input)
    print(f"[Валидация телефона] {phone_message}")

    # Валидация возраста
    if isinstance(age, int):
        is_age_valid, age_message = validate_age(age)
        print(f"[Валидация возраста] {age_message}")
        
        # Верификация: совершеннолетний?
        is_adult, adult_message = verify_adult(age)
        print(f"[Верификация] {adult_message}")
    else:
        print("[Ошибка] Возраст должен быть целым числом.")

if __name__ == "__main__":
    main()

from datetime import datetime, date
import re

def verify_data_schema(raw_data: dict) -> tuple[bool, str]:
    """Верификация: проверка структуры, типов и форматов."""
    required_fields = ['email', 'age', 'birth_date']
    for field in required_fields:
        if field not in raw_data:
            return False, f"Отсутствует обязательное поле: {field}"

    if not isinstance(raw_data['age'], int):
        return False, "Поле 'age' должно быть целым числом."
    
    # Простая проверка формата email (регэксп неидеален, но для примера подойдет)
    if not re.match(r"[^@]+@[^@]+\.[^@]+", raw_data['email']):
        return False, "Поле 'email' имеет неверный формат."
        
    # Проверка даты
    try:
        datetime.strptime(raw_data['birth_date'], '%Y-%m-%d')
    except ValueError:
        return False, "Поле 'birth_date' должно быть в формате ГГГГ-ММ-ДД."
        
    return True, ""

def validate_business_logic(raw_data: dict) -> tuple[bool, str]:
    """Валидация: проверка бизнес-логики."""
    age = raw_data['age']
    birth_date = datetime.strptime(raw_data['birth_date'], '%Y-%m-%d').date()
    
    if age < 13:
        return False, 'Пользователь должен быть старше 13 лет.'
    if age > 120:
        return False, 'Указанный возраст выглядит неправдоподобно.'
        
    if raw_data.get('role') == 'admin' and age < 18:
        return False, 'Администраторами могут быть только совершеннолетние.'
        
    if birth_date > date.today():
        return False, 'Дата рождения не может быть в будущем.'
        
    # Проверка соответствия возраста и даты рождения
    today = date.today()
    calculated_age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if calculated_age != age:
        return False, f'Возраст ({age}) не совпадает с датой рождения. Должно быть {calculated_age}.'

    return True, ""

def process_user_data_manual(raw_data: dict):
    print("Входящие сырые данные:", raw_data)

    is_verified, verify_msg = verify_data_schema(raw_data)
    if not is_verified:
        print(f"\nОШИБКА ВЕРИФИКАЦИИ: {verify_msg}")
        return

    is_valid, validate_msg = validate_business_logic(raw_data)
    if not is_valid:
        print(f"\nОШИБКА ВАЛИДАЦИИ: {validate_msg}")
        return

    print("\nДанные успешно прошли проверку.")

process_user_data_manual({
    "email": "admin@company.com",
    "age": 17,
    "role": "admin",
    "birth_date": "2010-01-01"
})
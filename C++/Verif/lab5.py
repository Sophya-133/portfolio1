from datetime import date, datetime
from typing import Dict, Any, List, Optional
import re

# Устанавливаем Pydantic для удобной проверки типов: pip install pydantic
from pydantic import BaseModel, ValidationError

# ==============================
# 1. ЭТАП ВЕРИФИКАЦИИ (Проверка структуры)
# ==============================
# На этом этапе мы просто проверяем, что данные в принципе похожи на анкету.
# Мы не оцениваем смысл, только форму.

def verify_data_types(raw_data: Dict[str, Any]) -> List[str]:
    """
    Проверяет, что типы данных соответствуют ожиданиям.
    Возвращает список ошибок. Если список пуст — верификация пройдена.
    """
    errors = []
    
    # 1.1. Проверка строк
    string_fields = ['surname', 'first_name', 'city', 'street']
    for field in string_fields:
        if field not in raw_data:
            errors.append(f"Ошибка структуры: отсутствует поле '{field}'")
        elif not isinstance(raw_data[field], str):
            errors.append(f"Поле '{field}' должно быть текстом (строкой), а получено: {type(raw_data[field]).__name__}")
        elif len(raw_data[field].strip()) == 0:
            errors.append(f"Поле '{field}' не может быть пустым или содержать только пробелы")

    # 1.2. Проверка целых чисел
    int_fields = ['age', 'house_number']
    for field in int_fields:
        if field not in raw_data:
            errors.append(f"Ошибка структуры: отсутствует поле '{field}'")
        elif not isinstance(raw_data[field], int):
            # Пробуем преобразовать, если пришло строкой (частая ошибка ввода)
            try:
                raw_data[field] = int(raw_data[field])
            except (ValueError, TypeError):
                errors.append(f"Поле '{field}' должно быть целым числом, а получено: {raw_data[field]}")

    # 1.3. Проверка даты
    if 'birth_date' not in raw_data:
        errors.append("Ошибка структуры: отсутствует поле 'birth_date'")
    else:
        if not isinstance(raw_data['birth_date'], str):
            errors.append(f"Поле 'birth_date' должно быть строкой в формате ГГГГ-ММ-ДД")
        else:
            try:
                # Проверяем, что строка вообще может быть датой
                datetime.strptime(raw_data['birth_date'], '%Y-%m-%d')
            except ValueError:
                errors.append(f"Поле 'birth_date' имеет неверный формат. Нужно ГГГГ-ММ-ДД (например, 1985-05-20)")

    # 1.4. Проверка опционального телефона
    if 'phone' in raw_data and raw_data['phone'] is not None:
        if not isinstance(raw_data['phone'], str):
            errors.append("Поле 'phone' должно быть строкой")
            
    return errors

# ==============================
# 2. ЭТАП ВАЛИДАЦИИ (Проверка смысла)
# ==============================
# Структура верна. Теперь проверяем, не противоречат ли данные здравому смыслу.

def validate_data_logic(raw_data: Dict[str, Any]) -> List[str]:
    """
    Проверяет бизнес-логику и смысловую корректность данных.
    """
    errors = []
    
    # 2.1. Валидация возраста
    age = raw_data.get('age')
    birth_date_str = raw_data.get('birth_date')
    
    if age is not None:
        if age < 0:
            errors.append("Возраст не может быть отрицательным.")
        if age > 120:
            errors.append("Указанный возраст ({}) выглядит неправдоподобно для человека.".format(age))
            
        # Кросс-проверка: возраст должен примерно совпадать с датой рождения
        if birth_date_str:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            today = date.today()
            # Вычисляем реальный возраст
            real_age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if abs(real_age - age) > 2: # Допускаем погрешность в 2 года из-за дня заполнения
                errors.append(f"Возраст ({age}) не совпадает с датой рождения. По дате должно быть {real_age}.")

    # 2.2. Валидация номера телефона (простая)
    phone = raw_data.get('phone')
    if phone:
        # Убираем все, кроме цифр
        digits = re.sub(r'\D', '', phone)
        # Для примера считаем, что номер должен быть длиной 11 цифр (как +7...)
        if len(digits) != 11:
            errors.append(f"Номер телефона должен содержать 11 цифр (включая код страны/оператора). Получено: {phone}")

    # 2.3. Валидация адреса (смысловая)
    city = raw_data.get('city', '').lower()
    street = raw_data.get('street', '').lower()
    
    if city == 'москва':
        if 'ленин' in street or 'октябрь' in street:
             errors.append("В Москве не может быть улиц с названиями 'Ленина' или 'Октябрьская' (исторический пример).")
    
    return errors

# ==============================
# 3. МОДЕЛЬ ДАННЫХ (Финальная сборка)
# ==============================
# Если верификация и валидация пройдены, упаковываем данные в строгую модель.

class SurveyResult(BaseModel):
    surname: str
    first_name: str
    age: int
    birth_date: date
    city: str
    street: str
    house_number: int
    phone: Optional[str] = None

# ==============================
# 4. ОСНОВНОЙ ПРОЦЕССОР
# ==============================

def process_survey(raw_data: Dict[str, Any]) -> Optional[SurveyResult]:
    """
    Главная функция: запускает все этапы проверки по порядку.
    """
    print("\n" + "="*60)
    print("ПОЛУЧЕНА НОВАЯ АНКЕТА:")
    print("ФИО: {} {}, Возраст: {}".format(
        raw_data.get('first_name', '---'), 
        raw_data.get('surname', '---'), 
        raw_data.get('age', '---')
    ))
    print("="*60)

    # ЭТАП 1: ВЕРИФИКАЦИЯ (Проверка "железа" и типов)
    print("ЭТАП 1: Верификация структуры...")
    type_errors = verify_data_types(raw_data)
    if type_errors:
        print("ВЕРИФИКАЦИЯ ПРОВАЛЕНА. Обнаружены ошибки в структуре данных:")
        for err in type_errors:
            print("  -", err)
        return None
    else:
        print("Верификация структуры пройдена успешно.")

    # ЭТАП 2: ВАЛИДАЦИЯ (Проверка смысла)
    print("\nЭТАП 2: Валидация бизнес-логики...")
    logic_errors = validate_data_logic(raw_data)
    if logic_errors:
        print("ВАЛИДАЦИЯ ПРОВАЛЕНА. Данные противоречат логике:")
        for err in logic_errors:
            print("  -", err)
        return None
    else:
        print("Валидация логики пройдена успешно.")

    print("\nЭТАП 3: Финальная упаковка в модель...")
    try:
        result = SurveyResult(**raw_data)
        print("АНКЕТА ПРИНЯТА И ЗАРЕГИСТРИРОВАНА.")
        print("Внутренний ID (объект Pydantic):", result)
        return result
    except ValidationError as e:
        print("КРИТИЧЕСКАЯ ОШИБКА при создании объекта (это баг в коде):")
        for err in e.errors():
            print("  -", err['msg'])
        return None

if __name__ == "__main__":

    survey_1 = {
        "surname": "Иванов",
        "first_name": "Петр",
        "age": 35,
        "birth_date": "1989-05-15",
        "city": "Казань",
        "street": "Баумана",
        "house_number": 10,
        "phone": "+7 (999) 123-45-67"
    }
    process_survey(survey_1)


    survey_2 = {
        "surname": "", 
        "first_name": "Анна",
        "age": "двадцать", 
        "birth_date": "15/05/1990", 
        "city": "Москва",
        "street": "Улица Ленина", 
        "house_number": -5, 
        "phone": "123" 
    }
    process_survey(survey_2)


    survey_3 = {
        "surname": "Сидоров",
        "first_name": "Иван",
        "age": 20, 
        "birth_date": "1970-01-01", 
        "city": "Новосибирск",
        "street": "Советская",
        "house_number": 1
    }
    process_survey(survey_3)
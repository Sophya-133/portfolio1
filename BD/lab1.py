import json
import os

DB_FILE = "database.json"

def load_db():
    """Загрузить всю базу данных."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    """Сохранить базу данных."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def create_table(db, table_name):
    """Создать новую таблицу (если еще не существует)."""
    if table_name in db:
        print(f"Таблица '{table_name}' уже существует.")
        return
    db[table_name] = []
    save_db(db)
    print(f"Таблица '{table_name}' создана.")

def describe_table(db, table_name):
    """Показать схему таблицы (типы столбцов по первой строке)."""
    if table_name not in db or not db[table_name]:
        print(f"Таблица '{table_name}' пуста или не существует.")
        return
    if len(db[table_name]) == 0:
        print(f"В таблице '{table_name}' нет строк для определения структуры.")
        return
    sample = db[table_name][0]
    print(f"Схема таблицы '{table_name}':")
    for key in sample.keys():
        # Если не все строки одинаковы по полям — выводим "динамическую схему"
        all_same = all(set(row.keys()) == set(sample.keys()) for row in db[table_name])
        if all_same:
            print(f"  {key}: {type(sample[key]).__name__}")
        else:
            print(f"  {key}: разные типы")
    if not all_same:
        print("Внимание: не все строки имеют одинаковую структуру.")

def insert_row(db, table_name, row_data):
    """Добавить строку в таблицу."""
    if table_name not in db:
        print(f"Таблица '{table_name}' не существует.")
        return
    # Проверяем, что все строки в таблице имеют одинаковые ключи, если уже есть данные
    if db[table_name]:
        existing_keys = set(db[table_name][0].keys())
        if set(row_data.keys()) != existing_keys:
            print("Ошибка: Новая строка не совпадает по полям с существующими.")
            return
    db[table_name].append(row_data)
    save_db(db)
    print(f"Строка добавлена в таблицу '{table_name}'.")

def update_row(db, table_name, condition_key, condition_value, update_data):
    """
    Обновить строки, удовлетворяющие условию.
    condition_key — поле по которому искать
    condition_value — значение
    update_data — поля и новые значения
    """
    if table_name not in db or not db[table_name]:
        print(f"Таблица '{table_name}' пуста или не существует.")
        return
    updated = False
    for row in db[table_name]:
        if row.get(condition_key) == condition_value:
            row.update(update_data)
            updated = True
    if not updated:
        print(f"Ничего не обновлено в таблице '{table_name}'.")
    else:
        save_db(db)
        print(f"Строки обновлены в таблице '{table_name}'.")

def delete_row(db, table_name, condition_key, condition_value):
    """Удалить строки по условию."""
    if table_name not in db or not db[table_name]:
        print(f"Таблица '{table_name}' пуста или не существует.")
        return
    to_delete = []
    for idx, row in enumerate(db[table_name]):
        if row.get(condition_key) == condition_value:
            to_delete.append(idx)
    if not to_delete:
        print(f"Ничего не найдено для удаления в таблице '{table_name}'.")
        return
    # Удаляем с конца к началу, чтобы индексы не сбивались
    for idx in sorted(to_delete, reverse=True):
        del db[table_name][idx]
    save_db(db)
    print(f"{len(to_delete)} строк(ы) удалены из таблицы '{table_name}'.")

def select_rows(db, table_name, condition=None):
    """
    Вывести строки из таблицы. condition — словарь фильтрации, например: {"email": "ivan@example.com"}
    """
    if table_name not in db or not db[table_name]:
        print(f"Таблица '{table_name}' пуста или не существует.")
        return
    if condition is None:
        # Выводим всё
        for idx, row in enumerate(db[table_name], 1):
            print(f"{idx}. {row}")
        return
    # Фильтрация по условию
    found = False
    for row in db[table_name]:
        if all(row.get(k) == v for k, v in condition.items()):
            print(row)
            found = True
    if not found:
        print("Ничего не найдено.")

def main():
    db = load_db()
    while True:
        print("\n--- Простая JSON-БД ---")
        print("1. Создать таблицу")
        print("2. Описать структуру таблицы")
        print("3. Добавить строку")
        print("4. Обновить строки")
        print("5. Удалить строки")
        print("6. Выбрать строки (SELECT)")
        print("7. Выйти")
        cmd = input("Выберите действие: ").strip()
        if cmd == "1":
            table_name = input("Название таблицы: ").strip()
            create_table(db, table_name)
        elif cmd == "2":
            table_name = input("Название таблицы: ").strip()
            describe_table(db, table_name)
        elif cmd == "3":
            table_name = input("Название таблицы: ").strip()
            print("Введите значения полей (каждое на новой строке, пустая — пустое значение):")
            keys = []
            row = {}
            # Сначала определим ключи по первой пустой строке или дадим шанс ввести их явно
            print("Введите имена столбцов через запятую (например: id,name,email):")
            keys_input = input("Столбцы: ").strip()
            if keys_input:
                keys = [k.strip() for k in keys_input.split(",") if k.strip()]
            else:
                # Если пользователь не указал, прочитаем первую строку как ключи
                print("Введите первую строку данных, чтобы определить столбцы:")
                first_line = input("> ").strip()
                if not first_line:
                    print("Ошибка: первая строка пуста.")
                    continue
                keys = [k.strip() for k in first_line.split("\t") if k.strip()]
            # Теперь вводим значения
            row = {}
            for k in keys:
                val = input(f"{k}: ").strip()
                row[k] = val if val else None
            # Если таблица уже есть, проверяем совпадение ключей
            insert_row(db, table_name, row)
        elif cmd == "4":
            table_name = input("Название таблицы: ").strip()
            condition_key = input("По какому полю искать? ")
            condition_value = input("Значение для поиска: ")
            update_data = {}
            print("Введите поля для обновления (ключ=значение), пустая строка — конец:")
            while True:
                line = input("> ").strip()
                if not line:
                    break
                if '=' in line:
                    k, v = line.split('=', 1)
                    update_data[k.strip()] = v.strip()
            update_row(db, table_name, condition_key, condition_value, update_data)
        elif cmd == "5":
            table_name = input("Название таблицы: ").strip()
            condition_key = input("По какому полю удалять? ")
            condition_value = input("Значение для удаления: ")
            delete_row(db, table_name, condition_key, condition_value)
        elif cmd == "6":
            table_name = input("Название таблицы: ").strip()
            use_condition = input("Использовать фильтр? (y/n) ").strip().lower() == "y"
            if use_condition:
                print("Введите фильтр в формате key=value, разделённые запятыми (например: email=ivan@example.com):")
                condition_str = input("> ").strip()
                condition = {}
                if condition_str:
                    for pair in condition_str.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            condition[k.strip()] = v.strip()
            else:
                condition = None
            select_rows(db, table_name, condition)
        elif cmd == "7":
            print("Сохраняем и выходим.")
            save_db(db)
            break
        else:
            print("Неизвестная команда.")

if __name__ == "__main__":
    main()

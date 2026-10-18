import json
import os

DB_FILE = "database.json"
INDEX_SUFFIX = "_index"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def get_table(db, table_name):
    return db.get(table_name, [])

def get_index(db, table_name):
    """Возвращает индекс для таблицы, если есть."""
    idx_name = f"{table_name}{INDEX_SUFFIX}"
    return db.get(idx_name, {})

def create_table(db, table_name):
    """Создаёт таблицу и соответствующий пустой индекс."""
    if table_name in db:
        print(f"Таблица '{table_name}' уже существует.")
        return
    db[table_name] = []
    idx_name = f"{table_name}{INDEX_SUFFIX}"
    db[idx_name] = {}
    save_db(db)
    print(f"Таблица '{table_name}' и её индекс созданы.")

def insert_row(db, table_name, row, indexed_fields=None):
    """
    Добавляет строку в таблицу и обновляет индексы.
    indexed_fields — список полей, по которым строится индекс.
    """
    table = get_table(db, table_name)
    idx_name = f"{table_name}{INDEX_SUFFIX}"
    index = get_index(db, table_name) or {}

    table_id = len(table)
    table.append(row)
    # Для каждого индексируемого поля добавляем в индекс
    if indexed_fields:
        for field in indexed_fields:
            value = row
            # Поддержка вложенных полей, например, 'address.city'
            parts = field.split('.')
            curr = value
            for part in parts:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                else:
                    curr = None
                    break
            if curr is None:
                # Если такого поля нет, пропускаем
                continue
            if curr not in index:
                index[curr] = []
            index[curr].append(table_id)
    db[table_name] = table
    db[idx_name] = index
    save_db(db)
    print(f"Строка добавлена в таблицу '{table_name}'.")

def drop_table(db, table_name):
    """Удаляет таблицу и её индекс."""
    if table_name in db:
        del db[table_name]
        idx_name = f"{table_name}{INDEX_SUFFIX}"
        if idx_name in db:
            del db[idx_name]
        save_db(db)
        print(f"Таблица '{table_name}' удалена.")
    else:
        print(f"Таблица '{table_name}' не найдена.")

def select_by_index(db, table_name, field, value):
    """
    Быстрый поиск по индексу.
    """
    idx_name = f"{table_name}{INDEX_SUFFIX}"
    index = db.get(idx_name, {})
    if not index:
        print("Для этой таблицы нет индекса по этому полю.")
        return

    if value not in index:
        print(f"Ничего не найдено по значению '{value}' в индексе '{field}'.")
        return

    table = get_table(db, table_name)
    if not table:
        print("Таблица пуста.")
        return

    # Разбиваем поле на части для get_nested
    path = field

    def get_nested(row, path):
        if not isinstance(row, dict):
            return None
        curr = row
        for part in path.split('.'):
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr

    found_rows = []
    for row_id in index[value]:
        if row_id >= len(table):
            # Строка удалена или индекс устарел
            continue
        row = table[row_id]
        # Проверяем реальное значение в строке
        actual_value = get_nested(row, path)
        if actual_value is not None and actual_value == value:
            found_rows.append(row)
    if not found_rows:
        print("Ничего не найдено.")
    else:
        for row in found_rows:
            print(row)

def describe_table(db, table_name):
    """Определяет структуру таблицы (ключи первой строки и их типы)."""
    table = get_table(db, table_name)
    if not table:
        print(f"Таблица '{table_name}' пуста или не существует.")
        return
    sample = table[0]
    print(f"Схема таблицы '{table_name}':")
    for key in sample.keys():
        # Если значения разных типов — укажем "динамический"
        types = set(type(r.get(key, None).__class__) if key in r else None for r in table)
        if len(types) == 1 and None not in types:
            print(f"  {key}: {types.pop().__name__}")
        else:
            print(f"  {key}: разные типы или отсутствует")
    # Выводим индексируемые поля
    idx_name = f"{table_name}{INDEX_SUFFIX}"
    if idx_name in db:
        print(f"\nИндексируемые поля: {list(db[idx_name].keys())}")

def main():
    db = load_db()
    while True:
        print("\n--- JSON-БД с индексами ---")
        print("1. Создать таблицу с индексом")
        print("2. Описать структуру таблицы")
        print("3. Добавить строку (с указанием индексируемых полей)")
        print("4. Быстрый поиск по индексу")
        print("5. Удалить таблицу")
        print("6. Выйти")
        cmd = input("Выберите действие: ").strip()
        if cmd == "1":
            table_name = input("Название таблицы: ").strip()
            indexed_fields = input("Индексируемые поля (через запятую, например: email, address.city): ").strip()
            if not indexed_fields:
                print("Не указаны индексируемые поля.")
                continue
            indexed_fields = [f.strip() for f in indexed_fields.split(",") if f.strip()]
            create_table(db, table_name)
            # Добавим пустой индекс, но значения появятся после первой вставки
            save_db(db)
            # После создания таблицы можно сразу добавить строку
            row = {}
            print("Введите значения полей (по одному на строку, пустая — None):")
            keys = []
            # Сначала узнаём ключи из введённых значений или дадим шанс ввести их
            print("Введите имена столбцов через запятую:")
            cols_input = input("> ").strip()
            if cols_input:
                keys = [k.strip() for k in cols_input.split(",") if k.strip()]
            else:
                # Вводим первую строку для определения ключей
                first_line = input("> ").strip()
                if not first_line:
                    print("Ошибка: первая строка пуста.")
                    continue
                keys = [k.strip() for k in first_line.split("\t") if k.strip()]
            for k in keys:
                val = input(f"{k}: ").strip()
                row[k] = None if val == "" else val
            # Возможно, некоторые поля — вложенные объекты. Для простоты — пользователь вручную вводит JSON-строку, если нужно вложенное
            use_nested = input("Есть вложенные объекты (например, address)? (y/n) ").strip().lower() == "y"
            if use_nested:
                print("Введите поля вложенного объекта через запятую (например: city,zip):")
                nested_keys = [k.strip() for k in input("> ").split(",") if k.strip()]
                nested_val = {}
                for nk in nested_keys:
                    nested_val[nk] = input(f"{nk}: ").strip()
                row["address"] = nested_val
            insert_row(db, table_name, row, indexed_fields)
        elif cmd == "2":
            table_name = input("Название таблицы: ").strip()
            describe_table(db, table_name)
        elif cmd == "3":
            table_name = input("Название таблицы: ").strip()
            print("Введите данные строки (каждое на новой строке):")
            # Сначала определим ключи (аналогично команде 1)
            cols_input = input("Имена столбцов (через запятую): ").strip()
            if not cols_input:
                print("Не указаны ключи.")
                continue
            keys = [k.strip() for k in cols_input.split(",") if k.strip()]
            row = {}
            for k in keys:
                val = input(f"{k}: ").strip()
                # Если поле — вложенный объект, дадим шанс ввести его как JSON
                if k == "address":
                    addr_json = input("Вводить address как JSON? (y/n) ").strip().lower() == "y"
                    if addr_json:
                        addr_str = input("Введите address в формате JSON: ")
                        try:
                            import json as j
                            row[k] = j.loads(addr_str)
                        except Exception:
                            print("Ошибка парсинга JSON. Будет пусто.")
                            row[k] = {}
                    else:
                        city = input(f"{k}.city: ").strip()
                        zipc = input(f"{k}.zip: ").strip()
                        row[k] = {"city": city, "zip": zipc}
                else:
                    row[k] = None if val == "" else val
            indexed_fields = input("Какие поля индексируются в этой таблице? (оставьте пустым — индекс не обновляется): ").strip()
            if indexed_fields:
                indexed_fields = [f.strip() for f in indexed_fields.split(",") if f.strip()]
                insert_row(db, table_name, row, indexed_fields)
            else:
                insert_row(db, table_name, row)
        elif cmd == "4":
            table_name = input("Название таблицы: ").strip()
            field = input("По какому полю искать (можно: email или address.city): ").strip()
            value = input("Значение для поиска: ").strip()
            select_by_index(db, table_name, field, value)
        elif cmd == "5":
            table_name = input("Название таблицы для удаления: ").strip()
            drop_table(db, table_name)
        elif cmd == "6":
            print("Сохраняем и выходим.")
            save_db(db)
            break
        else:
            print("Неизвестная команда.")

if __name__ == "__main__":
    main()

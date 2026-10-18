import json
import os
import time
import threading
import hashlib
import shutil
from datetime import datetime

DB_PATH = "./json_db_storage"
LOCK = threading.Lock()

def _ensure_db():
    if not os.path.exists(DB_PATH):
        os.makedirs(DB_PATH)

def _get_table_path(table_name):
    return os.path.join(DB_PATH, f"{table_name}.json")

def _generate_id(data):
    string_data = json.dumps(data, sort_keys=True) + str(time.time())
    return hashlib.md5(string_data.encode()).hexdigest()[:16]

def _read_db(table_name):
    path = _get_table_path(table_name)
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_db(table_name, data):
    path = _get_table_path(table_name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def create_table(table_name):
    """Проектирование: создание структуры таблицы"""
    _ensure_db()
    path = _get_table_path(table_name)
    if not os.path.exists(path):
        schema = {"__metadata__": {"created": datetime.now().isoformat(), "records": 0}}
        _write_db(table_name, schema)
        return True
    return False

def describe_table(table_name):
    """Сопровождение: описание структуры (наличие файла и метаданных)"""
    db = _read_db(table_name)
    if db:
        return db.get("__metadata__")
    return None

def insert(table_name, data):
    with LOCK:
        db = _read_db(table_name)
        if not db:
            return {"error": "Table not found"}
            
        record_id = _generate_id(data)
        data["id"] = record_id
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        db[record_id] = data
        db["__metadata__"]["records"] += 1
        _write_db(table_name, db)
        return {"status": "ok", "id": record_id}

def select(table_name, filters=None):
    db = _read_db(table_name)
    if not db:
        return []
        
    results = []
    for key, value in db.items():
        if key.startswith("__"):
            continue
        
        if not filters:
            results.append(value)
        else:
            if all(value.get(k) == v for k, v in filters.items()):
                results.append(value)
    return results

def update(table_name, record_id, new_data):
    with LOCK:
        db = _read_db(table_name)
        if not db or record_id not in db:
            return {"error": "Not found"}
            
        db[record_id].update(new_data)
        db[record_id]["updated_at"] = datetime.now().isoformat()
        _write_db(table_name, db)
        return {"status": "ok"}

def delete(table_name, record_id):
    with LOCK:
        db = _read_db(table_name)
        if not db or record_id not in db:
            return {"error": "Not found"}
            
        del db[record_id]
        db["__metadata__"]["records"] -= 1
        _write_db(table_name, db)
        return {"status": "ok"}


def optimize_table(table_name):
    """Сопровождение: дефрагментация файла (удаление пустот)"""
    with LOCK:
        db = _read_db(table_name)
        if not db:
            return False
        

        clean_db = {"__metadata__": db["__metadata__"]}
        count = 0
        for k, v in db.items():
            if not k.startswith("__"):
                clean_db[k] = v
                count += 1
        clean_db["__metadata__"]["records"] = count
        
        _write_db(table_name, clean_db)
        return True

def backup_database():
    """Сопровождение: полное резервное копирование БД"""
    _ensure_db()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(DB_PATH, f"backup_{ts}")
    os.makedirs(backup_dir)
    
    for file in os.listdir(DB_PATH):
        if file.endswith(".json") and not file.startswith("backup_"):
            shutil.copy2(os.path.join(DB_PATH, file), os.path.join(backup_dir, file))
    return backup_dir

def check_referential_integrity():
    """Сопровождение: проверка целостности связей"""
    issues = []
    orders_db = _read_db("orders")
    users_db = _read_db("users")
    
    if not orders_db or not users_db:
        return issues
        
    valid_user_ids = {uid for uid in users_db if not uid.startswith("__")}
    
    for oid, order in orders_db.items():
        if oid.startswith("__"):
            continue
        user_id = order.get("user_id")
        if user_id and user_id not in valid_user_ids:
            issues.append(f"Order '{order.get('product')}' (ID: {oid}) ссылается на несуществующего UserID: {user_id}")
    return issues


def main():
    print("=== JSON Database Design & Management System ===\n")
    

    if os.path.exists(DB_PATH):
        shutil.rmtree(DB_PATH)


    print("[ЭТАП 1] Проектирование схемы данных")
    create_table("users")
    create_table("orders")
    create_table("products")
 
    insert("products", {"name": "Laptop Pro", "price": 120000, "stock": 5})
    insert("products", {"name": "Mouse Wireless", "price": 2500, "stock": 50})
    
    print("\n[ЭТАП 2] Наполнение данными (Data Ingestion)")
    insert("users", {"name": "Alexey", "email": "alex@corp.ru", "dept": "IT"})
    insert("users", {"name": "Dmitry", "email": "dmitry@corp.ru", "dept": "Sales"})
    
   
    users = select("users", {"email": "alex@corp.ru"})
    products = select("products", {"name": "Laptop Pro"})
    
    if users and products:
        insert("orders", {
            "user_id": users[0]["id"], 
            "product_id": products[0]["id"], 
            "quantity": 1,
            "status": "pending"
        })
        
        insert("orders", {
            "user_id": users[0]["id"], 
            "product_id": products[0]["id"], 
            "quantity": 2,
            "status": "shipped"
        })

    # 3. УПРАВЛЕНИЕ И МОНИТОРИНГ (Admin & Monitoring)
    print("\n[ЭТАП 3] Мониторинг состояния БД")
    for tbl in ["users", "orders", "products"]:
        meta = describe_table(tbl)
        print(f"  -> {tbl}: {meta['records']} записей | Создана: {meta['created'][:10]}")

    # 4. СОПРОВОЖДЕНИЕ (Maintenance: Optimization & Backup)
    print("\n[ЭТАП 4] Техническое обслуживание")
    print("  * Выполняем удаление тестовой записи для создания фрагментации...")
    all_users = select("users")
    if all_users:
        delete("users", all_users[0]["id"])
    
    print("  * Запуск дефрагментации (Optimize)...")
    optimize_table("users")
    print(f"  * Результат: {describe_table('users')['records']} записей (файл очищен).")
    
    print("  * Создание резервной копии...")
    backup_path = backup_database()
    print(f"  * Бэкап сохранен: {backup_path}")

    print("\n[ЭТАП 5] Аудит данных и целостности")
    
    large_orders = select("orders", {"quantity": 2}) 
    if large_orders:
        print("  [AUDIT] Найден заказ с увеличенным количеством:")
        for o in large_orders:
            print(f"    - ID: {o['id']} | Товар: {o['product_id']} | Кол-во: {o['quantity']}")

    integrity_issues = check_referential_integrity()
    if integrity_issues:
        print("  [AUDIT] Обнаружены нарушения целостности (Orphaned Records):")
        for issue in integrity_issues:
            print(f"    - {issue}")
    else:
        print("  [AUDIT] Ссылочная целостность: OK")

    print("\n[ЭТАП 6] Бизнес-аналитика (Joins эмуляция)")
    print("  Список заказов с именами клиентов:")
    for order in select("orders"):
        user = select("users", {"id": order["user_id"]})
        user_name = user[0]["name"] if user else "Unknown"
        print(f"    - Заказ {order['id']} от {user_name} на сумму: {order.get('quantity', 1) * 1000} руб.") # Упрощенная цена
        
    # Отчет по отделам
    print("\n  Статистика по отделам:")
    it_users = select("users", {"dept": "IT"})
    sales_users = select("users", {"dept": "Sales"})
    print(f"    - IT отдел: {len(it_users)} чел.")
    print(f"    - Sales отдел: {len(sales_users)} чел.")

if __name__ == "__main__":
    main()
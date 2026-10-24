import json
import os
import threading
import hashlib
import shutil
import time
from datetime import datetime
from collections import defaultdict

DB_DIR = "./complex_json_db"
WAL_LOG_FILE = os.path.join(DB_DIR, "wal.log")
SCHEMA_FILE = os.path.join(DB_DIR, "schema.json")
LOCK = threading.Lock()

def _init_fs():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

def _get_table_path(table):
    return os.path.join(DB_DIR, f"{table}.json")

def _read_table(table):
    path = _get_table_path(table)
    if not os.path.exists(path):
        return {"__data__": {}, "__metadata__": {"created": datetime.now().isoformat(), "records": 0, "indexes": {}}}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_table(table, data):
    path = _get_table_path(table)
    # Блокируем запись на уровне ОС, чтобы триггеры не конфликтовали с основным потоком
    with LOCK:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

def _update_index(table, field, old_val, new_val, record_id):
    db = _read_table(table)
    indexes = db["__metadata__"]["indexes"]
    
    if field not in indexes:
        return
    
    index_name = f"{table}_{field}_idx"
    
    # Инициализируем индекс, если его еще нет в файле (важно для первого добавления)
    if index_name not in db:
        db[index_name] = {}

    # Конвертируем множества индексов в списки для JSON
    if old_val is not None:
        if old_val in db[index_name]:
            # Если в индексе множество, работаем с ним, иначе со списком
            container = db[index_name][old_val]
            if isinstance(container, set):
                container.discard(record_id)
            else:
                container.discard(record_id) if hasattr(container, 'discard') else None
                if record_id in container:
                    container.remove(record_id)
            if not db[index_name][old_val]:
                del db[index_name][old_val]

    if new_val is not None:
        if new_val not in db[index_name]:
            # Создаем множество для быстрой работы в памяти
            db[index_name][new_val] = set()
        db[index_name][new_val].add(record_id)
        
    # Перед сохранением конвертируем все множества в списках в списки
    for key, val in db.get(index_name, {}).items():
        if isinstance(val, set):
            db[index_name][key] = list(val)
            
    _write_table(table, db)

def _select_by_index(table, field, value):
    db = _read_table(table)
    indexes = db["__metadata__"]["indexes"]
    if field not in indexes:
        return None
        
    index_name = f"{table}_{field}_idx"
    if value not in db.get(index_name, {}):
        return []
        
    # В файле индексы лежат как списки, для работы превращаем обратно в set
    record_ids = set(db[index_name][value])
    return [db["__data__"][rid] for rid in record_ids if rid in db["__data__"]]

def _wal_append(action):
    with LOCK:
        with open(WAL_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(action, ensure_ascii=False) + "\n")

def _wal_clear():
    if os.path.exists(WAL_LOG_FILE):
        os.remove(WAL_LOG_FILE)

def _wal_replay():
    if not os.path.exists(WAL_LOG_FILE):
        return
    print("[WAL] Выполняется восстановление...")
    with open(WAL_LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    act = entry["action"]
                    if act["type"] == "insert":
                        __force_insert(act["table"], act["data"])
                    elif act["type"] == "update":
                        __force_update(act["table"], act["id"], act["new_data"], act["old_data"])
                    elif act["type"] == "delete":
                        __force_delete(act["table"], act["id"], act["data"])
                except Exception:
                    continue
    _wal_clear()

def __force_insert(table, data):
    db = _read_table(table)
    db["__data__"][data["id"]] = data
    db["__metadata__"]["records"] += 1
    for field in db["__metadata__"]["indexes"].keys():
        _update_index(table, field, None, data.get(field), data["id"])
    _write_table(table, db)

def __force_update(table, record_id, new_data, old_data):
    db = _read_table(table)
    if record_id in db["__data__"]:
        db["__data__"][record_id].update(new_data)
        for field in db["__metadata__"]["indexes"].keys():
            _update_index(table, field, old_data.get(field), new_data.get(field), record_id)
        _write_table(table, db)

def __force_delete(table, record_id, data):
    db = _read_table(table)
    if record_id in db["__data__"]:
        del db["__data__"][record_id]
        db["__metadata__"]["records"] -= 1
        for field in db["__metadata__"]["indexes"].keys():
            _update_index(table, field, data.get(field), None, record_id)
        _write_table(table, db)

def create_table(table, indexes=None):
    _init_fs()
    path = _get_table_path(table)
    if not os.path.exists(path):
        data = {
            "__data__": {},
            "__metadata__": {"created": datetime.now().isoformat(), "records": 0, "indexes": indexes or {}}
        }
        for idx_field in (indexes or {}):
            data[f"{table}_{idx_field}_idx"] = {}
        _write_table(table, data)
        return True
    return False

def create_trigger(table, event, func):
    if not hasattr(create_trigger, "registry"):
        create_trigger.registry = defaultdict(list)
    create_trigger.registry[(table, event)].append(func)

def _execute_triggers(table, event, **kwargs):
    if hasattr(create_trigger, "registry"):
        for func in create_trigger.registry.get((table, event), []):
            func(**kwargs)

def insert(table, data):
    record_id = hashlib.md5((json.dumps(data, sort_keys=True) + str(time.time())).encode()).hexdigest()[:12]
    data["id"] = record_id
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    _wal_append({"timestamp": datetime.now().isoformat(), "action": {"type": "insert", "table": table, "data": data}})
    __force_insert(table, data)
    _execute_triggers(table, "AFTER_INSERT", record=data)
    return record_id

def update(table, record_id, new_data):
    db = _read_table(table)
    if record_id not in db["__data__"]:
        return {"error": "Not found"}
    old_data = db["__data__"][record_id].copy()
    new_data["updated_at"] = datetime.now().isoformat()
    _wal_append({"timestamp": datetime.now().isoformat(), "action": {"type": "update", "table": table, "id": record_id, "new_data": new_data, "old_data": old_data}})
    __force_update(table, record_id, new_data, old_data)
    _execute_triggers(table, "AFTER_UPDATE", record_id=record_id, old_data=old_data, new_data={**old_data, **new_data})
    return {"status": "ok"}

def delete(table, record_id):
    db = _read_table(table)
    if record_id not in db["__data__"]:
        return {"error": "Not found"}
    data = db["__data__"][record_id]
    _wal_append({"timestamp": datetime.now().isoformat(), "action": {"type": "delete", "table": table, "id": record_id, "data": data}})
    __force_delete(table, record_id, data)
    _execute_triggers(table, "AFTER_DELETE", record=data)
    return {"status": "ok"}

def select(table, filters=None, use_index=True):
    if filters and use_index:
        field, value = next(iter(filters.items()))
        db = _read_table(table)
        if field in db["__metadata__"]["indexes"]:
            return _select_by_index(table, field, value)
    db = _read_table(table)
    results = []
    for v in db["__data__"].values():
        if not filters or all(v.get(k) == val for k, val in filters.items()):
            results.append(v)
    return results

def create_view(name, query_func):
    if not hasattr(create_view, "views"):
        create_view.views = {}
    create_view.views[name] = query_func

def select_view(name):
    if not hasattr(create_view, "views") or name not in create_view.views:
        return {"error": "View not found"}
    return create_view.views[name]()

def aggregate(table, field, operation):
    data = select(table)
    values = [item.get(field) for item in data if isinstance(item.get(field), (int, float))]
    if operation == "count":
        return len(values)
    if operation == "sum":
        return sum(values)
    if operation == "avg":
        return sum(values) / len(values) if values else 0
    return None

def _stock_update_trigger(**kwargs):
    record = kwargs.get("record", {})
    product_id = record.get("product_id")
    qty = record.get("quantity", 0)
    if product_id and qty > 0:
        prod = select("products", {"id": product_id})
        if prod:
            current_stock = prod[0].get("stock", 0)
            new_stock = max(0, current_stock - qty)
            # Исправлено: передаем record_id (UUID), а не product_id (SKU)
            update("products", product_id, {"stock": new_stock})
            print(f"[TRIGGER] Остаток товара {product_id} изменен: {current_stock} -> {new_stock}")

def _user_balance_trigger(**kwargs):
    pass

create_trigger("orders", "AFTER_INSERT", _stock_update_trigger)
create_trigger("orders", "AFTER_INSERT", _user_balance_trigger)

def main():
    print("=== Complex JSON DB: Indexes, Triggers, Views ===\n")
    _init_fs()
    _wal_replay()

    print("[1] Проектирование схемы...")
    create_table("users", indexes={"email": "unique"})
    create_table("products", indexes={"sku": "unique"})
    create_table("orders", indexes={"user_id": "btree", "product_id": "btree"})

    print("[2] Создание представления 'order_details_view'...")
    def get_order_details():
        orders = select("orders")
        users = {u["id"]: u["name"] for u in select("users")}
        products = {p["id"]: p["name"] for p in select("products")}
        
        view_data = []
        for o in orders:
            view_data.append({
                "order_id": o["id"],
                "user_name": users.get(o["user_id"], "N/A"),
                "product_name": products.get(o["product_id"], "N/A"),
                "qty": o["quantity"],
                "total": o["quantity"] * 100
            })
        return view_data
        
    create_view("order_details_view", get_order_details)

    print("\n[3] Наполнение данными (Транзакция)...")
    
    def begin_transaction():
        LOCK.acquire()

    def commit_transaction():
        _wal_clear()
        if LOCK.locked():
            LOCK.release()

    def rollback_transaction():
        _wal_clear()
        if LOCK.locked():
            LOCK.release()

    try:
        begin_transaction()
        
        u1 = insert("users", {"name": "Alex", "email": "alex@corp.ru"})
        u2 = insert("users", {"name": "Jane", "email": "jane@corp.ru"})
        
        p1 = insert("products", {"name": "Laptop", "sku": "LP-001", "stock": 10})
        p2 = insert("products", {"name": "Mouse", "sku": "MS-002", "stock": 50})
        
        insert("orders", {"user_id": u1, "product_id": p2, "quantity": 5})
        insert("orders", {"user_id": u2, "product_id": p1, "quantity": 1})
        
        commit_transaction()
        print("Транзакция завершена.\n")
    except Exception as e:
        rollback_transaction()
        print(f"Ошибка транзакции: {e}")

    print("[4] Поиск по индексу (SKU=MS-002):")
    fast_result = select("products", {"sku": "MS-002"})
    # Добавлена проверка на пустой результат
    if fast_result:
        print(fast_result[0])
    else:
        print("Товар не найден. Проверьте создание индекса 'unique'.")

    print("\n[5] Аналитика (Aggregate):")
    print(f"  Всего пользователей: {aggregate('users', 'id', 'count')}")
    print(f"  Сумма всех заказов (кол-во): {aggregate('orders', 'quantity', 'sum')}")

    print("\n[6] Данные из представления (JOIN):")
    for row in select_view("order_details_view"):
        print(f"  Заказ {row['order_id']}: {row['user_name']} купил {row['qty']}x {row['product_name']}")

    print("\n[7] Проверка остатков после триггера:")
    print(select("products", {"name": "Mouse"}))

if __name__ == "__main__":
    main()
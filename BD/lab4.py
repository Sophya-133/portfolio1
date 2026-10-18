import json
import os
import threading
import hashlib
import shutil
import time
from datetime import datetime

DB_DIR = "./adv_json_db"
WAL_LOG_FILE = os.path.join(DB_DIR, "write_ahead.log")
MIGRATIONS_DIR = os.path.join(DB_DIR, "migrations")
SCHEMA_VERSION_FILE = os.path.join(DB_DIR, "schema_version.json")

LOCK = threading.Lock()
_in_transaction = False  

def _init_fs():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    if not os.path.exists(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR)

def _wal_append(action):
    with open(WAL_LOG_FILE, 'a', encoding='utf-8') as f:
        entry = {"timestamp": datetime.now().isoformat(), "action": action}
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def _wal_clear():
    if os.path.exists(WAL_LOG_FILE):
        os.remove(WAL_LOG_FILE)

def _wal_replay():
    if not os.path.exists(WAL_LOG_FILE):
        return
    print("[WAL] Восстановление после сбоя...")
    with open(WAL_LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    action = entry["action"]
                    if action["type"] == "insert":
                        _force_insert(action["table"], action["data"])
                    elif action["type"] == "update":
                        _force_update(action["table"], action["id"], action["data"])
                    elif action["type"] == "delete":
                        _force_delete(action["table"], action["id"])
                except Exception:
                    continue
    _wal_clear()

def _get_table_path(table):
    return os.path.join(DB_DIR, f"{table}.json")

def _read_table(table):
    path = _get_table_path(table)
    if not os.path.exists(path):
        return {"__metadata__": {"created": datetime.now().isoformat(), "records": 0}}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_table(table, data):
    path = _get_table_path(table)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _force_insert(table, data):
    db = _read_table(table)
    db[data["id"]] = data
    db["__metadata__"]["records"] += 1
    _write_table(table, db)

def _force_update(table, record_id, data):
    db = _read_table(table)
    if record_id in db:
        db[record_id].update(data)
        _write_table(table, db)

def _force_delete(table, record_id):
    db = _read_table(table)
    if record_id in db:
        del db[record_id]
        db["__metadata__"]["records"] -= 1
        _write_table(table, db)

def begin_transaction():
    global _in_transaction
    LOCK.acquire()
    _in_transaction = True

def commit_transaction():
    global _in_transaction
    _wal_clear()
    if LOCK.locked():
        LOCK.release()
    _in_transaction = False

def rollback_transaction():
    global _in_transaction
    _wal_clear()
    if LOCK.locked():
        LOCK.release()
    _in_transaction = False

def insert(table, data):
    record_id = hashlib.md5((json.dumps(data, sort_keys=True) + str(time.time())).encode()).hexdigest()[:12]
    data["id"] = record_id
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    _wal_append({"type": "insert", "table": table, "data": data})
    _force_insert(table, data)
    return record_id

def update(table, record_id, data):
    data["updated_at"] = datetime.now().isoformat()
    _wal_append({"type": "update", "table": table, "id": record_id, "data": data})
    _force_update(table, record_id, data)

def delete(table, record_id):
    _wal_append({"type": "delete", "table": table, "id": record_id})
    _force_delete(table, record_id)

def select(table, filters=None):
    db = _read_table(table)
    results = []
    for k, v in db.items():
        if k.startswith("__"):
            continue
        if not filters or all(v.get(fk) == fv for fk, fv in filters.items()):
            results.append(v)
    return results

def create_table(table):
    path = _get_table_path(table)
    if not os.path.exists(path):
        schema = {"__metadata__": {"created": datetime.now().isoformat(), "records": 0}}
        _write_table(table, schema)
        return True
    return False

def _get_schema_version():
    if not os.path.exists(SCHEMA_VERSION_FILE):
        return 0
    with open(SCHEMA_VERSION_FILE, 'r', encoding='utf-8') as f:
        return json.load(f).get("version", 0)

def _set_schema_version(version):
    with open(SCHEMA_VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump({"version": version, "updated": datetime.now().isoformat()}, f)

def create_migration(name):
    version = _get_schema_version() + 1
    filename = f"{version:03d}_{name}.py"
    path = os.path.join(MIGRATIONS_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# Migration {version}: {name}\n\ndef up(): pass\n\ndef down(): pass\n")
    print(f"[MIGRATION] Создана заглушка: {filename}")

def run_migrations():
    current_version = _get_schema_version()
    files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.py')])
    
    for file in files:
        mig_version = int(file[:3])
        if mig_version > current_version:
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("mig", os.path.join(MIGRATIONS_DIR, file))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"[MIGRATION] Применена {file}")
                module.up()
                _set_schema_version(mig_version)
            except Exception as e:
                print(f"[MIGRATION][ERROR] {file}: {e}")

def backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = f"{DB_DIR}_backup_{ts}"
    shutil.copytree(DB_DIR, dest, ignore=shutil.ignore_patterns('write_ahead.log'))
    return dest

def check_health():
    issues = []
    if os.path.exists(WAL_LOG_FILE):
        issues.append("Обнаружен незавершенный WAL (требуется _wal_replay).")
    return issues

def _bootstrap_schema():
    """Создание базовых таблиц при первом запуске"""
    if _get_schema_version() == 0:
        print("[SETUP] Инициализация базы данных (v1)...")
        create_table("departments")
        create_table("employees")
        _set_schema_version(1)

def main():
    print("=== Advanced JSON DB: WAL + Migrations (Fixed) ===\n")
    _init_fs()
    
    _wal_replay()
    
    _bootstrap_schema()
    
    run_migrations()
    
    print("\n[TXN] Запись данных...")
    begin_transaction()
    try:

        dept_id = insert("departments", {"name": "Engineering"})
        
        insert("employees", {"name": "Ivan", "dept_id": dept_id, "salary": 150000})
        insert("employees", {"name": "Pyotr", "dept_id": dept_id, "salary": 120000})
        
        commit_transaction()
        print("Транзакция зафиксирована (COMMIT).")
    except Exception as e:
        rollback_transaction()
        print(f"!!! ROLLBACK. Ошибка: {e}")

    print("\n[QUERY] Текущее состояние БД:")
    print("Отделы:")
    for d in select("departments"):
        print(f" - {d['name']} (ID: {d['id']})")
        
    print("\nСотрудники:")
    for e in select("employees"):
        print(f" - {e['name']}: {e['salary']} руб.")

    print("\n[MAINTENANCE] Состояние системы:")
    health = check_health()
    if health:
        for h in health: print(f" - [WARN] {h}")
    else:
        print(" - Статус: OK")
        
    backup_path = backup()
    print(f" - Бэкап сохранен: {backup_path}")

if __name__ == "__main__":
    main()
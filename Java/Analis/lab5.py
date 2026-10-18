import os
import json
import datetime
import subprocess
import platform
import time
import winreg

CONFIG_BASELINE = {
    "current_user_autostart": {
        "Teams": "allowed", 
        "OneDrive": "allowed"
    }
}


KNOWN_CVES = {
    "Google Chrome": {
        "115.0.0.0": ["CVE-2023-4762"],
    },
    "7-Zip": {
        "21.07": ["CVE-2022-29716"]
    },
    "Zoom": {
        "5.13.0": ["CVE-2023-2859"]
    }
}

AUDIT_INTERVAL = 3600 
BACKLOG_FILE = "user_vuln_backlog.json"
BASELINE_FILE = "user_config_baseline.json"

def get_installed_programs():
    """Получает список ПО, видимого текущему пользователю (HKCU) и общего (HKLM)"""
    programs = {}
    keys_to_check = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hive, key_path in keys_to_check:
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                        programs[name] = version
                    except FileNotFoundError:
                        pass
                    winreg.CloseKey(subkey)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except FileNotFoundError:
            continue
        except PermissionError:
            continue 
    return programs

def check_vulnerabilities():
    findings = []
    installed = get_installed_programs()
    
    for pkg_name, pkg_version in installed.items():
        if pkg_name in KNOWN_CVES:
            if pkg_version in KNOWN_CVES[pkg_name]:
                for cve in KNOWN_CVES[pkg_name][pkg_version]:
                    findings.append({
                        "type": "cve",
                        "package": pkg_name,
                        "version": pkg_version,
                        "cve_id": cve,
                        "description": f"Уязвимость {cve} в {pkg_name} v{pkg_version}."
                    })
    return findings

def check_users():
    """Проверяет наличие встроенных учетных записей (Guest) через WMI-подобный вызов"""
    findings = []
    try:

        result = subprocess.run(['net', 'user'], capture_output=True, text=True, encoding='cp866')
        lines = result.stdout.splitlines()
        if "Alias name" in lines[0]: 
            users = [line.strip() for line in lines if line and not line.startswith("---------------------------------")]
            for user in users:
                if user.lower() == 'guest':
                    findings.append({
                        "type": "weak_account",
                        "username": user,
                        "description": "Встроенная учетная запись Guest активна."
                    })
    except Exception:
        pass
    return findings

def check_current_user_autostart():
    findings = []
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        i = 0
        current_autostart = {}
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                current_autostart[name] = value
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)

        for app, status in CONFIG_BASELINE["current_user_autostart"].items():
            if status == "forbidden" and app in current_autostart:
                findings.append({
                    "type": "compliance_fail",
                    "component": "autostart",
                    "key": app,
                    "description": f"Запрещенное приложение '{app}' находится в автозагрузке пользователя."
                })
    except FileNotFoundError:
        pass
    return findings

def load_json_file(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default

def save_json_file(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_backlog(new_findings):
    backlog = load_json_file(BACKLOG_FILE, {})
    
    for finding in new_findings:
        key = f"{finding['type']}-{finding.get('cve_id') or finding.get('component') or finding.get('username')}"
        
        if key not in backlog:
            finding["id"] = key
            finding["status"] = "new"
            finding["created_at"] = datetime.datetime.now().isoformat()
            finding["assigned_to"] = "unassigned"
            backlog[key] = finding
            
    save_json_file(BACKLOG_FILE, backlog)
    return backlog

def check_baseline_drift():
    findings = []
    current_baseline = {"autostart": {}}
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                name, value, _ = winreg.EnumValue(key, i)
                current_baseline["autostart"][name] = value
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass

    if not os.path.exists(BASELINE_FILE):
        save_json_file(BASELINE_FILE, current_baseline)
        findings.append({"type": "baseline_info", "description": "Базлайн автозагрузки пользователя создан."})
    else:
        saved = load_json_file(BASELINE_FILE, {})
        saved_apps = set(saved.get("autostart", {}).keys())
        current_apps = set(current_baseline.get("autostart", {}).keys())
        
        added = current_apps - saved_apps
        removed = saved_apps - current_apps
        
        if added:
            findings.append({
                "type": "baseline_drift",
                "component": "autostart",
                "change": "added",
                "items": list(added),
                "description": "В автозагрузке появились новые приложения."
            })
        if removed:
            findings.append({
                "type": "baseline_drift",
                "component": "autostart",
                "change": "removed",
                "items": list(removed),
                "description": "Приложения исчезли из автозагрузки."
            })
            
    return findings

def run_full_audit():
    print(f"[{datetime.datetime.now()}] Запуск аудита (Пользователь: {os.getlogin()})...")
    
    all_findings = []
    all_findings.extend(check_vulnerabilities())
    all_findings.extend(check_users())
    all_findings.extend(check_current_user_autostart())
    all_findings.extend(check_baseline_drift())
    
    backlog = update_backlog(all_findings)
    
    print(f"\n=== ОТЧЕТ АУДИТА (User Mode) ===")
    print(f"Найдено новых/актуальных проблем: {len(all_findings)}")
    print(f"Всего записей в бэклоге: {len(backlog)}\n")
    
    new_issues = [v for v in all_findings if v.get('status') == 'new']
    if new_issues:
        print("НОВЫЕ НАХОДКИ:")
        for v in new_issues:
            print(f" - [{v['type'].upper()}] {v.get('cve_id') or v.get('component')}: {v['description']}")

def check_compliance():
    findings = []
    findings.extend(check_current_user_autostart())
    return findings

def main():
    print("Запуск планировщика аудита (без прав администратора).")
    print("Скрипт проверяет только ваши личные программы и настройки автозагрузки.\n")
    
    while True:
        try:
            run_full_audit()
        except KeyboardInterrupt:
            print("\nПланировщик остановлен.")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            
        print(f"Ожидание {AUDIT_INTERVAL // 60} минут...\n")
        time.sleep(AUDIT_INTERVAL)

if __name__ == "__main__":
    main()
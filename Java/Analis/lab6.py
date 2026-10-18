import os
import json
import datetime
import subprocess
import time
import winreg
import sqlite3
from urllib.parse import urlparse

SUSPICIOUS_DOMAINS = [
    "blackmarket-site.com", 
    "login-update-verify.com", 
    "mega-pack-download.ru"
]
LOCAL_NETWORK_RANGES = ["192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31."]
CLOUD_FOLDERS = ["OneDrive", "Google Drive", "Dropbox", "YandexDisk"]

AUDIT_INTERVAL = 1800  
BACKLOG_FILE = "user_behavior_backlog.json"
RISK_SCORE_FILE = "user_risk_score.json"


def check_process_integrity():
    findings = []
    try:
        result = subprocess.run(['wmic', 'process', 'get', 'ExecutablePath,Name,ProcessId', '/format:csv'], 
                                capture_output=True, text=True, encoding='cp866')
        lines = [l for l in result.splitlines() if l.strip()]
        
        for line in lines[1:]: 
            parts = line.split(',')
            if len(parts) < 3: continue
            
            pid, name, path = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
            
            if path and ('\\Temp\\' in path or '\\AppData\\Local\\Temp\\' in path):
                findings.append({
                    "type": "behavior_process",
                    "pid": pid,
                    "name": name,
                    "description": f"Процесс запущен из временной папки: {path}"
                })
            
            if name.lower() in ['explorer.exe', 'svchost.exe', 'winlogon.exe']:
                if not path.lower().startswith('c:\\windows\\'):
                    findings.append({
                        "type": "process_impersonation",
                        "pid": pid,
                        "name": name,
                        "path": path,
                        "description": f"Легитимное имя '{name}', но запущен из подозрительной директории."
                    })
    except Exception:
        pass
    return findings

def check_network_connections():
    findings = []
    try:
        result = subprocess.run(['netstat', '-ano', '-p', 'tcp'], capture_output=True, text=True, encoding='cp866')
        lines = result.stdout.splitlines()
        
        for line in lines:
            if 'ESTABLISHED' in line and '127.0.0.1' not in line:
                parts = line.split()
                if len(parts) >= 5:
                    local_addr, remote_addr, pid = parts[1], parts[2], parts[4]
                    
                    if any(remote_addr.startswith(ip) for ip in LOCAL_NETWORK_RANGES):
                        port = remote_addr.split(':')[-1]
                        findings.append({
                            "type": "lateral_movement",
                            "local": local_addr,
                            "remote": remote_addr,
                            "pid": pid,
                            "description": f"Установлено соединение с ПК в локальной сети (порт {port})."
                        })
    except Exception:
        pass
    return findings

def check_browser_history():
    findings = []
    local_appdata = os.environ['LOCALAPPDATA']
    chrome_history_path = os.path.join(local_appdata, r"Google\Chrome\User Data\Default\History")
    edge_history_path = os.path.join(local_appdata, r"Microsoft\Edge\User Data\Default\History")
    
    for path in [chrome_history_path, edge_history_path]:
        if os.path.exists(path):
            temp_path = path + ".tmp"
            try:
                import shutil
                shutil.copy2(path, temp_path)
                
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title FROM urls ORDER BY last_visit_time DESC LIMIT 500")
                rows = cursor.fetchall()
                
                for url, title in rows:
                    domain = urlparse(url).netloc
                    for susp in SUSPICIOUS_DOMAINS:
                        if susp in domain:
                            findings.append({
                                "type": "phishing_history",
                                "url": url,
                                "title": title,
                                "description": f"Обнаружено посещение подозрительного ресурса."
                            })
                            break
                conn.close()
            except Exception:
                continue
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
    return findings

def check_scheduled_tasks():
    findings = []
    try:
        result = subprocess.run(['schtasks', '/query', '/fo', 'csv', '/v'], capture_output=True, text=True, encoding='cp866')
        lines = result.splitlines()
        for line in lines[1:]:
            parts = line.split('","')
            if len(parts) > 10:
                task_name = parts[1].strip('"')
                run_as = parts[6].strip('"')
                task_path = parts[9].strip('"')
                
                if ('\\Temp\\' in task_path or '\\AppData\\Local\\Temp\\' in task_path) or 'Users\\' in run_as:
                    findings.append({
                        "type": "persistence_task",
                        "task": task_name,
                        "path": task_path,
                        "description": "Обнаружена подозрительная задача в планировщике."
                    })
    except Exception:
        pass
    return findings

def update_backlog_and_score(findings):
    backlog = {}
    if os.path.exists(BACKLOG_FILE):
        with open(BACKLOG_FILE, 'r', encoding='utf-8') as f:
            backlog = json.load(f)
            
    risk_score = 0
    if os.path.exists(RISK_SCORE_FILE):
        with open(RISK_SCORE_FILE, 'r', encoding='utf-8') as f:
            risk_score = json.load(f).get("score", 0)
            
    for f in findings:
        key = f"{f['type']}-{f.get('pid') or f.get('url') or f.get('task')}"
        if key not in backlog:
            f.update({
                "id": key,
                "status": "new",
                "created_at": datetime.datetime.now().isoformat()
            })
            backlog[key] = f
            risk_score += 10 
            
    with open(BACKLOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(backlog, f, indent=4, ensure_ascii=False)
        
    with open(RISK_SCORE_FILE, 'w', encoding='utf-8') as f:
        json.dump({"score": risk_score, "last_check": datetime.datetime.now().isoformat()}, f, indent=4)
        
    return backlog, risk_score

def run_audit():
    print(f"[{datetime.datetime.now()}] Старт поведенческого аудита...")
    
    all_findings = []
    all_findings.extend(check_process_integrity())
    all_findings.extend(check_network_connections())
    all_findings.extend(check_browser_history())
    all_findings.extend(check_scheduled_tasks())
    
    backlog, score = update_backlog_and_score(all_findings)
    
    print(f"\n=== ОТЧЕТ ПОВЕДЕНЧЕСКОГО АУДИТА ===")
    print(f"Уровень риска пользователя: {score}/100")
    print(f"Новых событий: {len(all_findings)} | Всего в бэклоге: {len(backlog)}\n")
    
    if all_findings:
        for f in all_findings:
            print(f" - [!] {f['description']}")
    
    if score > 70:
        print("\n!!! КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ !!!")
        print("Уровень риска аномально высок. Рекомендуется сменить пароли и проверить ПК антивирусом.")

def main():
    while True:
        try:
            run_audit()
        except KeyboardInterrupt:
            print("\nАудит остановлен.")
            break
        time.sleep(AUDIT_INTERVAL)

if __name__ == "__main__":
    main()
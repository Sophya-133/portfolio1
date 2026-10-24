import os
import stat
import json
import datetime
import subprocess
import platform

CRITICAL_FILES = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/group",
    "config.json",
    "settings.py" 
]
SESSION_DIRS = ["/tmp", "/var/tmp"]
AUDIT_DATE = datetime.datetime.now().isoformat()

def check_weak_passwords():
    """Проверяет наличие пользователей с пустыми паролями (только для Unix-подобных систем)"""
    vulnerabilities = []
    if os.name != 'posix':
        return vulnerabilities
        
    try:
        with open('/etc/shadow', 'r') as f:
            for line in f:
                parts = line.strip().split(':')
                if len(parts) > 1:
                    username = parts[0]
                    # Второй поле в /etc/shadow — хэш пароля. Если он пустой или '!', пароля нет.
                    if parts[1] in ['', '!']:
                        vulnerabilities.append({
                            "type": "weak_password",
                            "username": username,
                            "description": "Учетная запись имеет пустой или заблокированный пароль."
                        })
    except PermissionError:
        vulnerabilities.append({
            "type": "permission_error",
            "resource": "/etc/shadow",
            "description": "Недостаточно прав для проверки хэшей паролей."
        })
    except FileNotFoundError:
        pass 
    return vulnerabilities

def check_critical_files():
    """Проверяет права доступа к критическим файлам"""
    vulnerabilities = []
    for file_path in CRITICAL_FILES:
        if not os.path.exists(file_path):
            continue
            
        try:
            file_stat = os.stat(file_path)
            mode = stat.filemode(file_stat.st_mode)
         
            if mode[7] == 'w':
                vulnerabilities.append({
                    "type": "file_permission",
                    "path": file_path,
                    "permissions": mode,
                    "description": "Файл доступен для записи всем пользователям системы."
                })
        except PermissionError:
            vulnerabilities.append({
                "type": "permission_error",
                "resource": file_path,
                "description": "Недостаточно прав для проверки атрибутов файла."
            })
    return vulnerabilities

def check_suid_sgid():
    """Ищет исполняемые файлы с битами SUID/SGID (только для Unix)"""
    vulnerabilities = []
    if os.name != 'posix':
        return vulnerabilities

    for root, dirs, files in os.walk('/', topdown=True):

        dirs[:] = [d for d in dirs if not d.startswith('proc') and not d.startswith('sys') and not d.startswith('dev')]
        
        for name in files:
            path = os.path.join(root, name)
            try:
                file_stat = os.lstat(path)

                if file_stat.st_mode & (stat.S_ISUID | stat.S_ISGID):
                    vulnerabilities.append({
                        "type": "suid_sgid",
                        "path": path,
                        "description": f"Файл имеет повышенный бит привилегий ({'SUID' if file_stat.st_mode & stat.S_ISUID else ''}{' ' if file_stat.st_mode & stat.S_ISUID and file_stat.st_mode & stat.S_ISGID else ''}{'SGID' if file_stat.st_mode & stat.S_ISGID else ''})."
                    })
            except (PermissionError, FileNotFoundError):
                continue

        if root.count(os.sep) > 4: 
            break
    return vulnerabilities

def check_open_ports():
    """Проверяет открытые порты через системную утилиту netstat"""
    vulnerabilities = []
    try:

        param = '-ano' if platform.system() == 'Windows' else '-tuln'
        result = subprocess.run(['netstat', param], capture_output=True, text=True, check=True)
        lines = result.stdout.splitlines()
        
        for line in lines:
            if 'LISTEN' in line or 'LISTENING' in line:
                parts = line.split()
                local_addr = parts[-2] if platform.system() == 'Windows' else parts[3]
                if ':' in local_addr:
                    port = local_addr.split(':')[-1]
                    if port.isdigit() and int(port) < 1024:
                        vulnerabilities.append({
                            "type": "open_port",
                            "port": port,
                            "description": "Критический порт (<1024) находится в состоянии прослушивания."
                        })
    except (subprocess.SubprocessError, FileNotFoundError, IndexError):
        vulnerabilities.append({
            "type": "tool_error",
            "description": "Не удалось выполнить netstat для проверки открытых портов."
        })
    return vulnerabilities

def check_old_sessions():
    """Ищет старые файлы сессий в директориях /tmp"""
    vulnerabilities = []
    now = datetime.datetime.now().timestamp()

    threshold = 24 * 60 * 60 
    
    for session_dir in SESSION_DIRS:
        if not os.path.exists(session_dir):
            continue
        try:
            for entry in os.scandir(session_dir):
                if entry.is_file():
                    age = now - entry.stat().st_mtime
                    if age > threshold:
                        vulnerabilities.append({
                            "type": "old_session",
                            "path": entry.path,
                            "age_hours": round(age / 3600, 1),
                            "description": "Временный файл сессии не был удален после использования."
                        })
        except PermissionError:
            continue
    return vulnerabilities

def generate_report(vulns):
    """Собирает отчет и сохраняет его в JSON"""
    report = {
        "audit_date": AUDIT_DATE,
        "hostname": os.uname().nodename if hasattr(os, 'uname') else platform.node(),
        "os": platform.system(),
        "total_findings": len(vulns),
        "findings": vulns
    }
    
    with open("security_audit_report.json", "w") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    print(f"Аудит завершен. Найдено проблем: {len(vulns)}")
    print("Отчет сохранен в security_audit_report.json")
    
    if vulns:
        print("\nСводка уязвимостей:")
        for v in vulns:
            print(f"- [{v['type'].upper()}] {v.get('path') or v.get('username') or v.get('port')}: {v['description']}")

if __name__ == "__main__":
    all_vulnerabilities = []
    all_vulnerabilities.extend(check_weak_passwords())
    all_vulnerabilities.extend(check_critical_files())
    all_vulnerabilities.extend(check_suid_sgid())
    all_vulnerabilities.extend(check_open_ports())
    all_vulnerabilities.extend(check_old_sessions())
    
    generate_report(all_vulnerabilities)
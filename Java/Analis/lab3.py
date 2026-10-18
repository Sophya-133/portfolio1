import os
import re
import configparser
import json
import yaml
import html

DANGEROUS_KEYS = [
    'password', 'passwd', 'api_key', 'secret', 'token', 'private_key',
    'client_secret', 'aws_access_key_id', 'aws_secret_access_key',
    'db_password', 'db_user', 'ssh_key', 'auth_token'
]
PASSWORD_PATTERNS = [
    r'(?:password|passwd|api_key|secret|token|key|passwd_wd|auth_token)\s*=\s*["\']([^"\']+)["\']',
    r'(?:password|passwd|api_key|secret|token)\s*=\s*([a-zA-Z0-9_/+=@:.-]+)',
    r'set\s+password\s*$\s*["\']([^"\']+)["\']',
    r'#\s*(password|passwd|api_key|secret|token)\s*[:=]\s*["\']([^"\']+)["\']',
    r'(?:password|token|auth_token)\s*=\s*[^\n#]*',
    r'os\.environ\.get\("?(?P<key>[A-Z_]\w*)"?["\)]',
    r'sys\.argv\s*\[\d+\]\s*["\'](?P<arg>[^"\']+)["\']',
    r'requests\.Session\(.+\)\.auth\s*=\s*["\']([^"\']+)["\']',
    r'json\.load\([^"\']*(secrets|config|credentials)[^"\']*\)',
    r'secrets?\s*=\s*[^\n]+',
    r'secret_key\s*=\s*[^\n]+',
    r'private_key\s*=\s*[^\n]+',
    r'key\s*=\s*[^\n]+',
]

def find_python_files(directory):
    result = []
    for root, dirs, files in os.walk(directory):
        for fname in files:
            if fname.endswith('.py'):
                result.append(os.path.join(root, fname))
    return result

def audit_python(file_path):
    warnings = []
    if not os.path.isfile(file_path):
        return warnings

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        content = ''.join(lines)
        for lnum, line in enumerate(lines, 1):
            
            for pattern in PASSWORD_PATTERNS:
                flags = re.IGNORECASE if 're.IGNORECASE' not in str(pattern) else re.IGNORECASE
                matches = re.findall(pattern, line, flags=flags)
             
                for match in matches:
                    if isinstance(match, tuple):
                        
                        for part in match:
                            if part and len(part.strip()) > 3:
                                masked = '*' * len(part)
                                
                                msg = f"В Python-файле `{file_path}` строка {lnum}: "
                                if 'environ.get' in pattern:
                               
                                    if len(match) > 1 and match[1]:
                                        msg += f"Используется секрет из переменной окружения: os.environ.get('{match[0]}') = '{masked}'"
                                    else:
                                        msg += f"Используется функция os.environ.get с ключом: '{match[0]}'"
                                elif 'json.load' in pattern or 'secrets' in pattern:
                                   
                                    msg += f"Попытка загрузить секреты из файла (шаблон: {pattern})"
                                elif 'set password' in pattern:
                                    msg += f"Установка пароля в коде (строка: {line.strip()})"
                                else:
                                   
                                    msg += f"Найдено потенциальное секрет: '{part}'"
                                warnings.append((msg, 'warning'))
                                warnings.append((
                                    f"📌 Рекомендация: Секреты не должны храниться в исходном коде. "
                                    f"Используйте переменные окружения, Vault или конфигурационные файлы с защитой.",
                                    'info'
                                ))
                    else:
                    
                        if len(match.strip()) > 3:
                           
                            masked = match[:3] + '*' * (len(match) - 3)
                            msg = f"В Python-файле `{file_path}` строка {lnum}: найдено потенциальное секрет: {masked}"
                            warnings.append((msg, 'warning'))
                            warnings.append((
                                f"📌 Рекомендация: Перенесите секрет в защищённое место (переменную окружения, Vault и т.д.).",
                                'info'
                            ))


            
            if re.search(r'(json\.load|yaml\.load|config\.read|secrets\.load)\s*\([^"\']*(secrets?|config|credentials)[^"\']*\)', line, re.IGNORECASE):
                warnings.append((
                    f"⚠️ В Python-файле `{file_path}` строка {lnum}: Потенциально загружаются секреты из файла.",
                    'warning'
                ))
                warnings.append((
                    f"📌 Рекомендация: Не загружайте секреты напрямую из исходного кода. Используйте защищённые способы.",
                    'info'
                ))

           
            if re.search(r'(print|logging\.debug|logging\.info)\s*\([^"\']*(password|secret|token|key)[^"\']*\)', line, re.IGNORECASE):
                warnings.append((
                    f"⚠️ В Python-файле `{file_path}` строка {lnum}: Возможное раскрытие секрета через print/logging.",
                    'warning'
                ))
                warnings.append((
                    f"📌 Рекомендация: Не раскрывайте секреты в логах или stdout.",
                    'info'
                ))

         
            if '#' in line:
                comment = line.split('#', 1)[1].strip()
                for pattern in PASSWORD_PATTERNS:
                    for match in re.findall(pattern, comment, re.IGNORECASE):
                        for part in (match if isinstance(match, tuple) else (match,)):
                            if part and len(part.strip()) > 3:
                                warnings.append((
                                    f"⚠️ В Python-файле `{file_path}` строка {lnum} (в комментарии): найден потенциальный секрет '{part[:10]}{'*'*(len(part)-10 if len(part)>10 else 0)}'",
                                    'warning'
                                ))
                                warnings.append((
                                    f"📌 Рекомендация: Секреты не должны храниться даже в комментариях кода.",
                                    'info'
                                ))

    return warnings


def main(root_dir='.', output_html='security_report_python.html'):
    print("[*] Сбор Python-файлов...")
    python_files = find_python_files(root_dir)
    if not python_files:
        print("[-] Нет .py файлов для анализа.")
        return

    all_warnings = []

    for f in python_files:
        print(f"[+] Анализирую: {f}")
        w = audit_python(f)
        all_warnings.extend(w)

    
    print(f"[+] Генерируем отчёт: {output_html}")
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n<head>\n")
        f.write("    <title>Аудит секретов в Python-файлах</title>\n")
        f.write("    <style>\n")
        f.write("        body { font-family: sans-serif; background: #f9f9f9; color: #222; }\n")
        f.write("        .warning { color: #e74c3c; font-weight: bold; }\n")
        f.write("        .info { color: #2ecc71; }\n")
        f.write("        table { width: 100%; border-collapse: collapse; }\n")
        f.write("        th, td { padding: 8px; text-align: left; border: 1px solid #bbb; }\n")
        f.write("        th { background: #e6e6fa; }\n")
        f.write("    </style>\n")
        f.write("</head>\n<body>\n")
        f.write("<h1>Аудит секретов в Python-файлах</h1>\n")
        f.write("<table>\n")
        f.write("  <thead>\n    <tr>\n      <th>№</th><th>Файл</th><th>Строка</th><th>Проблема</th><th>Рекомендация</th>\n    </tr>\n  </thead>\n  <tbody>\n")
        row_idx = 1
        for warn in all_warnings:
            if not isinstance(warn, tuple) or len(warn) < 2:
                continue
            issue, level = warn[0], warn[1]
            rec = warn[2] if len(warn) > 2 else ''
            file_name = re.search(r'файл `([^`]+)`', issue, re.IGNORECASE)
            file_name = file_name.group(1) if file_name else ''
            m = re.search(r'строки\s*(\d+)', issue, re.IGNORECASE)
            line_num = m.group(1) if m else ''
            
            issue_short = (issue[:120] + '...') if len(issue) > 120 else issue
            f.write(f"<tr style='color: {'red' if level == 'warning' else 'orange'};'>\n")
            f.write(f"      <td>{row_idx}</td>\n")
            f.write(f"      <td>{html.escape(file_name)}</td>\n")
            f.write(f"      <td>{line_num}</td>\n")
            f.write(f"      <td class='{level}'>{issue_short}</td>\n")
            if rec:
                f.write(f"      <td class='info'>{rec}</td>\n")
            else:
                f.write(f"      <td></td>\n")
            f.write("    </tr>\n")
            row_idx += 1
        f.write("  </tbody>\n</table>\n")
        f.write("</body>\n</html>\n")
    print(f"[+] Отчёт готов: {output_html}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Рекурсивный аудит секретов только в Python-файлах')
    parser.add_argument('dir', nargs='?', default='.', help='Корневая директория (по умолчанию текущая)')
    parser.add_argument('--output', '-o', default='security_report_python.html', help='Имя HTML отчёта')
    args = parser.parse_args()
    main(args.dir, args.output)

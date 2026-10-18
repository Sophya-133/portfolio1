import os
import re
import yaml
import json
import configparser
from colorama import Fore, Style  # Для цветов в консоли (опционально)
import html

# Список опасных ключей и регулярных паттернов
DANGEROUS_KEYS = [
    'password', 'passwd', 'api_key', 'secret', 'token', 'private_key', 'client_secret'
]
DANGEROUS_SECTIONS = ['database', 'db', 'sql', 'api']

# Регулярки для поиска паролей в Python-кодах
PASSWORD_PATTERNS = [
    r'(?:password|passwd|api_key|secret|token)\s*=\s*["\']([^"\']+)["\']',
    r'(?:password|passwd|api_key|secret|token)\s*=\s*([a-zA-Z0-9_/+=@:.-]+)',  # без кавычек
    r'(?:set\s+password|setPassword)\s*\(\s*["\']([^"\']+)["\']\s*\)',
]

# Функция для поиска в INI
def audit_ini(file_path):
    warnings = []
    if not os.path.isfile(file_path):
        return warnings

    config = configparser.ConfigParser()
    try:
        config.read(file_path)
    except Exception as e:
        return [(f"❌ Не удалось прочитать INI-файл {file_path}: {e}", 'error')]

    for section in config.sections():
        if any(sec.lower() in section.lower() for sec in DANGEROUS_SECTIONS):
            warnings.append(
                (
                    f"⚠️ Опасная секция: `{section}`",
                    'warning'
                )
            )
        for key, value in config.items(section):
            if key.lower() in [k.lower() for k in DANGEROUS_KEYS]:
                masked = '*' * len(str(value))
                warnings.append(
                    (
                        f"⚠️ В секции `{section}` найден ключ `{key}` с значением: {masked}",
                        'warning'
                    )
                )
                if isinstance(value, str) and any(kw in key.lower() for kw in ['password', 'secret', 'token']):
                    warnings.append(
                        (
                            f"📌 Рекомендация: Не храните пароли в открытом виде. Используйте хеширование.",
                            'info'
                        )
                    )

    return warnings

# Анализ YAML
def audit_yaml(file_path):
    warnings = []
    if not os.path.isfile(file_path):
        return warnings

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return [(f"❌ Не удалось прочитать YAML-файл {file_path}: {e}", 'error')]

    def recurse(obj, path=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(k.lower() in dk.lower() for dk in DANGEROUS_KEYS):
                    masked = '*' * len(str(v)) if isinstance(v, str) else str(v)
                    warnings.append(
                        (
                            f"⚠️ В YAML-файле `{path}.{k}` найдено значение: {masked}",
                            'warning'
                        )
                    )
                    if isinstance(v, str) and any(kw in k.lower() for kw in ['password', 'secret', 'token']):
                        warnings.append(
                            (
                                f"📌 Рекомендация: Значение `{k}` содержит секрет. Храните его защищённо.",
                                'info'
                            )
                        )
                recurse(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                recurse(item, f"{path}[{i}]")

    recurse(data)
    return warnings

# Анализ JSON
def audit_json(file_path):
    warnings = []
    if not os.path.isfile(file_path):
        return warnings

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return [(f"❌ Не удалось прочитать JSON-файл {file_path}: {e}", 'error')]

    def recurse(obj, path=''):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(k.lower() in dk.lower() for dk in DANGEROUS_KEYS):
                    masked = '*' * len(str(v)) if isinstance(v, str) else str(v)
                    warnings.append(
                        (
                            f"⚠️ В JSON-файле `{path}.{k}` найдено значение: {masked}",
                            'warning'
                        )
                    )
                    if isinstance(v, str) and any(kw in k.lower() for kw in ['password', 'secret', 'token']):
                        warnings.append(
                            (
                                f"📌 Рекомендация: Не храните пароли в открытом виде в JSON.",
                                'info'
                            )
                        )
                recurse(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                recurse(item, f"{path}[{i}]")

    recurse(data)
    return warnings

# Анализ Python-скриптов
def audit_python(file_path):
    warnings = []
    if not os.path.isfile(file_path):
        return warnings

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ищем пароли и секреты в строках
    for pattern in PASSWORD_PATTERNS:
        for match in re.findall(pattern, content):
            # match[0] — найденное значение
            warnings.append(
                (
                    f"⚠️ В Python-файле `{file_path}` найдено возможное хранение пароля/секрета: {'*' * len(match[0])}",
                    'warning'
                )
            )
            warnings.append(
                (
                    f"📌 Рекомендация: Не храните пароли прямо в коде. Используйте переменные окружения или vault.",
                    'info'
                )
            )

    # Также ищем явные комментарии с паролями
    for line in content.splitlines():
        if re.search(r'(password|passwd|api_key|secret|token)\s*[:=]\s*[\'"]([^\'"]+)[\'"]', line, re.I):
            masked = '*' * len(re.search(r'(password|passwd|api_key|secret|token)\s*[:=]\s*[\'"]([^\'"]+)[\'"]', line, re.I).group(2))
            warnings.append(
                (
                    f"⚠️ В Python-файле `{file_path}` найден потенциальный пароль/секрет в комментарии: {masked}",
                    'warning'
                )
            )
            warnings.append(
                (
                    f"📌 Рекомендация: Удалите или зашифруйте такие значения из кода.",
                    'info'
                )
            )

    return warnings

# Генерация HTML-отчёта
def generate_html_report(results, output_file='audit_report.html'):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Аудит конфигов и скриптов</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .ok { color: green; }
        .warning { color: red; background: #ffe0e0; padding: 5px 10px; border-radius: 5px; }
        .info { color: #336; }
        .error { color: #c00; background: #ffe0e0; }
    </style>
</head>
<body>
    <h1>Результаты аудита безопасности</h1>
    <table border="1" cellpadding="4" style="width:100%; border-collapse: collapse;">
        <tr><th>Найдено</th><th>Описание</th><th>Рекомендация</th></tr>
""")
        for msg, level in results:
            color = ''
            if level == 'warning':
                color = '<td class="warning">'
            elif level == 'info':
                color = '<td class="info">'
            elif level == 'error':
                color = '<td class="error">'
            else:
                color = '<td>'

            f.write(f"{color}")
            if level in ['warning', 'error']:
                f.write(f"<b>{msg}</b><br>")
            else:
                f.write(f"{msg}<br>")
            if 'Рекомендация:' in msg:
                f.write('<td colspan="2" class="info">' + msg.split('Рекомендация:')[1].strip() + '</td>')
            else:
                f.write('<td>Следите, чтобы секреты не лежали открытыми. Используйте хранение в vault/ENV.</td>')
            f.write("</td><td></td></tr>")
        f.write("""
    </table>
    <p>Аудит завершён.</p>
</body>
</html>
""")

def find_files(directory, extensions):
    """Возвращает список файлов с нужными расширениями"""
    result = []
    for root, dirs, files in os.walk(directory):
        for fname in files:
            if any(fname.lower().endswith(ext) for ext in extensions):
                result.append(os.path.join(root, fname))
    return result

def main():
    target_dir = input("Введите путь к папке для аудита (или нажмите Enter для текущей директории): ").strip()
    if not target_dir:
        target_dir = os.getcwd()
    print(f"Аудитирую папку: {target_dir}")

    extensions = ['.ini', '.yaml', '.yml', '.json', '.py']
    files = find_files(target_dir, extensions)
    print("Находящиеся файлы для аудита:")
    for f in files:
        print(f"  - {f}")

    all_results = []

    for f in files:
        print(f"\nАнализирую: {f}")
        if f.lower().endswith('.ini'):
            all_results.extend(audit_ini(f))
        elif f.lower().endswith(('.yaml', '.yml')):
            all_results.extend(audit_yaml(f))
        elif f.lower().endswith('.json'):
            all_results.extend(audit_json(f))
        elif f.lower().endswith('.py'):
            all_results.extend(audit_python(f))

    # Если ничего не найдено — сообщение
    if not all_results:
        all_results.append(("✅ Никаких опасных настроек или явно видных уязвимостей не обнаружено.", 'ok'))

    # Генерируем отчёт
    generate_html_report(all_results, 'audit_report.html')
    print("\nОтчёт готов: audit_report.html")

    # (Опционально) Открываем отчёт в браузере (только на Windows)
    import webbrowser
    try:
        webbrowser.open('file://' + os.path.abspath('audit_report.html'))
        print("Отчёт открыт в браузере.")
    except Exception:
        print("Отчёт сохранён как audit_report.html. Откройте его вручную.")

if __name__ == "__main__":
    main()
#C:\Users\Asus\Documents\Labors
"""
Простой скрипт для базового аудита INI-файла.
Ищет опасные настройки и генерирует отчет в формате Markdown.
"""

import configparser
import os

# Список опасных секций и параметров
DANGEROUS_SECTIONS = [
    'database', 'db', 'sql', 'api_key', 'secret', 'password'
]

DANGEROUS_OPTIONS = {
    # Нешифрованные пароли
    ('password',): 'Пароль указан в открытом виде',
    # Открытый хост
    ('host', 'localhost'): 'БД/Сервис слушает на localhost без ограничения доступа',
    # Открытый порт
    ('port', 3306): 'MySQL порт 3306 доступен извне (рекомендуется ограничить доступ)',
    ('port', 5432): 'PostgreSQL порт 5432 доступен извне',
    ('port', 8080): 'Веб-порт 8080 доступен извне без аутентификации',
    ('port', 5432, 'host', 'localhost'): 'PostgreSQL слушает на localhost:5432 без ограничения доступа',
    # Явно указанные пароли
    ('password', 'root'): 'Используется стандартный или слабый пароль root',
    ('api_key',): 'API ключ указан в конфиге',
    ('secret',): 'Секретный ключ указан в конфиге',
}

def load_config(file_path):
    """Загрузить INI-файл."""
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        print(f"Файл конфигурации '{file_path}' не найден.")
        return None
    config.read(file_path)
    return config

def audit_config(config):
    """
    Аудит конфига и возвращает список предупреждений.
    """
    warnings = []

    if config is None:
        return warnings

    # Перебор всех секций
    for section in config.sections():
        if any(sec.lower() in section.lower() for sec in DANGEROUS_SECTIONS):
            # Предупреждение о секции
            warnings.append(f"⚠️  **Опасная секция:** `{section}`")

        # Перебор всех опций в секции
        for option in config.options(section):
            option_tuple = (option,)
            # Поиск по комбинации опций (например, host и port)
            for keys in DANGEROUS_OPTIONS:
                if all(key in config[section] for key in keys):
                    # Проверяем сочетание опций
                    if tuple(sorted(keys)) == tuple(sorted(option_tuple + tuple(
                        (k, config[section][k]) for k in keys if k != option
                    ))):
                        warning_msg = DANGEROUS_OPTIONS[tuple(sorted(keys))]
                        # Добавляем конкретные значения, если нужны
                        details = ', '.join(f"{k}={config[section][k]}" for k in keys if k != option)
                        warnings.append(f"⚠️  **{warning_msg}** (например: {details})")
                    continue

                if option_tuple in DANGEROUS_OPTIONS:
                    warning_msg = DANGEROUS_OPTIONS[option_tuple]
                    value = config[section][option]
                    # Маскируем пароли
                    if option in ['password', 'api_key', 'secret']:
                        value = '*' * len(value)
                    warnings.append(f"⚠️  **{warning_msg}:** `{option}` = {value}")

    return warnings

def generate_markdown_report(file_path, warnings):
    """Генерирует отчет в Markdown."""
    report = f"# Отчет по аудиту файла конфигурации: {os.path.basename(file_path)}\n\n"

    if not warnings:
        report += "✅ Не обнаружено критических уязвимостей.\n"
    else:
        report += "⚠️ Найдены потенциальные уязвимости:\n\n"
        for warn in warnings:
            report += f"- {warn}\n\n"

    report += "## Рекомендации\n"
    report += "- Не храните пароли и секреты в открытом виде.\n"
    report += "- Используйте соленые хеши для паролей.\n"
    report += "- Ограничивайте доступ к сервисам только из локальной сети или через VPN.\n"
    report += "- Измените стандартные пароли (например, root, admin).\n"
    report += "- Проверьте настройки firewall.\n\n"
    report += "## Анализ завершён.\n"

    return report

def main():
    config_file = input("Введите путь к INI-файлу для аудита: ").strip()
    config = load_config(config_file)
    warnings = audit_config(config)

    report = generate_markdown_report(config_file, warnings)

    print("\n--- ОТЧЁТ ---\n")
    print(report)
    print("\nСохраняю отчет в audit_report.md...")
    with open("audit_report.md", "w", encoding="utf-8") as f:
        f.write(report)

if __name__ == "__main__":
    main()
#C:\eSupport\eDriver\Software\Win32App\ASUS\ROGLiveService pack\1.1.16.3\13104\DevicePage\DeviceHTML\ALL MB\E7C8DA76-C9B9-4297-8681-DD878330AFE7\config.ini
import json
import csv
import os
import sys

CONTACTS_FILE = "contacts.json"
CSV_EXPORT_FILE = "exported_contacts.csv"

def load_contacts():
    """Загрузить контакты из файла."""
    if not os.path.exists(CONTACTS_FILE):
        return []
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_contacts(contacts):
    """Сохранить контакты в файл."""
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)

def add_contact(contacts):
    """Добавить нового контакта."""
    name = input("Имя: ").strip()
    phone = input("Телефон: ").strip()
    email = input("Email: ").strip().lower()
    group = input("Группа: ").strip()

    # Проверка уникальности email
    for cont in contacts:
        if cont['email'] == email:
            print("Ошибка: Контакт с таким email уже существует.")
            return

    new_contact = {
        "name": name,
        "phone": phone,
        "email": email,
        "group": group
    }
    contacts.append(new_contact)
    print("Контакт успешно добавлен.")

def list_contacts(contacts):
    """Показать контакты, отсортированные по группам."""
    if not contacts:
        print("Нет контактов.")
        return

    # Группировка по названию группы
    groups = {}
    for cont in contacts:
        g = cont['group']
        if g not in groups:
            groups[g] = []
        groups[g].append(cont)

    # Сортировка групп (по алфавиту)
    for group_name in sorted(groups.keys()):
        print(f"\nГруппа: {group_name}")
        for idx, cont in enumerate(groups[group_name], 1):
            print(f"{idx}. {cont['name']} ({cont['email']}) — телефон: {cont['phone']}")

def search_by_email_domain(contacts):
    """Поиск по части email (например, по домену @mail.ru)"""
    query = input("Введите часть email для поиска (например, @mail.ru): ").strip().lower()
    found = False
    for cont in contacts:
        if query in cont['email']:
            print(f"- {cont['name']} <{cont['email']}> (группа: {cont['group']})")
            found = True
    if not found:
        print("Ничего не найдено.")

def export_to_csv(contacts):
    """Экспортировать выбранные контакты в CSV."""
    if not contacts:
        print("Нет контактов для экспорта.")
        return

    # Пусть пользователь выберет группу для экспорта
    print("Доступные группы:")
    groups = set([cont['group'] for cont in contacts])
    for g in sorted(groups):
        print(f"- {g}")

    group_to_export = input("Введите название группы для экспорта: ").strip()
    selected = [cont for cont in contacts if cont['group'] == group_to_export]
    if not selected:
        print("В выбранной группе нет контактов.")
        return

    # Записываем в CSV
    with open(CSV_EXPORT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["name", "phone", "email", "group"])
        writer.writeheader()
        for cont in selected:
            writer.writerow(cont)
    print(f"Контакты группы '{group_to_export}' экспортированы в файл {CSV_EXPORT_FILE}")

def main_menu():
    while True:
        print("\n--- Мой CRM ---")
        print("1. Добавить контакт")
        print("2. Показать контакты")
        print("3. Поиск по email")
        print("4. Экспортировать группу в CSV")
        print("5. Выход")
        choice = input("Выберите действие: ").strip()
        if choice == "1":
            contacts = load_contacts()
            add_contact(contacts)
            save_contacts(contacts)
        elif choice == "2":
            contacts = load_contacts()
            list_contacts(contacts)
        elif choice == "3":
            contacts = load_contacts()
            search_by_email_domain(contacts)
        elif choice == "4":
            contacts = load_contacts()
            export_to_csv(contacts)
        elif choice == "5":
            print("Выход из программы.")
            break
        else:
            print("Неверный выбор. Повторите попытку.")

if __name__ == "__main__":
    main_menu()

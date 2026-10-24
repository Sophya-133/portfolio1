import json
import os

CONTACTS_FILE = "contacts.json"

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_contacts(contacts):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)

def add_contact():
    name = input("Ваше имя: ").strip()
    phone = input("Телефон: ").strip()
    email = input("Email: ").strip()
    if not (name and phone and email):
        print("Все поля обязательны!")
        return
    contacts = load_contacts()
    contacts.append({"name": name, "phone": phone, "email": email})
    save_contacts(contacts)
    print("Контакт успешно добавлен.")

def show_contacts():
    contacts = load_contacts()
    if not contacts:
        print("Нет контактов.")
        return

    # Генерируем HTML без кнопки удаления
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Мой CRM — Контакты</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f7fa;}
        table { width: 100%; border-collapse: collapse; margin: 20px 0;}
        th, td { border: 1px solid #ccc; padding: 12px; text-align: left;}
        th { background-color: #e0e6ec; font-weight: bold;}
        tr:hover { background-color: #f2f5fa;}
    </style>
</head>
<body>
    <h1>Список контактов</h1>
    <table>
        <tr>
            <th>№</th>
            <th>Имя</th>
            <th>Телефон</th>
            <th>Email</th>
        </tr>
"""
    for idx, cont in enumerate(contacts, 1):
        html_content += f"""
        <tr>
            <td>{idx}</td>
            <td>{cont['name']}</td>
            <td>{cont['phone']}</td>
            <td>{cont['email']}</td>
        </tr>
        """
    html_content += """
    </table>
    <p>Для удаления контакта используйте консольную программу.</p>
</body>
</html>
"""

    with open("contacts.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Файл contacts.html успешно сгенерирован. Откройте его в браузере.")

def delete_contact():
    contacts = load_contacts()
    if not contacts:
        print("Нет контактов для удаления.")
        return
    print("Список контактов:")
    for idx, cont in enumerate(contacts, 1):
        print(f"{idx}. {cont['name']} ({cont['phone']}) — {cont['email']}")
    try:
        num = int(input("Введите номер контакта для удаления: "))
        if 1 <= num <= len(contacts):
            del contacts[num-1]
            save_contacts(contacts)
            print(f"Контакт номер {num} удалён.")
        else:
            print("Неверный номер контакта.")
    except ValueError:
        print("Введите число.")

def main():
    while True:
        print("\nВыберите действие:")
        print("1. Добавить контакт")
        print("2. Показать контакты")
        print("3. Удалить контакт")
        print("4. Выход")
        choice = input("> ").strip()
        if choice == "1":
            add_contact()
        elif choice == "2":
            show_contacts()
        elif choice == "3":
            delete_contact()
        elif choice == "4":
            print("До свидания!")
            break
        else:
            print("Неизвестное действие.")

if __name__ == "__main__":
    main()

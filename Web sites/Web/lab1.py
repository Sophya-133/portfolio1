def main():
    name = input("Ваше имя: ").strip()
    phone = input("Телефон: ").strip()
    email = input("Email: ").strip()

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Контакты</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #aaa; padding: 8px; text-align: left; }}
        th {{ background-color: #eee; }}
    </style>
</head>
<body>
    <h1>Контакты</h1>
    <table>
        <tr><th>Поле</th><th>Значение</th></tr>
        <tr><td>Имя:</td><td>{name}</td></tr>
        <tr><td>Телефон:</td><td>{phone}</td></tr>
        <tr><td>Email:</td><td>{email}</td></tr>
    </table>
</body>
</html>
"""

    with open("contacts.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("Файл contacts.html успешно создан.")

if __name__ == "__main__":
    main()

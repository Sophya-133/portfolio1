while True:
    user_input = input("Введите строку текста:\n").strip()
    if not user_input:
        print("Ошибка: строка не должна быть пустой. Попробуйте ещё раз.")
        continue

    words = user_input.lower().split()
    if not words:
        print("Ошибка: строка должна содержать слова. Попробуйте ещё раз.")
        continue

    в = words.count('в')
    на = words.count('на')
    с = words.count('с')
    у = words.count('у')

    print('Общее количество предлогов:', в + на + с + у)
    break

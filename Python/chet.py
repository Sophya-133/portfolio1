while True:
    user_input = input("Введите целое положительное число n:\n")
    try:
        n = int(user_input)
        if n <= 0:
            print("Ошибка: число должно быть положительным. Попробуйте ещё раз.")
            continue
    except ValueError:
        print("Ошибка: введено не целое число. Попробуйте ещё раз.")
        continue

    spisok = [i**2 for i in range(1, n+1)]
    for i in spisok:
        print(i)
    break

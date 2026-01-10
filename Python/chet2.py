while True:
    user_input = input("Введите натуральные числа через пробел:\n")
    n = user_input.split()

    try:
        numbers = [int(i) for i in n]
        if any(num <= 0 for num in numbers):
            print("Ошибка: все числа должны быть натуральными (больше 0). Попробуйте ещё раз.")
            continue
    except ValueError:
        print("Ошибка: введены не все числа. Попробуйте ещё раз.")
        continue

    expression = '+'.join(n)
    print(f"{expression}={sum(numbers)}")
    break

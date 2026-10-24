import string

def main():
    # Ввод текста с клавиатуры
    print("Введите текст:")
    text = input()

    # Удаление знаков препинания и перевод в нижний регистр
    translator = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translator).lower()

    # Разделение текста на слова
    words = cleaned_text.split()

    # Считаем частоту слов
    frequency = {}
    for word in words:
        if word:  # чтобы не было пустых строк
            frequency[word] = frequency.get(word, 0) + 1

    # Сортируем слова по убыванию частоты
    sorted_words = sorted(frequency.items(), key=lambda x: x[1], reverse=True)

    # Выводим 5 наиболее частых слов
    print("\n5 наиболее частых слов:")
    count_to_show = min(5, len(sorted_words))
    for word, freq in sorted_words[:count_to_show]:
        print(f"{word}: {freq}")

if __name__ == "__main__":
    main()

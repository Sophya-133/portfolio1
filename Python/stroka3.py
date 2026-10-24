input_string = input("Введите строку: ")

words = input_string.split()

longest_word = ""

for word in words:
    if len(word) > len(longest_word):
        longest_word = word

print(f"Самое длинное слово в строке: {longest_word}")

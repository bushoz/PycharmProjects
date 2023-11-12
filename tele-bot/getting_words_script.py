import re

with open('your_text_file.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

words_list = []

for line in lines:
    parts = re.split(r' - (?![^(]*\))', line.strip())
    if len(parts) == 2:
        word_translation, example = parts
        english_word, translation = word_translation.split(' (')
        translation = translation[:-1]  # Убираем закрывающую скобку ")"
        words_list.append((english_word, translation, example))
print(words_list)
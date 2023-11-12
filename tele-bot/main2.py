import telebot
from telebot import types
import time
import sqlite3
import getting_words_script


bot = telebot.TeleBot('6571156680:AAEqTlvY2OtLV2eLvx_XGiWJ65gNm__aeUw')
emoji_thinking = u'\U0001F914'


# creating a new bd with words if it doesn't exist
def create_bd_with_words():
    conn = sqlite3.connect('words.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
    if cursor.fetchone() is None:
        cursor.execute(
            '''CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                english_word TEXT,
                translation TEXT,
                example TEXT,
                is_learned BOOLEAN DEFAULT 0
            )'''
        )
        cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            ''')
        for word_data in getting_words_script.words_list:
            english_word, translation, example = word_data
            cursor.execute('INSERT INTO words (english_word, translation, example, is_learned) VALUES (?, ?, ?, ?)',
                           (english_word, translation, example, 0))
        conn.commit()
    conn.close()


# adding new user if doesn't exist
def add_new_user(user_id, username):
    print('try to add new user')
    try:
        conn = sqlite3.connect('words.db')
        cursor = conn.cursor()
        cursor.execute(
            'SELECT user_id FROM users WHERE user_id = ?', (user_id,)
        )
        existing_user = cursor.fetchone()
        if existing_user:
            print(f'user {existing_user} already exist')
            pass
        else:
            print('adding new user')
            sql = "INSERT INTO users (user_id, username) VALUES (?, ?)"
            cursor.execute(sql, (user_id, username))
            conn.commit()
    finally:
        conn.close()


def get_new_word_info(user_table_name):
    conn = sqlite3.connect('words.db')
    cursor = conn.cursor()
    cursor.execute(
        f'SELECT * FROM words WHERE english_word NOT IN (SELECT english_word FROM {user_table_name} WHERE is_learned = 1) '
        f'ORDER BY RANDOM() LIMIT 1'
    )
    row = cursor.fetchone()
    _, english_word, translation, example, is_learned = row
    cursor.execute(
        f'INSERT INTO {user_table_name} (english_word, translation, example, is_learned) VALUES (?, ?, ?, ?)',
                   (english_word, translation, example, 0)
    )
    conn.commit()
    conn.close()
    return row


# try to create a new bd with words on start
create_bd_with_words()


@bot.message_handler(commands=['start'])
def start(message):
    print(f'user with id: {message.from_user.id} starts dialog. Try to create bd for them')
    user_table_name = f"user_{message.from_user.id}_words"
    conn = sqlite3.connect('words.db')
    cursor = conn.cursor()
    cursor.execute(
        f'''CREATE TABLE IF NOT EXISTS {user_table_name} (
            id INTEGER PRIMARY KEY,
            english_word TEXT,
            translation TEXT,
            example TEXT,
            is_learned BOOLEAN DEFAULT 0,
            FOREIGN KEY (id) REFERENCES words (id)
        )'''
    )
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, 'Привет! Если ты тут, то скорее всего ты хочешь подучить слова, которые '
                                      'пригодились бы при сдаче экзамена IELTS')
    user_id = message.from_user.id
    if message.from_user.username:
        username = message.from_user.username
    else:
        username = "Рандом Хьюман"
    add_new_user(user_id, username)
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Показать слово', callback_data='show_word')
    markup.add(btn)
    bot.send_message(message.chat.id, f'Ну что, {username}, Начнем? ', reply_markup=markup)
    types.


@bot.callback_query_handler(func=lambda call: call.data == 'show_word')
def show_new_word(callback_query):
    print(f'Try to show word for user {callback_query.from_user.id}')
    user_table_name = f"user_{callback_query.from_user.id}_words"
    word = get_new_word_info(user_table_name)
    if word:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Показать перевод', callback_data='translation')
        markup.add(btn)
        id, english_word, translation, example, is_learned = word
        print(id, english_word, translation, example, is_learned)
        bot.send_message(callback_query.message.chat.id, english_word, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'translation')
def show_translation(callback_query):
    user_table_name = f"user_{callback_query.from_user.id}_words"
    conn = sqlite3.connect('words.db')
    cursor = conn.cursor()
    cursor.execute(
         f'SELECT translation, example FROM {user_table_name} ORDER BY id DESC LIMIT 1'
    )
    translation, example = cursor.fetchone()
    conn.close()
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Я знаю это слово', callback_data='known_word')
    btn2 = types.InlineKeyboardButton('Я продолжаю учить это слово', callback_data='unknown_word')
    markup.add(btn1, btn2)
    bot.send_message(callback_query.message.chat.id, f'{translation}.\n{example}', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'known_word')
def making_word_known(callback_query):
    print('сейчас выучим')
    user_table_name = f"user_{callback_query.from_user.id}_words"
    conn = sqlite3.connect('words.db')
    cursor = conn.cursor()
    is_learned = 1
    cursor.execute(
        f'UPDATE {user_table_name} SET is_learned = ? WHERE id = (SELECT MAX(id) FROM {user_table_name})', (is_learned,)
    )
    conn.commit()
    conn.close()
    print('выучили')
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Показать слово', callback_data='show_word')
    markup.add(btn)
    time.sleep(2)
    bot.send_message(callback_query.message.chat.id, 'Отлично! Продолжаем? ', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'unknown_word')
    def return_unknown_word_in_valhalla(callback_query):
        print('сейчас удалим')
        use_table_name = f"user_{callback_query.from_user.id}_words"
        conn = sqlite3.connect('words.db')
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM {user_table_name} WHERE id = (SELECT MAX(id) FROM {use_table_name})'
        )
        conn.commit()
        conn.close()
        print('удалили')
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Показать слово', callback_data='show_word')
        markup.add(btn)
        time.sleep(3)
        bot.send_message(callback_query.message.chat.id, 'Окей, продолжаем? ', reply_markup=markup)



bot.polling(none_stop=True, timeout=60)
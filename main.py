import dotenv
import telebot
import os
import sqlite3
from telebot import types

# Подключение к Telegram-боту

dotenv.load_dotenv()
API_TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(API_TOKEN)

# Подключение к базе данных SQLite
connection = sqlite3.connect('school.db', check_same_thread=False)
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS timetable(
    id INTEGER PRIMARY KEY,
    course INTEGER NOT NULL,
    time TEXT NOT NULL,
    date TEXT NOT NULL,
    address TEXT NOT NULL)
''')
connection.commit()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY, title TEXT NOT NULL)
''')
connection.commit()

admin_password = "qwerty"

cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY, username TEXT NOT NULL)
''')
connection.commit()


# Функционал бота

@bot.message_handler(commands=['timetable'])
def timetable(message):
    answer = 'Наше расписание:'
    cursor.execute('''SELECT * FROM timetable''')
    timetable = cursor.fetchall()
    for entry in timetable:
        cursor.execute('''SELECT title FROM courses WHERE id = (?)''', (entry[0],))
        course = cursor.fetchone()[0]
        answer += f'\n{course} ({entry[3]} / {entry[2]}):\nАдрес: {entry[4]}'
    if answer == 'Наше расписание:':
        answer = 'Расписание отсутствует'
    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=['add_lesson'])
def add_lesson(message):
    cursor.execute('''SELECT * FROM admins WHERE username = (?)''', (message.from_user.username,))
    username_fetch = cursor.fetchone()
    if username_fetch is None:
        bot.send_message(message.chat.id, 'У вас нет прав для этого действия')
        return
    bot.send_message(message.chat.id, 'Введите название курса')
    bot.register_next_step_handler(message, get_timetable_course)


def get_timetable_course(message):
    course_title = message.text
    bot.send_message(message.chat.id, 'Супер! Введите дату и время курса в формате ДД.ММ.ГГГГ Час:Минута')
    bot.register_next_step_handler(message, get_timetable_date_time, course_title)


def get_timetable_date_time(message, course_title):
    date, time = message.text.split()
    bot.send_message(message.chat.id, 'И последнее! Введите адрес')
    bot.register_next_step_handler(message, get_timetable_address, course_title, date, time)


def get_timetable_address(message, course_title, date, time):
    cursor.execute('''SELECT id FROM courses WHERE title = (?)''', (course_title,))
    course_fetch = cursor.fetchone()
    if course_fetch is None:
        cursor.execute('''INSERT INTO courses (title) VALUES (?)''', (course_title,))
        connection.commit()
        cursor.execute('''SELECT id FROM courses WHERE title = (?)''', (course_title,))
        course_fetch = cursor.fetchone()
    course = course_fetch[0]
    cursor.execute('''
            INSERT INTO timetable (course, time, date, address) VALUES (?, ?, ?, ?)''', (course, time, date, message.text))
    connection.commit()
    bot.send_message(message.chat.id, 'Замечательно! Вы добавили новое занятие!')


@bot.message_handler(commands=['get_superuser_rights'])
def get_superuser_rights(message):
    bot.send_message(message.chat.id, 'Введите пароль администратора')
    bot.register_next_step_handler(message, check_password)


def check_password(message):
    password = message.text
    global admin_password
    if password == admin_password:
        cursor.execute('''SELECT * FROM admins WHERE username = (?)''', (message.from_user.username,))
        username_fetch = cursor.fetchone()
        if username_fetch is None:
            cursor.execute('''INSERT INTO admins (username) VALUES (?)''', (message.from_user.username,))
            connection.commit()
        bot.send_message(message.chat.id, 'Вам выданы права администратора')
    else:
        bot.send_message(message.chat.id, 'Пароль неверный')
    bot.delete_message(message.chat.id, message.id)


@bot.message_handler(commands=['logout'])
def logout(message):
    cursor.execute('''DELETE FROM admins WHERE username = (?)''', (message.from_user.username,))
    connection.commit()
    bot.send_message(message.chat.id, 'Вы вышли')


bot.infinity_polling()

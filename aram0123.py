import dotenv
import telebot
import os
import sqlite3

connection = sqlite3.connect('clients.db', check_same_thread=False)
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS timetable(
    id INTEGER PRIMARY KEY,
    adress varchar(20),
    time varchar(20),
    course varchar(20))
''')
connection.commit()

dotenv.load_dotenv()
API_TOKEN = os.getenv("ARAM_TOKEN")
bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['timetable'])
def timetable(message):
    answer = 'Наше расписание'
    cursor.execute('''SELECT * FROM timetable''')
    timetable = cursor.fetchall()
    for entry in timetable:
        answer += f'\n{entry[0]}, {entry[1]}, {entry[2]}, {entry[3]}'
    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=['add_lesson'])
def add_lesson(message):
    bot.send_message(message.chat.id, 'Введите название, время и адрес нового курса')
    bot.register_next_step_handler(message, get_timetable_info)


def get_timetable_info(message):
    name_course, time, adress = message.text.split()
    cursor.execute('''
        INSERT INTO timetable (adress, time, course) VALUES (?, ?, ?)''', (adress, time, name_course))
    connection.commit()
    bot.send_message(message.chat.id, f'Вы добавили новое занятие!')


bot.infinity_polling()

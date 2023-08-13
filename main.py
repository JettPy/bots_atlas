import dotenv
import telebot
import sqlite3
import os

dotenv.load_dotenv()
API_TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(API_TOKEN)

# Подключение к базе данных SQLite
connection = sqlite3.connect('school.db', check_same_thread=False)
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients(
    id INTEGER PRIMARY KEY, 
    name TEXT NOT NULL, 
    surname TEXT NOT NULL, 
    phone TEXT NOT NULL, 
    course INTEGER)
''')
connection.commit()

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

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_message(message.chat.id,
                     '''Привет!
/help - вывести список команд
/add_course - добавить курс в базу данных (админ)
/courses - просмотреть список доступных курсов
/enroll - записаться на курс
/check_clients - посмотреть базу данных клиентов (админ)
/check_courses - посмотреть базу данных курсов (админ)
/timetable - вывести расписание курсов
/add_lesson - добавить урок в расписание (админ)
/check_timetable - посмотреть базу данных расписания (админ)
/check_admins - посмотреть базу данных администраторов (админ)
/get_superuser_rights - выдать права администратора
/logout - выйти из режима администратора''')


@bot.message_handler(commands=['add_course'])
def add_course(message):
    cursor.execute('''SELECT * FROM admins WHERE username = (?)''', (message.from_user.username,))
    username_fetch = cursor.fetchone()
    if username_fetch is None:
        bot.send_message(message.chat.id, 'У вас нет прав для этого действия')
        return
    bot.send_message(message.chat.id, 'Введите название нового курса')
    bot.register_next_step_handler(message, get_course_title)


def get_course_title(message):
    title = message.text
    cursor.execute('''
        INSERT INTO courses (title) VALUES (?)''', (title,))
    connection.commit()
    bot.send_message(message.chat.id, f'Вы добавили курс {title}!')


@bot.message_handler(commands=['courses'])
def courses(message):
    answer = 'У нас есть следующие курсы:'
    cursor.execute('''SELECT title FROM courses''')
    courses = cursor.fetchall()
    if len(courses) > 0:
        for course in courses:
            answer += f'\n{course[0]}'
    else:
        answer = "Курсов пока нет"
    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=['enroll'])
def enroll(message):
    bot.send_message(message.chat.id, 'Для записи на курс укажите ваше имя и фамилию через пробел')
    bot.register_next_step_handler(message, get_name)


def get_name(message):
    try:
        name, surname = message.text.split()
        bot.send_message(message.chat.id, 'Отлично! Теперь введите ваш телефон')
        bot.register_next_step_handler(message, get_phone, name, surname)
    except ValueError:
        bot.send_message(message.chat.id, 'Упс! Вы ввели что то не так попробуйте с начала')


def get_phone(message, name, surname):
    phone = message.text
    courses_menu = telebot.types.ReplyKeyboardMarkup(row_width=1)
    cursor.execute('''SELECT title FROM courses''')
    courses = cursor.fetchall()
    for course in courses:
        courses_menu.add(telebot.types.KeyboardButton(course[0]))
    bot.send_message(message.chat.id, 'Выберите курс на который хотите записаться', reply_markup=courses_menu)
    bot.register_next_step_handler(message, get_course, name, surname, phone)


def get_course(message, name, surname, phone):
    cursor.execute('''SELECT id FROM courses WHERE title = (?)''', (message.text,))
    course = cursor.fetchone()[0]
    cursor.execute('''
    INSERT INTO clients ( name, surname, phone, course) VALUES (?, ?, ?, ?)''', (name, surname, phone, course))
    connection.commit()
    bot.send_message(
        message.chat.id,
        f'Ура! Вы успешно записались на курс {message.text}!',
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )


@bot.message_handler(commands=['check_clients'])
def check_clients(message):
    cursor.execute('''SELECT * FROM admins WHERE username = (?)''', (message.from_user.username,))
    username_fetch = cursor.fetchone()
    if username_fetch is None:
        bot.send_message(message.chat.id, 'У вас нет прав для этого действия')
        return
    answer = ''
    cursor.execute('''SELECT * FROM clients''')
    clients = cursor.fetchall()
    if len(clients) > 0:
        for entry in clients:
            answer += f'{entry[0]}, {entry[1]}, {entry[2]}, {entry[3]}, {entry[4]}\n'
    else:
        answer = 'Записей клиентов нет'
    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=['check_courses'])
def check_courses(message):
    cursor.execute('''SELECT * FROM admins WHERE username = (?)''', (message.from_user.username,))
    username_fetch = cursor.fetchone()
    if username_fetch is None:
        bot.send_message(message.chat.id, 'У вас нет прав для этого действия')
        return
    answer = ''
    cursor.execute('''SELECT * FROM courses''')
    courses = cursor.fetchall()
    if len(courses) > 0:
        for entry in courses:
            answer += f'{entry[0]}, {entry[1]}\n'
    else:
        answer = 'Записей курсов нет'
    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=['timetable'])
def timetable(message):
    answer = 'Наше расписание:'
    cursor.execute('''SELECT * FROM timetable''')
    timetable = cursor.fetchall()
    if len(timetable) > 0:
        for entry in timetable:
            cursor.execute('''SELECT title FROM courses WHERE id = (?)''', (entry[1],))
            course = cursor.fetchone()[0]
            answer += f'\n{course} ({entry[3]} / {entry[2]}):\nАдрес: {entry[4]}'
    else:
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
    try:
        date, time = message.text.split()
        bot.send_message(message.chat.id, 'И последнее! Введите адрес')
        bot.register_next_step_handler(message, get_timetable_address, course_title, date, time)
    except ValueError:
        bot.send_message(message.chat.id, 'Упс! Вы ввели что то не так попробуйте с начала')


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

@bot.message_handler(commands=['check_timetable'])
def check_timetable(message):
    cursor.execute('''SELECT * FROM admins WHERE username = (?)''', (message.from_user.username,))
    username_fetch = cursor.fetchone()
    if username_fetch is None:
        bot.send_message(message.chat.id, 'У вас нет прав для этого действия')
        return
    answer = ''
    cursor.execute('''SELECT * FROM timetable''')
    timetable = cursor.fetchall()
    if len(timetable) > 0:
        for entry in timetable:
            answer += f'{entry[0]}, {entry[1]}, {entry[2]}, {entry[3]}, {entry[4]}\n'
    else:
        answer = 'Записей в расписании нет'
    bot.send_message(message.chat.id, answer)


@bot.message_handler(commands=['check_admins'])
def check_admins(message):
    cursor.execute('''SELECT * FROM admins WHERE username = (?)''', (message.from_user.username,))
    username_fetch = cursor.fetchone()
    if username_fetch is None:
        bot.send_message(message.chat.id, 'У вас нет прав для этого действия')
        return
    answer = ''
    cursor.execute('''SELECT * FROM admins''')
    admins = cursor.fetchall()
    if len(admins) > 0:
        for entry in admins:
            answer += f'{entry[0]}, {entry[1]}\n'
    else:
        answer = 'Записей курсов нет'
    bot.send_message(message.chat.id, answer)


@bot.message_handler(content_types=['text'])
def default_message(message):
    bot.send_message(message.chat.id, 'Я тебя не понимаю. Введи /help для помощи со списком команд')


bot.infinity_polling()

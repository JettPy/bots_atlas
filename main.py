import dotenv
import telebot
import sqlite3
import os

# Подгружаем переменные окружения из .env файла
dotenv.load_dotenv()
API_TOKEN = os.getenv('SERGEY_TOKEN')
# Создаем бота
bot = telebot.TeleBot(API_TOKEN)
# Подключаем базу данных
connection = sqlite3.connect('clients.db', check_same_thread=False)
cursor = connection.cursor()

# Создаем таблицу для клиентов clients(id, имя, фамилия, телефон, id курса)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS clients(
    id INTEGER PRIMARY KEY, 
    name varchar(20), 
    surname varchar(20), 
    phone varchar(20), 
    course INTEGER)
''')
connection.commit()

# Создаем таблицу для курсов courses(id, название курса)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY, title varchar(20))
''')
connection.commit()


# Обработчик команды /start для вывода инструкций использования бота
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
                     '''Привет!
/add_course - добавить курс в базу данных
/courses - просмотреть список доступных курсов
/enroll - записаться на курс
/check_clients - посмотреть базу данных клиентов
/check_courses - посмотреть базу данных курсов''')


# Обработчик команды /add_course для записи нового курса
@bot.message_handler(commands=['add_course'])
def add_course(message):
    bot.send_message(message.chat.id, 'Введите название нового курса')
    # После ввода команды, подсказываем пользователю, что надо ввести название курса и делегируем
    # выполнение следующей функции - get_course_title
    bot.register_next_step_handler(message, get_course_title)


# Эта функция обрабатывает название нового курса и вносит ее в базу данных курсов
def get_course_title(message):
    title = message.text
    # Выполняем запрос на добавление названия курса в таблицу курсов
    cursor.execute('''
        INSERT INTO courses (title) VALUES (?)''', (title,))
    connection.commit()
    bot.send_message(message.chat.id, f'Вы добавили курс {title}!')


# Обработчик команды /courses, для получения информации о курсах
@bot.message_handler(commands=['courses'])
def courses(message):
    answer = 'У нас есть следующие курсы:'
    # Выполняем запрос на получение всех названий курсов из таблицы курсов
    cursor.execute('''SELECT title FROM courses''')
    courses = cursor.fetchall()
    # Добавляем каждый курс в текст ответа
    for course in courses:
        answer += f'\n{course[0]}'
    bot.send_message(message.chat.id, answer)


# Обработчик команды /enroll, для записи на курс
@bot.message_handler(commands=['enroll'])
def enroll(message):
    bot.send_message(message.chat.id, 'Для записи на курс укажите ваше имя и фамилию')
    # Подсказываем пользователю, что ему надо ввести имя и фамилию и делегируем выполнение функции get_name
    bot.register_next_step_handler(message, get_name)


# Эта функция обрабатывает имя и фамилию пользователя и вызывает функцию обработки номера телефона - get_phone
def get_name(message):
    name, surname = message.text.split()
    bot.send_message(message.chat.id, 'Отлично! Теперь введите ваш телефон')
    # Помимо message и функции обработчика get_phone необходимо пробросить переменные name и surname
    bot.register_next_step_handler(message, get_phone, name, surname)


# Эта функция обрабатывает номера телефона пользователя и вызывает функцию обработки курса - get_course
def get_phone(message, name, surname):
    phone = message.text
    # Создаем разметку для меню курсов
    courses_menu = telebot.types.ReplyKeyboardMarkup(row_width=1)
    # Выполняем запрос на получение названий курсов из таблицы курсов
    cursor.execute('''SELECT title FROM courses''')
    courses = cursor.fetchall()
    # Добавляем каждый курс как кнопку меню
    for course in courses:
        courses_menu.add(telebot.types.KeyboardButton(course[0]))
    # Отправляем сообщение с подсказкой и открываем меню с курсами
    bot.send_message(message.chat.id, 'Выберите курс на который хотите записаться', reply_markup=courses_menu)
    # Добавляем переменную phone и пробрасываем ее вместе с name и surname
    bot.register_next_step_handler(message, get_course, name, surname, phone)


# Эта функция обрабатывает выбранный курс и является последней в цепочке вызовов функций
def get_course(message, name, surname, phone):
    # Выполняем запрос на поиск id курса по названию в таблице курсов
    cursor.execute('''SELECT id FROM courses WHERE title = (?)''', (message.text,))
    course = cursor.fetchone()[0]
    # Выполняем запрос на добавление записи со всеми переменными в таблицу клиентов
    cursor.execute('''
    INSERT INTO clients ( name, surname, phone, course) VALUES (?, ?, ?, ?)''', (name, surname, phone, course))
    connection.commit()
    bot.send_message(
        message.chat.id,
        f'Ура! Вы успешно записались на курс {message.text}!',
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )


# Обработчик команды /check_clients, выводит поля таблицы clients
@bot.message_handler(commands=['check_clients'])
def check(message):
    answer = ''
    # Выполняем запрос на поиск всех записей в таблице клиентов
    cursor.execute('''SELECT * FROM clients''')
    clients = cursor.fetchall()
    if len(clients) > 0:
        for entry in clients:
            answer += f'{entry[0]}, {entry[1]}, {entry[2]}, {entry[3]}, {entry[4]}\n'
    else:
        answer = 'Записей клиентов нет'
    bot.send_message(message.chat.id, answer)


# Обработчик команды /check_courses, выводит поля таблицы courses
@bot.message_handler(commands=['check_courses'])
def check(message):
    answer = ''
    # Выполняем запрос на поиск всех записей в таблице курсов
    cursor.execute('''SELECT * FROM courses''')
    courses = cursor.fetchall()
    if len(courses) > 0:
        for entry in courses:
            answer += f'{entry[0]}, {entry[1]}\n'
    else:
        answer = 'Записей курсов нет'
    bot.send_message(message.chat.id, answer)


bot.infinity_polling()

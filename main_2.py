import telebot
from pymongo import MongoClient

tb = telebot.TeleBot('TOKEN')
ids = set()
isAdmin = False

password = "koza_admina"


@tb.message_handler(commands=['login'])
def login(message):
    tb.send_message(message.chat.id, 'Введите пароль')
    tb.register_next_step_handler(message, check_password)


def check_password(message):
    pd = message.text
    global password, isAdmin
    if pd == password:
        isAdmin = True
        tb.send_message(message.chat.id, 'Пароль верный')
    else:
        tb.send_message(message.chat.id, 'Пароль неверный')

@tb.message_handler(commands=['logout'])
def logout(message):
    isAdmin = False
    tb.send_message(message.chat.id, 'вы вышли')

@tb.message_handler(commands=['start', 'go'])
def start_handler(message):
    global ids
    if message.from_user.id not in ids:
        tb.send_message(message.chat.id, 'Ошибся адресом, дружок')
    else:
        msg = tb.send_message(message.chat.id, "Привет, чем займёмся? :)")
        tb.register_next_step_handler(msg, chosen)




        client = MongoClient()
        db = client.first_db
        users = db['users']

        @tb.message_handler(commands=['start', 'go'])
        def start_handler(message):
            msg = tb.send_message(message.chat.id, "Привет, отправь логин и пароль")
            tb.register_next_step_handler(msg, auth)

        def auth(message):
            data = message.text.split()

            check = users.find_one({
                'username': str(data['username']),
                'password': str(data['password']),
            })

            if check is None:
                tb.send_message(message.chat.id, r'Неправильно введен логин\пароль')

            else:
                msg = tb.send_message(message.chat.id, 'Что будем делать?')
                tb.register_next_step_handler(msg, next_step_func)


tb.infinity_polling()

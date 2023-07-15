import dotenv
import telebot
import os

dotenv.load_dotenv()
API_TOKEN = os.getenv("SERGEY_TOKEN")
bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет!')


bot.infinity_polling()

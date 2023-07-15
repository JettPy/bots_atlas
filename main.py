import dotenv
import telebot
import os

dotenv.load_dotenv()
API_TOKEN = os.getenv("KOZA_TOKEN")
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Иди нахуй!')

bot.infinity_polling()

#bot- Pizdakozy_bot
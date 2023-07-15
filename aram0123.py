import dotenv
import telebot
import os

dotenv.load_dotenv()
API_TOKEN = os.getenv("ARAM_TOKEN")
bot = telebot.TeleBot(API_TOKEN)
@bot.message_handler(commands=['MP'])
def MP(message):
    bot.send_message(message.chat.id, 'Спасибо!')

bot.infinity_polling()
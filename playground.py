from mysql.connector import connect, Error
import configparser
from aiogram import Bot, Dispatcher, executor, types
import logging

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')
logging.basicConfig(level=logging.INFO,
                    filename="vda_bot.log",
                    filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")

db_config = {'host': "127.0.0.1",
             'port': 3306,
             'user': config.get('mysql', 'user'),
             'password': config.get('mysql', 'password'),
             'database': "vda"}

bot_token = config.get('telegram', 'token')
bot = Bot(bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands="answer")
async def cmd_answer(message: types.Message):
    await message.answer("This is a simple reply.")


@dp.message_handler(commands="reply")
async def cmd_reply(message: types.Message):
    await message.reply("This is an answer with quoted reply.")


@dp.message_handler(commands="dice")
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

from mysql.connector import connect, Error
import configparser
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
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


@dp.message_handler(content_types=[types.ContentType.ANIMATION])
async def echo_document(message: types.Message):
    await message.answer_animation(message.animation.file_id)


@dp.message_handler(content_types=[types.ContentType.DOCUMENT])
async def download_doc(message: types.Message):
    # Скачивание в каталог с ботом с созданием подкаталогов по типу файла
    await message.document.download()


@dp.message_handler(content_types=[types.ContentType.PHOTO])
async def download_photo(message: types.Message):
    # Скачивание в каталог с ботом с созданием подкаталогов по типу файла
    await message.photo[-1].download()


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    buttons = ["With honey", "Without honey"]
    keyboard.add(*buttons)
    await message.answer("How to serve your pancakes?", reply_markup=keyboard)


@dp.message_handler(Text(equals="With honey"))
async def with_honey(message: types.Message):
    await message.answer("Nice choice!", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: message.text == "Without honey")
async def without_honey(message: types.Message):
    await message.answer("This is not delicious!")


@dp.message_handler(commands="inline_url")
async def cmd_inline_url(message: types.Message):
    buttons = [
        types.InlineKeyboardButton(text="GitHub", url="https://github.com"),
        types.InlineKeyboardButton(text="Motion to Compel", url="tg://resolve?domain=motiontocompel")
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)  # если убрать row_width, кнопки будут в ряд
    keyboard.add(*buttons)
    await message.answer("Кнопки-ссылки", reply_markup=keyboard)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

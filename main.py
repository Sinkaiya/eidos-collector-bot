from mysql.connector import connect, Error
import configparser
from aiogram import Bot, Dispatcher, executor, types
import time
import logging

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')

bot_token = config.get('telegram', 'token')


def get_text(text_id):  # tested
    select_query = "SELECT `text` FROM `vda_messages` WHERE `id` = %s;"
    with connection.cursor() as cursor:
        cursor.execute(select_query, [text_id])
        result = cursor.fetchall()
        for row in result:
            text = "".join(row[0].decode("utf8"))
        return text


def get_user_data(telegram_user_id):  # tested
    select_query = "SELECT `telegram_id`, `last_chapter_sent`, `on_hold` FROM `vda_users` WHERE id = %s;"
    with connection.cursor() as cursor:
        cursor.execute(select_query, [telegram_user_id])
        result = cursor.fetchall()
        telegram_id = result[0][0]
        last_chapter_sent = result[0][1]
        on_hold = result[0][2]
        return telegram_id, last_chapter_sent, on_hold


# Пока эта функция вообще не нужна, на самом деле.
# def db_update(table_name, cell_name, value, row_id):
#     with connection.cursor() as cursor:
#         # Может быть, всё запихнуть сразу в запрос через format? И в execute передавать только его?
#         update_query = f"UPDATE `{table_name}` SET {cell_name} = %s WHERE `id` = %s;"
#         cursor.execute(update_query, (value, row_id))
#         connection.commit()


def add_user_if_none(telegram_id):
    # Checking if there is a specific user in the db already:
    search_query = "SELECT `id` FROM `vda_users` WHERE `telegram_id`=(%s);"
    with connection.cursor() as cursor:
        cursor.execute(search_query, [telegram_id])
        # Adding a new user into the db:
        if cursor.fetchone() is None:
            insert_query = "INSERT INTO `vda_users` (`telegram_id`,`last_chapter_sent`, `on_hold`) " \
                           "VALUES (%s, '0', '0');"
            cursor.execute(insert_query, [telegram_id])
            connection.commit()


def set_last_chapter_sent(last_chapter_sent, user_id):
    with connection.cursor() as cursor:
        update_query = "UPDATE `vda_users` SET `last_chapter_sent` = %s WHERE `id` = %s"
        cursor.execute(update_query, (last_chapter_sent, user_id))
        connection.commit()



def db_table_rows_count(table_name):
    select_query = f"SELECT COUNT(*) FROM `{table_name}`;"
    with connection.cursor() as cursor:
        cursor.execute(select_query)
        result = cursor.fetchall()
        row_count = result[0][0]
        return row_count


# TODO функция, обрабатывающая on_hold-статус.
def process_on_hold_status():
    pass


def send_text_from_db_to_users():
    """
    # Функция, проходящая по таблице с пользователями и отправляющая каждому нужный
    # кусочек текста. находящая в таблице с пользователями конкретного, проверяющая его
    # on_hold-статус, находящая нужный текст в БД, отправляющая пользователю и обновляющая
    # позицию на следующую. Скорее всего, нужно будет запихнуть всё это в асинхронку сверху.
    # Или оставить её только для /start, а для обработки других событий написать ещё.
    # И для этого нужно будет как-то передавать из одной в другую telegram_id. Или просто
    # расширить уже существующую функцию, потому что кнопок-то на самом деле будет не так много.
    """
    # Проходим по таблице с пользователями, вытаскивая каждого по id.
    # Получаем количество пользователей.
    table_for_count = 'vda_users'
    users_count = db_table_rows_count(table_for_count)
    # TODO Здесь проблема: если пользователь был удалён из БД, в нумерации образуется дырка,
    #  и мы получаем index out of range. Нужно это как-то предотвратить.

    # Получив количество пользователей, перебираем каждого из них.
    for user_id in range(1, users_count + 1):
        telegram_id, last_chapter_sent, on_hold = get_user_data(user_id)
        # Для каждого пользователя роверяем статус on_hold, если он True -
        # идём к следующему пользователю.
        if on_hold == 1:
            continue

        # Если пользователь не на холде - Получаем его last_chapter_sent параметр:
        # номер последнего отправленного ему послания, чтобы понять, какое отправлять
        # следующее.
        # Получаем номер послания, которое мы отправим теперь:
        new_chapter_id = last_chapter_sent + 1
        # print('new chapter id = ', new_chapter_id)  # TEMPORARY STRING

        # Вытаскиваем соответствующее послание из таблицы с текстами, обращаясь по id.
        new_chapter = get_text(new_chapter_id)

        # Отправляем пользователю сообщение с посланием.
        bot.send_message(telegram_id, new_chapter)

        # Убеждаемся, что сообщение доставлено. (КАК?)
        # Если сообщение не доставлено - пытаемся отправить ещё раз.
        # TODO если что-то не шлётся несколько раз - видимо, нужно что-то сделать (сказать
        #  пользователю и отправить мне уведомление)
        # Если сообщение доставлено - обновляем last_chapter_sent для данного пользователя.
        set_last_chapter_sent(new_chapter_id, user_id)


try:
    connection = connect(host="127.0.0.1",
                         port=3306,
                         user=config.get('mysql', 'user'),
                         password=config.get('mysql', 'password'),
                         database="vda")
except Error as db_error_msg:
    print(db_error_msg)
    # TODO добавить сюда функцию, оповещающую меня, если что-то пошло не так.

# Создаём экземпляры классов Bot и Dispatcher, к боту привязываем токен,
# а к диспетчеру - самого бота.
bot = Bot(token=bot_token)
dp = Dispatcher(bot=bot)


# Декоратор, помогающий получить из диспетчера нужный функционал.
# В качестве аргумента передаём команды для обраобтки.
@dp.message_handler(commands=['start', 'join'])
# Асинхронная функция, обрабатывающая команду /start. Приветствует пользователя
# и обрабатывает сообщение, которое он отправляет в ответ.
async def message_handler(message: types.Message):
    # Приветствуем пользователя и определяем его дальнейшее поведение.
    if message.text.lower() == '/start':
        # Получаем полное имя пользователя:
        user_full_name = message.from_user.full_name
        # TODO
        #  - write a proper greeting
        #  - write the bot description
        #  - set the bot avatar
        #  - change the bot's nickname
        await message.reply(f"{user_full_name}, добро пожаловать в бот.")
    # Обрабатываем нового пользователя и добавляем его в БД.
    elif message.text.lower() == '/join':
        # Получаем telegram id:
        telegram_id = message.from_user.username
        # Функция add_user проверяет, есть ли такой telegram id в нашей БД,
        # и если нет - добавляет его туда.
        add_user(telegram_id)
        # Теперь нужно решить, как будут отправляться послания.
        # Первое послание должно отправляться сразу, а последующие - в восемь часов утра.
        # Полагаю, достаточно сделать функцию с условной логикой, которая проверяет номер
        # послания, и если он первый - отправляет сразу, а иначе - делает это в восемь утра.
        # send_text_from_db_to_users()  # TEMPORARILY DISABLED
        test_message = f'This is a test message, {telegram_id}'
        await bot.send_message(telegram_id, test_message)

    # msg = 'a message for user'
    # # await bot.send_message(user_id, msg.format(user_name))


@dp.message_handler(commands=['help'])
async def help_handler(message: types.Message):
    # Получаем telegram id:
    telegram_id = message.from_user.username
    # Проверяем, есть ли такой telegram id в нашей БД, и если нет - добавляем.
    # TODO По идее, нужно это делать после подтверждения от пользователя, я полагаю.
    #  После того, как он нажмёт кнопочку "Прислать первое письмо" или что-то типа того.
    add_user(telegram_id)


# Запускаем бота:
if __name__ == '__main__':
    executor.start_polling(dp)

connection.close()

# def check_on_hold(user_id):
#     select_query = "SELECT `on_hold` FROM `vda_users` WHERE `id` = %s;"
#     with connection.cursor() as cursor:
#         cursor.execute(select_query, [user_id])
#         result = cursor.fetchall()
#         on_hold_status = result[0][0]
#     if on_hold_status == 1:
#         return True
#     else:
#         return False
#
#
# def get_last_chapter_sent_id(user_id):
#     select_query = "SELECT `last_chapter_sent` FROM `vda_users` WHERE `id` = %s;"
#     with connection.cursor() as cursor:
#         cursor.execute(select_query, [user_id])
#         result = cursor.fetchall()
#         last_chapter_sent_id = result[0][0]
#         return last_chapter_sent_id
#
#
# def get_telegram_id(user_id):
#     select_query = "SELECT `telegram_id` FROM `vda_users` WHERE `id` = %s;"
#     with connection.cursor() as cursor:
#         cursor.execute(select_query, [user_id])
#         result = cursor.fetchall()
#         telegram_id = result[0][0]
#         return telegram_id
#
#
# def get_from_db(cell_name, table_name, row_id):
#     select_query = f"SELECT `{cell_name}` FROM `{table_name}` WHERE `id` = %s;"
#     with connection.cursor() as cursor:
#         cursor.execute(select_query, [row_id])
#         result = cursor.fetchall()
#         if cell_name == 'on_hold':  # def check_on_hold
#             on_hold_status = result[0][0]
#             if on_hold_status == 1:
#                 return True
#             else:
#                 return False
#         elif cell_name == 'last_chapter_sent':  # def get_last_chapter_sent_id()
#             last_chapter_sent = result[0][0]
#             return last_chapter_sent
#         elif cell_name == 'text':  # def get_text()
#             for row in result:
#                 text = "".join(row[0].decode("utf8"))
#             return text
#         elif cell_name == 'telegram_id':  # def get_telegram_id()
#             telegram_id = result[0][0]
#             return telegram_id

from mysql.connector import connect, Error
import configparser
from aiogram import Bot, Dispatcher, executor, types
import time
import logging

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')

bot_token = config.get('telegram', 'token')


def get_user_name():
    # TODO Функция, собирающая данные о пользователе: его telegram ID или аналог. Returns username.
    pass
    username = "here_will_be_username"
    return username


def add_user(username):
    # Checking if there is a specific user in the db already:
    search_query = "SELECT `id` FROM `vda_users` WHERE `telegram_id`=(%s);"
    with connection.cursor() as cursor:
        cursor.execute(search_query, [username])
        # Adding a new user into the db:
        if cursor.fetchone() is None:
            insert_query = "INSERT INTO `vda_users` (`telegram_id`,`last_chapter_sent`, `on_hold`) " \
                           "VALUES (%s, '0', '0');"
            cursor.execute(insert_query, [username])
            connection.commit()


def get_chapter(chapter_id):
    # TODO реализовать это тоже через get_from_db
    select_query = "SELECT `chapter` FROM `vda_messages` WHERE `id`=(%s);"
    with connection.cursor() as cursor:
        cursor.execute(select_query, [chapter_id])
        rows = cursor.fetchall()
        for row in rows:
            text = "".join(row[0].decode("utf8"))
        return text


# def check_on_hold(user_id):
#     select_query = f"SELECT `on_hold` FROM `vda_users` WHERE `id` = %s;"
#     with connection.cursor() as cursor:
#         # cursor.execute("SELECT `on_hold` FROM `vda_users` WHERE `id` = %s;" % user_id)
#         cursor.execute(select_query, [user_id])
#         result = cursor.fetchall()
#         on_hold_status = result[0][0]
#     if on_hold_status == 1:
#         return True
#     else:
#         return False


def get_from_db(cell_name, table_name, row_id):
    select_query = f"SELECT `{cell_name}` FROM `{table_name}` WHERE `id` = %s;"
    with connection.cursor() as cursor:
        cursor.execute(select_query, [row_id])
        result = cursor.fetchall()
        if cell_name == 'on_hold':
            on_hold_status = result[0][0]
            if on_hold_status == 1:
                return True
            else:
                return False
        elif cell_name == 'last_chapter_sent':
            last_chapter_sent = result[0][0]
            return last_chapter_sent
        elif cell_name == 'chapter':
            for row in result:
                text = "".join(row[0].decode("utf8"))
            return text


def db_update(table_name, cell_name, value, row_id):
    with connection.cursor() as cursor:
        # TODO Может быть, всё запихнуть сразу в запрос через format? И в execute передавать только его?
        update_query = f"UPDATE `{table_name}` SET {cell_name} = %s WHERE `id` = %s;"
        cursor.execute(update_query, (value, row_id))
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


connection = connect(host="127.0.0.1",
                     port=3306,
                     user=config.get('mysql', 'user'),
                     password=config.get('mysql', 'password'),
                     database="vda")

# Создадим экземпляр класса Bot, и экземпляр класса Dispatcher (dp), который в качестве аргумента
# получит bot. В результате получаем связку объекта класса bot с ключем, который привязан к боту,
# и диспетчера, который привязан к этому боту:
bot = Bot(token=bot_token)
dp = Dispatcher(bot=bot)


# Добавляем декоратор (massage_handler) — он помогает получить из диспетчера нужный функционал.
# В качестве аргумента прописываем команды, которые обрабатывает декоратор.
@dp.message_handler(commands=['start'])
# Прописываем функцию, которая будет обрабатывать команду /start. Функция приветствует пользователя
# и обрабатывает сообщение, которое он отправляет в ответ. Из сообщения можно получить информацию
# о пользователе, который его прислал, время отправки и его ID.
async def start_handler(message: types.Message):
    # Создаем переменную и сохраняем в ней user id:
    telegram_id = message.from_user.username
    # Проверяем, есть ли такой telegram id в нашей БД, и если нет - добавляем.
    # TODO По идее, нужно это делать после подтверждения от пользователя, я полагаю.
    #  После того, как он нажмёт кнопочку "Прислать первое письмо" или что-то типа того.
    add_user(telegram_id)

    # Получаем из сообщения короткое и полное имя пользователя:
    # user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name

    # Для того чтобы в логах отображалась информация о пользователе, передаем в виде текста
    # ID и полное имя, а также используем возможности библиотеки time, чтобы определить время,
    # когда писал пользователь:
    # logging.info(f'{telegram_id} {user_full_name} {time.asctime()}')
    # На знаю пока, нужно ли это, и куда это писать. По идее тоже куда-то в БД.

    # Приветствуем пользователя.
    await message.reply(f"{user_full_name}, добро пожаловать в ВДА бот.")

    msg = 'a message for user'
    # await bot.send_message(user_id, msg.format(user_name))


# Проверяем, равна ли переменная __name__ строке "__main__". Это условие всегда будет True,
# если мы запускаем этот файл как python-скрипт через терминал:
if __name__ == '__main__':
    # Теперь делаем нашего бота доступным в сети:
    executor.start_polling(dp)

# TODO Функция, проходящая по таблице с пользователями и отправляющая каждому нужный
#  кусочек текста. находящая в таблице с пользователями конкретного, проверяющая его
#  on_hold-статус, находящая нужный текст в БД, отправляющая пользователю и обновляющая
#  позицию на следующую. Скорее всего, нужно будет запихнуть всё это в асинхронку сверху.
#  Или оставить её только для /start, а для обработки других событий написать ещё.
#  И для этого нужно будет как-то передавать из одной в другую telegram_id. Или просто
#  расширить уже существующую функцию, потому что кнопок-то на самом деле будет не так много.

# [x] 1. Проходим по таблице с пользователями. Вытаскиваем каждого пользователя по id.
# Получаем количество пользователей.
table_for_count = 'vda_users'
users_count = db_table_rows_count(table_for_count)

for user in range(1, users_count + 1):

    # [x] 2. Проверяем статус on_hold, если он True - идём к следующему пользователю.
    if get_from_db('on_hold', table_for_count, user):
        continue

    # [x] 3. Получаем его last_chapter_sent параметр.
    print('user =', user)  # TEMPORARY STRING
    last_chapter_sent = get_from_db('last_chapter_sent', table_for_count, user)
    print('last chapter sent =', last_chapter_sent)  # TEMPORARY STRING

    # [x] 4. Увеличиваем его на 1.
    new_chapter_id = last_chapter_sent + 1
    print('new chapter id = ', new_chapter_id)  # TEMPORARY STRING

    # [x] 5. Вытаскиваем соответствующий кусочек текста из таблицы с текстами, обращаясь по id.
    new_chapter = get_from_db('chapter', 'vda_messages', new_chapter_id)
    print(new_chapter)  # TEMPORARY STRING

# [ ] 6. Отправляем пользователю. Убеждаемся, что сообщение доставлено. (КАК?)
# [ ] 7. Если сообщение не доставлено - возвращаемся к п. 5.
# [x] 8. Если сообщение доставлено - обновляем last_chapter_sent для данного пользователя.
table_name = 'vda_users'
cell_name = 'last_chapter_sent'
value = '6'
row_id = '2'
# db_update(table_name, cell_name, value, row_id)

connection.close()

from mysql.connector import connect, Error
import configparser
from aiogram import Bot, Dispatcher, executor, types
import time
import logging

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')
bot_token = config.get('telegram', 'token')
logging.basicConfig(level=logging.INFO,
                    filename="vda_bot.log",
                    filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")


def get_text(table_name, text_id):
    """Gets text pieces from DB.

    :param table_name: the name of the DB table we are getting the data from
    :type table_name: str
    :param text_id: the id of the text we are gettinng from the DB table
    :type text_id: str

    :return: the requered text piece from the DB or False if there was an error
    :rtype: str or bool
    """
    query = f"SELECT `text` FROM `{table_name}` WHERE `id` = %s;"
    logging.info(f'Trying to acquire text piece # {text_id} from the `{table_name}` table.')
    with connection.cursor() as cursor:
        try:
            cursor.execute(query, [text_id])
            result = cursor.fetchall()
            for row in result:
                text = "".join(row[0].decode("utf8"))
            logging.info(f'The text piece # {text_id} from the `{table_name}` table '
                         f'successfully acquired.')
            return text
        except Exception as e:
            logging.error(f'An attempt to acquire the text piece # {text_id} '
                          f'from the `{table_name}` table failed: {e}', exc_info=True)
            return False


def get_user_data(user_id):
    """Gets the user data from DB.

    :param user_id: the id of the user in the DB table
    :type user_id: str or int

    :rtype: (str, str, str)
    :return: the user's telegram id,
             the users personal DB table name,
             the id of the last text piece that has been sent to user
    """
    query = "SELECT `telegram_id`, `last_sent_id`, `user_table_name` FROM `users` WHERE id = %s;"
    with connection.cursor() as cursor:
        cursor.execute(query, [user_id])
        result = cursor.fetchall()
        telegram_id = result[0][0]
        last_chapter_sent = result[0][1]
        on_hold = result[0][2]
        return telegram_id, last_chapter_sent, on_hold


def add_user_if_none(telegram_id):
    """Checks if a user with such telegram id is present in the DB already,
        and creates a new entry if there is no such user in the DB.

    :param telegram_id: the telegram id of the user
    :type telegram_id: str

    :return: True of False, depending on whether everything worked correctly
    :rtype: bool
    """
    # Checking if there is a specific user in the db already:
    search_query = "SELECT `id` FROM `users` WHERE `telegram_id`=(%s);"
    with connection.cursor() as cursor:
        cursor.execute(search_query, [telegram_id])
        logging.info(f'Searching for user {telegram_id} in the DB.')
        # Adding a new user into the db if absent:
        if cursor.fetchone() is None:
            logging.info(f'Search for user {telegram_id} performed. User not found. Adding user...')
            insert_query = "INSERT INTO `users` (`telegram_i`, " \
                           "`last_sent_id`, `user_table_name`) VALUES (%s, '0', '0');"
            try:
                cursor.execute(insert_query, [telegram_id])
                connection.commit()
                logging.info(f'User {telegram_id} added to the DB.')
                return True
            except Exception as e:
                logging.error(f'An attempt to add a new user to the DB failed: {e}', exc_info=True)
                return False


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
        add_user_if_none(telegram_id)
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
    add_user_if_none(telegram_id)


# Запускаем бота:
if __name__ == '__main__':
    executor.start_polling(dp)

connection.close()

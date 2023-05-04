from mysql.connector import connect, Error
import configparser
from aiogram import Bot, Dispatcher, executor, types
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
    :rtype: str or bool (if something went wrong)
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

    :return: the user's telegram id,
             the users personal DB table name,
             the id of the last text piece that has been sent to user
             or False if there was an error
        :rtype: (str, str, str) or bool (if something went wrong)
    """
    query = "SELECT `telegram_id`, `last_sent_id`, `user_table_name` FROM `users` WHERE id = %s;"
    logging.info(f'Trying to acquire the data about the user # {user_id} from the `users` table.')
    with connection.cursor() as cursor:
        try:
            cursor.execute(query, [user_id])
            result = cursor.fetchall()
            telegram_id = result[0][0]
            last_chapter_sent = result[0][1]
            on_hold = result[0][2]
            logging.info(f'The data about the user # {user_id} from the `users` table '
                         f'successfully acquired.')
            return telegram_id, last_chapter_sent, on_hold
        except Exception as e:
            logging.error(f'An attempt to acquire the data about the user # {user_id} '
                          f'from the `users` table failed: {e}', exc_info=True)
            return False


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
            insert_query = "INSERT INTO `users` (`telegram_id`, " \
                           "`last_sent_id`, `user_table_name`) VALUES (%s, '0', %s);"
            try:
                cursor.execute(insert_query, [telegram_id, telegram_id])
                connection.commit()
                logging.info(f'User {telegram_id} added to the DB.')
                return True
            except Exception as e:
                logging.error(f'An attempt to add a new user to the DB failed: {e}', exc_info=True)
                return False


def create_user_table(telegram_id):
    """Creates a special table in the DB which belongs to the specific user and contains
    this user's ideas.

    :param telegram_id: the telegram id of the user
    :type telegram_id: str

    :return: True of False, depending on whether everything worked correctly
    :rtype: bool
    """
    create_query = f"CREATE TABLE IF NOT EXISTS `{telegram_id}` (`id` INT PRIMARY KEY " \
                   f"AUTO_INCREMENT NOT NULL, `text` TEXT NOT NULL) ENGINE=InnoDB;"
    logging.info(f'Creating a personal table for user {telegram_id}...')
    with connection.cursor() as cursor:
        try:
            cursor.execute(create_query)
            connection.commit()
            logging.info(f'A personal table for user {telegram_id} has been created successfully.')
            return True
        except Exception as e:
            logging.error(f'An attempt to create a personal table for user {telegram_id} '
                          f'failed: {e}', exc_info=True)
            return False


def set_user_data(user_id, user_data_type, user_data):
    """Writes the data into the `users` table; updates the specific field in this table,
    depending on the `user_data_type` parameter.

    :param user_id: the id of the user in the DB table
    :type user_id: str or int
    :param user_data_type: the field of the `users` table that should be updated
    :type user_data_type: str
    :param user_data: the data that should be written into the specific field of the `users` table
    :type user_data: str

    :return: True of False, depending on whether everything worked correctly
    :rtype: bool
    """
    update_query = f"UPDATE `users` SET `{user_data_type}` = %s WHERE `id` = %s"
    with connection.cursor() as cursor:
        try:
            logging.info(f'Trying to update the `{user_data_type}` field with `{user_data}` value '
                         f'for the user `{user_id}` in the `users` DB table.')
            cursor.execute(update_query, (user_data, user_id))
            connection.commit()
            logging.info(f'An attempt to update the `{user_data_type}` field with `{user_data}` value '
                         f'for the user `{user_id}` in the `users` DB table has been successful.')
            return True
        except Exception as e:
            logging.error(f'An attempt to update the `{user_data_type}` field with `{user_data}` value '
                          f'for the user `{user_id}` in the `users` DB table failed: {e}', exc_info=True)
            return False


# TEMPORARY CODE START
# current_user_id = 1
# current_user_data_type = 'user_table_name'
# current_user_data = 'sinkaiya'
# set_user_data(current_user_id, current_user_data_type, current_user_data)
# TEMPORARY CODE END


def db_table_rows_count(table_name):
    """Calculates the number of records in a table.

    :param table_name: a name of the table we need to count records in
    :type table_name: str

    :return: the number of records
    :rtype: int or bool (if something went wrong)
    """
    select_query = f"SELECT COUNT(*) FROM `{table_name}`;"
    logging.info(f'Calculating the number of records in the `{table_name}` table...')
    with connection.cursor() as cursor:
        try:
            cursor.execute(select_query)
            result = cursor.fetchall()
            row_count = result[0][0]
            logging.info(f'The number of records in the `{table_name}` table calculated successfully.')
            return row_count
        except Exception as e:
            logging.error(f'An attempt calculate the number of records '
                          f'in the `{table_name}` table failed: {e}', exc_info=True)
            return False


def send_text_from_db_to_users():
    """Iterates over the list of users and sends each other of them his own piece of text,
     according to the user's data.

    :return: True of False, depending on whether everything worked correctly
    :rtype: bool
    """
    table_for_count = 'users'
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
        set_last_sent(new_chapter_id, user_id)


# TODO I guess we should add some logging here as well. :3
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

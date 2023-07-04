import aioschedule
import asyncio
import configparser
import logging
import time

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import BotBlocked
from aiogram.dispatcher.filters.state import State, StatesGroup
import aiogram.utils.markdown as fmt
from mysql.connector import connect

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')
bot_token = config.get('telegram', 'token')
admin_id = int(config.get('telegram', 'admin_id'))

logging.basicConfig(level=logging.INFO,
                    filename="eidosbot.log",
                    filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")

db_config = {'host': "127.0.0.1",
             'port': 3306,
             'user': config.get('mysql', 'user'),
             'password': config.get('mysql', 'password'),
             'database': "eidosbot"}


def connect_to_db(host, port, user, password, database):
    """Connects to a MySQL database.

    :param host: host address
    :type host: str
    :param port: port number
    :type port: int
    :param user: username
    :type user: str
    :param password: password
    :type password: str
    :param database: DB name
    :type database: str

    :return: connection
    :rtype: mysql.connector.connection
    """
    connection = None
    for attempt in range(1, 11):
        logging.info(f'Connecting to the database. Attempt {attempt} of 10...')

        try:
            connection = connect(host=host,
                                 port=port,
                                 user=user,
                                 password=password,
                                 database=database)
        except Exception as e:
            logging.error(f'An attempt to connect to the database failed: {e}', exc_info=True)
            time.sleep(5)
            continue

        if connection.is_connected():
            logging.info(f'The connection to the database established successfully.')
            break

    return connection


def get_text(table_name, text_id):
    """Gets text pieces from DB.

    :param table_name: the name of the DB table we are getting the data from
    :type table_name: str
    :param text_id: the id of the text we are gettinng from the DB table
    :type text_id: str

    :return: the requered text piece from the DB or False if there was an error
    :rtype: str or bool (if something went wrong)
    """
    text = None
    query = f"SELECT `text` FROM `{table_name}` WHERE `id` = {text_id}"
    logging.info(f'Trying to acquire text piece # {text_id} from the `{table_name}` table.')
    connection = connect_to_db(**db_config)
    with connection.cursor() as cursor:
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            for row in result:
                text = "".join(row[0].decode("utf8"))
            if "\\'" in text:
                text = text.replace("'", "'")
            if "\\`" in text:
                text = text.replace("`", "`")
            logging.info(f'The text piece # {text_id} from the `{table_name}` table '
                         f'successfully acquired.')
        except Exception as e:
            logging.error(f'An attempt to acquire the text piece # {text_id} '
                          f'from the `{table_name}` table failed: {e}', exc_info=True)
        finally:
            connection.close()
            logging.info(f'Connection to the database closed.')
            if text:
                return text
            else:
                return False


def get_user_data(telegram_id):
    """Gets the user data from DB: telegram_name, user_table_name and last_sent_id.

    :param telegram_id: the id of the user in the DB table
    :type telegram_id: str or int

    :return: user's telegram name,
             user's personal DB table name,
             id of the last text piece that has been sent to user
             or False if there was an error
    :rtype: (str, str, str) or bool (if something went wrong)
    """
    query = f"SELECT `telegram_id`, `telegram_name`, `user_table_name`, `last_sent_id` " \
            f"FROM `users` WHERE telegram_id = {telegram_id};"
    logging.info(f'Trying to acquire data for user {telegram_id}...')
    connection = connect_to_db(**db_config)
    with connection.cursor() as cursor:
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            telegram_id = result[0][0]
            telegram_name = result[0][1]
            user_table_name = result[0][2]
            last_chapter_sent = result[0][3]
            logging.info(f'The data for user {telegram_id} successfully acquired.')
        except Exception as e:
            logging.error(f'An attempt to acquire data for user # {telegram_id} '
                          f'failed: {e}', exc_info=True)
        finally:
            connection.close()
            logging.info(f'Connection to the database closed.')
            if result:
                return telegram_id, telegram_name, user_table_name, last_chapter_sent
            else:
                return False


def create_user_table(telegram_id, telegram_name, table_name):
    """Creates a special table in the DB which belongs to specific user
     and contains this user's ideas.

    :param telegram_id: unique numeric id of user's telegram account
    :type telegram_id: int
    :param telegram_name: user's telegram name
    :type telegram_name: str
    :param table_name: name of the user's table we are about to create
    :type table_name: str

    :return: True of False, depending on whether everything worked correctly
    :rtype: bool
    """
    error = False
    create_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` (`id` INT PRIMARY KEY " \
                   f"AUTO_INCREMENT NOT NULL, `text` TEXT NOT NULL) ENGINE=InnoDB;"
    logging.info(f'Creating a personal table for user {telegram_id} ({telegram_name})...')
    connection = connect_to_db(**db_config)
    with connection.cursor() as cursor:
        try:
            cursor.execute(create_query)
            connection.commit()
            logging.info(f'A personal table for user {telegram_id} ({telegram_name}) '
                         f'has been created successfully.')
        except Exception as e:
            logging.error(f'An attempt to create a personal table for '
                          f'user {telegram_id} ({telegram_name}) failed: {e}', exc_info=True)
            error = True
        finally:
            connection.close()
            logging.info(f'Connection to the database closed.')
            if error:
                return False
            else:
                return True


def add_user_if_none(telegram_id, telegram_name):
    """Checks if a user with such telegram id is present in the DB already,
        and creates a new entry if there is no such user in the DB.

    :param telegram_id: unique numeric identifier of user's telegram account
    :type telegram_id: int
    :param telegram_name: the user's telegram name (the one that starts with @)
    :type telegram_name: str

    :return: True of False, depending on whether everything worked correctly
    :rtype: bool
    """
    search_query = f"SELECT * FROM `users` WHERE `telegram_id` = {telegram_id};"
    logging.info(f'Checking if the user {telegram_id} ({telegram_name}) is present '
                 f'in the DB already.')
    connection = connect_to_db(**db_config)
    table_name = 'db' + str(telegram_id)
    with connection.cursor() as cursor:
        try:
            cursor.execute(search_query)
        except Exception as e:
            logging.error(f'An attempt to check if the user {telegram_id} ({telegram_name}) '
                          f'is present in the DB already failed: {e}', exc_info=True)
        if cursor.fetchone() is None:
            logging.info(f'Search for user {telegram_id} ({telegram_name}) performed. '
                         f'User not found. Adding user...')
            insert_query = f"INSERT INTO `users` (`telegram_id`, `telegram_name`, " \
                           f"`last_sent_id`, `user_table_name`) VALUES ('{telegram_id}', " \
                           f"'{telegram_name}', 0, '{table_name}');"
            try:
                cursor.execute(insert_query)
                connection.commit()
                logging.info(f'User {telegram_id} ({telegram_name}) added to the DB.')
                create_user_table(telegram_id, telegram_name, table_name)
                connection.close()
                logging.info(f'Connection to the database closed.')
                return 'db_created'
            except Exception as e:
                logging.error(f'An attempt to add user {telegram_id} ({telegram_name}) '
                              f'to the DB failed: {e}', exc_info=True)
                connection.close()
                logging.info(f'Connection to the database closed.')
                return False
        else:
            logging.info(f'User {telegram_id} ({telegram_name}) is in the database '
                         f'already. No action is needed.')
            connection.close()
            logging.info(f'Connection to the database closed.')
            return 'db_exists'


def update_db(table_name, data_field, data, telegram_id=None):
    """Updates the data in the DB, depending on the `data_field` parameter.

    :param table_name: name of the DB table we are about to update
    :type table_name: str
    :param telegram_id: the id of the user in the DB table
    :type telegram_id: str or int
    :param data_field: field of the table that should be updated
    :type data_field: str
    :param data: the data that should be written into the specific field of the table
    :type data: str

    :return: True of False, depending on whether everything worked correctly
    :rtype: bool
    """
    error = False
    if "'" in str(data):
        data = data.replace("'", "\\'")
    if "`" in str(data):
        data = data.replace("`", "\\`")
    if table_name == 'users':
        update_query = f"UPDATE `{table_name}` SET `{data_field}` = '{data}' " \
                       f"WHERE `telegram_id` = '{telegram_id}'"
    else:
        update_query = f"INSERT INTO `{table_name}` (`{data_field}`) VALUES ('{data}');"
    logging.info(f'Trying to update the `{data_field}` field of `{table_name}` table '
                 f'with `{data}` value...')
    connection = connect_to_db(**db_config)
    with connection.cursor() as cursor:
        try:
            double_check_query = f"SELECT * FROM `{table_name}` WHERE `{data_field}` = '{data}';"
            logging.info(f'Checking if {data} is present in the {data_field} field '
                         f'of the {table_name} table...')
            cursor.execute(double_check_query)
            result = cursor.fetchall()
            if result and data_field != 'last_sent_id':
                logging.info(f'{data} is present in the {table_name} already.')
                return 'there_is_double'
            else:
                cursor.execute(update_query)
                connection.commit()
                logging.info(f'An attempt to update the `{data_field}` field of `{table_name}` '
                             f'table with `{data}` value has been successful.')
                return 'idea_saved'
        except Exception as e:
            logging.error(f'An attempt to update the `{data_field}` field of `{table_name}` '
                          f'table with `{data}` value failed: {e}', exc_info=True)
            error = True
        finally:
            connection.close()
            logging.info(f'Connection to the database closed.')
            if error:
                return False


def db_table_rows_count(table_name):
    """Calculates the number of records in a table.

    :param table_name: a name of the table we need to count records in
    :type table_name: str

    :return: the number of records
    :rtype: int or bool (if something went wrong)
    """
    select_query = f"SELECT COUNT(*) FROM `{table_name}`;"
    logging.info(f'Calculating the number of records in the `{table_name}` table...')
    connection = connect_to_db(**db_config)
    with connection.cursor() as cursor:
        try:
            cursor.execute(select_query)
            result = cursor.fetchall()
            row_count = result[0][0]
            logging.info(f'The number of records in the `{table_name}` table '
                         f'calculated successfully.')
        except Exception as e:
            logging.error(f'An attempt calculate the number of records '
                          f'in the `{table_name}` table failed: {e}', exc_info=True)
        finally:
            connection.close()
            logging.info(f'Connection to the database closed.')
            if result:
                return row_count
            else:
                return False


def get_telegram_ids(table_name):
    """Collects telegram ids of active users and creates a list with them.

    :param table_name: name of the DB table we are getting data from
    :type table_name: str

    :return: a list with telegram ids or False if there was an error
    :rtype: [int] or bool (if something went wrong)
    """
    telegram_ids_list = []
    query = f"SELECT `telegram_id` FROM `{table_name}`;"
    logging.info(f'Collecting telegram ids...')
    connection = connect_to_db(**db_config)
    with connection.cursor() as cursor:
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            # print(result)
            for entry in result:
                telegram_ids_list.append(entry[0])
            logging.info(f'Telegram ids collected successfully.')
        except Exception as e:
            logging.error(f'An attempt to collect telegram ids failed: {e}', exc_info=True)
        finally:
            connection.close()
            logging.info(f'Connection to the database closed.')
            if result:
                return telegram_ids_list
            else:
                return False


async def send_text_to_users(text=None):
    """Iterates over the list of users and sends each other of them his own piece of text,
     according to the user's 'last_sent_id' parameter.
    """
    current_table = 'users'
    # users_count = db_table_rows_count(current_table)
    # If users_count > 1000, we should add some logic which processes users in batches
    # to save memory. But for now, since the quantity of users is not too large,
    # we can consider it as a feature to add in the future. :)

    # Getting a list with telegram_ids:
    current_telegram_ids_list = get_telegram_ids(current_table)

    for telegram_id in current_telegram_ids_list:
        telegram_id, telegram_name, user_table_name, last_sent_id = get_user_data(telegram_id)

        if text:
            await bot.send_message(telegram_id, text)
        else:
            # Setting an id of text which should be sent to current user.
            # Checking if this id is not more than total count of texts
            # in user's DB, to prevent 'index out of range' error:
            user_table_size = db_table_rows_count(user_table_name)
            if user_table_size == 0:
                continue
            new_last_sent_id = last_sent_id + 1
            if new_last_sent_id > user_table_size:
                new_last_sent_id = 1

            new_text_to_send = get_text(user_table_name, new_last_sent_id)
            try:
                await bot.send_message(telegram_id, new_text_to_send)
            except BotBlocked as e:
                logging.error(f'An attempt to send message to user {telegram_id} failed:'
                              f' {e}', exc_info=True)
                continue

            update_db('users', 'last_sent_id', new_last_sent_id, telegram_id)


bot = Bot(token=bot_token)
dp = Dispatcher(bot=bot, storage=MemoryStorage())


# To keep the bot's states we need to create a class which is inherited from
# the StatesGroup class. The attributes within this class should be the instances
# of the State() class.
class GetUserIdea(StatesGroup):
    waiting_for_idea = State()
    waiting_for_broadcast = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    if message.text.lower() == '/start':
        greeting = 'Добро пожаловать в бот.\n\n' \
                   'Чтобы сохранить понравившуюся идею - нажмите "Сохранить идею".\n\n' \
                   'По умолчанию бот делает рассылку в 9 часов утра. Чтобы он прислал идею ' \
                   'прямо сейчас - нажмите "Попросить бота прислать идею".\n\n' \
                   'Приятного использования. :3'
        await message.answer(greeting)


@dp.message_handler(commands='save_idea', state='*')
async def idea_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    telegram_name = message.from_user.username
    full_name = message.from_user.full_name
    user_add_result = add_user_if_none(telegram_id, telegram_name)
    if user_add_result == 'db_created':
        await message.answer(f'Приветствуем, {fmt.hbold(full_name)}. Ваша база данных успешно '
                             f'создана. Приятного использования.', parse_mode=types.ParseMode.HTML)
    # Putting the bot into the 'waiting_for_idea' statement:
    await message.answer('Ожидаю идею. Её можно скопипастить или переслать прямо сюда.',
                         reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(GetUserIdea.waiting_for_idea.state)


# This function is being called only from the 'waiting_for_idea' statement.
@dp.message_handler(state=GetUserIdea.waiting_for_idea, content_types=['any'])
async def idea_acquired(message: types.Message, state: FSMContext):
    # If the user has sent not text but something weird, we are asking
    # to send us text only. The state the bot currently in stays the same,
    # so the bot continues to wait for user's idea.
    if message.content_type != 'text':
        await message.answer('Бот приемлет только текст. Попробуйте ещё раз.',
                             reply_markup=types.ReplyKeyboardRemove())
        return
    # Saving the idea in the FSM storage via the update_data() method.
    await state.update_data(user_idea=message.text)
    user_idea = message.text
    telegram_id = message.from_user.id
    table_name = 'db' + str(telegram_id)
    db_update_result = update_db(table_name, 'text', user_idea, telegram_id)
    if db_update_result == 'there_is_double':
        await message.answer('У вас уже есть эта идея. Сохранение не требуется.')
    elif db_update_result == 'idea_saved':
        await message.answer('Идея успешно сохранена.')
    else:
        await message.answer('Идея не сохранилась, что-то пошло не так.')
    await state.finish()


@dp.message_handler(commands='broadcast', state='*')
async def idea_start(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    if telegram_id == admin_id:
        await message.answer('Ожидаю широковещательное сообщение.')
        await state.set_state(GetUserIdea.waiting_for_broadcast.state)
    else:
        await message.answer('Ты не админ, тебе нельзя. >:3')


# This function is being called only from the 'waiting_for_idea' statement.
@dp.message_handler(state=GetUserIdea.waiting_for_broadcast, content_types=['any'])
async def idea_acquired(message: types.Message, state: FSMContext):
    # If the user has sent not text but something weird, we are asking
    # to send us text only. The state the bot currently in stays the same,
    # so the bot continues to wait for user's idea.
    if message.content_type != 'text':
        await message.answer('Широковещательное сообщение должно быть текстовым. '
                             'Попробуй ещё раз.')
        return
    # Saving the idea in the FSM storage via the update_data() method.
    await state.update_data(broadcast_message=message.text)
    await send_text_to_users(message.text)
    await message.answer('Широковещательное оповещение успешно разослано.')
    await state.finish()


@dp.message_handler(commands='get_idea')
async def cmd_get_idea(message: types.Message):
    telegram_id = message.from_user.id
    telegram_name = message.from_user.username
    full_name = message.from_user.full_name
    user_add_result = add_user_if_none(telegram_id, telegram_name)
    if user_add_result == 'db_created':
        await message.answer(f'Приветствуем, {fmt.hbold(full_name)}. Ваша база данных успешно '
                             f'создана, но идей, которые можно было бы прислать, пока нет.',
                             parse_mode=types.ParseMode.HTML)
        return True
    telegram_id, telegram_name, user_table_name, last_sent_id = get_user_data(telegram_id)
    user_table_size = db_table_rows_count(user_table_name)
    if user_table_size == 0:
        await message.answer('К сожалению, у вас пока ещё нет ни одной идеи.')
    else:
        new_last_sent_id = last_sent_id + 1
        if new_last_sent_id > user_table_size:
            new_last_sent_id = 1
        new_text_to_send = get_text(user_table_name, new_last_sent_id)
        await message.answer(new_text_to_send)
        update_db('users', 'last_sent_id', new_last_sent_id, telegram_id)


async def scheduler():
    aioschedule.every().day.at("09:00").do(send_text_to_users)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

# testing webhook AGAIN!!!!11

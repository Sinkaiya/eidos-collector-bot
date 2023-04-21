from mysql.connector import connect, Error
import configparser
from aiogram import Bot, Dispatcher, executor, types

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')

try:
    connection = connect(host="127.0.0.1",
                         port=3306,
                         user=config.get('mysql', 'user'),
                         password=config.get('mysql', 'password'),
                         database="vda")
except Error as db_error_msg:
    print(db_error_msg)


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
# def get_telegram_id(user_id):  # tested
#     select_query = "SELECT `telegram_id` FROM `vda_users` WHERE `id` = %s;"
#     with connection.cursor() as cursor:
#         cursor.execute(select_query, [user_id])
#         result = cursor.fetchall()
#         telegram_id = result[0][0]
#         return telegram_id


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


user_id = 1
telegram_id, last_chapter_sent, on_hold = get_user_data(user_id)
print('telegram id = ', telegram_id)
print('last chapter sent id = ', last_chapter_sent)
print('on hold status = ', on_hold)
print(type(on_hold))

connection.close()

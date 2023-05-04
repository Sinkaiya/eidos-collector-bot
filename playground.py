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

while True:
    logging.info(f'Trying to connect to the database...')
    connection = connect(host="127.0.0.1",
                         port=3306,
                         user=config.get('mysql', 'user'),
                         password=config.get('mysql', 'password'),
                         database="vda")




connection.close()

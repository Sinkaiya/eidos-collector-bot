from getpass import getpass
from mysql.connector import connect, Error
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')

try:
    with connect(
        host="127.0.0.1",
        port=3306,
        user=config.get('mysql', 'user'),
        password=config.get('mysql', 'password'),
        database='vda'
    ) as connection:

        # value_to_add = 'А тою же ночью, в чулане, кот Василий Васильевич, запертый под замок за покушение на разбой, ' \
        #                'орал хриплым мявом и не хотел даже ловить мышей, – сидел у двери и мяукал так, что самому ' \
        #                'было неприятно.'
        # write_db_query = "INSERT INTO `vda`.`108_messages` (`chapter`) VALUES ('" + value_to_add + "');"
        # with connection.cursor() as cursor:
        #     cursor.execute(write_db_query)

        # show_db_query = "SHOW COLUMNS from `108_messages`;"
        # show_db_query = "SELECT * FROM `108_messages`;"
        show_db_query = "SHOW COLUMNS FROM `108_messages`;"
        with connection.cursor() as cursor:
            cursor.execute(show_db_query)
            for db in cursor:
                print(db)

except Error as e:
    print(e)

# Connect to server
# cnx = mysql.connector.connect(
#     host="127.0.0.1",
#     port=3306,
#     user=input("Enter username: "),
#     password=getpass("Enter password: "))

# Get a cursor
# cur = cnx.cursor()

# Execute a query
# cur.execute("USE `vda`;")
# cur.execute('SHOW TABLES;')

# Fetch one result
# row = cur.fetchone()
# print(row)

# Close connection
# cnx.close()

# TODO Парсер текстового файла, который будет проходить по 108 посланиям и каждое из них писать в отдельную ячейку БД.

# letters_file = open('letters.txt', 'r', encoding='utf8')

# TODO What should act as a divider? Probably a simple line.

# for line in letters_file.readlines():


# letters_file.close()

# TODO Функция, собирающая данные о пользователе: его telegram ID или аналог, и пишущая в соответствующую таблицу.

# TODO Функция, находящая в таблице с пользователями конкретного, проверяющая его on_hold-статус и его текущую позицию
# TODO в списке, находящая нужный текст в БД, отправляющая пользователю и обновляющая позицию на следующую.

# TODO функция, обрабатывающая on_hold-статус.

# TODO
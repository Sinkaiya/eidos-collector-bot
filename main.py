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
        database="vda"
    ) as connection:

        number_to_add = '4'
        value_to_add = 'Test record # 44.'
        insert_query = "INSERT INTO `108_messages` (`id`, `chapter`) VALUES (%s, %s);"
        with connection.cursor() as cursor:
            cursor.execute(insert_query, [number_to_add, value_to_add])
        connection.commit()

        # show_db_query = "SHOW COLUMNS FROM `108_messages`;"
        # with connection.cursor() as cursor:
        #     cursor.execute(show_db_query)
        #     for db in cursor:
        #         print(db)

except Error as e:
    print(e)

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
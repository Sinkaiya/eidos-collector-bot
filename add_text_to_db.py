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
        text_file = open('letters.txt', 'r', encoding='utf8')
        for line in text_file.readlines():

            insert_query = "INSERT INTO `108_messages` (`chapter`) VALUES (%s)"
            with connection.cursor() as cursor:
                line = line.strip()
                if len(line) > 0:
                    cursor.execute(insert_query, [line])
            connection.commit()

        text_file.close()

except Error as e:
    print(e)

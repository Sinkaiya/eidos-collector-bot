from mysql.connector import connect, Error
import configparser

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

text_file = open('letters.txt', 'r', encoding='utf8')
separator = "#"
line_to_add = str()

for line in text_file.readlines():
    if separator in line:
        print(line_to_add)
        insert_query = "INSERT INTO `vda_messages` (`text`) VALUES (%s);"
        with connection.cursor() as cursor:
            cursor.execute(insert_query, [line_to_add])
        connection.commit()
        line_to_add = str()
        continue
    elif len(line) > 2:
        line_to_add += line

text_file.close()

connection.close()

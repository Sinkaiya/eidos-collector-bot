from mysql.connector import connect, Error
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8-sig')


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
            insert_query = "INSERT INTO `vda_users` (`telegram_id`,`last_chapter_sent`) VALUES (%s, '0');"
            cursor.execute(insert_query, [username])
            connection.commit()


def get_chapter(chapter_id):
    select_query = "SELECT `chapter` FROM `108_messages` WHERE `id`=(%s);"
    with connection.cursor() as cursor:
        cursor.execute(select_query, [chapter_id])
        rows = cursor.fetchall()
        for row in rows:
            text = "".join(row[0].decode("utf8"))
        return text


def db_update(table_name, cell_name, value, row_id):
    # UPDATE `vda_users` SET `last_chapter_sent` = '2' WHERE `id`='2';
    update_query = "UPDATE %s SET %s = %s WHERE id = %s;"
    with connection.cursor() as cursor:
        cursor.execute(update_query, [table_name, cell_name, value, row_id])
        connection.commit()


try:
    with connect(
            host="127.0.0.1",
            port=3306,
            user=config.get('mysql', 'user'),
            password=config.get('mysql', 'password'),
            database="vda"
    ) as connection:
        # get_user_name()
        # add_user(username_from_get_user_name)

        # TODO Функция, проходящая по таблице с пользователями и отправляющая каждому нужный кусочек текста.
        #  находящая в таблице с пользователями конкретного, проверяющая его on_hold-статус,
        #  находящая нужный текст в БД, отправляющая пользователю и обновляющая позицию на следующую.
        # Как она вообще должна работать?
        # [ ] 1. Проходим по таблице с пользователями. Вытаскиваем каждого пользователя по id.
        current_user_id = 1

        # [ ] 2. Проверяем статус on_hold. Если он True - пропускаем пользователя и переходим к следующему.
        # [ ] 3. Получаем его last_chapter_sent параметр.
        # [ ] 4. Увеличиваем его на 1.
        # [x] 5. Вытаскиваем соответствующий кусочек текста из таблицы с текстами, обращаясь по id.
        # [ ] 6. Отправляем пользователю. Убеждаемся, что сообщение доставлено. (КАК?)
        # [ ] 7. Если сообщение не доставлено - возвращаемся к п. 5.
        # [ ] 8. Если сообщение доставлено - обновляем last_chapter_sent для данного пользователя.
        table_name = 'vda_users'
        cell_name = 'last_chapter_sent'
        value = '3'
        row_id = '3'
        db_update(table_name, cell_name, value, row_id)
        # [ ] 9. Увеличиваем переменную, отвечающую за id пользователя, на 1, и переходим к п. 2.


except Error as e:
    print(e)

# Таблица с пользователями (поля):
#   - id
#   - telegram ID ()
#   - last sent chapter - id from 108_messages table ()
#   - on_hold (bool)

# CREATE SCHEMA `vda` DEFAULT CHARACTER SET utf8 COLLATE utf8_bin;

# CREATE TABLE IF NOT EXISTS `vda`.`vda_users` (
#     `id` INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
#     `telegram_id` VARCHAR(128) NOT NULL,
#     `last_chapter_sent` TINYINT NOT NULL,
#     `on_hold` BOOL
# ) ENGINE=InnoDB;

# Checking if there is such a user in the DB already.


# TODO функция, обрабатывающая on_hold-статус.

# TODO

# show_db_query = "SHOW COLUMNS FROM `108_messages`;"
# with connection.cursor() as cursor:
#     cursor.execute(show_db_query)
#     for db in cursor:
#         print(db)

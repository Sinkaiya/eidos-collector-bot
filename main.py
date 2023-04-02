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
            insert_query = "INSERT INTO `vda_users` (`telegram_id`,`last_chapter_sent`, `on_hold`) VALUES (%s, '0', '0');"
            cursor.execute(insert_query, [username])
            connection.commit()


def get_chapter(chapter_id):
    select_query = "SELECT `chapter` FROM `vda_messages` WHERE `id`=(%s);"
    with connection.cursor() as cursor:
        cursor.execute(select_query, [chapter_id])
        rows = cursor.fetchall()
        for row in rows:
            text = "".join(row[0].decode("utf8"))
        return text


def check_on_hold(user_id):
    with connection.cursor() as cursor:
        cursor.execute("SELECT `on_hold` FROM `vda_users` WHERE `id` = %s ;" % user_id)
        result = cursor.fetchall()
        on_hold_status = result[0][0]
    if on_hold_status == 1:
        return True
    else:
        return False


def db_update(table_name, cell_name, value, row_id):
    # Example: UPDATE `vda_users` SET `last_chapter_sent` = '2' WHERE `id`='2';
    update_query = "UPDATE `" + \
                   table_name + "` SET `" + \
                   cell_name + "` = '" + \
                   value + "' WHERE `id` = '" + \
                   row_id + "';"
    with connection.cursor() as cursor:
        cursor.execute(update_query)
        connection.commit()


def db_table_rows_count(table_name):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM %s;" % (table_name.upper()))
        result = cursor.fetchall()
        row_count = result[0][0]
        return row_count


try:
    with connect(
            host="127.0.0.1",
            port=3306,
            user=config.get('mysql', 'user'),
            password=config.get('mysql', 'password'),
            database="vda"
    ) as connection:
        # telegram_id = get_user_name()
        # add_user(telegram_id)

        # TODO Функция, проходящая по таблице с пользователями и отправляющая каждому нужный
        #  кусочек текста. находящая в таблице с пользователями конкретного, проверяющая его
        #  on_hold-статус, находящая нужный текст в БД, отправляющая пользователю и обновляющая
        #  позицию на следующую.
        # [ ] 1. Проходим по таблице с пользователями. Вытаскиваем каждого пользователя по id.
        # Получаем количество пользователей.
        table_for_count = 'vda_users'
        users_count = db_table_rows_count(table_for_count)

        for user in range(1, users_count + 1):

            # [x] 2. Проверяем статус on_hold, если он True - идём к следующему пользователю.
            if check_on_hold(user):
                continue

            # [ ] 3. Получаем его last_chapter_sent параметр.
            # TODO Можно реализовать через ту же функцию, что и получение on-hold-статуса

        # [ ] 4. Увеличиваем его на 1.
        # [x] 5. Вытаскиваем соответствующий кусочек текста из таблицы с текстами, обращаясь по id.
        # [ ] 6. Отправляем пользователю. Убеждаемся, что сообщение доставлено. (КАК?)
        # [ ] 7. Если сообщение не доставлено - возвращаемся к п. 5.
        # [x] 8. Если сообщение доставлено - обновляем last_chapter_sent для данного пользователя.
        table_name = 'vda_users'
        cell_name = 'last_chapter_sent'
        value = '3'
        row_id = '2'
        # db_update(table_name, cell_name, value, row_id)


except Error as e:
    print(e)

# TODO функция, обрабатывающая on_hold-статус.

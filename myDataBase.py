import sqlite3
import datetime


class MyDataBase:
    def __init__(self, database_name):
        # Соединение с БД
        self.conn = sqlite3.connect(database_name, check_same_thread=False)
        #
        self.conn.row_factory = sqlite3.Row
        # Создание объекта курсора
        cursor = self.conn.cursor()

        self.conn.commit()
        cursor.close()

    # Закрытие соединения
    def close(self):
        self.conn.close()

    # Добавление пользователя
    def add_user(self, user_id, user_name):
        # Запрос на добавление нового пользователя в БД
        query_add_user = """
                INSERT INTO users (user_id, name)
                VALUES (?, ?)
        """
        self.conn.execute(query_add_user, (user_id, user_name))

        # Запрос на получение всех слов из БД для заучивания
        query_get_words = """
                SELECT word_id
                FROM words"""
        # Заносим все слова из БД в список
        words = self.conn.execute(query_get_words).fetchall()
        all_words = []
        for rt in words:
            all_words.append(rt[0])

        # Запрос на добавление добавление данных в таблицу заучиваний
        query = """
                INSERT INTO learning (count_correct_answer, word, user)
                VALUES (?, ?, ?)
        """
        # К каждому пользователю привязываем все слова для заучивания
        for wrd in all_words:
            self.conn.execute(query, (0, wrd, user_id))

        # Обработка исключений
        try:
            self.conn.commit()
        except:
            self.conn.rollback()

    # Поиск пользователя в БД
    def find_user(self, user):
        query = """
                SELECT user_id
                FROM users
                WHERE user_id = ?
        """

        try:
            ret_value = self.conn.execute(query, (user, )).fetchone()
            return ret_value['user_id']
        except:
            return -1

    # Записываем время последнего ответа
    def set_last_time_answer(self, user, time):
        query = """
                UPDATE users SET last_time = ?
                WHERE user_id = ?;
        """
        self.conn.execute(query, (time, user))
        self.conn.commit()

    def set_learning(self, user, translate, true_or_false):
        query1 = """
                SELECT count_correct_answer, word
                FROM learning
                INNER JOIN words ON words.word_id = learning.word  
                WHERE learning.user = ? AND words.translate = ?
        """
        ret_value = self.conn.execute(query1, (user, translate)).fetchone()

        count = ret_value[0]
        one_word = ret_value[1]
        if true_or_false == 1:
            count += 1

        query2 = """
                UPDATE learning SET count_correct_answer = ?, last_time_answer = ?
                WHERE user = ? AND word = ?
        """
        date = datetime.datetime.now()
        self.conn.execute(query2, (count, date, user, one_word))
        self.conn.commit()

        return count

    # Получаем данные пользователя
    def get_data_user(self, user):
        data_user = []
        # Запрос на получение времени последнего прохождения опроса
        query_time = """
                SELECT last_time
                FROM users
                WHERE user_id = ?
        """
        time_value = self.conn.execute(query_time, (user, )).fetchone()
        data_user.append(time_value)

        # Запрос на получение сколько слов он выучил
        query_learned = """
                SELECT COUNT(word)
                FROM learning
                WHERE count_correct_answer > 20 AND user = ?
        """
        learned_value = self.conn.execute(query_learned, (user,)).fetchone()
        data_user.append(learned_value)

        # Запрос на получение слов, которые находятся в процессе изучения
        query_learn = """
                SELECT COUNT(word)
                FROM learning
                WHERE count_correct_answer > 0 AND user = ?
        """
        learn_value = self.conn.execute(query_learn, (user,)).fetchone()
        data_user.append(learn_value)
        self.conn.commit()

        return data_user


    def get_name_user(self, user_id):
        query = """
        SELECT name
        FROM users
        WHERE user_id = ?
        """
        user_name = self.conn.execute(query, (user_id,)).fetchone()
        self.conn.commit()
        return user_name['name']

    def check(self, user, word):
        query1 = """
                        SELECT count_correct_answer, word
                        FROM learning
                        INNER JOIN words ON words.word_id = learning.word  
                        WHERE learning.user = ? AND words.translate = ?
                """
        ret_value = self.conn.execute(query1, (user, word)).fetchone()

        count = ret_value[0]
        one_word = ret_value[1]
        count = 0

        query2 = """
                UPDATE learning SET count_correct_answer = ?, last_time_answer = ?
                WHERE user = ? AND word = ?
        """
        date = datetime.datetime.now()
        self.conn.execute(query2, (count, date, user, one_word))
        self.conn.commit()





from sqlalchemy import create_engine, MetaData, ForeignKey, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
import random
import sqlite3

# Декларативный базовый класс
Base = declarative_base()

# Подключение к БД
engine = create_engine(
    'postgres://waactudsnfbwxu:e73f01ad438e68683523415d9317065e7e3995a036d26451c6fe166b186cc775@ec2-54-75-231-215.eu-west-1.compute.amazonaws.com:5432/d6cpom1s22furu',
    echo=True)

metadata = MetaData()

# Сессия
Session = sessionmaker()
Session.configure(bind=engine)


class Users(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    last_time = Column(DateTime)
    name = Column(String)
    count_answer = Column(Integer)
    new_num_question = Column(Integer)
    old_num_question = Column(Integer)

    # Добавление нового пользователя в БД
    def add_user(self, user_id, user_name):
        session = Session()
        new_user = Users(user_id=user_id,
                         name=user_name,
                         last_time=None,
                         count_answer=0,
                         new_num_question=0,
                         old_num_question=0)

        # Добавление нового юзера
        session.add(new_user)
        session.commit()
        session.close()

        session = Session()
        # Привязка всех слов для заучивания к юзеру
        words = session.query(Words.word_id).all()
        session.close()

        for word in words:
            session = Session()
            try:
                learning = Learning(user=user_id,
                                    word=word[0],
                                    count_correct_answer=0,
                                    last_time_answer=None)
                session.add(learning)
                session.commit()
                session.close()
            except:
                session.rollback()
                session.close()

        # Добавление данных раунда к новому юзеру
        session = Session()
        raund = DataRaund(user_id=user_id,
                          word=None,
                          num_question=0,
                          num_correct_answer=0,
                          num_incorrect_answers=0,
                          this_example=0)
        session.add(raund)
        session.commit()
        session.close()

    # Поиск покупателя в БД
    def find_user(self, user_id):
        try:
            session = Session()
            select_id_user = session.query(Users.user_id).filter(Users.user_id == user_id).one()
            session.close()
            return select_id_user[0]
        except:
            return -1

    # Получение имени пользователя
    def get_name_user(self, user_id):
        session = Session()
        select_name_user = session.query(Users.name).filter(Users.user_id == user_id).one()
        session.close()
        try:
            return select_name_user[0]
        except:
            return -1

    def set_count_press(self, user_id, value, num_question):
        session = Session()
        try:
            update_name_user = session.query(Users).filter(Users.user_id == user_id).one()
            update_name_user.old_num_question = update_name_user.new_num_question
            update_name_user.new_num_question = num_question
            update_name_user.count_answer = value
            session.commit()
            session.close()
        except:
            session.rollback()
            session.close()

    @staticmethod
    def get_count_press(user_id):
        session = Session()
        select_query = session.query(Users.count_answer).filter(Users.user_id == user_id).one()
        session.close()
        try:
            return select_query[0]
        except:
            return -1

    @staticmethod
    def get_new_num_question(user_id):
        session = Session()
        select_query = session.query(Users.new_num_question).filter(Users.user_id == user_id).one()
        session.close()
        return select_query[0]

    @staticmethod
    def get_old_num_question(user_id):
        session = Session()
        select_query = session.query(Users.old_num_question).filter(Users.user_id == user_id).one()
        session.close()
        return select_query[0]

    # Плучение данных о данном пользователе
    def get_data_user(self, user_id):
        data_user = []
        # Получаем время последнего ответа
        session = Session()
        time_value = session.query(Users.last_time).filter(Users.user_id == user_id).one()
        session.close()
        data_user.append(time_value[0])

        # Получаем количество выученных слов
        count_ans = int(Settings.get_count_true_answer())
        session = Session()
        learned_value = session.query(Learning.word).filter(Learning.user == user_id).filter(
            Learning.count_correct_answer > count_ans).count()
        session.close()
        data_user.append(learned_value)

        # Получаем слова, которые находятся в процессе изучения
        session = Session()
        learn_value = session.query(Learning.word).filter(Learning.user == user_id).filter(
            Learning.count_correct_answer > 0).count()
        session.close()
        data_user.append(learn_value)

        return data_user

    # Записываем время последнего ответа
    def set_last_time_answer(self, user):
        session = Session()
        update_time = session.query(Users).filter(Users.user_id == user).one()
        update_time.last_time = datetime.now()
        session.commit()
        session.close()

    def get_reminder(self):
        session = Session()
        try:
            select_user = session.query(Users.user_id, Users.last_time).all()
            session.close()

            clock_time = int(Settings.get_clock_time())
            lst_id = []
            for s in select_user:
                delta = datetime.now() - s[1]
                if (int(delta.seconds / 60)) >= clock_time:
                    lst_id.append(s[0])

            return lst_id
        except:
            return -1



class Learning(Base):
    __tablename__ = 'learning'
    id = Column(Integer, primary_key=True)
    user = Column(String, ForeignKey('users.user_id'), nullable=False)
    word = Column(String, ForeignKey('words.word_id'), nullable=False)
    count_correct_answer = Column(Integer)
    last_time_answer = Column(DateTime)

    def set_learning(self, user, translate, true_or_false):
        session = Session()
        ret_value = session.query(Learning.count_correct_answer, Learning.word).filter(
            Learning.word == Words.word_id).filter(Learning.user == user).filter(Words.translate == translate).one()
        session.close()

        # Количество правильных ответов на слово
        count = ret_value[0]
        # Само слово
        one_word = ret_value[1]

        # Если правильный ответ
        if true_or_false == 1:
            count += 1

        try:
            # Апдейт таблицы
            session = Session()
            update_query = session.query(Learning).filter(Learning.user == user).filter(Learning.word == one_word).one()
            update_query.count_correct_answer = count
            update_query.last_time_answer = datetime.now()
            session.commit()
            session.close()
        except:
            session.rollback()
            session.close()

        return count

    def reset_true_answer(self, user, word):
        try:
            session = Session()
            update_true_answer = session.query(Learning).filter(Learning.word == Words.word_id).filter(
                Learning.user == user).filter(Words.translate == word).one()
            update_true_answer.count_correct_answer = 0
            session.commit()
            session.close()
        except:
            session.rollback()
            session.close()


# Таблица всех слов и их переводов
class Words(Base):
    __tablename__ = 'words'
    word_id = Column(String, primary_key=True)
    translate = Column(String)

    @staticmethod
    def get_one_random_word():
        session = Session()
        count_true_answer = Settings.get_count_true_answer()
        select_query = session.query(Words.word_id).filter(Words.word_id == Learning.word).filter(
            Learning.count_correct_answer < count_true_answer).all()
        session.close()
        random_word = select_query[random.randint(0, len(select_query) - 1)][0]
        return random_word

    @staticmethod
    def get_false_translates(word):
        session = Session()
        select_query = session.query(Words.translate).filter(Words.word_id != word).all()
        session.close()
        return select_query

    @staticmethod
    def get_true_translate(word):
        session = Session()
        select_query = session.query(Words.translate).filter(Words.word_id == word).one()
        session.close()
        return select_query[0]


# Таблица примеров
class Examples(Base):
    __tablename__ = 'examples'
    id = Column(Integer, primary_key=True)
    word = Column(String, ForeignKey('words.word_id'), nullable=False)
    example = Column(String)

    @staticmethod
    def get_example(word):
        session = Session()
        select_query = session.query(Examples.example).filter(Examples.word == word).all()
        session.close()
        return select_query


# Таблица настроек бота
class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    clock_time = Column(Integer, nullable=False)
    count_word_raund = Column(Integer, nullable=False)
    count_true_answer = Column(Integer, nullable=False)

    # Изменение настроек
    def edit_settings(self, ct, cwr, cta):
        try:
            session = Session()
            update_setting = session.query(Settings).one()
            update_setting.clock_time = ct
            update_setting.count_word_raund = cwr
            update_setting.count_true_answer = cta
            session.commit()
            session.close()
        except:
            session.rollback()
            session.close()

    @staticmethod
    def get_clock_time():
        try:
            session = Session()
            select_q = session.query(Settings.clock_time).one()
            session.close()
            return select_q[0]
        except:
            return -1

    @staticmethod
    def get_count_word_raund():
        session = Session()
        select_q = session.query(Settings.count_word_raund).one()
        session.close()
        return select_q[0]

    @staticmethod
    def get_count_true_answer():
        session = Session()
        select_q = session.query(Settings.count_true_answer).one()
        session.close()
        return select_q[0]


# Таблица для данных раунда
class DataRaund(Base):
    __tablename__ = 'dataraund'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    word = Column(String, ForeignKey('words.word_id'))
    num_question = Column(Integer)
    num_correct_answer = Column(Integer)
    num_incorrect_answers = Column(Integer)
    this_example = Column(Integer)

    def set_one_answer(self, user_id, word, num_question, num_correct_answer, num_incorrect_answers):
        session = Session()
        update_query = session.query(DataRaund).filter(DataRaund.user_id == user_id).one()
        update_query.word = word
        update_query.num_question = num_question
        update_query.num_correct_answer = num_correct_answer
        update_query.num_incorrect_answers = num_incorrect_answers
        session.commit()
        session.close()

    def example_or_not(self, user_id, example):
        session = Session()
        update_query = session.query(DataRaund).filter(DataRaund.user_id == user_id).one()
        update_query.this_example = example
        session.commit()
        session.close()

    @staticmethod
    def get_word(user_id):
        session = Session()
        select_query = session.query(DataRaund.word).filter(DataRaund.user_id == user_id).one()
        session.close()
        return select_query[0]

    @staticmethod
    def get_one_answer(user_id):
        session = Session()
        select_query = session.query(DataRaund.num_question, DataRaund.num_correct_answer,
                                     DataRaund.num_incorrect_answers).filter(DataRaund.user_id == user_id).one()
        session.close()
        return select_query

    @staticmethod
    def get_this_example(user_id):
        session = Session()
        select_query = session.query(DataRaund.this_example).filter(DataRaund.user_id == user_id).one()
        session.close()
        return select_query[0]


# Таблица для хранения токенов сообщений
class MessageInfo(Base):
    __tablename__ = 'messageinfo'
    user_id = Column(String, primary_key=True)
    token_message = Column(String)

    def add_record(self, user, token):
        session = Session()
        record = MessageInfo(user_id=user,
                             token_message=token)
        session.add(record)
        session.commit()
        session.close()

    def set_token_message(self, user, token):
        session = Session()
        insert_query = session.query(MessageInfo).filter(MessageInfo.user_id == user).one()
        insert_query.token_message = token
        session.commit()
        session.close()

    @staticmethod
    def get_token_message(user):
        try:
            session = Session()
            select_query = session.query(MessageInfo.token_message).filter(MessageInfo.user_id == user).one()
            session.close()
            return select_query[0]
        except:
            return -1


# Дефолтные настройки
def default_settings():
    session = Session()
    setting = Settings(clock_time=3,
                       count_word_raund=5,
                       count_true_answer=20)
    session.add(setting)
    session.commit()
    session.close()


# Занесение всех слов и прмеров в таблицы
def input_data():
    # Разбор файла "english_words" на элементы. При инициализации flask-приложения
    with open("english_words.json", "r", encoding="utf-8") as read_file:
        study_elements = json.load(read_file)

    for item in study_elements:
        try:
            session = Session()
            add_word = Words(word_id=item["word"],
                             translate=item["translation"])
            # Добавление нового слова
            session.add(add_word)
            session.commit()
            session.close()
        except:
            session.rollback()
            session.close()

        for item1 in item["examples"]:
            try:
                session = Session()
                add_exampl = Examples(word=item["word"],
                                      example=item1)
                # Добавление нового примера
                session.add(add_exampl)
                session.commit()
                session.close()
            except:
                session.rollback()
                session.close()

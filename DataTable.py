from sqlalchemy import create_engine, MetaData, ForeignKey, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

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

    # Добавление нового пользователя в БД
    def add_user(self, user_id, user_name):
        session = Session()
        new_user = Users(user_id=user_id,
                         name=user_name,
                         last_time=None)

        # Добавление нового юзера
        session.add(new_user)
        session.commit()
        session.close()

        session = Session()
        # Привязка всех слов для заучивания к юзеру
        words = session.query(Words.word_id).all()
        session.close()
        session = Session()
        for word in words:
            learning = Learning(user=user_id,
                                word=word[0],
                                count_correct_answer=0,
                                last_time_answer=None)
            session.add(learning)
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

    # Плучение данных о данном пользователе
    def get_data_user(self, user_id):
        data_user = []
        # Получаем время последнего ответа
        session = Session()
        time_value = session.query(Users.last_time).filter(Users.user_id == user_id).one()
        session.close()
        data_user.append(time_value[0])

        # Получаем количество выученных слов
        session = Session()
        learned_value = session.query(Learning.word).filter(Learning.user == user_id).filter(
            Learning.count_correct_answer > 20).count()
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

    def get_userd_id_last_time_in_30_min(self):
        session = Session()
        select_user = session.query(Users.user_id, Users.last_time).all()
        session.close()
        lst_id = []
        for s in select_user:
            delta = datetime.now() - s[1]
            if (delta.seconds / 60) > 3:
                lst_id.append(s[0])

        return lst_id


class Learning(Base):
    __tablename__ = 'learning'
    user = Column(String, ForeignKey('users.user_id'), nullable=False)
    word = Column(String, ForeignKey('words.word_id'), nullable=False)
    id = Column(Integer, primary_key=True)
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

        # Апдейт таблицы
        session = Session()
        update_query = session.query(Learning).filter(Learning.user == user).filter(Learning.word == one_word).one()
        update_query.count_correct_answer = count
        update_query.last_time_answer = datetime.now()
        session.commit()
        session.close()

        return count

    def reset_true_answer(self, user, word):
        session = Session()
        update_true_answer = session.query(Learning).filter(Learning.word == Words.word_id).filter(
            Learning.user == user).filter(Words.translate == word).one()
        update_true_answer.count_correct_answer = 0


class Words(Base):
    __tablename__ = 'words'
    word_id = Column(String, primary_key=True)
    translate = Column(String)


class Examples(Base):
    __tablename__ = 'examples'
    word = Column(String, ForeignKey('words.word_id'), nullable=False)
    id = Column(Integer, primary_key=True)
    example = Column(String)


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
                session = Session()
                add_exampl = Examples(word=item["word"],
                                      example=item1)
                # Добавление нового примера
                session.add(add_exampl)
                session.commit()
                session.close()

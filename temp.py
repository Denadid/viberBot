from sqlalchemy import create_engine, MetaData, ForeignKey, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
# Декларативный базовый класс
Base = declarative_base()


# Подключение к БД
engine = create_engine('sqlite:///database.db', echo=True)
metadata = MetaData()
# Сессия
Session = sessionmaker()
Session.configure(bind=engine)


class Users(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    last_time = Column(DateTime)
    name = Column(String)


class Learning(Base):
    __tablename__ = 'learning'
    user = Column(String, ForeignKey('users.user_id'), primary_key=True, nullable=False)
    word = Column(String, ForeignKey('words.word_id'), primary_key=True, nullable=False)
    id = Column(Integer, primary_key=True)
    count_correct_answer = Column(Integer)
    last_time_answer = Column(DateTime)


class Words(Base):
    __tablename__ = 'words'
    word_id = Column(String, primary_key=True)
    translate = Column(String)


class Examples(Base):
    __tablename__ = 'examples'
    word = Column(String, ForeignKey('words.word_id'), primary_key=True, nullable=False)
    id = Column(Integer, primary_key=True)
    example = Column(String)



user_id = "12345"
user_name="fige"
translate = "отвечать"
true_or_false = 1




for st in lst_id:
    print(st)

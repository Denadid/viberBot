from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from Setting import TOKEN
from OtherSettings import start_keyboard, round_keyboard, clock_keyboard
from user import User
import json
import random
import sqlite3
from DataTable import Users, Learning, Words, Examples, Base, engine, input_data
from datetime import datetime

app = Flask(__name__)

# Инициализация Viber-бота
viber = Api(BotConfiguration(
    name='FeaR',
    avatar='https://viber.com/avatar/jpg',
    auth_token=TOKEN
))

users_base = {}  # База пользователей (key: user_id, value: User object)
study_elements = []  # Элементы для изучения
study_words = []  # Слова для изучения ("word" (англ.))

user = Users()
# Разбор файла "english_words" на элементы. При инициализации flask-приложения
with open("english_words.json", "r", encoding="utf-8") as read_file:
    study_elements = json.load(read_file)

# Выделение только слов для изучения ("word") из study_elements
for item in study_elements:
    study_words.append(item["translation"])


# Обработка приходящих запросов
@app.route('/incoming', methods=['POST'])
def incoming():
    Base.metadata.create_all(engine)
    # Входящий запрос
    viber_request = viber.parse_request(request.get_data())

    # Обработка входящего запроса
    parsing_request(viber_request)

    # Успешно обработанный запрос
    return Response(status=200)


# Обработка запроса от пользователя
def parsing_request(viber_request):
    # Действия для новых пользователей
    if isinstance(viber_request, ViberConversationStartedRequest):
        # Добавление нового пользователя
        if user.find_user(viber_request.user.id) == -1:
            user.add_user(viber_request.user.id, viber_request.user.name)
        user_id = user.find_user(viber_request.user.id)
        users_base[user_id] = User(user_id, 0, 0, 0, None, None)

        # Вывод стартового окна
        show_start_area(viber_request, user_id)

    # Действия для пользователей из базы (уже подписавшихся)
    if isinstance(viber_request, ViberMessageRequest):
        user_id = user.find_user(viber_request.sender.id)
        # Обработка команды "start": запуск нового раунда
        message = viber_request.message.text
        if message == "start":
            # Вывод "второго" окна
            users_base[user_id] = User(user_id, 0, 0, 0, None, None)
            show_round_area(user_id)
            return

        if message == "remiend":
            user.set_last_time_answer(user_id)
            # Сообщение
            message = f"Напомню через 30 минут!"

            # Отправка сообщения
            viber.send_messages(user_id, [
                TextMessage(text=message)
            ])
            return

        if message == "inputdata":
            input_data()
            return 

        # Продолжение уже начатого раунда, если раунд не закончился
        total_count_raund = 5  # Общее количество раундов (по условию)


        # Обработка команды "show_example": вывод примера употребления слова
        if viber_request.message.text == "show_example":
            send_example_message(user_id)
        else:  # Если пользователь не запросил вывода примера и выбрал слово
            # Проверка на правильность ответа
            check_answer(viber_request, user_id)

            # Сброс примеров употребления
            users_base[user_id].example_list.clear()

        if users_base[user_id].count_question < total_count_raund:
            # Продолжение раунда
            show_round_area(user_id)
        else:  # При ответе на 10 вопросв - закончить раунд
            # Вывод результата раунда
            send_result_message(user_id)

            # Сброс данных пользователя
            users_base[user_id].count_question = 0
            users_base[user_id].num_correct_answers = 0
            users_base[user_id].num_incorrect_answers = 0

            # Вывод стартового окна
            show_start_area(viber_request, user_id)


# Отправка первого "экрана" (приветственного сообщения)
def show_start_area(viber_request, userID):
    # Приветственное сообщение
    data_us = user.get_data_user(userID)
    # Имя пользователя
    user_name = user.get_name_user(userID)
    if data_us[0] == None:
        message = "Приветствую вас, " + user_name + "!\n" +\
                  "Этот бот предназначен для заучивания английских слов. Для начала работы введите start или нажмите " \
                  "на кнопку внизу. "
    else:
        message = "Приветствую вас, " + user_name + "!\n" + f"Время последнего прохождения опроса: {data_us[0]}" + ".\n"+\
                   f" Количество выученных слов: {data_us[1]}" + f". Количесвто слов, которые находятся в процессе " \
                                                                 f"заучивания: {data_us[2]}" + ". "

    # Отправка сообщения
    viber.send_messages(userID, [
        TextMessage(text=message,
                    keyboard=start_keyboard,
                    tracking_data='tracking_data')
    ])


# Отправка "второго" экрана
def show_round_area(user1):
    # Количество доступных для изучения слов
    count_words = len(study_elements)

    # Случаный элемент для изучения
    num_item = random.randint(0, count_words - 1)
    study_item = study_elements[num_item]

    # Разбор study_item
    word = study_item["word"]
    translation = study_item["translation"]
    example_list = study_item["examples"]

    # Расстановка кнопок на клавиатуре
    set_round_keyboard(translation)

    # Отправка сообщения с вопросом
    send_question_message(user1, word)

    # Сохранения новых параметров пользователя
    users_base[user1].example_list = [item for item in example_list]
    users_base[user1].count_question += 1
    users_base[user1].current_word_rus = translation
    users_base[user1].current_word_eng = word


# Показать пример использования слова пользователю
def send_example_message(user1):
    # Вытащить случайное предложение с примером употребления слова
    # Текущее количество предложений и с примерами употребления слова
    count_example_words = len(users_base[user1].example_list)
    example = str(users_base[user1].example_list[random.randint(0, count_example_words - 1)])

    # Ответ
    viber.send_messages(user1, [
        TextMessage(text=example,
                    keyboard=round_keyboard,
                    tracking_data='tracking_data')
    ])


# Отправка сообщения с вопросом
def send_question_message(user1, word):
    # Формирование ответного сообщения
    message = f"{users_base[user1].count_question + 1}. Как переводится с английского слово [{word}]?"
    # Отправка сообщения
    viber.send_messages(user1, [
        TextMessage(text=message,
                    keyboard=round_keyboard,
                    tracking_data='tracking_data')
    ])


# Динамическая настройка клавиатуры
def set_round_keyboard(correct_word):
    # Случайная последовательность неправильных слов
    wrong_words = random.sample(study_words, 3)

    # Случайная последовательность для нумерации кнопок
    rand_list = random.sample([0, 1, 2, 3], 4)

    # Установка правильного ответа на случайную кнопку
    round_keyboard["Buttons"][rand_list[0]]["Text"] = correct_word
    round_keyboard["Buttons"][rand_list[0]]["ActionBody"] = correct_word

    # Расстановка неправильных слов на случайную кнопку
    round_keyboard["Buttons"][rand_list[1]]["Text"] = wrong_words[0]
    round_keyboard["Buttons"][rand_list[1]]["ActionBody"] = wrong_words[0]

    round_keyboard["Buttons"][rand_list[2]]["Text"] = wrong_words[1]
    round_keyboard["Buttons"][rand_list[2]]["ActionBody"] = wrong_words[1]

    round_keyboard["Buttons"][rand_list[3]]["Text"] = wrong_words[2]
    round_keyboard["Buttons"][rand_list[3]]["ActionBody"] = wrong_words[2]


# Проверка ответа на правильность
def check_answer(viber_request, user1):
    learn = Learning()
    if viber_request.message.text == users_base[user1].current_word_rus:
        # Правильный ответ
        users_base[user1].num_correct_answers += 1
        count_ok_answer = learn.set_learning(user1, viber_request.message.text, 1)
        # Отправка сообщения
        message = f"Ответ правильный. Количество правильных ответов на данное слово: {count_ok_answer}"
        viber.send_messages(user1, [
            TextMessage(text=message)
        ])

    else:
        # Неправильный ответ
        users_base[user1].num_incorrect_answers += 1

        learn.reset_true_answer(user1, viber_request.message.text)
        count_ok_answer = learn.set_learning(user1, viber_request.message.text, 0)
        # Отправка сообщения
        message = f"Ответ неправильный. Количество правильных ответов на данное слово: {count_ok_answer}"
        viber.send_messages(user1, [
            TextMessage(text=message)
        ])

    user.set_last_time_answer(user1)


# Отправка сообщения с результатами
def send_result_message(user1):
    count_correct = users_base[user1].num_correct_answers
    count_incorrect = users_base[user1].num_incorrect_answers

    # Сообщение
    message = f"Результат раунда. Правильных слов: {count_correct}, неверных ответов: {count_incorrect}"

    # Отправка сообщения
    viber.send_messages(user1, [
        TextMessage(text=message)
    ])


def clock_message(user):
    # Сообщение
    message = f"Прошло 30 минут с момента последнего прохождения теста!" \
              f" Пройдите заново, чтобы не забыдь ранее изученные слова!"

    # Отправка сообщения
    viber.send_messages(user, [
        TextMessage(text=message,
                    keyboard=clock_keyboard,
                    tracking_data='tracking_data')
    ])


# Запуск сервера
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)

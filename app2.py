from flask import Flask, request, Response, render_template
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from Setting import TOKEN
from OtherSettings import start_keyboard, round_keyboard, clock_keyboard
import json
import random
from DataTable import Users, Learning, Words, Examples, Base, engine, input_data, default_settings, Settings, DataRaund
from datetime import datetime

app = Flask(__name__)

# Инициализация Viber-бота
viber = Api(BotConfiguration(
    name='FeaR',
    avatar='https://viber.com/avatar/jpg',
    auth_token=TOKEN
))

user = Users()

# Обработка приходящих запросов
@app.route('/incoming', methods=['POST'])
def incoming():
    Base.metadata.create_all(engine)
    if Settings.get_clock_time() == -1:
        default_settings()
    # Входящий запрос
    viber_request = viber.parse_request(request.get_data())

    # Обработка входящего запроса
    parsing_request(viber_request)

    # Успешно обработанный запрос
    return Response(status=200)


# URL-адрес по умолчанию
@app.route('/')
def index():
    return render_template('index.html')


# URL-адрес для настроек бота
@app.route('/settings')
def settings():
    return render_template('settings.html')


# Получение значений настроек бота
@app.route('/result_settings')
def result_settings():
    time_remiend = int(request.args.get('time_remiend'))
    count_word = int(request.args.get('count_word'))
    count_answer = int(request.args.get('count_answer'))
    setting = Settings()
    setting.edit_settings(time_remiend, count_word, count_answer)
    return render_template('settings.html')


# Обработка запроса от пользователя
def parsing_request(viber_request):
    # Действия для новых пользователей
    if isinstance(viber_request, ViberConversationStartedRequest):
        # Добавление нового пользователя
        if user.find_user(viber_request.user.id) == -1:
            user.add_user(viber_request.user.id, viber_request.user.name)
        user_id = user.find_user(viber_request.user.id)

        # Вывод стартового окна
        show_start_area(viber_request, user_id)

    # Действия для пользователей из базы (уже подписавшихся)
    if isinstance(viber_request, ViberMessageRequest):
        user_id = user.find_user(viber_request.sender.id)
        raund = DataRaund()
        # Обработка команды "start": запуск нового раунда
        message = viber_request.message.text
        if message == "start":
            # Вывод "второго" окна
            show_round_area(user_id, raund)
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
        total_count_raund = int(Settings.get_count_word_raund())  # Общее количество раундов (по условию)

        # Обработка команды "show_example": вывод примера употребления слова
        if viber_request.message.text == "show_example":
            send_example_message(user_id)
        else:  # Если пользователь не запросил вывода примера и выбрал слово
            # Проверка на правильность ответа
            check_answer(viber_request, user_id, raund)

        num_question = DataRaund.get_one_answer(user_id)[0]

        if num_question < total_count_raund:
            # Продолжение раунда
            show_round_area(user_id, raund)
        else:  # При ответе на 10 вопросв - закончить раунд
            # Вывод результата раунда
            send_result_message(user_id)

            # Сброс данных пользователя
            num_question = 0
            raund.set_one_answer(user_id, None, num_question, 0, 0)

            # Вывод стартового окна
            show_start_area(viber_request, user_id)


# Отправка первого "экрана" (приветственного сообщения)
def show_start_area(viber_request, userID):
    # Приветственное сообщение
    data_us = user.get_data_user(userID)
    # Имя пользователя
    user_name = user.get_name_user(userID)
    if data_us[0] == None:
        message = "Приветствую вас, " + user_name + "!\n" + \
                  "Этот бот предназначен для заучивания английских слов. Для начала работы введите start или нажмите " \
                  "на кнопку внизу. "
    else:
        message = "Приветствую вас, " + user_name + "!\n" + f"Время последнего прохождения опроса: {data_us[0]}" + ".\n" + \
                  f" Количество выученных слов: {data_us[1]}" + f". Количесвто слов, которые находятся в процессе " \
                                                                f"заучивания: {data_us[2]}" + ". "

    # Отправка сообщения
    viber.send_messages(userID, [
        TextMessage(text=message,
                    keyboard=start_keyboard,
                    tracking_data='tracking_data')
    ])


# Отправка "второго" экрана
def show_round_area(user1, raund):
    # Рандомное слово для изучения
    word = Words.get_one_random_word()

    # Расстановка кнопок на клавиатуре
    set_round_keyboard(word)

    # Отправка сообщения с вопросом
    send_question_message(user1, word)

    # Сохранения новых параметров пользователя
    num_question = DataRaund.get_one_answer(user1)[0]
    num_question += 1
    num_correct_answer = DataRaund.get_one_answer(user1)[1]
    num_incorrect_answers = DataRaund.get_one_answer(user1)[2]
    raund.set_one_answer(user1, word, num_question, num_correct_answer, num_incorrect_answers)


# Показать пример использования слова пользователю
def send_example_message(user1):
    # Вытащить случайное предложение с примером употребления слова
    word = DataRaund.get_word(user1)
    examples = Examples.get_example(word)
    rand_example = examples[random.randint(0, len(examples) - 1)][0]

    # Ответ
    viber.send_messages(user1, [
        TextMessage(text=rand_example,
                    keyboard=round_keyboard,
                    tracking_data='tracking_data')
    ])


# Отправка сообщения с вопросом
def send_question_message(user1, word):
    # Формирование ответного сообщения
    count_question = DataRaund.get_one_answer(user1)[0]
    message = f"{count_question + 1}. Как переводится с английского слово [{word}]?"
    # Отправка сообщения
    viber.send_messages(user1, [
        TextMessage(text=message,
                    keyboard=round_keyboard,
                    tracking_data='tracking_data')
    ])


# Динамическая настройка клавиатуры
def set_round_keyboard(word):
    # Случайная последовательность неправильных слов
    false_words = Words.get_false_translates(word)
    f_words = random.sample(false_words, 3)
    # Правильное слово
    correct_word = Words.get_true_translate(word)

    # Случайная последовательность для нумерации кнопок
    rand_list = random.sample([0, 1, 2, 3], 4)

    # Установка правильного ответа на случайную кнопку
    round_keyboard["Buttons"][rand_list[0]]["Text"] = correct_word
    round_keyboard["Buttons"][rand_list[0]]["ActionBody"] = correct_word

    # Расстановка неправильных слов на случайную кнопку
    round_keyboard["Buttons"][rand_list[1]]["Text"] = f_words[0][0]
    round_keyboard["Buttons"][rand_list[1]]["ActionBody"] = f_words[0][0]

    round_keyboard["Buttons"][rand_list[2]]["Text"] = f_words[1][0]
    round_keyboard["Buttons"][rand_list[2]]["ActionBody"] = f_words[1][0]

    round_keyboard["Buttons"][rand_list[3]]["Text"] = f_words[2][0]
    round_keyboard["Buttons"][rand_list[3]]["ActionBody"] = f_words[2][0]


# Проверка ответа на правильность
def check_answer(viber_request, user1, raund):
    learn = Learning()
    word = DataRaund.get_word(user1)
    translate = Words.get_true_translate(word)

    num_question = DataRaund.get_one_answer(user1)[0]
    num_correct_answer = DataRaund.get_one_answer(user1)[1]
    num_incorrect_answers = DataRaund.get_one_answer(user1)[2]

    if viber_request.message.text == translate:
        # Правильный ответ
        num_correct_answer += 1
        count_ok_answer = learn.set_learning(user1, viber_request.message.text, 1)
        # Отправка сообщения
        message = f"Ответ правильный. Количество правильных ответов на данное слово: {count_ok_answer}"
        viber.send_messages(user1, [
            TextMessage(text=message)
        ])

    else:
        # Неправильный ответ
        num_incorrect_answers += 1

        learn.reset_true_answer(user1, viber_request.message.text)
        count_ok_answer = learn.set_learning(user1, viber_request.message.text, 0)
        # Отправка сообщения
        message = f"Ответ неправильный. Количество правильных ответов на данное слово: {count_ok_answer}"
        viber.send_messages(user1, [
            TextMessage(text=message)
        ])
    raund.set_one_answer(user1, word, num_question, num_correct_answer, num_incorrect_answers)
    user.set_last_time_answer(user1)


# Отправка сообщения с результатами
def send_result_message(user1):
    count_correct = DataRaund.get_one_answer(user1)[1]
    count_incorrect = DataRaund.get_one_answer(user1)[2]

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

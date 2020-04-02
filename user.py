class User(object):
    def __init__(self,
                 id,
                 num_question,
                 num_correct_answer,
                 num_incorrect_answers,
                 current_word_eng,
                 current_word_rus):
        self.id = id
        self.count_question = num_question
        self.num_correct_answers = num_correct_answer
        self.num_incorrect_answers = num_incorrect_answers
        self.current_word_eng = current_word_eng
        self.current_word_rus = current_word_rus
        self.example_list = []


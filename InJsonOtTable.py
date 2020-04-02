import sqlite3
import json

conn = sqlite3.connect('database.db')

cursor = conn.cursor()

# Разбор файла "english_words" на элементы. При инициализации flask-приложения
with open("english_words.json", "r", encoding="utf-8") as read_file:
    study_elements = json.load(read_file)


for item in study_elements:
    query = """
    INSERT INTO words (word_id, translate)
    VALUES (?, ?)
    """
    cursor.execute(query, (item["word"], item["translation"]))
    for item1 in item["examples"]:
        query1 = """
        INSERT INTO examples(word, example)
        VALUES (?, ?)
        """
        cursor.execute(query1, (item["word"], item1))

conn.commit()
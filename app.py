from flask import Flask, render_template, request
import requests
import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DATABASE = os.getenv('DATABASE')
DB_PORT = os.getenv('DB_PORT')

URL = 'https://api.animechan.io/v1'

def load_quotes():

    params = {
        "anime" : "Cowboy Bebop",
        "page" : 1
    }
    cnx = None
    cursor = None
    try:
        response = requests.get(f'{URL}/quotes/', params=params)
        response.raise_for_status()
        json_in=response.json()
        print("успешно")
    except requests.exceptions.RequestException as error:
        print(f"ошибка: {error}")
        return
    if not isinstance(json_in, dict) or 'data' not in json_in or not json_in['data']:
        print("ошибка: API не вернул список цитат или список пуст.")
        print(f"полученный ответ: {json_in}")
        return


    data_to_insert =[]
    json_quotes = json_in['data']

    for qoute_data in json_quotes:
        row_data = (
            qoute_data.get('content'),
            qoute_data.get('anime',{}).get('name'),
            qoute_data.get('character', {}).get('name')  
    )
        data_to_insert.append(row_data)

    
    try:
        cnx = mysql.connector.connect(
            host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
    )
        cursor = cnx.cursor()
        rqst = "INSERT INTO quotes(quote, anime_title, name_character) VALUES(%s, %s, %s)"
        cursor.executemany(rqst, data_to_insert)
        cnx.commit()
        print(f"вставлено {cursor.rowcount} записей в БД.")
    except requests.exceptions.RequestException as error:
        print(f"ошибка при запросе к API: {error}")
        return
    except mysql.connector.Error as e:
        print(f"ошибка:{e}")

    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()

def get_quotes():
    quotes = []
    cnx = None
    cursor = None
    try:
        cnx = mysql.connector.connect(
            host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
    )
        cursor = cnx.cursor(dictionary=True)
        rqst = "SELECT quote, anime_title, name_character FROM quotes ORDER BY RAND() LIMIT 1"
        cursor.execute(rqst)
        quotes = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"ошибка:{e}")
    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()
    return quotes

daily_cash = None
last_cash = None

def get_quotes_of_day():
    global daily_cash
    global last_cash
    today = date.today()

    if daily_cash is not None and last_cash==today:
        return daily_cash
    new_quotes = get_quotes()

    if new_quotes:
        daily_cash = new_quotes
        last_cash = today
        return daily_cash
    else:
        return[]
    
# def search_by_character():
#     quotes  = None
#     cnx = None
#     cursor = None
#     try:
#         cnx = mysql.connector.connect(
#             host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
#     )
#         cursor = cnx.cursor(dictionary=True)
#         rqst = "SELECT quote, anime_title, name_character FROM quotes WHERE name_character = %s ORDER BY RAND() LIMIT 1"
#         cursor.execute(rqst)
#         quotes = cursor.fetchall()
#     except mysql.connector.Error as e:
#         print(f"ошибка:{e}")
#     finally:
#         if cursor:
#             cursor.close()
#         if cnx and cnx.is_connected():
#             cnx.close()
#     return quotes

# def search_by_title():
#     quotes  = None
#     cnx = None
#     cursor = None
#     try:
#         cnx = mysql.connector.connect(
#             host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
#     )
#         cursor = cnx.cursor(dictionary=True)
#         rqst = "SELECT quote, anime_title, name_character FROM quotes WHERE anime_title = %s ORDER BY RAND() LIMIT 1"
#         cursor.execute(rqst)
#         quotes = cursor.fetchall()
#     except mysql.connector.Error as e:
#         print(f"ошибка:{e}")
#     finally:
#         if cursor:
#             cursor.close()
#         if cnx and cnx.is_connected():
#             cnx.close()
#     return quotes

app = Flask(__name__)



@app.route('/')
def index():
    random_quotes_list = get_quotes() 
    return render_template("index.html", random_quotes=random_quotes_list)

@app.route('/daily')
def daily():
    daily_quote_list = get_quotes_of_day() 
    daily_quote_data = daily_quote_list[0] if daily_quote_list else None
    
    return render_template("daily_quote.html", daily_quote=daily_quote_data) 

@app.route('/favorites')
def favorites():
    favorites_quotes_list = [] 
    return render_template("favorites.html", favorites_quotes=favorites_quotes_list)

if __name__ == "__main__":
    # load_quotes()
    app.run(debug=True)


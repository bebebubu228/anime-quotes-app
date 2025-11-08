from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
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

# функция для загрузки цитат с api и сохранения их в бд
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
        print("запрос к api прошел успешно.")
    except requests.exceptions.RequestException as error:
        print(f"ошибка библиотеки requests: {error}")
        return
    if not isinstance(json_in, dict) or 'data' not in json_in or not json_in['data']:
        print("ошибка: api не вернул список цитат или список пуст.")
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
        print(f"ошибка при запросе к api: {error}")
        return
    except mysql.connector.Error as e:
        print(f"ошибка бд:{e}")
    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()

# функция для получения одной случайной цитаты из бд
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
        print(f"ошибка бд:{e}")
    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()
    return quotes

daily_cash = None # глобальная переменная для хранения закэшированной "цитаты дня"
last_cash = None # глобальная переменная для хранения даты последнего кэширования

# функция для получения цитаты дня 
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
    
# функция для регистрации нового пользователя
def reg_form(username, email, password):
    cnx = None
    cursor = None
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8') # хэширование пароля перед сохранением
    try:
        cnx = mysql.connector.connect(
            host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
        )
        cursor = cnx.cursor()
        rqst_select = "SELECT id FROM users WHERE username = %s OR email = %s"
        cursor.execute(rqst_select, (username, email)) 
        
        if cursor.fetchone():
            return "gользователь с таким именем или email уже существует", False 
        rqst_insert = "INSERT INTO users(username, email, password_hash) VALUES(%s, %s, %s)"
        cursor.execute(rqst_insert, (username, email, password_hash))
        cnx.commit() 
        return "регистрация успешна! теперь вы можете войти.", True 
    
    except mysql.connector.Error as e:
        print(f"ошибка базы данных при регистрации: {e}")
        return f"ошибка базы данных: {e}", False 
    except Exception as e:
        print(f"непредвиденная ошибка при регистрации: {e}")
        return f"произошла непредвиденная ошибка: {e}", False
    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()

# функция для аутентификации пользователя
def log_form(username, email, password):
    user = None
    cnx = None
    cursor = None
    try:
        cnx = mysql.connector.connect(
            host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
        )
        cursor = cnx.cursor(dictionary=True)
        rqst = "SELECT id, username, email, password_hash FROM users WHERE username = %s AND email = %s"
        cursor.execute(rqst, (username, email))
        user = cursor.fetchone()
        
        if not user:
            return "неверное имя пользователя или email", False, None
        if bcrypt.check_password_hash(user['password_hash'], password): 
            return f"добро пожаловать, {user['username']}", True, user
        else:
            return "неверный пароль", False, None
            
    except mysql.connector.Error as e:
        return f"ошибка базы данных: {e}", False, None
    except Exception as e:
        return f"произошла непредвиденная ошибка: {e}", False, None
    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()

# функция для поиска цитат по имени персонажа.
def search_by_character(character_name):
    quotes  = None
    cnx = None
    cursor = None
    try:
        cnx = mysql.connector.connect(
            host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
    )
        cursor = cnx.cursor(dictionary=True)
        rqst = "SELECT quote, anime_title, name_character FROM quotes WHERE name_character LIKE %s ORDER BY RAND() LIMIT 1"
        search_term = f"%{character_name}%"
        cursor.execute(rqst, (search_term,))
        quotes = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"ошибка:{e}")
    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()
    return quotes

# функция для поиска цитат по названию аниме
def search_by_title(anime_title):
    quotes  = None
    cnx = None
    cursor = None
    try:
        cnx = mysql.connector.connect(
            host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
    )
        cursor = cnx.cursor(dictionary=True)
        rqst = "SELECT quote, anime_title, name_character FROM quotes WHERE anime_title LIKE %s ORDER BY RAND() LIMIT 1"
        search_term = f"%{anime_title}%"
        cursor.execute(rqst, (search_term,))
        quotes = cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"ошибка:{e}")
    finally:
        if cursor:
            cursor.close()
        if cnx and cnx.is_connected():
            cnx.close()
    return quotes

app = Flask(__name__)

bcrypt = Bcrypt(app)

@app.route('/')
@app.route('/index.html')
def index():
    quotes = get_quotes()
    return render_template('index.html', random_quotes=quotes, search_result_character=None, search_result_anime=None)

@app.route('/daily.html')
def daily():
    daily_quote_list = get_quotes_of_day() 
    daily_quote_data = daily_quote_list[0] if daily_quote_list else None
    
    return render_template("daily.html", daily_quote=daily_quote_data) 

@app.route('/favorites.html')
def favorites_page():
    return render_template('favorites.html')

@app.route('/search-character', methods=['POST'])
def handle_character_search():
    character_name = request.form.get('character_name')
    found_quotes = []
    
    if character_name:
        found_quotes = search_by_character(character_name)
    random_quotes = get_quotes()
    return render_template('index.html', random_quotes=random_quotes, search_result_character=found_quotes,search_result_anime=None) 

@app.route('/search-anime', methods=['POST'])
def handle_anime_search():
    anime_title = request.form.get('anime_title')
    found_quotes = []
    
    if anime_title:
        found_quotes = search_by_title(anime_title)
    random_quotes = get_quotes()
    return render_template('index.html', random_quotes=random_quotes, search_result_character=None, search_result_anime=found_quotes)

@app.route('/register.html')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def handle_register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not username or not email or not password:
        flash('пожалуйста, заполните все поля.', 'error')
        return redirect(url_for('register_page'))
    message, success = reg_form(username, email, password)
    if success:
        flash(message, 'success')
        return redirect(url_for('login_page')) 
    else:
        flash(message, 'error')
        return redirect(url_for('register_page'))

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not username or not email or not password:
        flash('пожалуйста, заполните все поля.', 'error')
        return redirect(url_for('login_page'))

    message, success, user = log_form(username, email, password)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('index')) 
    else:
        flash(message, 'error')
        return redirect(url_for('login_page'))

if __name__ == "__main__":
    # load_quotes()
    app.run(debug=True)

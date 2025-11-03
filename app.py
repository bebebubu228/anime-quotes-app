from flask import Flask, render_template
#import requests
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DATABASE = os.getenv('DATABASE')
DB_PORT = os.getenv('DB_PORT')

cnx = mysql.connector.connect(
    host = DB_HOST, user = DB_USER, password = DB_PASSWORD, database = DATABASE, port = DB_PORT
)
cursor = cnx.cursor()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")
#случайна цитата random
#response = requests.get(f'{https://api.animechan.io/v1}/quotes/random')

if __name__ == "__main__":
    app.run(debug=True)

cnx.commit() 
cursor.close()
cnx.close()
from flask import Flask, render_template
#import requests
import mysql.connector
cnx = mysql.connector.connect(user=USERNAME, password=PASSWORD, host=SERVER, database=DATABASE)
cursor = cnx.cursor()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

cnx.commit() 
cursor.close()
cnx.close()
from flask import Flask, render_template
import pandas as pd

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/evaluacion')
def evaluacion():
    return render_template('evaluacion.html')

if __name__ == '__main__':
    app.run(debug = True, port = 5000)
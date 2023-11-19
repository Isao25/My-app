from flask import Flask, render_template, request, session, redirect
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/evaluacion', methods=['GET', 'POST'])
def evaluacion():
    if request.method == 'POST':
        sintoma = request.form.get('sintoma')
        if sintoma:
            sintomas_agregados = session.get('sintomas_agregados', [])

            sintomas_permitidos = pd.read_csv('static/csv/sintomaSeveridad.csv')['Symptom'].unique().tolist()
            if sintoma in sintomas_permitidos:
                if sintoma not in sintomas_agregados:
                    sintomas_agregados.append(sintoma)
                    session['sintomas_agregados'] = sintomas_agregados
                    print(f'Síntoma {sintoma} agregado. Lista actualizada: {sintomas_agregados}')

    enfermedades = pd.read_csv('static/csv/enfermedadSintomas.csv')

    sintomas = pd.read_csv('static/csv/sintomaSeveridad.csv')
    lista_sintomas = sintomas['Symptom'].unique().tolist()

    sintomas_agregados = session.get('sintomas_agregados', [])

    return render_template('evaluacion.html', lista_sintomas=lista_sintomas, sintomas_agregados=sintomas_agregados)

@app.route('/eliminarSintoma', methods=['POST'])
def eliminar_sintoma():
    if request.method == 'POST':
        sintoma_a_eliminar = request.form.get('sintoma')
        if sintoma_a_eliminar:
            sintomas_agregados = session.get('sintomas_agregados', [])
            if sintoma_a_eliminar in sintomas_agregados:
                sintomas_agregados.remove(sintoma_a_eliminar)
                session['sintomas_agregados'] = sintomas_agregados
                print(f'Síntoma {sintoma_a_eliminar} eliminado. Lista actualizada: {sintomas_agregados}')

    return redirect('/evaluacion')



@app.route('/about')
def about():
    return render_template('about.html')
if __name__ == '__main__':
    app.run(debug = True, port = 5000)
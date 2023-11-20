from flask import Flask, render_template, request, session, redirect
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = os.urandom(24)

def calcular_similitud(enfermedad, sintomas_usuario):
    sintomas_enfermedad = set(symptom for symptom in enfermedad.iloc[1:].dropna().tolist() if symptom)
    sintomas_usuario = set(sintomas_usuario)

    if not sintomas_enfermedad:
        return None  # Evitar divisiones por cero

    # Calcular la similitud entre los conjuntos de síntomas
    similitud = len(sintomas_enfermedad.intersection(sintomas_usuario)) / len(sintomas_enfermedad)

    return similitud

def obtener_diccionario_similitud(df, sintomas_usuario):
    diccionario_similitud = {}

    for i, enfermedad in df.iterrows():
        similitud = calcular_similitud(enfermedad, sintomas_usuario)

        if similitud is not None and similitud > 0:
            diccionario_similitud[enfermedad['Disease']] = round(similitud * 100,2)  # Convertir a porcentaje

    return diccionario_similitud

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

@app.route('/evaluacion/analizarSintomas')
def analizar_sintoma():
    enfermedades = pd.read_csv('static/csv/enfermedadSintomas.csv')
    sintomas_agregados = session.get('sintomas_agregados', [])
    resultado = obtener_diccionario_similitud(enfermedades, sintomas_agregados)

    # Crear un DataFrame a partir del diccionario
    df_resultado = pd.DataFrame(list(resultado.items()), columns=['Enfermedad', 'Similitud (%)'])

    # Convertir DataFrame a HTML
    tabla_html = df_resultado.to_html(index=False, classes='table table-striped')

    # Crear un gráfico estadístico
    plt.bar(df_resultado['Enfermedad'], df_resultado['Similitud (%)'])
    plt.xlabel('Enfermedad')
    plt.ylabel('Similitud (%)')
    plt.title('Similitud de enfermedades con los síntomas ingresados')
    plt.xticks(rotation=45, ha='right')

    # Guardar el gráfico en un objeto BytesIO
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png', bbox_inches='tight')
    img_buf.seek(0)
    
    # Convertir la imagen a base64 para mostrarla en el HTML
    img_base64 = base64.b64encode(img_buf.read()).decode('utf-8')
    
    # Cerrar la figura de matplotlib
    plt.close()

    return render_template('analizarSintomas.html', tabla_html=tabla_html, img_base64=img_base64)


@app.route('/about')
def about():
    return render_template('about.html')
if __name__ == '__main__':
    app.run(debug = True, port = 5000)
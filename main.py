from flask import Flask, render_template, request, session, redirect, url_for
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
# Configurar Matplotlib para usar el modo sin interactividad
matplotlib.use('Agg')

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Cambia el nombre de la clave de sesión para evitar conflictos
SESSION_KEY = 'sintomas_agregados'

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

def obtener_lista_sintomas(enfermedades):
    columnas_sintomas = enfermedades.columns[1:]
    sintomas_unicos = set()
    for columna in columnas_sintomas:
        sintomas_unicos.update(enfermedades[columna].dropna())
    listaSintomas = list(filter(lambda x: x != '', sintomas_unicos))
    return listaSintomas

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/evaluacion', methods=['GET', 'POST'])
def evaluacion():
    # Cambios en el manejo de sesiones
    if 'sintomas_agregados' not in session:
        session['sintomas_agregados'] = []

    enfermedades = pd.read_csv('static/csv/dataEnfermedades.csv')
    
    if request.method == 'POST':
        sintoma = request.form.get('sintoma')
        if sintoma:
            sintomas_agregados = session['sintomas_agregados']

            sintomas_permitidos = obtener_lista_sintomas(enfermedades)
            if sintoma in sintomas_permitidos:
                if sintoma not in sintomas_agregados:
                    sintomas_agregados.append(sintoma)
                    session['sintomas_agregados'] = sintomas_agregados
                    

    sintomas_agregados = session['sintomas_agregados']

    #sintomas = pd.read_csv('static/csv/dataSintomas.csv')
    lista_sintomas = obtener_lista_sintomas(enfermedades)

    return render_template('evaluacion.html', lista_sintomas=lista_sintomas, sintomas_agregados=sintomas_agregados)

@app.route('/eliminarSintoma', methods=['POST'])
def eliminar_sintoma():
    if request.method == 'POST':
        sintoma_index = int(request.form.get('sintoma', -1))
        if sintoma_index != -1:
            sintomas_agregados = session['sintomas_agregados']
            # Asegúrate de que el índice esté en el rango correcto
            if 0 <= sintoma_index - 1 < len(sintomas_agregados):
                sintomas_agregados.pop(sintoma_index - 1)  # Restamos 1 ya que loop.index es 1-indexed
                session['sintomas_agregados'] = sintomas_agregados
                

    return redirect(url_for('evaluacion'))

@app.route('/evaluacion/analizarSintomas')
def analizar_sintoma():
    enfermedades = pd.read_csv('static/csv/dataEnfermedades.csv')
    sintomas_agregados = session['sintomas_agregados']
    resultado = obtener_diccionario_similitud(enfermedades, sintomas_agregados)
    # Ordenar el diccionario por similitud porcentual en orden descendente
    resultado = dict(sorted(resultado.items(), key=lambda item: item[1], reverse=True))
    # Obtener las tres primeras (o la primera) enfermedades con mayor similitud
    top_enfermedades = list(resultado.items())[:3] if len(resultado) >= 3 else list(resultado.items())[:1]
    #Dataset de descripción por enfermedad:
    descripcion = pd.read_csv('static/csv/dataDescripcionEnfermedades.csv')
    # Crear un DataFrame con las descripciones de las enfermedades
    df_descripciones = pd.DataFrame(top_enfermedades, columns=['Enfermedad', 'Similitud (%)'])

    # Fusionar con el DataFrame de descripciones usando 'Enfermedad' como clave
    df_completo = pd.merge(df_descripciones, descripcion, left_on='Enfermedad', right_on='Disease')
    # Crear un nuevo diccionario de enfermedades y sus descripciones
    dicionario_descripciones = dict(zip(df_completo['Enfermedad'], df_completo['Description']))
      
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

    return render_template('analizarSintomas.html', tabla_html=tabla_html, img_base64=img_base64, sintomas_agregados=sintomas_agregados, dicionario_descripciones=dicionario_descripciones)

@app.route('/nuevaEvaluacion', methods=['GET'])
def nueva_evaluacion():
    # Limpiar la lista de síntomas en la sesión
    session['sintomas_agregados'] = []
    
    # Redirigir a la página de evaluación
    return redirect(url_for('evaluacion'))

@app.route('/about')
def about():
    return render_template('about.html')
if __name__ == '__main__':
    app.run(debug = True, port = 5000)
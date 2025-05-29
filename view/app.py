from flask import Flask, render_template, request, redirect, url_for, flash
import os
from flask_mysqldb import MySQL

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'))



app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dinamyc_look_copia' # Nomnre de la base de datos
mysql = MySQL(app)

app.secret_key = 'mysecret_key'

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios')
    data = cur.fetchall()
    return render_template('Vistas_admin/usuarios.html', usuarios=data)

@app.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':  
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        co = request.form['Correo']
        tel = request.form['Telefono']
        clave = request.form['Clave']
        rol = 1
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO usuarios (Nombre, Apellido, Correo, Telefono, clave, ID_RolFK) VALUES (%s, %s, %s, %s, %s, %s)',
                    (nombre, apellido, co, tel, clave, rol))
        mysql.connection.commit()
        flash('usuario agregado correctamente')
        return redirect(url_for('index'))

@app.route('/edit/<id>')
def get_contact(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE id_usuario = %s', (id,)) 
    data = cur.fetchall()
    
    # Corregida la ruta del template
    return render_template('Vistas_admin/usuarios.html', usuarios=data)

@app.route('/delete')
def delete_contact():
    return 'delete contact'

# Ruta de diagnóstico mejorada
@app.route('/diagnostico')
def diagnostico():
    template_dir = os.path.abspath(app.template_folder)
    resultado = {
        'directorio_actual': os.getcwd(),
        'ruta_absoluta': template_dir,
        'template_folder': app.template_folder
    }

#----------------------------- COMPROBACIONES ----------------------------------
    # Comprobar si el directorio existe
    if os.path.exists(template_dir):
        resultado['template_dir_existe'] = True
        resultado['contenido_template_dir'] = os.listdir(template_dir)
        
        # Verificar la carpeta Vistas_admin
        vistas_admin_path = os.path.join(template_dir, 'Vistas_admin')
        
        if os.path.exists(vistas_admin_path):
            resultado['vistas_admin_existe'] = True
            resultado['contenido_vistas_admin'] = os.listdir(vistas_admin_path)
        else:
            resultado['vistas_admin_existe'] = False
    else:
        resultado['template_dir_existe'] = False
    
    return resultado

@app.route('/verificar_static')
def verificar_static():
    static_dir = os.path.join(BASE_DIR, 'static')
    return {
        "static_dir": static_dir,
        "static_existe": os.path.exists(static_dir),
        "contenido_static": os.listdir(static_dir)
    }


if __name__ == '__main__':
    # Imprime información útil de depuración al iniciar
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(f"Directorio de templates (ruta absoluta): {os.path.abspath(app.template_folder)}")
    print(f"Directorio de templates existe: {os.path.exists(os.path.abspath(app.template_folder))}")
    
    app.run(debug=True)
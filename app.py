import os
from flask import Flask, jsonify
from controller.routes import main_bp
from controller.auth_routes import auth_bp
from model.database import configure_db, get_db

# Directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Crear aplicación Flask
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
# ------------------ CONFIGURACIONES ------------------

# Configurar la base de datos
configure_db(app)

# Clave secreta para sesiones y flash messages
# En producción define la variable de entorno SECRET_KEY
app.secret_key = os.getenv("SECRET_KEY", "clave_super_secreta_123")

# Registrar los blueprints
app.register_blueprint(main_bp, url_prefix="/")
app.register_blueprint(auth_bp, url_prefix="/auth")

# ------------------ RUTAS DE DIAGNÓSTICO ------------------


@app.route('/diagnostico')
def diagnostico():
    template_dir = os.path.abspath(app.template_folder)
    resultado = {
        'directorio_actual': os.getcwd(),
        'ruta_absoluta': template_dir,
        'template_folder': app.template_folder
    }

    if os.path.exists(template_dir):
        resultado['template_dir_existe'] = True
        resultado['contenido_template_dir'] = os.listdir(template_dir)

        vista_admin_path = os.path.join(template_dir, 'vista_admin')
        if os.path.exists(vista_admin_path):
            resultado['vista_admin_existe'] = True
            resultado['contenido_vista_admin'] = os.listdir(vista_admin_path)
        else:
            resultado['vista_admin_existe'] = False
    else:
        resultado['template_dir_existe'] = False

    return jsonify(resultado)


@app.route('/verificar_static')
def verificar_static():
    static_dir = os.path.join(BASE_DIR, 'static')
    return jsonify({
        "static_dir": static_dir,
        "static_existe": os.path.exists(static_dir),
        "contenido_static": os.listdir(static_dir) if os.path.exists(static_dir) else []
    })


@app.route("/testdb")
def testdb():
    mysql = get_db()  # 👈 aquí recuperamos el objeto mysql
    cur = mysql.connection.cursor()
    cur.execute("SELECT DATABASE();")
    db = cur.fetchone()
    cur.close()
    return f"Conectado a la base: {db}"


# ------------------ MAIN ------------------


if __name__ == '__main__':
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(
        f"Directorio de templates (ruta absoluta): {os.path.abspath(app.template_folder)}")
    print(
        f"Directorio de templates existe: {os.path.exists(os.path.abspath(app.template_folder))}")

    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(debug=debug_mode)

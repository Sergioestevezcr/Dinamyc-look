from flask import Flask
import os
from flask import Flask, jsonify
from model.database import configure_db
from controller.routes import main_bp  # Importamos el blueprint principal
# Importamos el blueprint de autenticación
from controller.auth_routes import auth_bp

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

# Configurar la base de datos
configure_db(app)

# Configurar la clave secreta
# Asegúrate de que esta sea una clave secreta fuerte en producción
# app.secret_key = 'mysecret_key'

# Registrar los blueprints de rutas
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)  # Registramos el blueprint de autenticación


# -------------------------------------- DIAGNÓSTICO -----------------------------------------
# Mantener estas rutas aquí si son para la aplicación principal o mover a un blueprint de diagnóstico
# Dependiendo de su propósito

@app.route('/diagnostico')
def diagnostico():
    template_dir = os.path.abspath(app.template_folder)
    resultado = {
        'directorio_actual': os.getcwd(),
        'ruta_absoluta': template_dir,
        'template_folder': app.template_folder
    }

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

    return jsonify(resultado)


@app.route('/verificar_static')
def verificar_static():
    static_dir = os.path.join(BASE_DIR, 'static')
    return jsonify({
        "static_dir": static_dir,
        "static_existe": os.path.exists(static_dir),
        "contenido_static": os.listdir(static_dir) if os.path.exists(static_dir) else []
    })


if __name__ == '__main__':
    # Imprime información útil de depuración al iniciar
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(
        f"Directorio de templates (ruta absoluta): {os.path.abspath(app.template_folder)}")
    print(
        f"Directorio de templates existe: {os.path.exists(os.path.abspath(app.template_folder))}")

    app.run(debug=True)

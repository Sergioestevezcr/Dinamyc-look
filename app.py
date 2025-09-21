from flask import Flask, session
from flask_mysqldb import MySQL
import os

from database import mysql

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(__name__)

    # Configuración MySQL
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'dinamyc_look2'
    mysql.init_app(app)

    # Configuración correo
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'vargasruizlauravalentina@gmail.com'
    app.config['MAIL_PASSWORD'] = 'rjvc vwsr mtuq phzt'

    # Configuración uploads
    UPLOAD_FOLDER = 'static/imagenes'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.secret_key = 'mysecret_key'

    # Importar y registrar blueprints
    from controllers.auth_controller import auth_bp
    from controllers.client_controller import client_bp
    from controllers.admin_controller import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(client_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app   # 👈 muy importante


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

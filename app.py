# app.py
from flask import Flask, render_template
import os
from database import mysql  # extensión de MySQL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_app():
    flask_app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, 'templates'),
        static_folder=os.path.join(BASE_DIR, 'static')
    )

    # ---------------- Configuración MySQL ----------------
    flask_app.config['MYSQL_HOST'] = '13.59.80.138'
    flask_app.config['MYSQL_USER'] = 'admin1'
    flask_app.config['MYSQL_PASSWORD'] = 'Is41l0'
    flask_app.config['MYSQL_DB'] = 'dinamyc_look2'
    mysql.init_app(flask_app)

    # ---------------- Configuración correo ----------------
    flask_app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    flask_app.config['MAIL_PORT'] = 587
    flask_app.config['MAIL_USE_TLS'] = True
    flask_app.config['MAIL_USERNAME'] = 'vargasruizlauravalentina@gmail.com'
    flask_app.config['MAIL_PASSWORD'] = 'rjvc vwsr mtuq phzt'

    # ---------------- Configuración uploads ----------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'imagenes')
    flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # ---------------- Registro de Blueprints ----------------
    from controllers.client_controller import client_bp
    from controllers.auth_controller import auth_bp
    from controllers.admin_controller import admin_bp
    from controllers.diagnostic_controller import diagnostic_bp

    flask_app.register_blueprint(client_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(diagnostic_bp)

    # ---------------- Handlers de error ----------------
    @flask_app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @flask_app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return flask_app


# app.py
from flask import Flask, render_template
import os
from database import init_app
from config import Config


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_app():
    flask_app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, 'templates'),
        static_folder=os.path.join(BASE_DIR, 'static')
    )

    # ---------------- Configuración base ----------------
    flask_app.config.from_object(Config)

    # ---------------- Inicialización de extensiones ----------------
    init_app(flask_app)

    # ---------------- Configuración uploads ----------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'imagenes')
    flask_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # ---------------- Registro de Blueprints ----------------
    from controllers.client_controller import client_bp
    from controllers.auth_controller import auth_bp
    from controllers.admin_controller import admin_bp
    from controllers.diagnostic_controller import diagnostic_bp
    from controllers.payment_controller import payment_bp

    # Cada blueprint con su url_prefix para evitar conflictos
    flask_app.register_blueprint(client_bp, url_prefix="/")
    flask_app.register_blueprint(auth_bp, url_prefix="/auth")
    flask_app.register_blueprint(admin_bp, url_prefix="/admin")
    flask_app.register_blueprint(diagnostic_bp, url_prefix="/diagnostic")
    flask_app.register_blueprint(payment_bp, url_prefix="/")

    # ---------------- Handlers de error ----------------
    @flask_app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @flask_app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # return debe ir al final
    return flask_app
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'A_REALLY_SECRET_KEY_THAT_NO_ONE_KNOWS'

    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQL_HOST')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DB = os.getenv('MYSQL_DB')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # Use an app password for security

    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Mercado Pago

    # Token privado de Mercado Pago (de prueba o producción).
    # Debe ser un string plano SIN coma al final.
    # Ejemplo test: "TEST-1234..."
    # Ejemplo prod: "APP_USR-1234..."
    MP_ACCESS_TOKEN = os.getenv('MP_ACCESS_TOKEN')

    # Secreto para firmar/validar el webhook (puede ser token_hex(32))
    MP_WEBHOOK_SECRET = os.getenv('MP_WEBHOOK_SECRET')

    # URLs de redirección cuando Mercado Pago termina
    MP_SUCCESS_URL = "https://dinamyclook.com/pago/exitoso"
    MP_FAILURE_URL = "https://dinamyclook.com/pago/fallido"
    MP_PENDING_URL = "https://dinamyclook.com/pago/pendiente"

    # URL pública donde Mercado Pago te manda notificaciones (POST webhook)
    MP_NOTIFICATION_URL = "https://dinamyclook.com/webhook/mercadopago"

import os


class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'A_REALLY_SECRET_KEY_THAT_NO_ONE_KNOWS'

    # MySQL Configuration
    MYSQL_HOST = '3.131.159.165'
    MYSQL_USER = 'admin1'
    MYSQL_PASSWORD = 'Is41l0'
    MYSQL_DB = 'dinamyc_look2'

    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'dinamycloock@gmail.com'
    MAIL_PASSWORD = 'rprf tkea dmyi hunc'  # Use an app password for security

    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # Mercado Pago

    # Token privado de Mercado Pago (de prueba o producción).
    # Debe ser un string plano SIN coma al final.
    # Ejemplo test: "TEST-1234..."
    # Ejemplo prod: "APP_USR-1234..."
    MP_ACCESS_TOKEN = "APP_USR-3709518704049576-102719-94ed29cce6aa03c023cdbd42f1f0e1f2-91372455"

    # Secreto para firmar/validar el webhook (puede ser token_hex(32))
    MP_WEBHOOK_SECRET = "e3f10ba236d83cb15ca7482fd97dd0dcf6423daad060b7fe50d04160b1638216"

    # URLs de redirección cuando Mercado Pago termina
    MP_SUCCESS_URL = "https://dinamyclook.com/pago/exitoso"
    MP_FAILURE_URL = "https://dinamyclook.com/pago/fallido"
    MP_PENDING_URL = "https://dinamyclook.com/pago/pendiente"

    # URL pública donde Mercado Pago te manda notificaciones (POST webhook)
    MP_NOTIFICATION_URL = "https://dinamyclook.com/webhook/mercadopago"

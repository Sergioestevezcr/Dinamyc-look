import os


class Config:
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'A_REALLY_SECRET_KEY_THAT_NO_ONE_KNOWS'

    # MySQL Configuration
    MYSQL_HOST = '13.59.80.138'
    MYSQL_USER = 'admin1'
    MYSQL_PASSWORD = 'Is41l0'
    MYSQL_DB = 'dinamyc_look2'

    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'dinamycloock@gmail.com'
    MAIL_PASSWORD = 'dhuu wofn rsnw hyvl'  # Use an app password for security

    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

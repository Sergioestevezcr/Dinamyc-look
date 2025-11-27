from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy

mysql = MySQL()
db = SQLAlchemy()

def init_app(app):
    mysql.init_app(app)
    db.init_app(app)

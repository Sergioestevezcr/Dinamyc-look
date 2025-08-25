from flask_mysqldb import MySQL

mysql = MySQL()

def configure_db(app):
    """
    Configura la conexión a la base de datos MySQL para la aplicación Flask.

    Args:
        app: Instancia de la aplicación Flask.
    """
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'dinamyc_look'
    mysql.init_app(app)

def get_db():
    """
    Obtiene el objeto de conexión a la base de datos.
    """
    return mysql

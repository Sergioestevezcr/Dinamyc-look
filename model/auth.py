from model.database import get_db

def get_user_by_email_and_password(email, password):
    """
    Busca un usuario en la base de datos por su correo electrónico y clave.

    Args:
        email: El correo electrónico del usuario.
        password: La clave del usuario (sin hashear, según la lógica actual).

    Returns:
        Una tupla con los datos del usuario si las credenciales son correctas,
        o None si no se encuentra el usuario o la clave es incorrecta.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    # ADVERTENCIA: Almacenar contraseñas sin hashear es una vulnerabilidad de seguridad.
    # Deberías hashear las contraseñas al registrarlas y verificar el hash aquí.
    cur.execute('SELECT * FROM usuarios WHERE Correo = %s AND Clave = %s', (email, password))
    user_data = cur.fetchone()
    cur.close()
    return user_data

# Considerar añadir funciones para:
# - Registrar nuevos usuarios (si no se hace a través de add_usuario en el controlador principal)
# - Restablecer contraseña
# - Obtener información de usuario por ID (si no se hace en model/user.py)

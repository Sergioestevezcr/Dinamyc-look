from model.database import get_db

def get_all_users():
    """
    Obtiene todos los usuarios de la base de datos.

    Returns:
        Una lista de tuplas, donde cada tupla representa un usuario.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios ORDER BY ID_usuario DESC')
    data = cur.fetchall()
    cur.close()
    return data

def add_user(nombre, apellido, correo, telefono, direccion, ciudad, clave, rol="Cliente"):
    """
    Agrega un nuevo usuario a la base de datos.

    Args:
        nombre: Nombre del usuario.
        apellido: Apellido del usuario.
        correo: Correo electrónico del usuario.
        telefono: Teléfono del usuario.
        direccion: Dirección del usuario.
        ciudad: Ciudad del usuario.
        clave: Clave del usuario.
        rol: Rol del usuario (por defecto "Cliente").

    Returns:
        None
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO usuarios (Nombre, Apellido, Correo, Telefono, Direccion, Ciudad, Clave, Rol) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (nombre, apellido, correo, telefono, direccion, ciudad, clave, rol))
    mysql.connection.commit()
    cur.close()

def get_user_by_id(user_id):
    """
    Obtiene un usuario de la base de datos por su ID.

    Args:
        user_id: El ID del usuario a buscar.

    Returns:
        Una tupla con los datos del usuario si se encuentra, o None si no.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE id_usuario = %s', (user_id,))
    data = cur.fetchone()
    cur.close()
    return data


def update_user(user_id, nombre, apellido, correo, telefono, direccion, ciudad, clave):
    """
    Actualiza un usuario existente en la base de datos.

    Args:
        user_id: El ID del usuario a actualizar.
        nombre: Nuevo nombre del usuario.
        apellido: Nuevo apellido del usuario.
        correo: Nuevo correo electrónico del usuario.
        telefono: Nuevo teléfono del usuario.
        direccion: Nueva dirección del usuario.
        ciudad: Nueva ciudad del usuario.
        clave: Nueva clave del usuario.

    Returns:
        None
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('''UPDATE usuarios
                    SET Nombre = %s, Apellido = %s, Correo = %s,
                        Telefono = %s, Direccion = %s, Ciudad = %s, Clave = %s
                    WHERE id_usuario = %s''',
                (nombre, apellido, correo, telefono, direccion, ciudad, clave, user_id))
    mysql.connection.commit()
    cur.close()

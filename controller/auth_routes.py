from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import auth  # Importamos el módulo de autenticación
# Podríamos necesitar el modelo de usuario para obtener más datos del usuario autenticado

# Creamos un Blueprint para las rutas de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja las solicitudes de inicio de sesión.
    GET: Muestra el formulario de login.
    POST: Procesa los datos del formulario e intenta autenticar al usuario.
    """
    if request.method == 'POST':
        email = request.form['correo']
        password = request.form['clave']

        # Obtener usuario por email y password
        user_data = auth.get_user_by_email_and_password(email, password)

        if user_data:
            # Autenticación exitosa
            session['loggedin'] = True

            # Mapear columnas de la BD según tu tabla
            session['id'] = user_data[0]        # ID_Usuario
            session['nombre'] = user_data[1]    # Nombre
            session['apellido'] = user_data[2]  # Apellido
            # Normalizamos el rol (siempre en minúsculas, sin espacios extra)
            session['rol'] = user_data[8].strip().lower()

            flash('Inicio de sesión exitoso', 'success')

            # Redirigir según el rol del usuario
            if session['rol'] == 'administrador':
                return redirect(url_for('main.index_admin'))
            else:
                return redirect(url_for('main.index_usuario'))

        else:
            # Autenticación fallida
            flash('Correo o clave incorrectos', 'danger')
            return render_template('auth/login.html')

    # Si es un GET, mostrar formulario de login
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """
    Cierra la sesión del usuario.
    """
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('rol', None)
    session.pop('nombre', None)
    session.pop('apellido', None)
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('auth.login'))  # Redirige a la página de login

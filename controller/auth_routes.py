from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import auth  # Importamos el módulo de autenticación
# Podríamos necesitar el modelo de usuario para obtener más datos del usuario autenticado
from model import user

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
        # ADVERTENCIA: No seguro, ver model/auth.py
        password = request.form['clave']

        user_data = auth.get_user_by_email_and_password(email, password)

        if user_data:
            # Autenticación exitosa
            session['loggedin'] = True
            # Asumiendo que el ID está en la primera columna
            session['id'] = user_data[0]
            # Asumiendo que el Rol está en la novena columna (ajustar según tu tabla)
            session['rol'] = user_data[7]
            # Asumiendo que el Nombre está en la segunda columna
            session['nombre'] = user_data[1]
            # Asumiendo que el Apellido está en la tercera columna
            session['apellido'] = user_data[2]

            flash('Inicio de sesión exitoso', 'success')

            # Redirigir según el rol del usuario
            if session['rol'] == 'administrador':  # Ajusta el nombre del rol si es diferente
                # Redirige al dashboard de admin
                return redirect(url_for('main.index'))
            else:
                # Redirige a una página de usuario normal (Necesitarías crear esta ruta)
                return redirect(url_for('main.index_usuario'))
        else:
            # Autenticación fallida
            flash('Correo o clave incorrectos', 'danger')
            # Vuelve a mostrar el formulario de login
            return render_template('Vista_usuario/login.html')

    # Si es una solicitud GET, simplemente muestra el formulario de login
    return render_template('Vista_usuario/login.html')


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

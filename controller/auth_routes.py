from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from model import auth # Importamos el módulo de autenticación
from model import user # Podríamos necesitar el modelo de usuario para obtener más datos del usuario autenticado

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
        password = request.form['clave'] # ADVERTENCIA: No seguro, ver model/auth.py

        user_data = auth.get_user_by_email_and_password(email, password)

        if user_data:
            # Autenticación exitosa
            session['loggedin'] = True
            session['id'] = user_data[0] # Asumiendo que el ID está en la primera columna
            session['rol'] = user_data[7] # Asumiendo que el Rol está en la novena columna (ajustar según tu tabla)
            session['nombre'] = user_data[1] # Asumiendo que el Nombre está en la segunda columna
            session['apellido'] = user_data[2] # Asumiendo que el Apellido está en la tercera columna

            flash('Inicio de sesión exitoso', 'success')

            # Redirigir según el rol del usuario
            if session['rol'] == 'administrador': # Ajusta el nombre del rol si es diferente
                return redirect(url_for('main.index')) # Redirige al dashboard de admin
            else:
                return redirect(url_for('main.index_usuario')) # Redirige a una página de usuario normal (Necesitarías crear esta ruta)
        else:
            # Autenticación fallida
            flash('Correo o clave incorrectos', 'danger')
            return render_template('Vista_usuario/login.html') # Vuelve a mostrar el formulario de login

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
    return redirect(url_for('auth.login')) # Redirige a la página de login

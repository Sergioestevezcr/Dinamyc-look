import string
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database import mysql

auth_bp = Blueprint('auth_bp', __name__)

# -------------------------------------- DECORADORES -----------------------------------------


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', "info")
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', "info")
            return redirect(url_for('auth_bp.login'))
        elif session.get('user_role') != 'Admin':
            flash('No tienes permisos para acceder a esta página', "warning")
            return redirect(url_for('client_bp.index_cliente'))
        return f(*args, **kwargs)
    return decorated_function


def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página', "info")
            return redirect(url_for('auth_bp.login'))
        elif session.get('user_role') not in ['Cliente', 'Admin']:
            flash('No tienes permisos para acceder a esta página', "warning")
            return redirect(url_for('auth_bp.login'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------- LOGIN -----------------------------------------


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo', '').strip()
        clave = request.form.get('clave', '').strip()

        if not correo or not clave:
            flash('Por favor completa todos los campos', "info")
            return render_template('Vista_usuario/login.html')

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                'SELECT ID_Usuario, Nombre, Apellido, Correo, Clave, Rol FROM usuarios WHERE Correo = %s', (correo,))
            user = cur.fetchone()
            cur.close()

            if user:
                clave_bd = user[4] or ''
                if check_password_hash(clave_bd, clave):
                    session['user_id'] = user[0]
                    session['user_name'] = user[1]
                    session['user_lastname'] = user[2] if user[2] else ''
                    session['user_email'] = user[3]
                    session['user_role'] = user[5]

                    flash(f'¡Bienvenido/a {user[1]}!', 'success')

                    if user[5] == 'Admin':
                        return redirect(url_for('admin_bp.index'))
                    else:
                        return redirect(url_for('client_bp.index_cliente'))
                else:
                    flash('Correo o contraseña incorrectos', "error")
            else:
                flash('Correo o contraseña incorrectos', "error")

        except Exception as e:
            flash(f'Error en el sistema: {str(e)}', "error")

    return render_template('Vista_usuario/login.html')

# -------------------------------------- RECUPERAR CONTRASEÑA -----------------------------------------


def generate_reset_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(5))


@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Por favor ingresa tu correo electrónico', 'error')
            return render_template('Vista_usuario/clave_olvidada.html')

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                'SELECT ID_Usuario, Nombre FROM usuarios WHERE LOWER(Correo) = %s', (email,))
            user = cur.fetchone()

            if user:
                token = generate_reset_token()
                expires_at = datetime.now() + timedelta(hours=1)
                cur.execute('''INSERT INTO tokens (ID_UsuarioFK, Token, Vencimiento, Estado, Creacion) 
                                VALUES (%s, %s, %s, %s, NOW())''',
                            (user[0], token, expires_at, 'activo'))
                mysql.connection.commit()

                msg = MIMEMultipart()
                msg['From'] = formataddr(
                    ("Dinamyc Look", app.config['MAIL_USERNAME']))
                msg['To'] = email
                msg['Subject'] = 'Recuperación de contraseña - Dinamyc Look'
                body = f"""
                    Hola {user[1]},

                    Has solicitado restablecer tu contraseña. 
                    Haz clic en el siguiente enlace para crear una nueva contraseña (válido por 1 hora):

                    http://localhost:5000/reset_password/{token}

                    Si no solicitaste este cambio, puedes ignorar este mensaje.

                    Atentamente,  
                    El equipo de Dinamyc Look.
                    """
                msg.attach(MIMEText(body, 'plain'))

                try:
                    server = smtplib.SMTP(
                        app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
                    server.starttls()
                    server.login(app.config['MAIL_USERNAME'],
                                 app.config['MAIL_PASSWORD'])
                    server.send_message(msg)
                    server.quit()
                    flash(
                        'Hemos enviado un enlace de recuperación a tu correo electrónico', 'success')
                except smtplib.SMTPException:
                    flash('No se pudo enviar el correo. Intenta más tarde.', 'error')
            else:
                flash('Si el correo existe, recibirás un enlace de recuperación', 'info')

            cur.close()
        except Exception:
            flash('Error en el sistema.', 'error')

    return render_template('Vista_usuario/clave_olvidada.html')


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        cur = mysql.connection.cursor()
        cur.execute('''SELECT t.ID_Tokens, u.ID_Usuario, u.Nombre, u.Correo, t.Vencimiento
                        FROM tokens t
                        JOIN usuarios u ON t.ID_UsuarioFK = u.ID_Usuario
                        WHERE t.Token = %s AND t.Estado = %s''', (token, 'activo'))
        data = cur.fetchone()

        if not data:
            flash('El token es inválido o ya fue usado.', 'error')
            return redirect(url_for('auth_bp.login'))

        token_id, user_id, nombre, correo, vencimiento = data

        if datetime.now() > vencimiento:
            flash('El token ha expirado. Solicita uno nuevo.', 'error')
            return redirect(url_for('auth_bp.forgot_password'))

        if request.method == 'POST':
            nueva_clave = request.form['password']
            confirmar_clave = request.form['confirm_password']

            if nueva_clave != confirmar_clave:
                flash('Las contraseñas no coinciden.', 'error')
                return render_template('Vista_usuario/clave_nueva.html', token=token)

            hash_password = generate_password_hash(nueva_clave)
            cur.execute(
                'UPDATE usuarios SET Clave = %s WHERE ID_Usuario = %s', (hash_password, user_id))
            cur.execute(
                'UPDATE tokens SET Estado = %s WHERE ID_Tokens = %s', ('inactivo', token_id))
            mysql.connection.commit()

            flash(
                'Contraseña actualizada con éxito. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth_bp.login'))

        return render_template('Vista_usuario/clave_nueva.html', token=token)

    except Exception as e:
        flash('Ocurrió un error. Intenta nuevamente.', 'error')
        return redirect(url_for('auth_bp.forgot_password'))


@auth_bp.route('/admin/token_status')
@admin_required
def token_status():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT t.ID_Tokens, u.Nombre, u.Correo, t.Token, 
                        t.Vencimiento, t.Estado, t.Creacion
                    FROM tokens t
                    JOIN usuarios u ON t.ID_UsuarioFK = u.ID_Usuario
                    ORDER BY t.Creacion DESC
                    LIMIT 50''')
    tokens = cur.fetchall()
    cur.close()
    return render_template('Vistas_admin/token_status.html', tokens=tokens)

# -------------------------------------- REGISTRO -----------------------------------------


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        correo = request.form['Correo']
        confirmar_correo = request.form['Confirmar_correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave']
        confirmar_clave = request.form['Confirmar_clave']

        if not all([nombre, apellido, correo, confirmar_correo, telefono, direccion, ciudad, clave, confirmar_clave]):
            flash('Completa todos los campos', "info")
            return render_template('Vista_usuario/register.html')

        if correo != confirmar_correo:
            flash('Los correos no coinciden', "error")
            return render_template('Vista_usuario/register.html')

        if clave != confirmar_clave:
            flash('Las contraseñas no coinciden', "error")
            return render_template('Vista_usuario/register.html')

        if len(clave) < 6:
            flash('Contraseña muy corta', "error")
            return render_template('Vista_usuario/register.html')

        if len(telefono) < 10 or len(telefono) >= 11:
            flash('Telefono no valido', "error")
            return render_template('Vista_usuario/register.html')

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                'SELECT ID_Usuario FROM usuarios WHERE Correo = %s', (correo,))
            if cur.fetchone():
                flash('Correo ya registrado', "error")
                cur.close()
                return render_template('Vista_usuario/register.html')

            hashed_password = generate_password_hash(clave)
            cur.execute('''INSERT INTO usuarios (Nombre, Apellido, Correo, Telefono, Direccion, Ciudad, Clave, Rol) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                        (nombre, apellido, correo, telefono, direccion, ciudad, hashed_password, 'Cliente'))
            mysql.connection.commit()
            cur.close()

            flash('¡Registro exitoso!', "success")
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            flash(f'Error: {str(e)}', "error")

    return render_template('Vista_usuario/register.html')

# -------------------------------------- LOGOUT -----------------------------------------


@auth_bp.route('/logout')
@login_required
def logout():
    user_name = session.get('user_name', 'Usuario')
    session.clear()
    flash(f'¡Hasta pronto {user_name}!', "info")
    return redirect(url_for('auth_bp.login'))

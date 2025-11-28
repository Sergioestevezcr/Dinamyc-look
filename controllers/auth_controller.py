import string
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from werkzeug.security import generate_password_hash, check_password_hash
from database import mysql # Importar decoradores y clase PDF
from decorators import login_required, admin_required
from flask import Blueprint, request, render_template, flash, redirect, url_for, session, current_app as app
from services.email_service import EmailService
from forms.auth_forms import LoginForm, RegisterForm, ForgotPasswordForm

auth_bp = Blueprint('auth_bp', __name__)

# -------------------------------------- LOGIN -----------------------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        correo = form.correo.data
        clave = form.clave.data

        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT ID_Usuario, Nombre, Apellido, N_Documento, Correo, Clave, Rol FROM usuarios WHERE Correo = %s",
                (correo,),
            )
            user = cur.fetchone()
            cur.close()

            if user:
                clave_bd = user[5] or ""
                
                if check_password_hash(clave_bd, clave):
                    session["user_id"] = user[0]
                    session["user_name"] = user[1]
                    session["user_lastname"] = user[2]
                    session["user_email"] = user[4]
                    
                    rol = user[6].strip().lower()
                    session["user_role"] = rol

                    flash(f"¡Bienvenido/a {user[1]}!", "success")

                    if rol == "admin":
                        return redirect(url_for("admin_bp.index"))
                    else:
                        return redirect(url_for("client_bp.index_cliente"))
                else:
                    flash("Correo o contraseña incorrectos", "error")
            else:
                flash("Correo o contraseña incorrectos", "error")
        except Exception as e:
            flash(f"Error en el sistema: {e}", "error")

    return render_template("Vista_usuario/login.html", form=form)
# -------------------------------------- RECUPERAR CONTRASEÑA -----------------------------------------

# Generador de token aleatorio
def generate_reset_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(5))


# -------------------------------------- RUTA: Olvidé mi contraseña -----------------------------------

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

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

                reset_url = f"http://127.0.0.1:5000/auth/reset_password/{token}"

                if EmailService.send_password_reset_email(email, user[1], reset_url):
                    flash('Hemos enviado un enlace de recuperación a tu correo electrónico', 'success')
                else:
                    flash('No se pudo enviar el correo. Intenta más tarde.', 'error')
            else:
                flash('Si el correo existe, recibirás un enlace de recuperación', 'info')

            cur.close()
        except Exception as e:
            print(f"Error: {e}")
            flash('Error en el sistema.', 'error')

    return render_template('Vista_usuario/clave_olvidada.html', form=form)

# -------------------------------------- RUTA: Reset Password ----------------------------------------

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
            cur.execute('UPDATE usuarios SET Clave = %s WHERE ID_Usuario = %s', (hash_password, user_id))
            cur.execute('UPDATE tokens SET Estado = %s WHERE ID_Tokens = %s', ('inactivo', token_id))
            mysql.connection.commit()

            flash('Contraseña actualizada con éxito. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth_bp.login'))

        return render_template('Vista_usuario/clave_nueva.html', token=token)

    except Exception as e:
        flash('Ocurrió un error. Intenta nuevamente.', 'error')
        return redirect(url_for('auth_bp.forgot_password'))

# -------------------------------------- REGISTRO -----------------------------------------

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Toda la validación ya la hizo el form (passwords coinciden, email único, etc.)
        try:
            cur = mysql.connection.cursor()
            
            hashed_password = generate_password_hash(form.clave.data)
            cur.execute('''INSERT INTO usuarios (Nombre, Apellido, N_Documento, Correo, Telefono, Direccion, Ciudad, Clave, Rol, Estado) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                        (form.nombre.data, form.apellido.data, form.documento.data, 
                         form.correo.data, form.telefono.data, form.direccion.data, 
                         form.ciudad.data, hashed_password, 'Cliente', 'Activo'))
            mysql.connection.commit()
            cur.close()

            flash('¡Registro exitoso!', "success")
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            flash(f'Error: {str(e)}', "error")

    return render_template('Vista_usuario/register.html', form=form)

# -------------------------------------- LOGOUT -----------------------------------------


@auth_bp.route('/logout')
@login_required
def logout():
    user_name = session.get('user_name', 'Usuario')
    session.clear()
    flash(f'¡Hasta pronto {user_name}!', "info")
    return redirect(url_for('auth_bp.login'))

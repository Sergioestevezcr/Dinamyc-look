from database import mysql
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr


class UserModel:

    @staticmethod
    def login_user(email, password):
        cur = mysql.connection.cursor()
        cur.execute(
            'SELECT ID_Usuario, Nombre, Apellido, Correo, Clave, Rol FROM usuarios WHERE Correo = %s', (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[4], password):
            return user
        return None

    @staticmethod
    def register_user(nombre, apellido, correo, telefono, direccion, ciudad, clave):
        cur = mysql.connection.cursor()
        cur.execute(
            'SELECT ID_Usuario FROM usuarios WHERE Correo = %s', (correo,))
        if cur.fetchone():
            cur.close()
            return False

        hashed_password = generate_password_hash(clave)
        cur.execute('''INSERT INTO usuarios (Nombre, Apellido, Correo, Telefono, Direccion, Ciudad, Clave, Rol) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                    (nombre, apellido, correo, telefono, direccion, ciudad, hashed_password, 'Cliente'))
        mysql.connection.commit()
        cur.close()
        return True

    @staticmethod
    def get_user_name(user_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT Nombre FROM Usuarios WHERE ID_Usuario = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        return row[0] if row else None

    @staticmethod
    def toggle_favorite(user_id, product_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM favoritos WHERE ID_UsuarioFK = %s AND ID_ProductoFK = %s", (user_id, product_id))
        favorito = cur.fetchone()
        if favorito:
            cur.execute(
                "DELETE FROM favoritos WHERE ID_UsuarioFK = %s AND ID_ProductoFK = %s", (user_id, product_id))
            is_favorite = False
        else:
            cur.execute(
                "INSERT INTO favoritos (ID_UsuarioFK, ID_ProductoFK) VALUES (%s, %s)", (user_id, product_id))
            is_favorite = True
        mysql.connection.commit()
        cur.close()
        return is_favorite

    @staticmethod
    def get_favorite_products(user_id):
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT p.ID_Producto, p.Nombre, p.Precio, p.Imagen, p.Marca 
            FROM Productos p
            INNER JOIN favoritos f ON p.ID_Producto = f.ID_ProductoFK AND f.ID_UsuarioFK = %s
            ORDER BY p.Marca ASC
        ''', (user_id,))
        data = cur.fetchall()
        cur.close()
        return data

    @staticmethod
    def get_favorite_product_ids(user_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT ID_ProductoFK FROM favoritos WHERE ID_UsuarioFK = %s", (user_id,))
        ids = [row[0] for row in cur.fetchall()]
        cur.close()
        return ids

from services.email_service import EmailService

    @staticmethod
    def send_password_reset_email(email):
        cur = mysql.connection.cursor()
        cur.execute(
            'SELECT ID_Usuario, Nombre FROM usuarios WHERE LOWER(Correo) = %s', (email,))
        user = cur.fetchone()
        if not user:
            cur.close()
            return False

        token = UserModel.generate_reset_token()
        expires_at = datetime.now() + timedelta(hours=1)
        cur.execute('''INSERT INTO tokens (ID_UsuarioFK, Token, Vencimiento, Estado, Creacion) VALUES (%s, %s, %s, %s, NOW())''',
                    (user[0], token, expires_at, 'activo'))
        mysql.connection.commit()
        cur.close()

        reset_url = f"http://localhost:5000/auth/reset_password/{token}"
        return EmailService.send_password_reset_email(email, user[1], reset_url)

    @staticmethod
    def verify_reset_token(token):
        cur = mysql.connection.cursor()
        cur.execute('''SELECT t.ID_Tokens, u.ID_Usuario, u.Nombre, u.Correo, t.Vencimiento FROM tokens t JOIN usuarios u ON t.ID_UsuarioFK = u.ID_Usuario WHERE t.Token = %s AND t.Estado = %s''', (token, 'activo'))
        data = cur.fetchone()
        cur.close()

        if not data or datetime.now() > data[4]:
            return None
        return data

    @staticmethod
    def reset_password(token, new_password):
        cur = mysql.connection.cursor()
        cur.execute('''SELECT t.ID_Tokens, u.ID_Usuario FROM tokens t JOIN usuarios u ON t.ID_UsuarioFK = u.ID_Usuario WHERE t.Token = %s AND t.Estado = %s''', (token, 'activo'))
        token_id, user_id = cur.fetchone()

        hash_password = generate_password_hash(new_password)
        cur.execute(
            'UPDATE usuarios SET Clave = %s WHERE ID_Usuario = %s', (hash_password, user_id))
        cur.execute(
            'UPDATE tokens SET Estado = %s WHERE ID_Tokens = %s', ('inactivo', token_id))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def generate_reset_token():
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(5))

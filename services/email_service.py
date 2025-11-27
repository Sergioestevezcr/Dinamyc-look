import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from flask import current_app

class EmailService:
    @staticmethod
    def send_email(to_email, subject, body, is_html=False):
        """
        Send an email using the configured SMTP server.
        """
        msg = MIMEMultipart()
        msg['From'] = formataddr(("Dinamyc Look", current_app.config['MAIL_USERNAME']))
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

        try:
            server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
            server.starttls()
            server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    @staticmethod
    def send_password_reset_email(to_email, user_name, reset_link):
        """
        Send a password reset email.
        """
        subject = 'Recuperación de contraseña - Dinamyc Look'
        body = f"""
        Hola {user_name},

        Has solicitado restablecer tu contraseña.
        Haz clic en el siguiente enlace para crear una nueva contraseña (válido por 1 hora):

        {reset_link}

        Si no solicitaste este cambio, puedes ignorar este mensaje.

        Atentamente,
        El equipo de Dinamyc Look.
        """
        return EmailService.send_email(to_email, subject, body)

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from database import mysql


class LoginForm(FlaskForm):
    """Form for user login"""
    correo = StringField('Correo Electrónico', 
                        validators=[DataRequired(message='El correo es obligatorio'),
                                  Email(message='Ingresa un correo válido')])
    clave = PasswordField('Contraseña', 
                         validators=[DataRequired(message='La contraseña es obligatoria')])
    submit = SubmitField('Iniciar Sesión')


class RegisterForm(FlaskForm):
    """Form for user registration"""
    nombre = StringField('Nombre', 
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres')])
    apellido = StringField('Apellido',
                          validators=[DataRequired(message='El apellido es obligatorio'),
                                    Length(min=2, max=100, message='El apellido debe tener entre 2 y 100 caracteres')])
    documento = StringField('Documento',
                           validators=[DataRequired(message='El documento es obligatorio'),
                                     Length(min=5, max=20, message='El documento debe tener entre 5 y 20 caracteres')])
    correo = StringField('Correo Electrónico',
                        validators=[DataRequired(message='El correo es obligatorio'),
                                  Email(message='Ingresa un correo válido')])
    telefono = StringField('Teléfono',
                          validators=[DataRequired(message='El teléfono es obligatorio'),
                                    Length(min=7, max=20, message='El teléfono debe tener entre 7 y 20 caracteres')])
    direccion = StringField('Dirección',
                           validators=[DataRequired(message='La dirección es obligatoria'),
                                     Length(max=200)])
    ciudad = StringField('Ciudad',
                        validators=[DataRequired(message='La ciudad es obligatoria'),
                                  Length(max=100)])
    clave = PasswordField('Contraseña',
                         validators=[DataRequired(message='La contraseña es obligatoria'),
                                   Length(min=6, message='La contraseña debe tener al menos 6 caracteres')])
    confirmar_clave = PasswordField('Confirmar Contraseña',
                                   validators=[DataRequired(message='Confirma tu contraseña'),
                                             EqualTo('clave', message='Las contraseñas no coinciden')])
    submit = SubmitField('Registrarse')
    
    def validate_correo(self, correo):
        """Check if email already exists"""
        cur = mysql.connection.cursor()
        cur.execute('SELECT ID_Usuario FROM usuarios WHERE LOWER(Correo) = %s', (correo.data.lower(),))
        user = cur.fetchone()
        cur.close()
        if user:
            raise ValidationError('Este correo ya está registrado. Por favor usa otro.')
    
    def validate_documento(self, documento):
        """Check if document already exists"""
        cur = mysql.connection.cursor()
        cur.execute('SELECT ID_Usuario FROM usuarios WHERE Documento = %s', (documento.data,))
        user = cur.fetchone()
        cur.close()
        if user:
            raise ValidationError('Este documento ya está registrado.')


class ForgotPasswordForm(FlaskForm):
    """Form for forgot password"""
    email = StringField('Correo Electrónico',
                       validators=[DataRequired(message='El correo es obligatorio'),
                                 Email(message='Ingresa un correo válido')])
    submit = SubmitField('Enviar enlace de recuperación')

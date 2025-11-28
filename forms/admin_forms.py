from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, IntegerField, SelectField, DateField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email, EqualTo


class ProductForm(FlaskForm):
    """Form for adding/editing products"""
    nombre = StringField('Nombre del Producto',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(max=100)])
    descripcion = TextAreaField('Descripción',
                               validators=[DataRequired(message='La descripción es obligatoria')])
    categoria = StringField('Categoría',
                           validators=[DataRequired(message='La categoría es obligatoria'),
                                     Length(max=50)])
    precio = DecimalField('Precio',
                         validators=[DataRequired(message='El precio es obligatorio'),
                                   NumberRange(min=0, message='El precio debe ser mayor a 0')],
                         places=2)
    stock = IntegerField('Stock',
                        validators=[DataRequired(message='El stock es obligatorio'),
                                  NumberRange(min=0, message='El stock debe ser mayor o igual a 0')])
    marca = SelectField('Marca/Proveedor',
                       validators=[DataRequired(message='La marca es obligatoria')],
                       coerce=int)
    promocion = SelectField('Promoción',
                           validators=[Optional()],
                           coerce=int)
    imagen = FileField('Imagen del Producto',
                      validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                                             'Solo se permiten imágenes')])
    submit = SubmitField('Guardar Producto')


class PromotionForm(FlaskForm):
    """Form for adding/editing promotions"""
    descuento = DecimalField('Descuento (%)',
                            validators=[DataRequired(message='El descuento es obligatorio'),
                                      NumberRange(min=0, max=100, message='El descuento debe estar entre 0 y 100')],
                            places=2)
    fecha_inicial = DateField('Fecha Inicial',
                             validators=[DataRequired(message='La fecha inicial es obligatoria')],
                             format='%Y-%m-%d')
    fecha_final = DateField('Fecha Final',
                           validators=[DataRequired(message='La fecha final es obligatoria')],
                           format='%Y-%m-%d')
    submit = SubmitField('Guardar Promoción')


class UserForm(FlaskForm):
    """Form for adding/editing users"""
    nombre = StringField('Nombre',
                        validators=[DataRequired(message='El nombre es obligatorio'),
                                  Length(min=2, max=100)])
    apellido = StringField('Apellido',
                          validators=[DataRequired(message='El apellido es obligatorio'),
                                    Length(min=2, max=100)])
    documento = StringField('Documento',
                           validators=[DataRequired(message='El documento es obligatorio'),
                                     Length(min=5, max=20)])
    correo = StringField('Correo Electrónico',
                        validators=[DataRequired(message='El correo es obligatorio'),
                                  Email(message='Ingresa un correo válido')])
    telefono = StringField('Teléfono',
                          validators=[DataRequired(message='El teléfono es obligatorio'),
                                    Length(min=7, max=20)])
    direccion = StringField('Dirección',
                           validators=[DataRequired(message='La dirección es obligatoria'),
                                     Length(max=200)])
    ciudad = StringField('Ciudad',
                        validators=[DataRequired(message='La ciudad es obligatoria'),
                                  Length(max=100)])
    clave = PasswordField('Contraseña',
                         validators=[DataRequired(message='La contraseña es obligatoria'),
                                   Length(min=6, message='La contraseña debe tener al menos 6 caracteres')])
    submit = SubmitField('Guardar Usuario')

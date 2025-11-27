from database import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column('ID_Usuario', db.Integer, primary_key=True)
    nombre = db.Column('Nombre', db.String(100))
    apellido = db.Column('Apellido', db.String(100))
    documento = db.Column('Documento', db.String(20))
    correo = db.Column('Correo', db.String(100), unique=True)
    telefono = db.Column('Telefono', db.String(20))
    direccion = db.Column('Direccion', db.String(200))
    ciudad = db.Column('Ciudad', db.String(100))
    clave = db.Column('Clave', db.String(255))
    rol = db.Column('Rol', db.String(20))
    estado = db.Column('Estado', db.String(20))
    fecha_registro = db.Column('Fecha_registro', db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.nombre} {self.apellido}>'

class Product(db.Model):
    __tablename__ = 'productos'

    id = db.Column('ID_Producto', db.Integer, primary_key=True)
    nombre = db.Column('Nombre', db.String(100))
    descripcion = db.Column('Descripcion', db.Text)
    categoria = db.Column('Categoria', db.String(50))
    precio = db.Column('Precio', db.Numeric(10, 2))
    stock = db.Column('Stock', db.Integer)
    imagen = db.Column('Imagen', db.String(255))
    id_proveedor = db.Column('ID_ProveedorFK', db.Integer, db.ForeignKey('proveedores.ID_Proveedor'))
    id_promocion = db.Column('ID_PromocionFK', db.Integer, db.ForeignKey('promociones.ID_Promocion'), nullable=True)

    def __repr__(self):
        return f'<Product {self.nombre}>'

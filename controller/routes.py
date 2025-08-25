from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from model import product, user, sale
from model.database import get_db
import sys
from functools import wraps # Importamos wraps para crear decoradores

# Creamos un Blueprint para las rutas principales
main_bp = Blueprint('main', __name__)

# Decorador para requerir inicio de sesión
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session:
            flash('Por favor, inicia sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login')) # Redirige a la página de login
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir rol de administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'loggedin' not in session or session.get('rol') != 'Admin': # Ajusta el nombre del rol si es diferente
            flash('No tienes permisos para acceder a esta página.', 'danger')
            # Podrías redirigir a una página de error o a la página principal del usuario
            return redirect(url_for('main.index_usuario')) # Redirige a la página principal de usuario
        return f(*args, **kwargs)
    return decorated_function

# -------------------------------------- RUTAS PÚBLICAS -----------------------------------------\

@main_bp.route('/')
def index_usuario():
    """
    Página principal para usuarios no autenticados.
    """
    # Aquí podrías cargar datos para la página principal si es necesario
    return render_template('Vista_usuario/index.html')


# -------------------------------------- RUTAS DE ADMINISTRACIÓN (PROTEGIDAS) -----------------------------------------\

@main_bp.route('/admin') # Cambiamos la ruta del dashboard de admin
@admin_required # Requiere rol de administrador
def index():
    """
    Dashboard de administración (protegido).
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(ID_Venta) + 1 AS Ventas_Totales, Sum(Total) AS Ingresos_Totales FROM ventas')
    data_ventas = cur.fetchall()

    if data_ventas:
        ventas = data_ventas[0][0]
        ingresos = data_ventas[0][1]
    else:
        ventas = 0
        ingresos = 0

    cur.execute('SELECT SUM(Cantidad_p) FROM Detalles_venta')
    productosT = cur.fetchone()[0]
    cur.close()

    return render_template('Vistas_admin/index-admin.html',
                           ventas=ventas,
                           ingresos=ingresos,
                           productosT=productosT)

# -------------------------------------- PRODUCTOS (PROTEGIDAS PARA ADMIN) -----------------------------------------\

@main_bp.route('/productos')
@admin_required # Requiere rol de administrador
def productos():
    data = product.get_all_products()
    return render_template('Vistas_admin/productos.html', productos=data)

@main_bp.route('/add_producto', methods=['POST'])
@admin_required # Requiere rol de administrador
def add_producto():
    if request.method == 'POST':
        nombre = request.form['Nombre']
        descripcion = request.form['Descripcion']
        precio = request.form['Precio']
        Marca = request.form['Marca']
        stock = request.form['Stock']

        product.add_product(nombre, descripcion, precio, Marca, stock)
        flash('Producto agregado correctamente')
        return redirect(url_for('main.productos'))

@main_bp.route('/edit_producto/<id>')
@admin_required # Requiere rol de administrador
def edit_producto(id):
    data = product.get_product_by_id(id)
    if data:
        product_data = {
            'id': data[0],
            'nombre': data[1],
            'descripcion': data[2],
            'precio': data[4],
            'marca': data[6],
            'stock': data[5]
        }
        return jsonify(product_data)
    return jsonify({'error': 'Producto no encontrado'}), 404

@main_bp.route('/update_producto/<id>', methods=['POST'])
@admin_required # Requiere rol de administrador
def update_producto(id):
    if request.method == 'POST':
        nombre = request.form['Nombre']
        descripcion = request.form['Descripcion']
        precio = request.form['Precio']
        marca = request.form['Marca']
        stock = request.form['Stock']

        product.update_product(id, nombre, descripcion, precio, marca, stock)
        flash('Producto actualizado correctamente')
        return redirect(url_for('main.productos'))

# -------------------------------------- USUARIOS (PROTEGIDAS PARA ADMIN) -----------------------------------------\

@main_bp.route('/usuarios')
@admin_required # Requiere rol de administrador
def usuarios():
    data = user.get_all_users()
    usuarios_data = []
    for row in data:
        correo = row[3]
        correo_mod = correo.replace("@", "<wbr>@<wbr>").replace(".", ".<wbr>")
        row = list(row)
        row[3] = correo_mod
        usuarios_data.append(row)

    return render_template('Vistas_admin/usuarios.html', usuarios=usuarios_data)

@main_bp.route('/add_usuario', methods=['POST'])
@admin_required # Requiere rol de administrador
def add_usuario():
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave'] # Considerar hashear la clave

        user.add_user(nombre, apellido, correo, telefono, direccion, ciudad, clave)
        flash('Usuario agregado correctamente')
        return redirect(url_for('main.usuarios'))

@main_bp.route('/edit_usuario/<id>')
@admin_required # Requiere rol de administrador
def edit_usuario(id):
    data = user.get_user_by_id(id)
    if data:
        user_data = {
            'id': data[0],
            'nombre': data[1],
            'apellido': data[2],
            'correo': data[3],
            'telefono': data[4],
            'direccion': data[5],
            'ciudad': data[6],
            'clave': data[7]
        }
        return jsonify(user_data)
    return jsonify({'error': 'Usuario no encontrado'}), 404

@main_bp.route('/update_usuario/<id>', methods=['POST'])
@admin_required # Requiere rol de administrador
def update_usuario(id):
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave'] # Considerar hashear la clave

        user.update_user(id, nombre, apellido, correo, telefono, direccion, ciudad, clave)
        flash('Usuario actualizado correctamente')
        return redirect(url_for('main.usuarios'))

# -------------------------------------- VENTAS (PROTEGIDAS PARA ADMIN Y COMPRA PARA LOGGEDIN) -----------------------------------------\

@main_bp.route('/ventas')
@admin_required # La vista de reporte de ventas es solo para admin
def ventas():
    reportes_data = sale.get_sales_report()
    usuarios = user.get_all_users()
    productos = product.get_all_products()

    return render_template('Vistas_admin/ventas.html',
                            reportes=reportes_data,
                            usuarios=usuarios,
                            productos=productos)

@main_bp.route('/add_venta', methods=['POST'])
@login_required # Solo requiere que el usuario esté logueado para comprar
def add_venta():
    if request.method == 'POST':
        # Obtenemos el ID del usuario logueado de la sesión
        id_usuario = session.get('id')
        if not id_usuario:
             flash('Debes iniciar sesión para realizar una compra.', 'warning')
             return redirect(url_for('auth.login'))


        productos_data = request.form.getlist('productos[]')
        cantidades = request.form.getlist('cantidades[]')

        if not productos_data or not cantidades:
            flash('Debe seleccionar al menos un producto', 'warning')
            return redirect(url_for('main.ventas')) # Podrías redirigir a otra página de usuario si la venta no es en la vista admin

        productos_venta = []
        for i, producto_id in enumerate(productos_data):
            if producto_id and int(cantidades[i]) > 0:
                producto_info = product.get_product_price_and_stock(producto_id)
                if producto_info:
                    precio = int(producto_info[0])
                    stock_disponible = int(producto_info[1])
                    cantidad_solicitada = int(cantidades[i])

                    # Obtener el nombre del producto para el mensaje de stock insuficiente
                    producto_completo = product.get_product_by_id(producto_id)
                    nombre_producto = producto_completo[1] if producto_completo else f"Producto ID {producto_id}"


                    if cantidad_solicitada > stock_disponible:
                        flash(f'Stock insuficiente para {nombre_producto}. Disponible: {stock_disponible}', 'warning')
                        return redirect(url_for('main.ventas')) # Podrías redirigir a una página de usuario

                    subtotal = precio * cantidad_solicitada
                    productos_venta.append({
                        'id': int(producto_id),
                        'cantidad': cantidad_solicitada,
                        'precio': precio,
                        'subtotal': subtotal
                    })

        if not productos_venta:
            flash('No hay productos válidos en la venta', 'warning')
            return redirect(url_for('main.ventas')) # Podrías redirigir a una página de usuario

        venta_id = sale.add_new_sale(id_usuario, productos_venta)

        if venta_id:
            flash('Venta registrada correctamente', 'success')
            # Redirigir a una página de confirmación o al historial de compras del usuario
            # return redirect(url_for('main.factura', id_venta=venta_id)) # Ejemplo: redirigir a la factura
            return redirect(url_for('main.index_usuario')) # Redirigir a la página principal de usuario
        else:
            flash('Error al registrar la venta', 'danger')
            return redirect(url_for('main.ventas')) # Podrías redirigir a una página de usuario

@main_bp.route('/get_producto_precio/<id>')
@login_required # Aunque sea AJAX, la información de precio y stock podría ser sensible, o solo necesaria para usuarios logueados
def get_producto_precio(id):
    """Endpoint para obtener precio y stock de un producto específico vía AJAX"""
    data = product.get_product_price_and_stock(id)

    if data:
        return jsonify({
            'precio': int(data[0]),
            'stock': int(data[1])
        })
    return jsonify({'error': 'Producto no encontrado'}), 404

# -------------------------------------- FACTURA (PROTEGIDA) -----------------------------------------\

@main_bp.route('/factura/<id_venta>')
@login_required # La factura debe ser accesible por el usuario que realizó la compra o un admin
def factura(id_venta):
    factura_data = sale.get_invoice_data(id_venta)

    # Opcional: Verificar si el usuario logueado es el dueño de la factura o un admin
    # if factura_data and session.get('rol') != 'Admin' and factura_data[0][???] != session.get('id'): # Necesitas saber qué columna de 'reporte' tiene el ID del usuario
    #     flash('No tienes permisos para ver esta factura.', 'danger')
    #     return redirect(url_for('main.index_usuario'))

    if factura_data:
        nombre_cliente = factura_data[0][2]
        apellido_cliente = factura_data[0][3]
        fecha = factura_data[0][1]
        total = factura_data[0][10]
    else:
        nombre_cliente = ''
        apellido_cliente = ''
        fecha = ''
        total = 0

    return render_template('Vistas_admin/factura.html', # Considera tener una plantilla de factura separada para usuarios si la vista de admin es muy diferente
                            factura=factura_data,
                            nombre=nombre_cliente,
                            apellido=apellido_cliente,
                            fecha=fecha,
                            id_venta=id_venta,
                            total=total)

# Mantener las rutas de diagnóstico por ahora si son necesarias para depuración
# ... (Las rutas de diagnóstico y verificar_static se agregarán aquí si las quieres mantener en el controlador principal)

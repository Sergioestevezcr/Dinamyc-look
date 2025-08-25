from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from model import product, user, sale # Importamos los módulos del modelo
from model.database import get_db # Todavía necesitamos get_db para lógica que no se ha movido al modelo
import sys

# Creamos un Blueprint para las rutas principales
main_bp = Blueprint('main', __name__)

# -------------------------------------- RUTA PRINCIPAL -----------------------------------------\

@main_bp.route('/')
def index():
    # Obtener datos para el dashboard del modelo (podría ir a un módulo específico del modelo)
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

# -------------------------------------- PRODUCTOS -----------------------------------------\

@main_bp.route('/productos')
def productos():
    data = product.get_all_products()
    return render_template('Vistas_admin/productos.html', productos=data)

@main_bp.route('/add_producto', methods=['POST'])
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

# -------------------------------------- USUARIOS -----------------------------------------\

@main_bp.route('/usuarios')
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

# -------------------------------------- VENTAS -----------------------------------------\

@main_bp.route('/ventas')
def ventas():
    # Obtener datos de ventas del modelo
    reportes_data = sale.get_sales_report()

    # Obtener listas de usuarios y productos del modelo
    usuarios = user.get_all_users()
    productos = product.get_all_products()

    return render_template('Vistas_admin/ventas.html',
                            reportes=reportes_data,
                            usuarios=usuarios,
                            productos=productos)

@main_bp.route('/add_venta', methods=['POST'])
def add_venta():
    if request.method == 'POST':
        id_usuario = request.form['ID_Usuario']
        productos_data = request.form.getlist('productos[]')
        cantidades = request.form.getlist('cantidades[]')

        if not productos_data or not cantidades:
            flash('Debe seleccionar al menos un producto')
            return redirect(url_for('main.ventas'))

        productos_venta = []
        for i, producto_id in enumerate(productos_data):
            if producto_id and int(cantidades[i]) > 0:
                producto_info = product.get_product_price_and_stock(producto_id)
                if producto_info:
                    precio = int(producto_info[0])
                    stock_disponible = int(producto_info[1])
                    cantidad_solicitada = int(cantidades[i])

                    if cantidad_solicitada > stock_disponible:
                        flash(f'Stock insuficiente para {producto_info[2]}. Disponible: {stock_disponible}') # Nota: producto_info[2] no está disponible aquí, debería ser el nombre del producto
                        return redirect(url_for('main.ventas'))

                    subtotal = precio * cantidad_solicitada
                    productos_venta.append({
                        'id': int(producto_id),
                        'cantidad': cantidad_solicitada,
                        'precio': precio,
                        'subtotal': subtotal
                    })

        if not productos_venta:
            flash('No hay productos válidos en la venta')
            return redirect(url_for('main.ventas'))

        # Llamar a la función del modelo para agregar la venta
        venta_id = sale.add_new_sale(id_usuario, productos_venta)

        if venta_id:
            flash('Venta registrada correctamente')
        else:
            flash('Error al registrar la venta') # El error detallado se imprime en la consola desde el modelo

        return redirect(url_for('main.ventas'))

@main_bp.route('/get_producto_precio/<id>')
def get_producto_precio(id):
    """Endpoint para obtener precio y stock de un producto específico vía AJAX"""
    data = product.get_product_price_and_stock(id)

    if data:
        return jsonify({
            'precio': int(data[0]),
            'stock': int(data[1])
        })
    return jsonify({'error': 'Producto no encontrado'}), 404

# -------------------------------------- FACTURA -----------------------------------------\

@main_bp.route('/factura/<id_venta>')
def factura(id_venta):
    # Obtener datos de la factura del modelo
    factura_data = sale.get_invoice_data(id_venta)

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

    return render_template('Vistas_admin/factura.html',
                            factura=factura_data,
                            nombre=nombre_cliente,
                            apellido=apellido_cliente,
                            fecha=fecha,
                            id_venta=id_venta,
                            total=total)

# Mantener las rutas de diagnóstico por ahora si son necesarias para depuración
# ... (Las rutas de diagnóstico y verificar_static se agregarán aquí si las quieres mantener en el controlador principal)

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mysqldb import MySQL
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'))

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'dinamyc_look'
mysql = MySQL(app)

app.secret_key = 'mysecret_key'

# -------------------------------------- RUTA PRINCIPAL -----------------------------------------

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT COUNT(ID_Venta) + 1 AS Ventas_Totales, Sum(Total) AS Ingresos_Totales FROM ventas')
    data_ventas = cur.fetchall()
    
    if data_ventas:
        ventas= data_ventas[0][0]
        ingresos = data_ventas[0][1]
    else:
        ventas = 0
        ingresos = 0

    cur.execute('SELECT SUM(Cantidad_p) FROM Detalles_venta')
    productosT = cur.fetchone()[0]

    return render_template('Vistas_admin/index-admin.html', 
                            ventas = ventas,
                            ingresos = ingresos,
                            productosT = productosT)

# -------------------------------------- PRODUCTOS -----------------------------------------

@app.route('/productos')
def productos():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos')
    data = cur.fetchall()
    return render_template('Vistas_admin/productos.html', productos=data)

@app.route('/add_producto', methods=['POST'])
def add_producto():  # Nombre corregido
    if request.method == 'POST':  
        # Asumiendo que los productos tienen estos campos
        nombre = request.form['Nombre']
        descripcion = request.form['Descripcion']
        precio = request.form['Precio']
        Marca = request.form['Marca']
        stock = request.form['Stock']
        
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO productos (Nombre, Descripcion, Precio, Marca, Stock) VALUES (%s, %s, %s, %s, %s)',
                    (nombre, descripcion, precio, Marca, stock))
        mysql.connection.commit()
        flash('Producto agregado correctamente')
        return redirect(url_for('productos'))

@app.route('/edit_producto/<id>')
def edit_producto(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
    data = cur.fetchone()
    if data:
        # Ajustar según la estructura real de tu tabla productos
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

@app.route('/update_producto/<id>', methods=['POST'])
def update_producto(id):
    if request.method == 'POST':
        nombre = request.form['Nombre']
        descripcion = request.form['Descripcion']
        precio = request.form['Precio']
        marca = request.form['Marca']
        stock = request.form['Stock']
        
        cur = mysql.connection.cursor()
        cur.execute('''UPDATE productos 
                        SET Nombre = %s, Descripcion = %s, Precio = %s, 
                            Marca = %s, Stock = %s 
                        WHERE id_producto = %s''',
                    (nombre, descripcion, precio, marca, stock, id))
        mysql.connection.commit()
        flash('Producto actualizado correctamente')
        return redirect(url_for('productos'))

# -------------------------------------- USUARIOS -----------------------------------------

@app.route('/usuarios')
def usuarios():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios ORDER BY ID_usuario DESC')
    data = cur.fetchall()

    usuarios_data = []
    for row in data:
        # Suponiendo que la columna Correo está en la posición 3
        correo = row[3]
        # Insertar puntos de quiebre después de @ y .
        correo_mod = correo.replace("@", "<wbr>@<wbr>").replace(".", ".<wbr>")

        # Convertir la tupla a lista para poder reemplazar el valor
        row = list(row)
        row[3] = correo_mod
        usuarios_data.append(row)

    # Pasar datos ya modificados a la plantilla
    return render_template('Vistas_admin/usuarios.html', usuarios=usuarios_data)


@app.route('/add_usuario', methods=['POST'])
def add_usuario():
    if request.method == 'POST':  
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave']
        rol = "Cliente"
        
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO usuarios (Nombre, Apellido, Correo, Telefono, Direccion, Ciudad, Clave, Rol) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (nombre, apellido, correo, telefono, direccion, ciudad, clave, rol))
        mysql.connection.commit()
        flash('Usuario agregado correctamente')
        return redirect(url_for('usuarios'))

@app.route('/edit_usuario/<id>')
def edit_usuario(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE id_usuario = %s', (id,)) 
    data = cur.fetchone()
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

@app.route('/update_usuario/<id>', methods=['POST'])
def update_usuario(id):
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave']
        
        cur = mysql.connection.cursor()
        cur.execute('''UPDATE usuarios 
                        SET Nombre = %s, Apellido = %s, Correo = %s, 
                            Telefono = %s, Direccion = %s, Ciudad = %s, Clave = %s 
                        WHERE id_usuario = %s''',
                    (nombre, apellido, correo, telefono, direccion, ciudad, clave, id))
        mysql.connection.commit()
        flash('Usuario actualizado correctamente')
        return redirect(url_for('usuarios'))

# -------------------------------------- VENTAS -----------------------------------------

@app.route('/ventas')
def ventas():
    # Crear un cursor para ejecutar consultas SQL
    cur = mysql.connection.cursor()
    
    # Usar la vista "reporte" para obtener los datos de ventas ya procesados
    cur.execute('''SELECT
                    Num_venta,
                    Fecha,
                    Nombre_Cliente,
                    Apellido_Cliente,
                    SUM(SubTotal_Final) AS Total_Comprado,
                    SUM(Cantidad_p) AS Total_Productos
                    FROM reporte
                    GROUP BY Num_venta
                    ORDER BY Num_venta DESC;
                ''')
    data = cur.fetchall()
    
    # Obtener la lista de usuarios que son clientes para mostrarlos en el formulario
    cur.execute('SELECT ID_Usuario, Nombre, Apellido FROM usuarios WHERE Rol = "Cliente"')
    usuarios = cur.fetchall()
    
    # Obtener la lista de productos disponibles (con stock mayor a 0) para el formulario
    cur.execute('SELECT ID_Producto, Nombre, Precio FROM productos WHERE Stock > 0')
    productos = cur.fetchall()
    
    # Cerrar el cursor
    cur.close()
    
    # Renderizar la plantilla "ventas.html" enviando los datos necesarios
    return render_template('Vistas_admin/ventas.html', 
                            reportes=data, 
                            usuarios=usuarios, 
                            productos=productos)

@app.route('/add_venta', methods=['POST'])
def add_venta():
    # Esta ruta se encarga de agregar una nueva venta al sistema
    if request.method == 'POST':
        try:
            # Obtener datos enviados desde el formulario
            id_usuario = request.form['ID_Usuario']
            productos_data = request.form.getlist('productos[]')  # Lista de IDs de productos seleccionados
            cantidades = request.form.getlist('cantidades[]')    # Lista de cantidades para cada producto
            
            # Validar que se haya seleccionado al menos un producto
            if not productos_data or not cantidades:
                flash('Debe seleccionar al menos un producto')
                return redirect(url_for('ventas'))
            
            # Crear cursor para operaciones de base de datos
            cur = mysql.connection.cursor()
            
            # Variables para calcular el total de la venta
            total_venta = 0
            productos_venta = []  # Lista para almacenar los productos válidos de la venta
            
            # Recorrer productos y cantidades para validar y calcular subtotales
            for i, producto_id in enumerate(productos_data):
                if producto_id and int(cantidades[i]) > 0:
                    # Consultar precio y stock del producto
                    cur.execute('''SELECT Precio, Stock, Nombre FROM productos 
                                    WHERE ID_Producto = %s''', (producto_id,))
                    producto_info = cur.fetchone()
                    
                    if producto_info:
                        precio = int(producto_info[0])
                        stock_disponible = int(producto_info[1])
                        cantidad_solicitada = int(cantidades[i])
                        
                        # Validar que haya suficiente stock
                        if cantidad_solicitada > stock_disponible:
                            flash(f'Stock insuficiente para {producto_info[2]}. Disponible: {stock_disponible}')
                            return redirect(url_for('ventas'))
                        
                        # Calcular subtotal y sumarlo al total de la venta
                        subtotal = precio * cantidad_solicitada
                        total_venta += subtotal
                        
                        # Guardar la información del producto validado
                        productos_venta.append({
                            'id': producto_id,
                            'cantidad': cantidad_solicitada,
                            'precio': precio,
                            'subtotal': subtotal
                        })
            
            # Validar que haya al menos un producto válido
            if not productos_venta:
                flash('No hay productos válidos en la venta')
                return redirect(url_for('ventas'))
            
            # Insertar registro principal de la venta en la tabla "ventas"
            cur.execute('''INSERT INTO ventas (ID_UsuarioFK, Fecha, Total) 
                            VALUES (%s, NOW(), %s)''',
                        (id_usuario, total_venta))
            
            # Obtener el ID de la venta recién insertada para los detalles
            venta_id = cur.lastrowid
            
            # Insertar cada detalle de producto vendido y actualizar stock
            for producto in productos_venta:
                # Insertar detalle de venta
                cur.execute('''INSERT INTO detalles_venta (ID_VentaFK, ID_ProductoFK, Cantidad_p) 
                                VALUES (%s, %s, %s)''',
                            (venta_id, producto['id'], producto['cantidad']))
                
                # Actualizar el stock del producto vendido
                cur.execute('''UPDATE productos 
                                SET Stock = Stock - %s 
                                WHERE ID_Producto = %s''',
                            (producto['cantidad'], producto['id']))
            
            # Confirmar cambios en la base de datos
            mysql.connection.commit()
            flash('Venta registrada correctamente')
        
        except Exception as e:
            # Si ocurre un error, deshacer todos los cambios
            mysql.connection.rollback()
            flash(f'Error al registrar la venta: {str(e)}')
        
        finally:
            # Cerrar el cursor
            cur.close()
        
        # Redirigir nuevamente a la página de ventas
        return redirect(url_for('ventas'))

@app.route('/get_producto_precio/<id>')
def get_producto_precio(id):
    """Endpoint para obtener precio y stock de un producto específico vía AJAX"""
    cur = mysql.connection.cursor()
    # Buscar el producto por su ID
    cur.execute('SELECT Precio, Stock FROM productos WHERE ID_Producto = %s', (id,))
    data = cur.fetchone()
    cur.close()
    
    # Si se encuentra el producto, devolver datos en formato JSON
    if data:
        return jsonify({
            'precio': int(data[0]),
            'stock': int(data[1])
        })
    # Si no se encuentra, devolver un error 404
    return jsonify({'error': 'Producto no encontrado'}), 404

# -------------------------------------- FACTURA -----------------------------------------
    
@app.route('/factura/<id_venta>')
def factura(id_venta):
    cur = mysql.connection.cursor()
    
    # Consultamos la vista reporte filtrando por el número de venta
    cur.execute('''
        SELECT Num_venta, Fecha, Nombre_Cliente, Apellido_Cliente,
                Producto, Precio_Original, Descuento, Precio_Final,
                Cantidad_p, SubTotal_Final, Total_Venta
        FROM reporte
        WHERE Num_venta = %s
    ''', (id_venta,))
    
    factura_data = cur.fetchall()
    cur.close()
    
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

# -------------------------------------- LOGIN -----------------------------------------



# -------------------------------------- DIAGNÓSTICO -----------------------------------------

@app.route('/diagnostico')
def diagnostico():
    template_dir = os.path.abspath(app.template_folder)
    resultado = {
        'directorio_actual': os.getcwd(),
        'ruta_absoluta': template_dir,
        'template_folder': app.template_folder
    }

    # Comprobar si el directorio existe
    if os.path.exists(template_dir):
        resultado['template_dir_existe'] = True
        resultado['contenido_template_dir'] = os.listdir(template_dir)
        
        # Verificar la carpeta Vistas_admin
        vistas_admin_path = os.path.join(template_dir, 'Vistas_admin')
        
        if os.path.exists(vistas_admin_path):
            resultado['vistas_admin_existe'] = True
            resultado['contenido_vistas_admin'] = os.listdir(vistas_admin_path)
        else:
            resultado['vistas_admin_existe'] = False
    else:
        resultado['template_dir_existe'] = False
    
    return jsonify(resultado)

@app.route('/verificar_static')
def verificar_static():
    static_dir = os.path.join(BASE_DIR, 'static')
    return jsonify({
        "static_dir": static_dir,
        "static_existe": os.path.exists(static_dir),
        "contenido_static": os.listdir(static_dir) if os.path.exists(static_dir) else []
    })

if __name__ == '__main__':
    # Imprime información útil de depuración al iniciar
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(f"Directorio de templates (ruta absoluta): {os.path.abspath(app.template_folder)}")
    print(f"Directorio de templates existe: {os.path.exists(os.path.abspath(app.template_folder))}")
    
    app.run(debug=True)
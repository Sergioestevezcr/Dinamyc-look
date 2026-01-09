from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app as app, Response, send_file, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image 
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime, timedelta
from database import mysql  # mysql está definido en database.py
import io
import os
import uuid


# Importar decoradores y clase PDF
from decorators import login_required, admin_required
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

admin_bp = Blueprint('admin_bp', __name__)  # Creacion del blueprint

# -------------------------------------- DASHBOARD -----------------------------------------
@admin_bp.route('/')
def index():
    """Dashboard principal para administradores"""
    cur = mysql.connection.cursor()
    cur.execute('''SELECT 
                    COUNT(ID_Venta) AS pedidos_Totales, 
                    SUM(Total) AS Ingresos_Totales
                    FROM pedidos''')
    data_pedidos = cur.fetchall()

    if data_pedidos:
        pedidos_count = data_pedidos[0][0] or 0
        ingresos = data_pedidos[0][1] or 0
    else:
        pedidos_count = 0
        ingresos = 0
        
    cur.execute('''SELECT 
                    COUNT(ID_Usuario) AS pedidos_Totales
                    FROM usuarios''')
    usuariosT = cur.fetchone()[0] or 0

    cur.execute('''SELECT SUM(detalles_venta.Cantidad_p) AS Total_Cantidad_Mes_Actual
                    FROM detalles_venta''')
    productosT = cur.fetchone()[0] or 0

    cur.execute(
        'SELECT Nombre , Marca, Total_Vendido FROM masvendido ORDER BY masvendido.Total_Vendido DESC LIMIT 10')
    mas_vendidos = cur.fetchall()

    cur.execute(
        'SELECT * FROM prductosxacabar ORDER BY prductosxacabar.Stock DESC LIMIT 10')
    xacabar = cur.fetchall()

    cur.close()

    return render_template(
        'Vistas_admin/index-admin.html',
        pedidos=pedidos_count,
        ingresos=ingresos,
        productosT=productosT,
        usuariosT=usuariosT,
        vendidos=mas_vendidos,
        acabados=xacabar,
        admin_name=session.get('user_name')
    )


# ------------------ Datos para la gráfica ------------------
@admin_bp.route('/usuarios_productos_por_mes')
def usuarios_productos_por_mes():
    cur = mysql.connection.cursor()

    # --- Usuarios nuevos por mes ---
    cur.execute('''
        SELECT 
            DATE_FORMAT(Fecha_registro, '%b') AS mes,
            COUNT(ID_Usuario) AS nuevos_usuarios
        FROM usuarios
        WHERE YEAR(Fecha_registro) = YEAR(CURDATE())
        GROUP BY MONTH(Fecha_registro), mes
        ORDER BY MONTH(Fecha_registro);
    ''')
    data_usuarios = cur.fetchall()

    # --- Productos vendidos por mes ---
    cur.execute('''
        SELECT 
            DATE_FORMAT(pedidos.Fecha, '%b') AS mes,
            SUM(detalles_venta.Cantidad_p) AS productos_vendidos
        FROM pedidos
        JOIN detalles_venta ON pedidos.ID_Venta = detalles_venta.ID_VentaFK
        WHERE YEAR(pedidos.Fecha) = YEAR(CURDATE())
        GROUP BY MONTH(pedidos.Fecha), mes
        ORDER BY MONTH(pedidos.Fecha);
    ''')
    data_productos = cur.fetchall()
    cur.close()

    # Crear un diccionario base con los meses encontrados
    meses = sorted(list(set([fila[0] for fila in data_usuarios] + [fila[0] for fila in data_productos])),
                   key=lambda m: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].index(m))

    usuarios_por_mes = []
    productos_por_mes = []

    for mes in meses:
        usuarios_mes = next((u[1] for u in data_usuarios if u[0] == mes), 0)
        productos_mes = next((p[1] for p in data_productos if p[0] == mes), 0)
        usuarios_por_mes.append(usuarios_mes)
        productos_por_mes.append(productos_mes)

    return jsonify({
        "labels": meses,
        "usuarios": usuarios_por_mes,
        "productos": productos_por_mes
    })


@admin_bp.route('/pedidos_por_mes')
@admin_required
def pedidos_por_mes():
    ingresos_mensuales = [0] * 12
    pedidos_mensuales = [0] * 12
    meses = ['Ene.', 'Feb.', 'Mar.', 'Abr.', 'May.', 'Jun.',
             'Jul.', 'Ago.', 'Sep.', 'Oct.', 'Nov.', 'Dic.']

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT MONTH(Fecha) AS mes, 
            SUM(Total) AS total_ingresos,
            COUNT(*) AS total_pedidos
        FROM pedidos
        GROUP BY mes
        ORDER BY mes """)
    resultados = cur.fetchall()
    cur.close()

    for fila in resultados:
        mes_idx = int(fila[0]) - 1
        ingresos_mensuales[mes_idx] = int(fila[1]) if fila[1] else 0
        pedidos_mensuales[mes_idx] = int(fila[2]) if fila[2] else 0

    return jsonify({
        'labels': meses[:datetime.now().month],
        'dataIngresos': ingresos_mensuales[:datetime.now().month],
        'datapedidos': pedidos_mensuales[:datetime.now().month]
    })
# -------------------------------------- productos -----------------------------------------
@admin_bp.route('/productos')
@admin_required
def productos():
    cur = mysql.connection.cursor()

    # Listado de productos con marca, promo y precio_final calculado si hay descuento activo hoy
    cur.execute('''
        SELECT 
            p.ID_Producto, 
            p.Nombre, 
            p.Descripcion, 
            p.Imagen, 
            p.Precio AS precio_original,
            p.Stock, 
            prov.Marca, 
            p.Categoria,
            pr.ID_Promocion,
            pr.Descuento,
            CASE
                WHEN pr.Fecha_Inicial <= CURDATE() 
                    AND pr.Fecha_Final >= CURDATE()
                    AND pr.Descuento IS NOT NULL
                THEN p.Precio - (p.Precio * pr.Descuento / 100)
                ELSE NULL
            END AS precio_final
        FROM productos p
        LEFT JOIN promociones pr ON p.ID_PromocionFK = pr.ID_Promocion
        LEFT JOIN proveedores prov ON p.ID_ProveedorFK = prov.ID_Proveedor
    ''')
    productos_list = cur.fetchall()

    # Promociones activas o futuras (para seleccionar en el modal)
    cur.execute('''
        SELECT 
            ID_Promocion, 
            Descuento, 
            Fecha_Inicial, 
            Fecha_Final
        FROM promociones
        WHERE Fecha_Final > CURDATE()
        ORDER BY Fecha_Inicial ASC
    ''')
    promociones = cur.fetchall()

    # Marcas / proveedores (para el select de marca)
    cur.execute("SELECT ID_Proveedor, Marca FROM proveedores")
    marcas = cur.fetchall()

    cur.close()

    return render_template(
        "Vistas_admin/productos.html",
        productos=productos_list,
        marcas=marcas,
        promociones=promociones
    )


@admin_bp.route('/add_producto', methods=['POST'])
@admin_required
def add_producto():
    # Datos básicos del formulario
    nombre = request.form['Nombre']
    descripcion = request.form['Descripcion']
    precio = request.form['Precio']
    categoria = request.form['Categoria']
    stock = request.form['Stock']
    idmarca = request.form['Marca']  # ID_Proveedor
    id_promocion = request.form.get('ID_PromocionFK') or None

    cur = mysql.connection.cursor()

    # Obtener la marca (texto) a partir del proveedor, para armar carpeta de imágenes
    cur.execute(
        "SELECT Marca FROM proveedores WHERE ID_Proveedor = %s",
        (idmarca,)
    )
    marca = cur.fetchone()[0]

    # Manejo de imagen (opcional)
    file = request.files.get('Imagen')
    filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Carpeta final: <UPLOAD_FOLDER>/<Nombre_Marca_sin_espacios>/
        folder_name = marca.replace(" ", "_")
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(folder_path, exist_ok=True)

        file.save(os.path.join(folder_path, filename))

        # Guardamos la ruta relativa que vas a usar en las cards
        filename = f"/{folder_name}/{filename}"

    # Insertar el producto en la base de datos
    cur.execute(
        '''INSERT INTO productos 
           (Nombre, Descripcion, Categoria, Precio, Stock, Imagen, ID_ProveedorFK, ID_PromocionFK) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
        (nombre, descripcion, categoria, precio, stock, filename, idmarca, id_promocion)
    )
    mysql.connection.commit()
    cur.close()

    flash('Producto agregado correctamente', "success")
    return redirect(url_for('admin_bp.productos'))


@admin_bp.route('/edit_producto/<id>')
@admin_required
def edit_producto(id):
    cur = mysql.connection.cursor()

    # Pedimos columnas en orden controlado (NO SELECT *)
    cur.execute('''
        SELECT 
            ID_Producto,
            Nombre,
            Descripcion,
            Categoria,
            Precio,
            Stock,
            ID_ProveedorFK,
            ID_PromocionFK
        FROM productos
        WHERE ID_Producto = %s
    ''', (id,))
    data = cur.fetchone()
    cur.close()

    if not data:
        return jsonify({'error': 'Producto no encontrado'}), 404

    # data[x] coincide con el orden del SELECT de arriba
    product_data = {
        'id': data[0],
        'nombre': data[1],
        'descripcion': data[2],
        'categoria': data[3],
        'precio': data[4],
        'stock': data[5],
        'idmarca': data[6],
        'promocion': data[7]
    }

    return jsonify(product_data)


@admin_bp.route('/update_producto/<id>', methods=['POST'])
@admin_required
def update_producto(id):
    nombre = request.form['Nombre']
    descripcion = request.form['Descripcion']
    precio = request.form['Precio']
    categoria = request.form['Categoria']
    stock = request.form['Stock']
    idmarca = request.form['Marca']  # ID_Proveedor
    id_promocion = request.form.get('ID_PromocionFK') or None

    cur = mysql.connection.cursor()

    # De nuevo, sacamos la marca texto para la carpeta de imágenes
    cur.execute(
        "SELECT Marca FROM proveedores WHERE ID_Proveedor = %s",
        (idmarca,)
    )
    marca = cur.fetchone()[0]

    # ¿El admin subió una imagen nueva?
    file = request.files.get('Imagen')
    filename = None
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        folder_name = marca.replace(" ", "_")
        folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(folder_path, exist_ok=True)

        file.save(os.path.join(folder_path, filename))

        # ruta relativa que guardamos en la DB
        filename = f"/{folder_name}/{filename}"

    if filename:
        # Sí hay imagen nueva -> actualizamos todo incluyendo Imagen
        cur.execute(
            '''UPDATE productos 
               SET Nombre=%s,
                   Descripcion=%s,
                   Categoria=%s,
                   Precio=%s,
                   Stock=%s,
                   Imagen=%s,
                   ID_ProveedorFK=%s,
                   ID_PromocionFK=%s
               WHERE ID_Producto=%s''',
            (nombre, descripcion, categoria, precio, stock, filename, idmarca, id_promocion, id)
        )
    else:
        # No cambiaron imagen -> no tocamos la columna Imagen
        cur.execute(
            '''UPDATE productos 
               SET Nombre=%s,
                   Descripcion=%s,
                   Categoria=%s,
                   Precio=%s,
                   Stock=%s,
                   ID_ProveedorFK=%s,
                   ID_PromocionFK=%s
               WHERE ID_Producto=%s''',
            (nombre, descripcion, categoria, precio, stock, idmarca, id_promocion, id)
        )

    mysql.connection.commit()
    cur.close()

    flash('Producto actualizado correctamente', "success")
    return redirect(url_for('admin_bp.productos'))


# -------------------------------------- promociones/DESCUENTOS ----------------------------------------


@admin_bp.route('/promociones')
@admin_required
def promociones():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM promociones ORDER BY fecha_Inicial DESC')
    data = cur.fetchall()

    # Lista de promociones para el <select>
    cur.execute('''SELECT * FROM 
                    promociones
                    WHERE Fecha_Inicial > CURDATE()   -- solo promociones que aún no empiezan
                    ORDER BY Fecha_Inicial ASC''')
    promocionesf = cur.fetchall()

    cur.execute(
        'SELECT ID_Producto, Nombre, Precio FROM productos WHERE Stock > 0')
    productospromo = cur.fetchall()
    cur.close()

    # Pasar datos ya modificados a la plantilla
    return render_template('Vistas_admin/descuentos.html',
                           promocionesp=data,
                           promocionesf=promocionesf,
                           productospromo=productospromo)


@admin_bp.route('/add_promocion', methods=['POST'])
@admin_required
def add_promocion():
    descuento = request.form['Descuento']
    fechai = request.form['Fecha_Inicial']
    fechaf = request.form['Fecha_Final']

    cur = mysql.connection.cursor()
    cur.execute('''INSERT INTO promociones (Descuento, Fecha_Inicial, Fecha_Final)
                    VALUES (%s, %s, %s)''', (descuento, fechai, fechaf))
    mysql.connection.commit()
    cur.close()
    flash('Promoción agregada correctamente', "success")
    return redirect(url_for('admin_bp.promociones'))


@admin_bp.route('/edit_promocion/<id>')
def edit_promocion(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM promociones WHERE id_promocion = %s', (id,))
    data = cur.fetchone()
    if data:
        user_data = {
            'id': data[0],
            'descuento': data[1],
            'fechai': data[2],
            'fechaf': data[3]
        }
        return jsonify(user_data)
    return jsonify({'error': 'Promoción no encontrada'}), 404


@admin_bp.route('/update_promocion/<id>', methods=['POST'])
def update_promocion(id):
    if request.method == 'POST':
        descuento = request.form['Descuento']
        fechai = request.form['Fecha_Inicial']
        fechaf = request.form['Fecha_Final']

        cur = mysql.connection.cursor()
        cur.execute('''UPDATE promociones 
                        SET Descuento = %s, Fecha_Inicial = %s, Fecha_Final = %s
                        WHERE id_promocion = %s''',
                    (descuento, fechai, fechaf, id))
        mysql.connection.commit()
        flash('Promoción actualizada correctamente', "success")
        return redirect(url_for('admin_bp.promociones'))


@admin_bp.route("/asignar_promocion", methods=["POST"])
def asignar_promocion():
    # ID de la promo seleccionada
    promocion_id = request.form.get("ID_PromocionFK")
    productos_ids = request.form.getlist(
        "productos[]")  # lista de IDs de productos

    if not productos_ids:
        flash("No seleccionaste productos", "warning")
        return redirect(url_for("admin_bp.promociones"))

    cur = mysql.connection.cursor()

    if not promocion_id:
        # Quitar cualquier promoción
        query = "UPDATE productos SET ID_PromocionFK = NULL WHERE ID_Producto IN %s"
        cur.execute(query, (tuple(productos_ids),))
        mysql.connection.commit()
        cur.close()
        flash("Se quitó la promoción de los productos seleccionados", "success")
        return redirect(url_for("admin_bp.promociones"))
    else:
        # Validar que la promoción es futura
        cur.execute("""
            SELECT ID_Promocion 
            FROM promociones 
            WHERE ID_Promocion = %s AND Fecha_Inicial > CURDATE()
        """, (promocion_id,))

        futura = cur.fetchone()

        if futura:
            # Solo asignar si es futura
            query = "UPDATE productos SET ID_PromocionFK = %s WHERE ID_Producto IN %s"
            cur.execute(query, (promocion_id, tuple(productos_ids)))
            mysql.connection.commit()
            flash("Promoción asignada correctamente a los productos", "success")
        else:
            flash("No se puede asignar: la promoción no es futura", "error")

        cur.close()
        return redirect(url_for("admin_bp.promociones"))

# -------------------------------------- usuarios -----------------------------------------

@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE Rol = "Cliente" ORDER BY ID_usuario DESC')
    data = cur.fetchall()

    # Pasar datos ya modificados a la plantilla
    return render_template('Vistas_admin/usuarios.html', usuarios=data)


@admin_bp.route('/add_usuario', methods=['POST'])
def add_usuario():
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        documento = request.form['Documento']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave']
        rol = "Cliente"
        estado = "Activo"

        #  Hashear la contraseña
        clave_hash = generate_password_hash(clave)

        cur = mysql.connection.cursor()
        cur.execute(' CALL insertarusuario(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, rol, estado))

        mysql.connection.commit()
        cur.close()
        flash('Usuario agregado correctamente', "success")
        return redirect(url_for('admin_bp.usuarios'))


@admin_bp.route('/edit_usuario/<id>')
def edit_usuario(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE id_usuario = %s', (id,))
    data = cur.fetchone()
    if data:
        user_data = {
            'id': data[0],
            'nombre': data[1],
            'apellido': data[2],
            'documento': data[3],
            'correo': data[4],
            'telefono': data[5],
            'direccion': data[6],
            'ciudad': data[7],
            'clave': data[8]
        }
        return jsonify(user_data)
    return jsonify({'error': 'Usuario no encontrado'}), 404


@admin_bp.route('/update_usuario/<id>', methods=['POST'])
def update_usuario(id):
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        documento = request.form['Documento']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave']

        clave_hash = generate_password_hash(clave)

        cur = mysql.connection.cursor()
        cur.execute('''UPDATE usuarios 
                        SET Nombre = %s, Apellido = %s, N_Documento = %s,Correo = %s, 
                            Telefono = %s, Direccion = %s, Ciudad = %s, Clave = %s 
                        WHERE id_usuario = %s''',
                    (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, id))
        mysql.connection.commit()
        flash('Usuario actualizado correctamente', "success")
        return redirect(url_for('admin_bp.usuarios'))


@admin_bp.route('/delete_usuario/<id>', methods=['POST'])
def delete_usuario(id):
    cur = mysql.connection.cursor()
    # Solo actualiza si el usuario está activo
    cur.execute('CALL eliminarusuario(%s)', (id,))
    mysql.connection.commit()

    if cur.rowcount > 0:
        flash('Usuario inactivado correctamente', "success")
    else:
        flash('El usuario ya estaba inactivo o no existe', "warning")

    return redirect(url_for('admin_bp.usuarios'))

# -------------------------------------- admin -----------------------------------------

@admin_bp.route('/admin')
@admin_required
def admin():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE Rol = "Admin" ORDER BY ID_usuario DESC')
    data = cur.fetchall()

    # Pasar datos ya modificados a la plantilla
    return render_template('Vistas_admin/administradores.html', admins=data)


@admin_bp.route('/add_admin', methods=['POST'])
def add_admin():
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        documento = request.form['Documento']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave']
        rol = "Admin"
        estado = "Activo"

        #  Hashear la contraseña
        clave_hash = generate_password_hash(clave)

        cur = mysql.connection.cursor()
        cur.execute(' CALL insertarusuario(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, rol, estado))

        mysql.connection.commit()
        cur.close()
        flash('Usuario agregado correctamente', "success")
        return redirect(url_for('admin_bp.admin'))


@admin_bp.route('/edit_admin/<id>')
def edit_admin(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE id_usuario = %s', (id,))
    data = cur.fetchone()
    if data:
        user_data = {
            'id': data[0],
            'nombre': data[1],
            'apellido': data[2],
            'documento': data[3],
            'correo': data[4],
            'telefono': data[5],
            'direccion': data[6],
            'ciudad': data[7],
            'clave': data[8]
        }
        return jsonify(user_data)
    return jsonify({'error': 'Usuario no encontrado'}), 404


@admin_bp.route('/update_admin/<id>', methods=['POST'])
def update_admin(id):
    if request.method == 'POST':
        nombre = request.form['Nombre']
        apellido = request.form['Apellido']
        documento = request.form['Documento']
        correo = request.form['Correo']
        telefono = request.form['Telefono']
        direccion = request.form['Direccion']
        ciudad = request.form['Ciudad']
        clave = request.form['Clave']

        clave_hash = generate_password_hash(clave)

        cur = mysql.connection.cursor()
        cur.execute('''UPDATE usuarios 
                        SET Nombre = %s, Apellido = %s, N_Documento = %s,Correo = %s, 
                            Telefono = %s, Direccion = %s, Ciudad = %s, Clave = %s 
                        WHERE id_usuario = %s''',
                    (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, id))
        mysql.connection.commit()
        flash('Usuario actualizado correctamente', "success")
        return redirect(url_for('admin_bp.admin'))


@admin_bp.route('/delete_admin/<id>', methods=['POST'])
def delete_admin(id):
    cur = mysql.connection.cursor()
    # Solo actualiza si el usuario está activo
    cur.execute('CALL eliminarusuario(%s)', (id,))
    mysql.connection.commit()

    if cur.rowcount > 0:
        flash('Usuario inactivado correctamente', "success")
    else:
        flash('El usuario ya estaba inactivo o no existe', "warning")

    return redirect(url_for('admin_bp.admin'))
# -------------------------------------- pedidos -----------------------------------------
@admin_bp.route('/pedidos')
@admin_required
def pedidos_view():
    cur = mysql.connection.cursor()

    # Armamos los pedidos como los ve el admin.
    # p = pedidos (venta)
    # u = usuarios (cliente)
    # dv = detalles_venta (para contar cuántos productos compró)
    # pg = pagos (estado del pago, método)
    #
    # CLAVE: hacemos LEFT JOIN pagos usando la referencia.
    #
    cur.execute('''
        SELECT
            p.ID_Venta                                  AS Num_venta,
            p.Fecha                                     AS Fecha,
            u.Nombre                                    AS Nombre_Cliente,
            u.Apellido                                  AS Apellido_Cliente,
            p.Total                                     AS Total_Comprado,
            SUM(dv.Cantidad_p)                          AS Total_Productos,
            COALESCE(pg.estado, 'PENDING')              AS estado_pago,
            COALESCE(pg.metodo, 'MP')                   AS metodo_pago
        FROM pedidos p
        JOIN usuarios u 
            ON u.ID_Usuario = p.ID_UsuarioFK
        JOIN detalles_venta dv 
            ON dv.ID_VentaFK = p.ID_Venta
        LEFT JOIN pagos pg 
            ON pg.referencia = p.ReferenciaPago
        GROUP BY
            p.ID_Venta,
            p.Fecha,
            u.Nombre,
            u.Apellido,
            p.Total,
            pg.estado,
            pg.metodo
        ORDER BY p.ID_Venta DESC
    ''')
    data = cur.fetchall()

    # Lista de clientes para el modal "Nueva Venta"
    cur.execute('''
        SELECT ID_Usuario, Nombre, Apellido 
        FROM usuarios 
        WHERE Rol = "Cliente"
    ''')
    usuarios_list = cur.fetchall()

    # Lista de productos para el modal (stock > 0) con descuento activo si tiene
    cur.execute('''
        SELECT 
            p.ID_Producto, 
            p.Nombre, 
            p.Precio,
            COALESCE(pr.Descuento, 0) AS Descuento
        FROM productos p
        LEFT JOIN promociones pr 
            ON p.ID_PromocionFK = pr.ID_Promocion
            AND CURDATE() BETWEEN pr.Fecha_Inicial AND pr.Fecha_Final
        WHERE p.Stock > 0
    ''')
    productos_disponibles = cur.fetchall()

    cur.close()

    return render_template(
        'Vistas_admin/pedidos.html',
        reportes=data,
        usuarios=usuarios_list,
        productos=productos_disponibles
    )
@admin_bp.route('/add_venta', methods=['POST'])
@admin_required
def add_venta():
    if request.method == 'POST':
        try:
            id_usuario = request.form['ID_Usuario']
            productos_data = request.form.getlist('productos[]')
            cantidades = request.form.getlist('cantidades[]')

            if not id_usuario:
                flash('Debe seleccionar un cliente', "warning")
                return redirect(url_for('admin_bp.pedidos_view'))

            if not productos_data or not cantidades:
                flash('Debe seleccionar al menos un producto', "warning")
                return redirect(url_for('admin_bp.pedidos_view'))

            cur = mysql.connection.cursor()

            total_venta = 0
            productos_venta = []

            # 1. Recorremos productos enviados desde el modal
            for i, producto_raw in enumerate(productos_data):
                if not producto_raw:
                    continue
                if i >= len(cantidades) or not cantidades[i]:
                    continue

                cantidad_solicitada = int(cantidades[i])
                if cantidad_solicitada <= 0:
                    continue

                # "Shampoo X - $25000" -> "Shampoo X"
                nombre_producto = producto_raw.split(' - $')[0].strip()

                # buscamos el producto real en DB
                cur.execute('''
                    SELECT 
                        p.ID_Producto, 
                        p.Precio, 
                        p.Stock, 
                        p.Nombre, 
                        pr.Descuento
                    FROM productos p
                    LEFT JOIN promociones pr 
                        ON p.ID_PromocionFK = pr.ID_Promocion
                        AND CURDATE() BETWEEN pr.Fecha_Inicial AND pr.Fecha_Final
                    WHERE p.Nombre = %s
                ''', (nombre_producto,))
                producto_info = cur.fetchone()

                if not producto_info:
                    flash(f'Producto "{nombre_producto}" no encontrado', "error")
                    return redirect(url_for('admin_bp.pedidos_view'))

                producto_id        = producto_info[0]
                precio_base        = int(producto_info[1])
                stock_disponible   = int(producto_info[2])
                nombre_producto_db = producto_info[3]
                descuento          = producto_info[4] if producto_info[4] else 0

                if cantidad_solicitada > stock_disponible:
                    flash(
                        f'Stock insuficiente para {nombre_producto_db}. Disponible: {stock_disponible}',
                        "warning"
                    )
                    return redirect(url_for('admin_bp.pedidos_view'))

                precio_final = precio_base - (precio_base * descuento / 100.0)
                subtotal = precio_final * cantidad_solicitada
                total_venta += subtotal

                productos_venta.append({
                    'id': producto_id,
                    'cantidad': cantidad_solicitada,
                    'precio_original': precio_base,
                    'descuento': descuento,
                    'precio_final': precio_final,
                    'subtotal': subtotal,
                    'nombre': nombre_producto_db
                })

            if not productos_venta:
                flash('No hay productos válidos en la venta', "error")
                return redirect(url_for('admin_bp.pedidos_view'))

            # 2. Generar referencia única para este pedido/pago
            referencia = uuid.uuid4().hex  # ej: 'a3b1c9...'

            # 3. Insertar cabecera de la venta en 'pedidos'
            #    -> OJO: AÑADIMOS ReferenciaPago
            cur.execute('''
                INSERT INTO pedidos (ID_UsuarioFK, Fecha, Total, ReferenciaPago) 
                VALUES (%s, NOW(), %s, %s)
            ''', (id_usuario, total_venta, referencia))
            venta_id = cur.lastrowid  # ID_Venta generado

            # 4. Insertar cada línea en detalles_venta
            for producto in productos_venta:
                cur.execute('''
                    INSERT INTO detalles_venta 
                        (ID_VentaFK, ID_ProductoFK, Cantidad_p, SubTotal) 
                    VALUES (%s, %s, %s, %s)
                ''', (
                    venta_id,
                    producto['id'],
                    producto['cantidad'],
                    producto['subtotal']
                ))

                # bajar stock
                cur.execute('''
                    UPDATE productos 
                    SET Stock = Stock - %s 
                    WHERE ID_Producto = %s
                ''', (
                    producto['cantidad'],
                    producto['id']
                ))

            # 5. Crear registro en pagos asociado a esta venta
            #
            # Nota: tu tabla `pagos` NO tiene venta_id,
            # pero SÍ tiene:
            #   referencia,
            #   user_id,
            #   total_cents,
            #   estado,
            #   metodo,
            #   direccion_entrega
            #
            # Vamos a usar:
            #   metodo = 'COD'    porque esto lo está creando el admin a mano
            #   estado = 'COD_PENDIENTE_ENVIO'
            #   total_cents = total_venta * 100 (pasado a entero)
            #
            total_cents = int(round(total_venta * 100))

            cur.execute('''
                INSERT INTO pagos (
                    referencia,
                    user_id,
                    total_cents,
                    mp_preference_id,
                    mp_payment_id,
                    estado,
                    raw_json,
                    metodo,
                    direccion_entrega
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                referencia,
                id_usuario,
                total_cents,
                None,              # mp_preference_id (esto es para MP, aquí no aplica)
                None,              # mp_payment_id (esto es para MP)
                'COD_PENDIENTE_ENVIO',  # estado inicial para contraentrega
                None,              # raw_json (puedes guardar info extra si quieres)
                'COD',             # método de pago: Contraentrega
                None               # dirección_entrega (puedes llenarla luego)
            ))

            mysql.connection.commit()
            flash('Venta registrada correctamente.', "success")

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al registrar la venta: {str(e)}', "error")
            print(f"Error detallado: {str(e)}")

        finally:
            try:
                cur.close()
            except Exception:
                pass

        return redirect(url_for('admin_bp.pedidos_view'))

# -------------------------------------- REPORTES -----------------------------------------


@admin_bp.route('/reportes')
@admin_required
def reportes():
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT id, fecha_generacion, fecha_inicio, fecha_fin FROM reportes ORDER BY id DESC")
    data = cur.fetchall()
    return render_template("Vistas_admin/reportes.html", reportes=data)

@admin_bp.route('/generar_reporte', methods=['POST'])
@admin_required
def generar_reporte():
    try:
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        if not fecha_inicio or not fecha_fin:
            flash("Debes seleccionar ambas fechas", "error")
            return redirect(url_for("admin_bp.reportes"))

        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
        fecha_fin = fecha_fin_dt.strftime("%Y-%m-%d")

        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT
                v.ID_Venta AS Num_venta,
                v.Fecha AS Fecha,
                CONCAT(u.nombre, ' ', u.apellido) AS cliente,
                p.Nombre AS Producto,
                p.Precio AS Precio_Original,
                IFNULL(pr.Descuento, 0) AS Descuento,
                ROUND(dv.SubTotal / NULLIF(dv.Cantidad_p, 0), 0) AS Precio_Final,
                dv.Cantidad_p AS Cantidad_p,
                dv.SubTotal AS SubTotal_Final,
                v.Total AS Total_Venta
            FROM pedidos v
            JOIN usuarios u ON u.ID_Usuario = v.ID_UsuarioFK
            JOIN detalles_venta dv ON dv.ID_VentaFK = v.ID_Venta
            JOIN productos p ON p.ID_Producto = dv.ID_ProductoFK
            LEFT JOIN promociones pr 
                ON pr.ID_Promocion = p.ID_PromocionFK 
                AND CURDATE() BETWEEN pr.Fecha_Inicial AND pr.Fecha_Final
            WHERE v.Fecha >= %s AND v.Fecha < %s
            ORDER BY v.Fecha ASC
        """, (fecha_inicio, fecha_fin))

        pedidos = cur.fetchall()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        #  Evitar desbordes en texto largo
        normal_style = styles["Normal"]
        normal_style.wordWrap = 'CJK'  # activa el ajuste automático de texto

         #  Ruta del logo (ajusta a tu carpeta real)
        logo_path = os.path.join(os.getcwd(), "static", "imagenes", "logo.png")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        #  Evitar desbordes en texto largo
        normal_style = styles["Normal"]
        normal_style.wordWrap = 'CJK'  # activa el ajuste automático de texto

         #  Ruta del logo (ajusta a tu carpeta real)
        logo_path = os.path.join(os.getcwd(), "static", "imagenes", "logos", "logo.png")

        if os.path.exists(logo_path):
            logo = Image(logo_path, width=120, height=80)
            # Ajustar sin deformar si la imagen es más grande:
            logo._restrictSize(120, 80)   # limita ancho/alto máximo, preserva relación de aspecto
        else:
            # Si no existe el logo, crear un Paragraph de aviso pequeño para mantener estructura
            logo = Paragraph(" ", normal_style)  # espacio en blanco para que la columna exista

        # Preparar el título como Paragraph (usar estilo Title o uno personalizado)
        titulo_paragraph = Paragraph("<b>Reporte de pedidos</b><br/><small>Periodo: {}</small>".format(
            f"{fecha_inicio} a {fecha_fin}"
        ), styles["Title"])

        # Crear una tabla con 1 fila y 2 columnas: [logo, titulo]
        header_table = Table([[logo, titulo_paragraph]], colWidths=[130, 420])  # ajustar colWidths según tu página

        # Estilos: quitar borde, alinear texto a la izquierda y centrar verticalmente
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),    # centra verticalmente ambos items
            ('LEFTPADDING', (0, 0), (0, 0), 0),        # quitar padding izquierdo de la celda del logo
            ('RIGHTPADDING', (0, 0), (0, 0), 6),       # pequeño espacio entre logo y título
            ('LEFTPADDING', (1, 0), (1, 0), 6),        # padding del lado izquierdo del título
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),         # logo alineado a la izquierda
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),         # título alineado a la izquierda dentro de su celda
            ('GRID', (0,0), (-1,-1), 0, colors.white)  # sin grid visible (0 = sin borde)
        ]))

        # Agregar la tabla-header a elements
        elements.append(header_table)
        elements.append(Spacer(1, 12))

        # Encabezados
        data = [[
            Paragraph("<b>Fecha</b>", styles["Normal"]),
            Paragraph("<b>Cliente</b>", styles["Normal"]),
            Paragraph("<b>Producto</b>", styles["Normal"]),
            Paragraph("<b>Cant.</b>", styles["Normal"]),
            Paragraph("<b>Precio</b>", styles["Normal"]),
            Paragraph("<b>Desc.</b>", styles["Normal"]),
            Paragraph("<b>P. Final</b>", styles["Normal"]),
            Paragraph("<b>Subtotal</b>", styles["Normal"]),
        ]]

        total_general = 0

        for v in pedidos:
            precio_original = f"${v[4]:,.0f}".replace(",", ".")
            precio_final = f"${v[6]:,.0f}".replace(",", ".")
            subtotal = f"${v[8]:,.0f}".replace(",", ".")
            data.append([
                Paragraph(str(v[1]), normal_style),
                Paragraph(v[2], normal_style),        #  texto largo envuelto
                Paragraph(v[3], normal_style),        #  texto largo envuelto
                Paragraph(str(v[7]), normal_style),
                Paragraph(precio_original, normal_style),
                Paragraph(f"{v[5]}%", normal_style),
                Paragraph(precio_final, normal_style),
                Paragraph(subtotal, normal_style)
            ])
            total_general += v[8]

        total_general_formatted = f"${total_general:,.0f}".replace(",", ".")
        data.append([
            "", "", "", "", "", "",
            Paragraph("<b>TOTAL</b>", styles["Normal"]),
            Paragraph(f"<b>{total_general_formatted}</b>", styles["Normal"])
        ])

        #  Ajuste de ancho de columnas (más espacio a cliente y producto)
        table = Table(data, colWidths=[65, 100, 120, 40, 60, 50, 60, 70])

        # Estilos
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDB4CD")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#EDB4CD")),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))

        elements.append(table)
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Guardar en DB
        cur.execute("""
            INSERT INTO reportes (fecha_inicio, fecha_fin, archivo)
            VALUES (%s, %s, %s)
        """, (fecha_inicio, fecha_fin, pdf_bytes))
        mysql.connection.commit()

        flash("Reporte generado y guardado correctamente", "success")
        return redirect(url_for("admin_bp.reportes"))

    except Exception as e:
        mysql.connection.rollback()
        print("ERROR AL GENERAR REPORTE:", e)
        flash(f"Error al generar el reporte: {e}", "error")
        return redirect(url_for("admin_bp.reportes"))


@admin_bp.route('/descargar_reporte/<int:id>', methods=['GET'])
@admin_required
def descargar_reporte(id):
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT archivo, fecha_inicio, fecha_fin FROM reportes WHERE id = %s", (id,))
    reporte = cur.fetchone()

    if not reporte:
        flash("El reporte no existe", "error")
        return redirect(url_for("admin_bp.reportes"))

    archivo, fecha_inicio, fecha_fin = reporte
    nombre_archivo = f"reporte_{fecha_inicio}_{fecha_fin}.pdf"

    return send_file(io.BytesIO(archivo), as_attachment=True, download_name=nombre_archivo, mimetype="application/pdf")


@admin_bp.route('/ver_reporte/<int:id>', methods=['GET'])
@admin_required
def ver_reporte(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT archivo FROM reportes WHERE id = %s", (id,))
    reporte = cur.fetchone()

    if not reporte:
        flash("El reporte no existe", "error")
        return redirect(url_for("admin_bp.reportes"))

    archivo = reporte[0]
    return Response(archivo, mimetype="application/pdf")

# -------------------------------------- FACTURA -----------------------------------------

@admin_bp.route('/factura/<id_venta>')
@login_required
def factura(id_venta):
    user_id = session['user_id']
    rol = (session.get('user_role') or "").lower()   # cambio mínimo: siempre minúsculas

    cur = mysql.connection.cursor()

    if rol == 'admin':
        cur.execute('''
            SELECT Num_venta, Fecha, Nombre_Cliente, Apellido_Cliente, N_Documento,
                   Producto, Precio_Original, Descuento, Precio_Final,
                   Cantidad_p, SubTotal_Final, Total_Venta
            FROM reporte
            WHERE Num_venta = %s
        ''', (id_venta,))
    elif rol == 'cliente':
        cur.execute('''
            SELECT Num_venta, Fecha, Nombre_Cliente, Apellido_Cliente, N_Documento,
                   Producto, Precio_Original, Descuento, Precio_Final,
                   Cantidad_p, SubTotal_Final, Total_Venta
            FROM reporte
            WHERE Num_venta = %s AND ID_Cliente = %s
        ''', (id_venta, user_id))
    else:
        flash('Rol no reconocido', 'error')
        return redirect(url_for('auth_bp.login'))

    factura_data = cur.fetchall()
    cur.close()

    if factura_data:
        nombre_cliente = factura_data[0][2]
        apellido_cliente = factura_data[0][3]
        documento = factura_data[0][4]
        fecha = factura_data[0][1]
        total = factura_data[0][11]
    else:
        flash('Factura no encontrada o no autorizada', 'warning')
        return redirect(url_for('client_bp.compras'))

    if rol == 'admin':
        return render_template(
            'Vistas_admin/factura.html',
            factura=factura_data,
            nombre=nombre_cliente,
            apellido=apellido_cliente,
            documento=documento,
            fecha=fecha,
            id_venta=id_venta,
            total=total
        )
    else:  # cliente
        return render_template(
            'Vista_usuario/factura.html',
            factura=factura_data,
            nombre=nombre_cliente,
            apellido=apellido_cliente,
            documento=documento,
            fecha=fecha,
            id_venta=id_venta,
            total=total
        )
        
@admin_bp.route("/descargar_factura/<int:id>")
@login_required
def descargar_factura(id):
    user_id = session.get("user_id")
    if not user_id:
        return "No autenticado", 401

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT Num_venta, Fecha, Nombre_Cliente, Apellido_Cliente, N_Documento,
               Producto, Precio_Original, Descuento, Precio_Final,
               Cantidad_p, SubTotal_Final, Total_Venta
        FROM reporte
        WHERE Num_venta = %s
    """, (id,))
    datos = cursor.fetchall()

    if not datos:
        return "Factura no encontrada", 404

    # Datos del cliente
    cliente_nombre = datos[0][2]
    cliente_apellido = datos[0][3]
    documento = datos[0][4]
    fecha = datos[0][1].strftime("%Y-%m-%d")
    total = sum(row[11] for row in datos)

    # Crear PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    #  Paleta de colores
    COLOR_PRINCIPAL = colors.HexColor("#C1416D")
    COLOR_SECUNDARIO = colors.HexColor("#F4D6E4")
    COLOR_TEXTO = colors.HexColor("#333333")
    COLOR_CLARO = colors.HexColor("#FFFFFF")
    COLOR_OSCURO = colors.HexColor("#ededed")
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        name="TituloFactura",
        fontSize=18,
        alignment=1,
        textColor=COLOR_TEXTO,
        spaceAfter=20,
        fontName="Helvetica-Bold"
    )

    normal_center = ParagraphStyle(
        name="Center",
        alignment=1,
        textColor=COLOR_TEXTO,
        fontSize=11
    )
    
    normal_centert = ParagraphStyle(
        name="Center",
        alignment=1,
        textColor=COLOR_CLARO,
        fontSize=11
    )

    normal_left = ParagraphStyle(
        name="Left",
        alignment=0,
        textColor=COLOR_TEXTO,
        fontSize=10,
        leading=12
    )

    bold_right = ParagraphStyle(
        name="BoldRight",
        alignment=2,
        fontName="Helvetica-Bold",
        textColor=COLOR_PRINCIPAL,
        fontSize=11
    )

    #  Título
    elements.append(Paragraph(f"Factura N.º {id}", title_style))
    elements.append(Spacer(1, 12))

    # Información del cliente
    info_cliente = f"""
    <b>Cliente:</b> {cliente_nombre} {cliente_apellido}<br/>
    <b>C.C:</b> {documento}<br/>
    <b>Fecha:</b> {fecha}<br/>
    """
    elements.append(Paragraph(info_cliente, normal_center))
    elements.append(Spacer(1, 12))

    # Datos de tabla
    data = [
        [
            Paragraph("<b>Producto</b>", normal_centert,),
            Paragraph("<b>Precio Original</b>", normal_centert),
            Paragraph("<b>Descuento</b>", normal_centert),
            Paragraph("<b>Precio Final</b>", normal_centert),
            Paragraph("<b>Cant.</b>", normal_centert),
            Paragraph("<b>Subtotal</b>", normal_centert)
        ]
    ]

    # Filas de productos (usa Paragraph para que el texto se ajuste)
    for row in datos:
        data.append([
            Paragraph(str(row[5]), normal_left),  # Producto largo se ajusta
            Paragraph(f"${row[6]:,.0f}".replace(",", "."), normal_center),
            Paragraph(f"{row[7]}%", normal_center),
            Paragraph(f"${row[8]:,.0f}".replace(",", "."), normal_center),
            Paragraph(str(row[9]), normal_center),
            Paragraph(f"${row[10]:,.0f}".replace(",", "."), normal_center)
        ])

    # Fila total (sin etiquetas HTML)
    data.append([
        "", "", "", "",
        Paragraph("<b>Total:</b>", bold_right),
        Paragraph(f"<b>${total:,.0f}</b>".replace(",", "."), bold_right)
    ])

    # Anchos de columna ajustados
    col_widths = [150, 80, 60, 80, 50, 80]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Encabezado
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRINCIPAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),

        # Alternancia de filas
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [COLOR_CLARO, COLOR_OSCURO]),

        # Fila total
        ("BACKGROUND", (0, -1), (-1, -1), COLOR_SECUNDARIO),
        ("TEXTCOLOR", (0, -1), (-1, -1), COLOR_PRINCIPAL),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

        # Bordes y alineación
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    nombre_archivo = f"Factura_{id}_{fecha}.pdf"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/pdf"
    )

# -------------------------------------- CONFIGURACIÓN / PERFIL -----------------------------------------

@admin_bp.route('/configuracion', methods=['GET'])
@login_required
def configuracion():
    id = session['user_id']
    rol = (session.get('user_role') or "").lower()   # cambio mínimo: minúsculas
    
    if id and rol == 'cliente':
        flash('El Nombre, el Apellido y el N° de Documento no pueden ser editados', 'info')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE ID_Usuario = %s', (id,))
    data = cur.fetchone()

    if not data:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('auth_bp.login'))

    usuario = {
        'id_usuario': data[0],
        'nombre': data[1],
        'apellido': data[2],
        'documento': data[3],
        'correo': data[4],
        'telefono': data[5],
        'direccion': data[6],
        'ciudad': data[7],
        'clave': data[8]
    }
    
    if id:
        cur.execute("SELECT Nombre FROM usuarios WHERE ID_Usuario = %s", (id,))
        row = cur.fetchone()
        nombre = row[0] if row else None
    cur.close()

    if rol == 'admin':
        return render_template('Vistas_admin/configuracion.html', usuario=usuario)
    elif rol == 'cliente':
        return render_template('Vista_usuario/perfil.html', usuario=usuario, user=id, nombre=nombre)
    else:
        flash('Rol no reconocido', 'error')
        return redirect(url_for('auth_bp.login'))


@admin_bp.route('/actualizar_usuario/<int:id>', methods=['POST'])
@login_required
def actualizar_usuario(id):
    usuario_id = session['user_id']
    rol = (session.get('user_role') or "").lower()   # cambio mínimo: minúsculas

    if rol == 'cliente' and usuario_id != id:
        flash('No tienes permiso para actualizar este usuario', 'error')
        return redirect(url_for('admin_bp.configuracion'))

    nombre = request.form['Nombre']
    apellido = request.form['Apellido']
    documento = request.form['Documento']
    correo = request.form['Correo']
    telefono = request.form['Telefono']
    direccion = request.form['Direccion']
    ciudad = request.form['Ciudad']
    clave = request.form['Clave'].strip()

    cur = mysql.connection.cursor()

    if clave:
        clave_hash = generate_password_hash(clave)
        cur.execute("""
            UPDATE usuarios 
            SET Nombre=%s, Apellido=%s, N_Documento=%s, Correo=%s, Telefono=%s, Direccion=%s, Ciudad=%s, Clave=%s
            WHERE ID_Usuario=%s
        """, (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, id))
    else:
        cur.execute("""
            UPDATE usuarios 
            SET Nombre=%s, Apellido=%s, N_Documento=%s, Correo=%s, Telefono=%s, Direccion=%s, Ciudad=%s
            WHERE ID_Usuario=%s
        """, (nombre, apellido, documento, correo, telefono, direccion, ciudad, id))

    mysql.connection.commit()
    cur.close()

    flash('Usuario actualizado correctamente', 'success')
    return redirect(url_for('admin_bp.configuracion'))
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app as app, Response, send_file, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image 
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime, timedelta
from database import mysql  # mysql está definido en database.py
import io
import os

# Importar decoradores y clase PDF
from decorators import login_required, admin_required
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

admin_bp = Blueprint('admin_bp', __name__)  # Creacion del blueprint

# -------------------------------------- DASHBOARD -----------------------------------------


@admin_bp.route('/')
@admin_required
def index():
    """Dashboard principal para administradores"""
    cur = mysql.connection.cursor()
    cur.execute('''SELECT 
                    COUNT(ID_Venta) AS Ventas_Totales, 
                    SUM(Total) AS Ingresos_Totales
                    FROM ventas
                    WHERE MONTH(Fecha) = MONTH(CURDATE())
                    AND YEAR(Fecha) = YEAR(CURDATE())''')
    data_ventas = cur.fetchall()

    if data_ventas:
        ventas_count = data_ventas[0][0] or 0
        ingresos = data_ventas[0][1] or 0
    else:
        ventas_count = 0
        ingresos = 0

    cur.execute('''SELECT SUM(detalles_venta.Cantidad_p) AS Total_Cantidad_Mes_Actual
                    FROM detalles_venta 
                    JOIN ventas ON detalles_venta.ID_VentaFK = ventas.ID_Venta
                    WHERE MONTH(ventas.Fecha) = MONTH(CURDATE())
                    AND YEAR(ventas.Fecha) = YEAR(CURDATE())''')
    productosT = cur.fetchone()[0] or 0

    cur.execute(
        'SELECT Nombre , Marca, Total_Vendido FROM mas_vendidos ORDER BY mas_vendidos.Total_Vendido DESC LIMIT 10')
    mas_vendidos = cur.fetchall()

    cur.execute(
        'SELECT * FROM prductosxacabar ORDER BY prductosxacabar.Stock DESC LIMIT 10')
    xacabar = cur.fetchall()

    cur.close()

    return render_template(
        'Vistas_admin/index-admin.html',
        ventas=ventas_count,
        ingresos=ingresos,
        productosT=productosT,
        vendidos=mas_vendidos,
        acabados=xacabar,
        admin_name=session.get('user_name')
    )


# ------------------ Datos para la gráfica ------------------

@admin_bp.route('/ventas_por_mes')
@admin_required
def ventas_por_mes():
    ingresos_mensuales = [0] * 12
    ventas_mensuales = [0] * 12
    meses = ['Ene.', 'Feb.', 'Mar.', 'Abr.', 'May.', 'Jun.',
             'Jul.', 'Ago.', 'Sep.', 'Oct.', 'Nov.', 'Dic.']

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT MONTH(Fecha) AS mes, 
            SUM(Total) AS total_ingresos,
            COUNT(*) AS total_ventas
        FROM ventas
        GROUP BY mes
        ORDER BY mes """)
    resultados = cur.fetchall()
    cur.close()

    for fila in resultados:
        mes_idx = int(fila[0]) - 1
        ingresos_mensuales[mes_idx] = int(fila[1]) if fila[1] else 0
        ventas_mensuales[mes_idx] = int(fila[2]) if fila[2] else 0

    return jsonify({
        'labels': meses[:datetime.now().month],
        'dataIngresos': ingresos_mensuales[:datetime.now().month],
        'dataVentas': ventas_mensuales[:datetime.now().month]
    })
# -------------------------------------- productos -----------------------------------------


@admin_bp.route('/productos')
@admin_required
def productos():
    cur = mysql.connection.cursor()

    # Productos con su precio final
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

    # Lista de promociones futuras
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
    if request.method == 'POST':
        nombre = request.form['Nombre']
        descripcion = request.form['Descripcion']
        precio = request.form['Precio']
        categoria = request.form['Categoria']
        stock = request.form['Stock']
        idmarca = request.form['Marca']
        id_promocion = request.form.get('ID_PromocionFK') or None
        
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT Marca FROM proveedores WHERE ID_Proveedor = %s", (idmarca))
        marca = cur.fetchone()[0]

        # Manejo de archivo
        file = request.files.get('Imagen')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            folder_name = marca.replace(" ", "_")
            folder_path = os.path.join(
                app.config['UPLOAD_FOLDER'], folder_name)
            os.makedirs(folder_path, exist_ok=True)
            file.save(os.path.join(folder_path, filename))
            filename = f"/{folder_name}/{filename}"

        cur.execute('''INSERT INTO productos 
                        (Nombre, Descripcion, Categoria, Precio, Stock, Imagen, ID_ProveedorFK, ID_PromocionFK) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                    (nombre, descripcion, categoria, precio, stock, filename, idmarca, id_promocion))
        mysql.connection.commit()
        cur.close()

        flash('Producto agregado correctamente', "success")
        return redirect(url_for('admin_bp.productos'))


@admin_bp.route('/edit_producto/<id>')
@admin_required
def edit_producto(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE id_producto = %s', (id,))
    data = cur.fetchone()
    cur.close()

    if data:
        product_data = {
            'id': data[0],
            'nombre': data[1],
            'descripcion': data[2],
            'categoria': data[3],
            'precio': data[5],
            'stock': data[6],
            'idmarca': data[7],
            'promocion': data[8]
        }
        return jsonify(product_data)
    return jsonify({'error': 'Producto no encontrado'}), 404


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.route('/update_producto/<id>', methods=['POST'])
@admin_required
def update_producto(id):
    if request.method == 'POST':
        nombre = request.form['Nombre']
        descripcion = request.form['Descripcion']
        precio = request.form['Precio']
        categoria = request.form['Categoria']
        stock = request.form['Stock']
        idmarca = request.form['Marca']
        id_promocion = request.form.get('ID_PromocionFK') or None
        
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT Marca FROM proveedores WHERE ID_Proveedor = %s", (idmarca))
        marca = cur.fetchone()[0]

        file = request.files.get('Imagen')
        filename = None
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            folder_name = marca.lower().replace(" ", "_")
            folder_path = os.path.join(
                app.config['UPLOAD_FOLDER'], folder_name)
            os.makedirs(folder_path, exist_ok=True)

            file.save(os.path.join(folder_path, filename))
            filename = f"/{folder_name}/{filename}"

        if filename:
            cur.execute('''UPDATE productos 
                            SET Nombre=%s, Descripcion=%s, Categoria=%s, Precio=%s, 
                            Stock=%s, Imagen=%s, ID_ProveedorFK=%s, ID_PromocionFK=%s
                            WHERE id_producto=%s''',
                        (nombre, descripcion, categoria, precio, stock, filename, idmarca, id_promocion, id))
        else:
            cur.execute('''UPDATE productos 
                            SET Nombre=%s, Descripcion=%s, Categoria=%s, Precio=%s, 
                            Stock=%s, Id_ProveedorFK=%s, ID_PromocionFK=%s
                            WHERE id_producto=%s''',
                        (nombre, descripcion, categoria, precio, stock, idmarca, id_promocion, id))
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
# -------------------------------------- ventas -----------------------------------------


@admin_bp.route('/ventas')
@admin_required
def ventas_view():
    cur = mysql.connection.cursor()

    # Usar la vista "reporte" para obtener los datos de ventas ya procesados
    cur.execute('''
        SELECT
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

    # Obtener la lista de usuarios que son clientes
    cur.execute(
        'SELECT ID_Usuario, Nombre, Apellido FROM usuarios WHERE Rol = "Cliente"')
    usuarios_list = cur.fetchall()

    # Obtener la lista de productos disponibles (stock > 0)
    cur.execute(''' SELECT 
                        p.ID_Producto, 
                        p.Nombre, 
                        p.Precio,
                        COALESCE(pr.Descuento, 0) AS Descuento
                    FROM productos p
                    LEFT JOIN promociones pr 
                        ON p.ID_PromocionFK = pr.ID_Promocion
                        AND CURDATE() BETWEEN pr.Fecha_Inicial AND pr.Fecha_Final
                    WHERE p.Stock > 0''')
    productos_disponibles = cur.fetchall()

    cur.close()

    return render_template(
        'Vistas_admin/ventas.html',
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
                return redirect(url_for('admin_bp.ventas_view'))

            if not productos_data or not cantidades:
                flash('Debe seleccionar al menos un producto', "warning")
                return redirect(url_for('admin_bp.ventas_view'))

            cur = mysql.connection.cursor()
            total_venta = 0
            productos_venta = []

            for i, producto_nombre in enumerate(productos_data):
                if producto_nombre and i < len(cantidades) and cantidades[i] and int(cantidades[i]) > 0:
                    nombre_producto = producto_nombre.split(' - $')[0].strip()
                    cantidad_solicitada = int(cantidades[i])

                    # Buscar el producto
                    cur.execute('''
                        SELECT p.ID_Producto, p.Precio, p.Stock, p.Nombre, pr.Descuento
                        FROM productos p
                        LEFT JOIN promociones pr 
                            ON p.ID_PromocionFK = pr.ID_Promocion
                            AND CURDATE() BETWEEN pr.Fecha_Inicial AND pr.Fecha_Final
                        WHERE p.Nombre = %s
                    ''', (nombre_producto,))

                    producto_info = cur.fetchone()

                    if producto_info:
                        producto_id = producto_info[0]
                        precio = int(producto_info[1])
                        stock_disponible = int(producto_info[2])
                        nombre_producto = producto_info[3]
                        descuento = producto_info[4] if producto_info[4] else 0

                        if cantidad_solicitada > stock_disponible:
                            flash(
                                f'Stock insuficiente para {nombre_producto}. Disponible: {stock_disponible}', "warning")
                            return redirect(url_for('admin_bp.ventas_view'))

                        precio_final = precio - (precio * descuento / 100)
                        subtotal = precio_final * cantidad_solicitada
                        total_venta += subtotal

                        productos_venta.append({
                            'id': producto_id,
                            'cantidad': cantidad_solicitada,
                            'precio_original': precio,
                            'descuento': descuento,
                            'precio_final': precio_final,
                            'subtotal': subtotal,
                            'nombre': nombre_producto
                        })
                    else:
                        flash(
                            f'Producto "{nombre_producto}" no encontrado', "error")
                        return redirect(url_for('admin_bp.ventas_view'))

            if not productos_venta:
                flash('No hay productos válidos en la venta', "error")
                return redirect(url_for('admin_bp.ventas_view'))

            # Insertar en ventas
            cur.execute(
                '''INSERT INTO ventas (ID_UsuarioFK, Fecha, Total) VALUES (%s, NOW(), %s)''',
                (id_usuario, total_venta)
            )
            venta_id = cur.lastrowid

            # Insertar detalles de venta y actualizar stock
            for producto in productos_venta:
                cur.execute('''
                    INSERT INTO detalles_venta 
                        (ID_VentaFK, ID_ProductoFK, Cantidad_p, SubTotal) 
                    VALUES (%s, %s, %s, %s)
                ''', (venta_id, producto['id'], producto['cantidad'], producto['subtotal']))

                cur.execute('''
                    UPDATE productos 
                    SET Stock = Stock - %s 
                    WHERE ID_Producto = %s
                ''', (producto['cantidad'], producto['id']))

            mysql.connection.commit()
            flash('Venta registrada correctamente.', "success")

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al registrar la venta: {str(e)}', "error")
            print(f"Error detallado: {str(e)}")

        finally:
            cur.close()

        return redirect(url_for('admin_bp.ventas_view'))

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
            FROM ventas v
            JOIN usuarios u ON u.ID_Usuario = v.ID_UsuarioFK
            JOIN detalles_venta dv ON dv.ID_VentaFK = v.ID_Venta
            JOIN productos p ON p.ID_Producto = dv.ID_ProductoFK
            LEFT JOIN promociones pr 
                ON pr.ID_Promocion = p.ID_PromocionFK 
                AND CURDATE() BETWEEN pr.Fecha_Inicial AND pr.Fecha_Final
            WHERE v.Fecha >= %s AND v.Fecha < %s
            ORDER BY v.Fecha ASC
        """, (fecha_inicio, fecha_fin))

        ventas = cur.fetchall()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # 🔧 Evitar desbordes en texto largo
        normal_style = styles["Normal"]
        normal_style.wordWrap = 'CJK'  # activa el ajuste automático de texto

         # 🔧 Ruta del logo (ajusta a tu carpeta real)
        logo_path = os.path.join(os.getcwd(), "static", "imagenes", "logo.png")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()

        # 🔧 Evitar desbordes en texto largo
        normal_style = styles["Normal"]
        normal_style.wordWrap = 'CJK'  # activa el ajuste automático de texto

         # 🔧 Ruta del logo (ajusta a tu carpeta real)
        logo_path = os.path.join(os.getcwd(), "static", "imagenes", "logos", "logo.png")

        if os.path.exists(logo_path):
            logo = Image(logo_path, width=120, height=80)
            # Ajustar sin deformar si la imagen es más grande:
            logo._restrictSize(120, 80)   # limita ancho/alto máximo, preserva relación de aspecto
        else:
            # Si no existe el logo, crear un Paragraph de aviso pequeño para mantener estructura
            logo = Paragraph(" ", normal_style)  # espacio en blanco para que la columna exista

        # Preparar el título como Paragraph (usar estilo Title o uno personalizado)
        titulo_paragraph = Paragraph("<b>Reporte de Ventas</b><br/><small>Periodo: {}</small>".format(
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

        for v in ventas:
            precio_original = f"${v[4]:,.0f}".replace(",", ".")
            precio_final = f"${v[6]:,.0f}".replace(",", ".")
            subtotal = f"${v[8]:,.0f}".replace(",", ".")
            data.append([
                Paragraph(str(v[1]), normal_style),
                Paragraph(v[2], normal_style),        # 🔧 texto largo envuelto
                Paragraph(v[3], normal_style),        # 🔧 texto largo envuelto
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

        # 🔧 Ajuste de ancho de columnas (más espacio a cliente y producto)
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
        print("❌ ERROR AL GENERAR REPORTE:", e)
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


# -------------------------------------- CONFIGURACIÓN / PERFIL -----------------------------------------

@admin_bp.route('/configuracion', methods=['GET'])
@login_required
def configuracion():
    id = session['user_id']
    rol = (session.get('user_role') or "").lower()   # cambio mínimo: minúsculas

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
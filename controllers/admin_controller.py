from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app as app, Response, send_file, jsonify
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime, timedelta
from collections import defaultdict
from database import mysql  # mysql está definido en database.py
import io
import os
import uuid


# Importar decoradores y clase PDF
from decorators import login_required, admin_required
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
BRAND_OPTIONS = [
    "EPA Colombia",
    "Anyeluz",
    "Milagros",
    "D’Luchi",
    "Kaba",
    "La Receta",
    "Magic Hair",
    "OMG",
    "La Poción"
]

admin_bp = Blueprint('admin_bp', __name__)  # Creacion del blueprint


# Función para validar extensión de archivo
def allowed_file(filename):
    """Valida si la extensión del archivo está permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------------------------- DASHBOARD -----------------------------------------


@admin_bp.route('/')
@admin_required
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
                   key=lambda m: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].index(m))

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


def _ensure_home_content_tables():
    cur = mysql.connection.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS home_product_config (
            product_id BIGINT(20) NOT NULL,
            section_name VARCHAR(30) NOT NULL DEFAULT 'ninguno',
            sort_order INT NOT NULL DEFAULT 999,
            enabled TINYINT(1) NOT NULL DEFAULT 0,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (product_id),
            CONSTRAINT fk_home_product_config_producto
                FOREIGN KEY (product_id) REFERENCES productos(ID_Producto)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS home_banners (
            id BIGINT(20) NOT NULL AUTO_INCREMENT,
            title VARCHAR(100) DEFAULT NULL,
            desktop_image VARCHAR(255) DEFAULT NULL,
            mobile_image VARCHAR(255) DEFAULT NULL,
            sort_order INT NOT NULL DEFAULT 0,
            enabled TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS brand_banners (
            id BIGINT(20) NOT NULL AUTO_INCREMENT,
            brand_name VARCHAR(100) NOT NULL,
            title VARCHAR(100) DEFAULT NULL,
            desktop_image VARCHAR(255) DEFAULT NULL,
            mobile_image VARCHAR(255) DEFAULT NULL,
            sort_order INT NOT NULL DEFAULT 0,
            enabled TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY idx_brand_enabled_order (brand_name, enabled, sort_order)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    ''')

    mysql.connection.commit()
    cur.close()


def _guardar_config_producto_home(cur, product_id, section_name, sort_order, enabled):
    section_name = (section_name or 'ninguno').strip().lower()
    if section_name not in ['destacado', 'combo', 'ninguno']:
        section_name = 'ninguno'

    try:
        sort_order = int(sort_order)
    except Exception:
        sort_order = 999

    enabled = 1 if str(enabled) == '1' else 0

    if section_name == 'ninguno' and enabled == 0:
        cur.execute('DELETE FROM home_product_config WHERE product_id = %s',
                    (product_id,))
        return

    cur.execute('''
        INSERT INTO home_product_config (product_id, section_name, sort_order, enabled)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            section_name = VALUES(section_name),
            sort_order = VALUES(sort_order),
            enabled = VALUES(enabled)
    ''', (product_id, section_name, sort_order, enabled))


def _save_banner_image(file_obj, target_folder):
    if not file_obj or not file_obj.filename or not allowed_file(file_obj.filename):
        return None

    safe_name = secure_filename(file_obj.filename)
    unique_name = f"{uuid.uuid4().hex[:10]}_{safe_name}"

    folder_path = os.path.join(
        app.config['UPLOAD_FOLDER'], 'banners', target_folder)
    os.makedirs(folder_path, exist_ok=True)
    file_obj.save(os.path.join(folder_path, unique_name))

    return f"/banners/{target_folder}/{unique_name}"


@admin_bp.route('/productos')
@admin_required
def productos():
    _ensure_home_content_tables()
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
            COALESCE(hpc.section_name, 'ninguno') AS home_section,
            COALESCE(hpc.sort_order, 999) AS home_order,
            COALESCE(hpc.enabled, 0) AS home_enabled,
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
        LEFT JOIN home_product_config hpc ON hpc.product_id = p.ID_Producto
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

    # Categorías existentes para permitir gestión dinámica desde el formulario
    cur.execute('''
        SELECT DISTINCT Categoria
        FROM productos
        WHERE Categoria IS NOT NULL AND TRIM(Categoria) <> ''
        ORDER BY Categoria ASC
    ''')
    categorias_db = [row[0] for row in cur.fetchall()]

    cur.execute('''
        SELECT Categoria, COUNT(*) AS total
        FROM productos
        WHERE Categoria IS NOT NULL AND TRIM(Categoria) <> ''
        GROUP BY Categoria
        ORDER BY Categoria ASC
    ''')
    categorias_resumen = cur.fetchall()

    categorias_base = ['Cuidado capilar', 'Cuidado de la piel']
    categorias = []
    for c in categorias_base + categorias_db:
        if c and c not in categorias:
            categorias.append(c)

    cur.close()

    return render_template(
        "Vistas_admin/productos.html",
        productos=productos_list,
        marcas=marcas,
        promociones=promociones,
        categorias=categorias,
        categorias_resumen=categorias_resumen
    )


@admin_bp.route('/categorias/renombrar', methods=['POST'])
@admin_required
def renombrar_categoria_producto():
    categoria_actual = (request.form.get('categoria_actual') or '').strip()
    categoria_nueva = (request.form.get('categoria_nueva') or '').strip()

    if not categoria_actual or not categoria_nueva:
        flash(
            'Debes seleccionar la categoría actual y escribir el nuevo nombre.', 'warning')
        return redirect(url_for('admin_bp.productos'))

    if categoria_actual.lower() == categoria_nueva.lower():
        flash('La categoría nueva debe ser diferente a la actual.', 'warning')
        return redirect(url_for('admin_bp.productos'))

    cur = mysql.connection.cursor()
    cur.execute('''
        UPDATE productos
        SET Categoria = %s
        WHERE Categoria = %s
    ''', (categoria_nueva, categoria_actual))
    mysql.connection.commit()
    cambios = cur.rowcount
    cur.close()

    if cambios > 0:
        flash(
            f'Categoría renombrada correctamente en {cambios} producto(s).', 'success')
    else:
        flash('No se encontraron productos con esa categoría para renombrar.', 'warning')

    return redirect(url_for('admin_bp.productos'))


@admin_bp.route('/categorias/eliminar', methods=['POST'])
@admin_required
def eliminar_categoria_producto():
    categoria_origen = (request.form.get('categoria_origen') or '').strip()
    categoria_destino = (request.form.get(
        'categoria_destino') or 'Sin categoría').strip()

    if not categoria_origen:
        flash('Debes seleccionar una categoría para eliminar.', 'warning')
        return redirect(url_for('admin_bp.productos'))

    if categoria_origen.lower() == categoria_destino.lower():
        flash(
            'La categoría destino debe ser diferente a la categoría a eliminar.', 'warning')
        return redirect(url_for('admin_bp.productos'))

    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT COUNT(*)
        FROM (
            SELECT DISTINCT Categoria
            FROM productos
            WHERE Categoria IS NOT NULL AND TRIM(Categoria) <> ''
        ) t
    ''')
    total_categorias = int(cur.fetchone()[0] or 0)

    if total_categorias <= 1:
        cur.close()
        flash('No puedes eliminar la única categoría activa. Crea o usa otra categoría primero.', 'warning')
        return redirect(url_for('admin_bp.productos'))

    cur.execute('''
        UPDATE productos
        SET Categoria = %s
        WHERE Categoria = %s
    ''', (categoria_destino, categoria_origen))
    mysql.connection.commit()
    cambios = cur.rowcount
    cur.close()

    if cambios > 0:
        flash(
            f'Categoría "{categoria_origen}" eliminada. {cambios} producto(s) movido(s) a "{categoria_destino}".',
            'success'
        )
    else:
        flash('No se encontraron productos en esa categoría para eliminar.', 'warning')

    return redirect(url_for('admin_bp.productos'))


@admin_bp.route('/categorias/fusionar', methods=['POST'])
@admin_required
def fusionar_categorias_producto():
    categorias_origen_raw = request.form.getlist('categorias_origen[]')
    categoria_destino = (request.form.get('categoria_destino') or '').strip()

    categorias_origen = []
    seen = set()
    for c in categorias_origen_raw:
        val = (c or '').strip()
        if not val:
            continue
        key = val.lower()
        if key in seen:
            continue
        seen.add(key)
        categorias_origen.append(val)

    if len(categorias_origen) < 2 or not categoria_destino:
        flash(
            'Debes seleccionar al menos dos categorías de origen y escribir la categoría destino.',
            'warning'
        )
        return redirect(url_for('admin_bp.productos'))

    cur = mysql.connection.cursor()
    placeholders = ', '.join(['%s'] * len(categorias_origen))
    query = f'''
        UPDATE productos
        SET Categoria = %s
        WHERE Categoria IN ({placeholders})
    '''
    cur.execute(query, [categoria_destino] + categorias_origen)
    mysql.connection.commit()
    cambios = cur.rowcount
    cur.close()

    origen_texto = ', '.join([f'"{c}"' for c in categorias_origen])

    if cambios > 0:
        flash(
            f'Categorías {origen_texto} fusionadas en "{categoria_destino}" ({cambios} producto(s)).',
            'success'
        )
    else:
        flash('No se encontraron productos en las categorías seleccionadas para fusionar.', 'warning')

    return redirect(url_for('admin_bp.productos'))


@admin_bp.route('/banners')
@admin_required
def banners():
    _ensure_home_content_tables()
    cur = mysql.connection.cursor()

    cur.execute('''
        SELECT id, title, desktop_image, mobile_image, sort_order, enabled
        FROM home_banners
        ORDER BY sort_order ASC, id ASC
    ''')
    banners_home = cur.fetchall()

    cur.execute('''
        SELECT id, brand_name, title, desktop_image, mobile_image, sort_order, enabled
        FROM brand_banners
        ORDER BY brand_name ASC, sort_order ASC, id ASC
    ''')
    brand_banners = cur.fetchall()

    cur.close()

    return render_template(
        "Vistas_admin/banners.html",
        banners=banners_home,
        brand_banners=brand_banners,
        brand_options=BRAND_OPTIONS
    )


@admin_bp.route('/add_producto', methods=['POST'])
@admin_required
def add_producto():
    _ensure_home_content_tables()
    # Datos básicos del formulario
    nombre = request.form['Nombre']
    descripcion = request.form['Descripcion']
    precio = request.form['Precio']
    categoria = request.form['Categoria']
    stock = request.form['Stock']
    idmarca = request.form['Marca']  # ID_Proveedor
    home_section = request.form.get('HomeSection', 'ninguno')
    home_order = request.form.get('HomeOrder', '999')
    home_enabled = request.form.get('HomeEnabled', '0')

    # Promoción es opcional - si viene vacío, será None
    id_promocion = request.form.get('ID_PromocionFK')
    id_promocion = id_promocion if id_promocion and id_promocion != '' else None

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
        folder_path = os.path.join(
            app.config['UPLOAD_FOLDER'], folder_name)
        os.makedirs(folder_path, exist_ok=True)

        file.save(os.path.join(folder_path, filename))

        # Guardamos la ruta relativa que vas a usar en las cards
        filename = f"/{folder_name}/{filename}"

    # Insertar el producto en la base de datos
    cur.execute(
        '''INSERT INTO productos
           (Nombre, Descripcion, Categoria, Precio,
            Stock, Imagen, ID_ProveedorFK, ID_PromocionFK)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
        (nombre, descripcion, categoria, precio,
         stock, filename, idmarca, id_promocion)
    )
    product_id = cur.lastrowid
    _guardar_config_producto_home(cur, product_id,
                                  home_section, home_order, home_enabled)
    mysql.connection.commit()
    cur.close()

    flash('Producto agregado correctamente', "success")
    return redirect(url_for('admin_bp.productos'))


@admin_bp.route('/edit_producto/<product_id>')
@admin_required
def edit_producto(product_id):
    _ensure_home_content_tables()
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
            ID_PromocionFK,
            COALESCE((SELECT section_name FROM home_product_config WHERE product_id = productos.ID_Producto), 'ninguno') AS HomeSection,
            COALESCE((SELECT sort_order FROM home_product_config WHERE product_id = productos.ID_Producto), 999) AS HomeOrder,
            COALESCE((SELECT enabled FROM home_product_config WHERE product_id = productos.ID_Producto), 0) AS HomeEnabled
        FROM productos
        WHERE ID_Producto = %s
    ''', (product_id,))
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
        'promocion': data[7],
        'homesection': data[8],
        'homeorder': data[9],
        'homeenabled': data[10]
    }

    return jsonify(product_data)


@admin_bp.route('/update_producto/<product_id>', methods=['POST'])
@admin_required
def update_producto(product_id):
    _ensure_home_content_tables()
    nombre = request.form['Nombre']
    descripcion = request.form['Descripcion']
    precio = request.form['Precio']
    categoria = request.form['Categoria']
    stock = request.form['Stock']
    idmarca = request.form['Marca']  # ID_Proveedor
    home_section = request.form.get('HomeSection', 'ninguno')
    home_order = request.form.get('HomeOrder', '999')
    home_enabled = request.form.get('HomeEnabled', '0')

    # Promoción es opcional - si viene vacío, será None
    id_promocion = request.form.get('ID_PromocionFK')
    id_promocion = id_promocion if id_promocion and id_promocion != '' else None

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
        folder_path = os.path.join(
            app.config['UPLOAD_FOLDER'], folder_name)
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
            (nombre, descripcion, categoria, precio,
             stock, filename, idmarca, id_promocion, product_id)
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
            (nombre, descripcion, categoria, precio,
             stock, idmarca, id_promocion, product_id)
        )

    _guardar_config_producto_home(cur, product_id,
                                  home_section, home_order, home_enabled)
    mysql.connection.commit()
    cur.close()

    flash('Producto actualizado correctamente', "success")
    return redirect(url_for('admin_bp.productos'))


@admin_bp.route('/add_banner_home', methods=['POST'])
@admin_required
def add_banner_home():
    _ensure_home_content_tables()
    title = request.form.get('title', '').strip()
    sort_order = request.form.get('sort_order', '0')
    enabled = 1 if request.form.get('enabled') == '1' else 0

    desktop_path = _save_banner_image(
        request.files.get('desktop_image'), 'desktop')
    mobile_path = _save_banner_image(
        request.files.get('mobile_image'), 'mobile')

    if not desktop_path and not mobile_path:
        flash('Debes subir al menos una imagen para el banner', 'warning')
        return redirect(url_for('admin_bp.banners'))

    try:
        sort_order = int(sort_order)
    except Exception:
        sort_order = 0

    cur = mysql.connection.cursor()
    cur.execute('''
        INSERT INTO home_banners (title, desktop_image, mobile_image, sort_order, enabled)
        VALUES (%s, %s, %s, %s, %s)
    ''', (title, desktop_path, mobile_path, sort_order, enabled))
    mysql.connection.commit()
    cur.close()

    flash('Banner agregado correctamente', 'success')
    return redirect(url_for('admin_bp.banners'))


@admin_bp.route('/update_banner_home/<int:banner_id>', methods=['POST'])
@admin_required
def update_banner_home(banner_id):
    _ensure_home_content_tables()
    title = request.form.get('title', '').strip()
    sort_order = request.form.get('sort_order', '0')
    enabled = 1 if request.form.get('enabled') == '1' else 0

    try:
        sort_order = int(sort_order)
    except Exception:
        sort_order = 0

    new_desktop = _save_banner_image(
        request.files.get('desktop_image'), 'desktop')
    new_mobile = _save_banner_image(
        request.files.get('mobile_image'), 'mobile')

    cur = mysql.connection.cursor()
    if new_desktop and new_mobile:
        cur.execute('''
            UPDATE home_banners
            SET title=%s, desktop_image=%s, mobile_image=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (title, new_desktop, new_mobile, sort_order, enabled, banner_id))
    elif new_desktop:
        cur.execute('''
            UPDATE home_banners
            SET title=%s, desktop_image=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (title, new_desktop, sort_order, enabled, banner_id))
    elif new_mobile:
        cur.execute('''
            UPDATE home_banners
            SET title=%s, mobile_image=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (title, new_mobile, sort_order, enabled, banner_id))
    else:
        cur.execute('''
            UPDATE home_banners
            SET title=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (title, sort_order, enabled, banner_id))

    mysql.connection.commit()
    cur.close()

    flash('Banner actualizado correctamente', 'success')
    return redirect(url_for('admin_bp.banners'))


@admin_bp.route('/delete_banner_home/<int:banner_id>', methods=['POST'])
@admin_required
def delete_banner_home(banner_id):
    _ensure_home_content_tables()
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM home_banners WHERE id = %s', (banner_id,))
    mysql.connection.commit()
    cur.close()
    flash('Banner eliminado', 'success')
    return redirect(url_for('admin_bp.banners'))


@admin_bp.route('/add_banner_brand', methods=['POST'])
@admin_required
def add_banner_brand():
    _ensure_home_content_tables()
    brand_name = request.form.get('brand_name', '').strip()
    title = request.form.get('title', '').strip()
    sort_order = request.form.get('sort_order', '0')
    enabled = 1 if request.form.get('enabled') == '1' else 0

    if brand_name not in BRAND_OPTIONS:
        flash('Marca de banner no válida', 'warning')
        return redirect(url_for('admin_bp.banners'))

    desktop_path = _save_banner_image(
        request.files.get('desktop_image'), 'marcas_desktop')
    mobile_path = _save_banner_image(
        request.files.get('mobile_image'), 'marcas_mobile')

    if not desktop_path and not mobile_path:
        flash('Debes subir al menos una imagen para el banner de marca', 'warning')
        return redirect(url_for('admin_bp.banners'))

    try:
        sort_order = int(sort_order)
    except Exception:
        sort_order = 0

    cur = mysql.connection.cursor()
    cur.execute('''
        INSERT INTO brand_banners (brand_name, title, desktop_image, mobile_image, sort_order, enabled)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (brand_name, title, desktop_path, mobile_path, sort_order, enabled))
    mysql.connection.commit()
    cur.close()

    flash('Banner de marca agregado correctamente', 'success')
    return redirect(url_for('admin_bp.banners'))


@admin_bp.route('/update_banner_brand/<int:banner_id>', methods=['POST'])
@admin_required
def update_banner_brand(banner_id):
    _ensure_home_content_tables()
    brand_name = request.form.get('brand_name', '').strip()
    title = request.form.get('title', '').strip()
    sort_order = request.form.get('sort_order', '0')
    enabled = 1 if request.form.get('enabled') == '1' else 0

    if brand_name not in BRAND_OPTIONS:
        flash('Marca de banner no válida', 'warning')
        return redirect(url_for('admin_bp.banners'))

    try:
        sort_order = int(sort_order)
    except Exception:
        sort_order = 0

    new_desktop = _save_banner_image(
        request.files.get('desktop_image'), 'marcas_desktop')
    new_mobile = _save_banner_image(
        request.files.get('mobile_image'), 'marcas_mobile')

    cur = mysql.connection.cursor()
    if new_desktop and new_mobile:
        cur.execute('''
            UPDATE brand_banners
            SET brand_name=%s, title=%s, desktop_image=%s, mobile_image=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (brand_name, title, new_desktop, new_mobile, sort_order, enabled, banner_id))
    elif new_desktop:
        cur.execute('''
            UPDATE brand_banners
            SET brand_name=%s, title=%s, desktop_image=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (brand_name, title, new_desktop, sort_order, enabled, banner_id))
    elif new_mobile:
        cur.execute('''
            UPDATE brand_banners
            SET brand_name=%s, title=%s, mobile_image=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (brand_name, title, new_mobile, sort_order, enabled, banner_id))
    else:
        cur.execute('''
            UPDATE brand_banners
            SET brand_name=%s, title=%s, sort_order=%s, enabled=%s
            WHERE id=%s
        ''', (brand_name, title, sort_order, enabled, banner_id))

    mysql.connection.commit()
    cur.close()

    flash('Banner de marca actualizado correctamente', 'success')
    return redirect(url_for('admin_bp.banners'))


@admin_bp.route('/delete_banner_brand/<int:banner_id>', methods=['POST'])
@admin_required
def delete_banner_brand(banner_id):
    _ensure_home_content_tables()
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM brand_banners WHERE id = %s', (banner_id,))
    mysql.connection.commit()
    cur.close()
    flash('Banner de marca eliminado', 'success')
    return redirect(url_for('admin_bp.banners'))


# -------------------------------------- promociones/DESCUENTOS ----------------------------------------


@admin_bp.route('/promociones')
@admin_required
def promociones():
    cur = mysql.connection.cursor()
    try:
        # Esquema actual con columna Nombre.
        cur.execute('''
            SELECT ID_Promocion, Nombre, Descuento, Fecha_Inicial, Fecha_Final
            FROM promociones
            ORDER BY Fecha_Inicial DESC
        ''')
        data_raw = cur.fetchall()
    except Exception:
        # Compatibilidad con esquema anterior sin columna Nombre.
        cur.execute('''
            SELECT ID_Promocion, Descuento, Fecha_Inicial, Fecha_Final
            FROM promociones
            ORDER BY Fecha_Inicial DESC
        ''')
        data_old = cur.fetchall()
        data_raw = [(r[0], "", r[1], r[2], r[3]) for r in data_old]

    data = [
        {
            "id": r[0],
            "nombre": r[1] or "Promoción",
            "descuento": r[2],
            "fecha_inicial": r[3],
            "fecha_final": r[4],
            "fecha_inicial_iso": r[3].strftime('%Y-%m-%d') if hasattr(r[3], 'strftime') else str(r[3]),
            "fecha_final_iso": r[4].strftime('%Y-%m-%d') if hasattr(r[4], 'strftime') else str(r[4]),
            "fecha_inicial_fmt": r[3].strftime('%d/%m/%Y') if hasattr(r[3], 'strftime') else str(r[3]),
            "fecha_final_fmt": r[4].strftime('%d/%m/%Y') if hasattr(r[4], 'strftime') else str(r[4])
        }
        for r in data_raw
    ]

    # Lista de promociones para el <select>
    try:
        cur.execute('''
            SELECT ID_Promocion, Nombre, Descuento, Fecha_Inicial, Fecha_Final
            FROM promociones
            WHERE Fecha_Inicial > CURDATE()
            ORDER BY Fecha_Inicial ASC
        ''')
        promocionesf_raw = cur.fetchall()
    except Exception:
        cur.execute('''
            SELECT ID_Promocion, Descuento, Fecha_Inicial, Fecha_Final
            FROM promociones
            WHERE Fecha_Inicial > CURDATE()
            ORDER BY Fecha_Inicial ASC
        ''')
        promos_old = cur.fetchall()
        promocionesf_raw = [(r[0], "", r[1], r[2], r[3]) for r in promos_old]

    promocionesf = [
        {
            "id": r[0],
            "nombre": r[1] or "Promoción",
            "descuento": r[2],
            "fecha_inicial": r[3],
            "fecha_final": r[4],
            "fecha_inicial_iso": r[3].strftime('%Y-%m-%d') if hasattr(r[3], 'strftime') else str(r[3]),
            "fecha_final_iso": r[4].strftime('%Y-%m-%d') if hasattr(r[4], 'strftime') else str(r[4]),
            "fecha_inicial_fmt": r[3].strftime('%d/%m/%Y') if hasattr(r[3], 'strftime') else str(r[3]),
            "fecha_final_fmt": r[4].strftime('%d/%m/%Y') if hasattr(r[4], 'strftime') else str(r[4])
        }
        for r in promocionesf_raw
    ]

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
    nombre = request.form.get('Nombre', '').strip()
    descuento = request.form['Descuento']
    fechai = request.form['Fecha_Inicial']
    fechaf = request.form['Fecha_Final']

    if not nombre:
        flash('El nombre de la promoción es obligatorio', "error")
        return redirect(url_for('admin_bp.promociones'))

    cur = mysql.connection.cursor()
    try:
        cur.execute('''INSERT INTO promociones (Nombre, Descuento, Fecha_Inicial, Fecha_Final)
                        VALUES (%s, %s, %s, %s)''', (nombre, descuento, fechai, fechaf))
    except Exception:
        # Compatibilidad con esquema viejo sin columna Nombre.
        cur.execute('''INSERT INTO promociones (Descuento, Fecha_Inicial, Fecha_Final)
                        VALUES (%s, %s, %s)''', (descuento, fechai, fechaf))
    mysql.connection.commit()
    cur.close()
    flash('Promoción agregada correctamente', "success")
    return redirect(url_for('admin_bp.promociones'))


@admin_bp.route('/edit_promocion/<promo_id>')
@admin_required
def edit_promocion(promo_id):
    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT ID_Promocion, Nombre, Descuento, Fecha_Inicial, Fecha_Final
            FROM promociones
            WHERE ID_Promocion = %s
        ''', (promo_id,))
        data = cur.fetchone()
        if data:
            user_data = {
                'id': data[0],
                'nombre': data[1],
                'descuento': data[2],
                'fechai': data[3].strftime('%Y-%m-%d'),
                'fechaf': data[4].strftime('%Y-%m-%d')
            }
            return jsonify(user_data)
    except Exception:
        pass

    cur.execute(
        'SELECT ID_Promocion, Descuento, Fecha_Inicial, Fecha_Final FROM promociones WHERE ID_Promocion = %s', (promo_id,))
    data = cur.fetchone()
    if data:
        user_data = {
            'id': data[0],
            'nombre': '',
            'descuento': data[1],
            'fechai': data[2],
            'fechaf': data[3]
        }
        return jsonify(user_data)
    return jsonify({'error': 'Promoción no encontrada'}), 404


@admin_bp.route('/update_promocion/<promo_id>', methods=['POST'])
@admin_required
def update_promocion(promo_id):
    if request.method == 'POST':
        nombre = request.form.get('Nombre', '').strip()
        descuento = request.form['Descuento']
        fechai = request.form['Fecha_Inicial']
        fechaf = request.form['Fecha_Final']

        if not nombre:
            flash('El nombre de la promoción es obligatorio', "error")
            return redirect(url_for('admin_bp.promociones'))

        cur = mysql.connection.cursor()
        try:
            cur.execute('''UPDATE promociones
                            SET Nombre = %s, Descuento = %s, Fecha_Inicial = %s, Fecha_Final = %s
                            WHERE ID_Promocion = %s''',
                        (nombre, descuento, fechai, fechaf, promo_id))
        except Exception:
            # Compatibilidad con esquema viejo sin columna Nombre.
            cur.execute('''UPDATE promociones
                            SET Descuento = %s, Fecha_Inicial = %s, Fecha_Final = %s
                            WHERE ID_Promocion = %s''',
                        (descuento, fechai, fechaf, promo_id))
        mysql.connection.commit()
        cur.close()
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
    cur.execute(
        'SELECT * FROM usuarios WHERE Rol = "Cliente" ORDER BY ID_Usuario DESC')
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
def edit_usuario(user_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE ID_Usuario = %s', (user_id,))
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


@admin_bp.route('/update_usuario/<user_id>', methods=['POST'])
def update_usuario(user_id):
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
                        WHERE ID_Usuario = %s''',
                    (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, user_id))
        mysql.connection.commit()
        flash('Usuario actualizado correctamente', "success")
        return redirect(url_for('admin_bp.usuarios'))


@admin_bp.route('/delete_usuario/<user_id>', methods=['POST'])
def delete_usuario(user_id):
    cur = mysql.connection.cursor()
    # Solo actualiza si el usuario está activo
    cur.execute('CALL eliminarusuario(%s)', (user_id,))
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
    cur.execute(
        'SELECT * FROM usuarios WHERE Rol = "Admin" ORDER BY ID_Usuario DESC')
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


@admin_bp.route('/edit_admin/<admin_id>')
def edit_admin(admin_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE ID_Usuario = %s', (admin_id,))
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


@admin_bp.route('/update_admin/<admin_id>', methods=['POST'])
def update_admin(admin_id):
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
                        WHERE ID_Usuario = %s''',
                    (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, admin_id))
        mysql.connection.commit()
        flash('Usuario actualizado correctamente', "success")
        return redirect(url_for('admin_bp.admin'))


@admin_bp.route('/delete_admin/<admin_id>', methods=['POST'])
def delete_admin(admin_id):
    cur = mysql.connection.cursor()
    # Solo actualiza si el usuario está activo
    cur.execute('CALL eliminarusuario(%s)', (admin_id,))
    mysql.connection.commit()

    if cur.rowcount > 0:
        flash('Usuario inactivado correctamente', "success")
    else:
        flash('El usuario ya estaba inactivo o no existe', "warning")

    return redirect(url_for('admin_bp.admin'))
# -------------------------------------- pedidos -----------------------------------------


ESTADOS_PEDIDO = [
    'EN TRÁNSITO',
    'DESPACHADO',
    'ENTREGADO',
    'PENDIENTE CONFIRMAR',
    'CONFIRMADO',
    'EN NOVEDAD',
    'EN DEVOLUCIÓN',
    'DEVUELTO A BODEGA',
    'ANULADO',
    'CANCELADO',
]


def _normalizar_estado_pedido(estado_pago, metodo_pago):
    estado = (estado_pago or '').strip().upper()

    if estado in ESTADOS_PEDIDO:
        return estado

    mapeo_legacy = {
        'PENDING': 'PENDIENTE CONFIRMAR',
        'PENDING_MP': 'PENDIENTE CONFIRMAR',
        'COD_PENDIENTE_ENVIO': 'PENDIENTE CONFIRMAR',
        'APPROVED': 'CONFIRMADO',
        'REJECTED': 'ANULADO',
    }

    if estado in mapeo_legacy:
        return mapeo_legacy[estado]

    if (metodo_pago or '').upper() == 'COD':
        return 'PENDIENTE CONFIRMAR'

    return 'PENDIENTE CONFIRMAR'


def _estado_pedido_display(estado_pago, metodo_pago):
    return _normalizar_estado_pedido(estado_pago, metodo_pago)


def _estado_pedido_clase(estado_display):
    clases = {
        'EN TRÁNSITO': 'estado-en-transito',
        'DESPACHADO': 'estado-despachado',
        'ENTREGADO': 'estado-entregado',
        'PENDIENTE CONFIRMAR': 'estado-pendiente-confirmar',
        'CONFIRMADO': 'estado-confirmado',
        'EN NOVEDAD': 'estado-en-novedad',
        'EN DEVOLUCIÓN': 'estado-en-devolucion',
        'DEVUELTO A BODEGA': 'estado-devuelto-bodega',
        'ANULADO': 'estado-anulado',
        'CANCELADO': 'estado-cancelado',
    }
    return clases.get(estado_display, 'estado-pendiente-confirmar')


def _obtener_pedidos_admin():
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT
            p.ID_Venta                                  AS Num_venta,
            p.Fecha                                     AS Fecha,
            u.Nombre                                    AS Nombre_Cliente,
            u.Apellido                                  AS Apellido_Cliente,
            COALESCE(u.Telefono, '')                    AS Telefono_Cliente,
            COALESCE(u.Correo, '')                      AS Correo_Cliente,
            COALESCE(u.Ciudad, '')                      AS Ciudad_Cliente,
            COALESCE(u.Direccion, '')                   AS Direccion_Cliente,
            COALESCE(u.N_Documento, u.Documento, '')    AS Documento_Cliente,
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
            u.Telefono,
            u.Correo,
            u.Ciudad,
            u.Direccion,
            u.N_Documento,
            u.Documento,
            p.Total,
            pg.estado,
            pg.metodo
        ORDER BY p.Fecha DESC, p.ID_Venta DESC
    ''')
    rows = cur.fetchall()
    cur.close()

    pedidos = []
    for row in rows:
        estado_display = _estado_pedido_display(row[11], row[12])
        fecha_obj = row[1]
        if hasattr(fecha_obj, 'strftime'):
            fecha_iso = fecha_obj.strftime('%Y-%m-%d')
            fecha_label = fecha_obj.strftime('%d/%m/%Y %H:%M')
            fecha_dia_label = fecha_obj.strftime('%d/%m/%Y')
        else:
            fecha_iso = str(fecha_obj)[:10]
            fecha_label = str(fecha_obj)
            fecha_dia_label = fecha_iso

        pedidos.append({
            'id': row[0],
            'fecha_obj': fecha_obj,
            'fecha_iso': fecha_iso,
            'fecha_label': fecha_label,
            'fecha_dia_label': fecha_dia_label,
            'nombre_cliente': row[2],
            'apellido_cliente': row[3],
            'cliente': f"{row[2]} {row[3]}",
            'telefono': row[4],
            'correo': row[5],
            'ciudad': row[6],
            'direccion': row[7],
            'documento': row[8],
            'total': float(row[9] or 0),
            'total_productos': int(row[10] or 0),
            'estado_pago': row[11],
            'metodo_pago': row[12],
            'estado_display': estado_display,
            'estado_clase': _estado_pedido_clase(estado_display),
        })

    return pedidos


def _filtrar_pedidos(pedidos, estado_filtro='TODOS', fecha_filtro='', texto_busqueda=''):
    estado_filtro = (estado_filtro or 'TODOS').upper()
    texto_busqueda = (texto_busqueda or '').strip().lower()
    fecha_filtro = (fecha_filtro or '').strip()

    def _cumple_estado(pedido):
        if estado_filtro == 'TODOS':
            return True
        return pedido['estado_display'] == estado_filtro

    filtrados = []
    for pedido in pedidos:
        if fecha_filtro and pedido['fecha_iso'] != fecha_filtro:
            continue

        if not _cumple_estado(pedido):
            continue

        if texto_busqueda:
            searchable = " ".join([
                str(pedido['id']),
                pedido['cliente'],
                pedido['telefono'] or '',
                pedido['correo'] or '',
                pedido['documento'] or '',
                pedido['estado_display'] or ''
            ]).lower()
            if texto_busqueda not in searchable:
                continue

        filtrados.append(pedido)

    return filtrados


@admin_bp.route('/pedidos')
@admin_required
def pedidos_view():
    estado_filtro = (request.args.get('estado') or 'TODOS').upper()
    fecha_filtro = (request.args.get('fecha') or '').strip()
    texto_busqueda = (request.args.get('q') or '').strip()

    if estado_filtro != 'TODOS' and estado_filtro not in ESTADOS_PEDIDO:
        estado_filtro = 'TODOS'

    pedidos = _obtener_pedidos_admin()
    data = _filtrar_pedidos(pedidos, estado_filtro,
                            fecha_filtro, texto_busqueda)

    pedidos_por_dia_map = defaultdict(list)
    for pedido in data:
        pedidos_por_dia_map[pedido['fecha_iso']].append(pedido)

    pedidos_por_dia = []
    for fecha_iso in sorted(pedidos_por_dia_map.keys(), reverse=True):
        grupo = pedidos_por_dia_map[fecha_iso]
        pedidos_por_dia.append({
            'fecha_iso': fecha_iso,
            'fecha_label': grupo[0]['fecha_dia_label'] if grupo else fecha_iso,
            'cantidad': len(grupo),
            'total': sum(p['total'] for p in grupo),
            'pedidos': grupo
        })

    resumen = {
        'total_pedidos': len(data),
        'total_ingresos': sum(p['total'] for p in data),
        'pendientes': sum(1 for p in data if p['estado_display'] == 'PENDIENTE CONFIRMAR'),
        'confirmados': sum(1 for p in data if p['estado_display'] == 'CONFIRMADO'),
        'en_transito': sum(1 for p in data if p['estado_display'] == 'EN TRÁNSITO'),
        'entregados': sum(1 for p in data if p['estado_display'] == 'ENTREGADO'),
        'anulados': sum(1 for p in data if p['estado_display'] in ['ANULADO', 'CANCELADO'])
    }

    # Lista de clientes para el modal "Nueva Venta"
    cur = mysql.connection.cursor()
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
        pedidos_por_dia=pedidos_por_dia,
        resumen=resumen,
        filtros={
            'estado': estado_filtro,
            'fecha': fecha_filtro,
            'q': texto_busqueda
        },
        estados_pedido=ESTADOS_PEDIDO,
        usuarios=usuarios_list,
        productos=productos_disponibles
    )


@admin_bp.route('/pedidos/actualizar_estado/<int:venta_id>', methods=['POST'])
@admin_required
def actualizar_estado_pedido(venta_id):
    nuevo_estado = (request.form.get('estado') or '').strip().upper()
    estado_filtro = (request.form.get('estado_filtro')
                     or 'TODOS').strip().upper()
    fecha_filtro = (request.form.get('fecha_filtro') or '').strip()
    texto_busqueda = (request.form.get('q_filtro') or '').strip()

    if nuevo_estado not in ESTADOS_PEDIDO:
        flash('Estado no válido', 'error')
        return redirect(url_for('admin_bp.pedidos_view', estado=estado_filtro, fecha=fecha_filtro, q=texto_busqueda))

    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT ReferenciaPago, ID_UsuarioFK, Total
            FROM pedidos
            WHERE ID_Venta = %s
        ''', (venta_id,))
        pedido = cur.fetchone()

        if not pedido:
            flash('Pedido no encontrado', 'error')
            return redirect(url_for('admin_bp.pedidos_view', estado=estado_filtro, fecha=fecha_filtro, q=texto_busqueda))

        referencia, user_id, total = pedido

        if not referencia:
            referencia = uuid.uuid4().hex
            cur.execute(
                'UPDATE pedidos SET ReferenciaPago = %s WHERE ID_Venta = %s', (referencia, venta_id))

        total_cents = int(round(float(total or 0) * 100))
        cur.execute('''
            INSERT INTO pagos (
                referencia, user_id, total_cents, estado, metodo
            )
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE estado = VALUES(estado)
        ''', (referencia, user_id, total_cents, nuevo_estado, 'COD'))

        mysql.connection.commit()
        flash('Estado actualizado correctamente', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error al actualizar estado: {str(e)}', 'error')
    finally:
        cur.close()

    return redirect(url_for('admin_bp.pedidos_view', estado=estado_filtro, fecha=fecha_filtro, q=texto_busqueda))


@admin_bp.route('/pedidos/resumen_pdf', methods=['POST'])
@admin_required
def descargar_resumen_pedidos_pdf():
    estado_filtro = (request.form.get('estado') or 'TODOS').upper()
    fecha_filtro = (request.form.get('fecha') or '').strip()
    texto_busqueda = (request.form.get('q') or '').strip()
    export_type = (request.form.get('export_type')
                   or 'selected').strip().lower()

    pedidos_filtrados = _filtrar_pedidos(
        _obtener_pedidos_admin(), estado_filtro, fecha_filtro, texto_busqueda)

    if export_type == 'day':
        fecha_objetivo = fecha_filtro or datetime.now().strftime('%Y-%m-%d')
        pedidos_exportar = [
            p for p in pedidos_filtrados if p['fecha_iso'] == fecha_objetivo]
    else:
        selected_raw = (request.form.get('selected_ids') or '').strip()
        selected_ids = []
        if selected_raw:
            for val in selected_raw.split(','):
                val = val.strip()
                if val.isdigit():
                    selected_ids.append(int(val))
        pedidos_exportar = [
            p for p in pedidos_filtrados if p['id'] in set(selected_ids)]

    if not pedidos_exportar:
        flash('No hay pedidos para exportar con ese criterio', 'warning')
        return redirect(url_for(
            'admin_bp.pedidos_view',
            estado=estado_filtro,
            fecha=fecha_filtro,
            q=texto_busqueda
        ))

    pedidos_exportar = sorted(
        pedidos_exportar, key=lambda p: (p['fecha_iso'], p['id']))
    ids = [p['id'] for p in pedidos_exportar]

    cur = mysql.connection.cursor()
    placeholders = ','.join(['%s'] * len(ids))
    cur.execute(f'''
        SELECT
            dv.ID_VentaFK,
            p.Nombre,
            dv.Cantidad_p,
            ROUND(dv.SubTotal / NULLIF(dv.Cantidad_p, 0), 0) AS Precio_Unitario,
            dv.SubTotal
        FROM detalles_venta dv
        JOIN productos p ON p.ID_Producto = dv.ID_ProductoFK
        WHERE dv.ID_VentaFK IN ({placeholders})
        ORDER BY dv.ID_VentaFK ASC, p.Nombre ASC
    ''', tuple(ids))
    detalle_rows = cur.fetchall()
    cur.close()

    detalles_por_venta = defaultdict(list)
    for d in detalle_rows:
        detalles_por_venta[d[0]].append({
            'producto': d[1],
            'cantidad': int(d[2] or 0),
            'precio_unitario': float(d[3] or 0),
            'subtotal': float(d[4] or 0)
        })

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=35,
        leftMargin=35,
        topMargin=40,
        bottomMargin=30
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name='PedidosTitulo',
        fontSize=16,
        alignment=1,
        textColor=colors.HexColor('#C1416D'),
        fontName='Helvetica-Bold',
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        name='PedidosSubtitulo',
        fontSize=10,
        alignment=1,
        textColor=colors.HexColor('#444444'),
        spaceAfter=16
    )

    body_style = ParagraphStyle(
        name='PedidosBody',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#222222')
    )

    elements.append(Paragraph('Resumen de Pedidos', title_style))
    elements.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} - Total pedidos: {len(pedidos_exportar)}",
        subtitle_style
    ))

    for pedido in pedidos_exportar:
        elements.append(Paragraph(
            f"<b>Pedido #{pedido['id']}</b> - {pedido['fecha_label']} - Estado: {pedido['estado_display']}",
            body_style
        ))
        elements.append(Paragraph(
            (
                f"<b>Cliente:</b> {pedido['cliente']}<br/>"
                f"<b>Documento:</b> {pedido['documento'] or 'N/A'}<br/>"
                f"<b>Teléfono:</b> {pedido['telefono'] or 'N/A'}<br/>"
                f"<b>Correo:</b> {pedido['correo'] or 'N/A'}<br/>"
                f"<b>Ciudad:</b> {pedido['ciudad'] or 'N/A'}<br/>"
                f"<b>Dirección:</b> {pedido['direccion'] or 'N/A'}"
            ),
            body_style
        ))
        elements.append(Spacer(1, 6))

        detalle = detalles_por_venta.get(pedido['id'], [])
        if detalle:
            table_data = [[
                Paragraph('<b>Producto</b>', body_style),
                Paragraph('<b>Cant.</b>', body_style),
                Paragraph('<b>Precio Unit.</b>', body_style),
                Paragraph('<b>Subtotal</b>', body_style),
            ]]

            for item in detalle:
                table_data.append([
                    Paragraph(item['producto'], body_style),
                    Paragraph(str(item['cantidad']), body_style),
                    Paragraph(f"${item['precio_unitario']:,.0f}".replace(
                        ',', '.'), body_style),
                    Paragraph(f"${item['subtotal']:,.0f}".replace(
                        ',', '.'), body_style),
                ])

            tabla = Table(table_data, colWidths=[250, 55, 95, 95])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDB4CD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#B5B5B5')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(tabla)
        else:
            elements.append(
                Paragraph('Sin líneas de detalle para este pedido.', body_style))

        elements.append(Paragraph(
            f"<b>Total pedido:</b> ${pedido['total']:,.0f}".replace(',', '.'),
            body_style
        ))
        elements.append(Spacer(1, 14))

    doc.build(elements)
    buffer.seek(0)

    sufijo = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre = f"resumen_pedidos_{sufijo}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nombre, mimetype='application/pdf')


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
                    flash(
                        f'Producto "{nombre_producto}" no encontrado', "error")
                    return redirect(url_for('admin_bp.pedidos_view'))

                producto_id = producto_info[0]
                precio_base = int(producto_info[1])
                stock_disponible = int(producto_info[2])
                nombre_producto_db = producto_info[3]
                descuento = producto_info[4] if producto_info[4] else 0

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
            #   estado = 'PENDIENTE CONFIRMAR'
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
                # mp_preference_id (esto es para MP, aquí no aplica)
                None,
                None,              # mp_payment_id (esto es para MP)
                'PENDIENTE CONFIRMAR',  # estado inicial del flujo operativo
                # raw_json (puedes guardar info extra si quieres)
                None,
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
    try:
        # Esquema legado: incluye fechas de rango para mostrar en tabla.
        cur.execute(
            "SELECT id, fecha_generacion, fecha_inicio, fecha_fin FROM reportes ORDER BY id DESC")
        data = cur.fetchall()
    except Exception:
        # Esquema nuevo: mantiene metadatos en columnas de texto.
        cur.execute(
            "SELECT id, Fecha_Creacion, Titulo, Ruta_Archivo FROM reportes ORDER BY id DESC")
        data = cur.fetchall()
    finally:
        cur.close()

    return render_template("Vistas_admin/reportes.html", reportes=data)


@admin_bp.route('/generar_reporte', methods=['POST'])
@admin_required
def generar_reporte():
    cur = None
    try:
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        if not fecha_inicio or not fecha_fin:
            flash("Debes seleccionar ambas fechas", "error")
            return redirect(url_for("admin_bp.reportes"))

        fecha_fin_dt = datetime.strptime(
            fecha_fin, "%Y-%m-%d") + timedelta(days=1)
        fecha_fin = fecha_fin_dt.strftime("%Y-%m-%d")

        # Asegura conexión viva antes de consultar datos.
        mysql.connection.ping(True)
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
        cur.close()
        cur = None

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
        logo_path = os.path.join(
            os.getcwd(), "static", "imagenes", "logos", "logo.png")

        if os.path.exists(logo_path):
            logo = Image(logo_path, width=120, height=80)
            # Ajustar sin deformar si la imagen es más grande:
            # limita ancho/alto máximo, preserva relación de aspecto
            logo._restrictSize(120, 80)
        else:
            # Si no existe el logo, crear un Paragraph de aviso pequeño para mantener estructura
            # espacio en blanco para que la columna exista
            logo = Paragraph(" ", normal_style)

        # Preparar el título como Paragraph (usar estilo Title o uno personalizado)
        titulo_paragraph = Paragraph("<b>Reporte de pedidos</b><br/><small>Periodo: {}</small>".format(
            f"{fecha_inicio} a {fecha_fin}"
        ), styles["Title"])

        # Crear una tabla con 1 fila y 2 columnas: [logo, titulo]
        header_table = Table([[logo, titulo_paragraph]], colWidths=[
                             130, 420])  # ajustar colWidths según tu página

        # Estilos: quitar borde, alinear texto a la izquierda y centrar verticalmente
        header_table.setStyle(TableStyle([
            # centra verticalmente ambos items
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            # quitar padding izquierdo de la celda del logo
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            # pequeño espacio entre logo y título
            ('RIGHTPADDING', (0, 0), (0, 0), 6),
            # padding del lado izquierdo del título
            ('LEFTPADDING', (1, 0), (1, 0), 6),
            # logo alineado a la izquierda
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            # título alineado a la izquierda dentro de su celda
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            # sin grid visible (0 = sin borde)
            ('GRID', (0, 0), (-1, -1), 0, colors.white)
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
                Paragraph(v[2], normal_style),  # texto largo envuelto
                Paragraph(v[3], normal_style),  # texto largo envuelto
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

        # Guardar el PDF en disco para evitar límites de paquete al persistir.
        reportes_dir = os.path.join(os.getcwd(), "static", "reportes")
        os.makedirs(reportes_dir, exist_ok=True)

        fecha_inicio_archivo = fecha_inicio.replace("-", "")
        fecha_fin_archivo = fecha_fin.replace("-", "")
        nombre_archivo = f"reporte_{fecha_inicio_archivo}_{fecha_fin_archivo}_{uuid.uuid4().hex[:8]}.pdf"
        ruta_relativa = os.path.join(
            "reportes", nombre_archivo).replace("\\", "/")
        ruta_fisica = os.path.join(reportes_dir, nombre_archivo)

        with open(ruta_fisica, "wb") as f:
            f.write(pdf_bytes)

        # El armado del PDF puede tardar; revalida/conecta antes de guardar metadatos.
        mysql.connection.ping(True)
        cur = mysql.connection.cursor()

        # Intenta esquema moderno primero.
        try:
            titulo = f"Reporte {fecha_inicio} a {fecha_fin}"
            descripcion = f"Reporte de pedidos del {fecha_inicio} al {fecha_fin}"
            cur.execute("""
                INSERT INTO reportes (Titulo, Descripcion, Ruta_Archivo)
                VALUES (%s, %s, %s)
            """, (titulo, descripcion, ruta_relativa))
            mysql.connection.commit()
        except Exception:
            mysql.connection.rollback()

            # Fallback para esquema legado: guarda la ruta en `archivo` (BLOB) para evitar max_allowed_packet.
            cur.execute("""
                INSERT INTO reportes (fecha_inicio, fecha_fin, archivo)
                VALUES (%s, %s, %s)
            """, (fecha_inicio, fecha_fin, ruta_relativa.encode("utf-8")))
            mysql.connection.commit()

        cur.close()
        cur = None

        flash("Reporte generado y guardado correctamente", "success")
        return redirect(url_for("admin_bp.reportes"))

    except Exception as e:
        try:
            mysql.connection.rollback()
        except Exception:
            pass

        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass

        print("ERROR AL GENERAR REPORTE:", e)
        flash(f"Error al generar el reporte: {e}", "error")
        return redirect(url_for("admin_bp.reportes"))


@admin_bp.route('/descargar_reporte/<int:report_id>', methods=['GET'])
@admin_required
def descargar_reporte(report_id):
    cur = mysql.connection.cursor()
    reporte = None
    try:
        cur.execute(
            "SELECT Ruta_Archivo, Titulo, Fecha_Creacion FROM reportes WHERE id = %s", (report_id,))
        reporte = cur.fetchone()
    except Exception:
        pass

    if reporte:
        ruta_relativa, titulo, fecha_creacion = reporte
        if ruta_relativa:
            ruta_fisica = os.path.join(os.getcwd(), "static", ruta_relativa)
            if os.path.exists(ruta_fisica):
                nombre_archivo = os.path.basename(ruta_fisica)
                cur.close()
                return send_file(ruta_fisica, as_attachment=True, download_name=nombre_archivo, mimetype="application/pdf")

    cur.execute(
        "SELECT archivo, fecha_inicio, fecha_fin FROM reportes WHERE id = %s", (report_id,))
    reporte_legacy = cur.fetchone()
    cur.close()

    if not reporte_legacy:
        flash("El reporte no existe", "error")
        return redirect(url_for("admin_bp.reportes"))

    archivo, fecha_inicio, fecha_fin = reporte_legacy
    if archivo and isinstance(archivo, (bytes, bytearray)) and archivo[:4] == b"%PDF":
        nombre_archivo = f"reporte_{fecha_inicio}_{fecha_fin}.pdf"
        return send_file(io.BytesIO(archivo), as_attachment=True, download_name=nombre_archivo, mimetype="application/pdf")

    # Compatibilidad: en esquema legado el blob puede guardar una ruta en texto.
    if isinstance(archivo, (bytes, bytearray)):
        ruta_relativa = archivo.decode("utf-8", errors="ignore")
    else:
        ruta_relativa = str(archivo or "")

    ruta_fisica = os.path.join(os.getcwd(), "static", ruta_relativa)
    if os.path.exists(ruta_fisica):
        nombre_archivo = os.path.basename(ruta_fisica)
        return send_file(ruta_fisica, as_attachment=True, download_name=nombre_archivo, mimetype="application/pdf")

    flash("El archivo del reporte no está disponible", "error")
    return redirect(url_for("admin_bp.reportes"))


@admin_bp.route('/ver_reporte/<int:report_id>', methods=['GET'])
@admin_required
def ver_reporte(report_id):
    cur = mysql.connection.cursor()
    reporte = None
    try:
        cur.execute(
            "SELECT Ruta_Archivo FROM reportes WHERE id = %s", (report_id,))
        reporte = cur.fetchone()
    except Exception:
        pass

    if reporte and reporte[0]:
        ruta_fisica = os.path.join(os.getcwd(), "static", reporte[0])
        if os.path.exists(ruta_fisica):
            cur.close()
            return send_file(ruta_fisica, mimetype="application/pdf")

    cur.execute("SELECT archivo FROM reportes WHERE id = %s", (report_id,))
    reporte_legacy = cur.fetchone()
    cur.close()

    if not reporte_legacy:
        flash("El reporte no existe", "error")
        return redirect(url_for("admin_bp.reportes"))

    archivo = reporte_legacy[0]
    if archivo and isinstance(archivo, (bytes, bytearray)) and archivo[:4] == b"%PDF":
        return Response(archivo, mimetype="application/pdf")

    if isinstance(archivo, (bytes, bytearray)):
        ruta_relativa = archivo.decode("utf-8", errors="ignore")
    else:
        ruta_relativa = str(archivo or "")

    ruta_fisica = os.path.join(os.getcwd(), "static", ruta_relativa)
    if os.path.exists(ruta_fisica):
        return send_file(ruta_fisica, mimetype="application/pdf")

    flash("El archivo del reporte no está disponible", "error")
    return redirect(url_for("admin_bp.reportes"))

# -------------------------------------- FACTURA -----------------------------------------


@admin_bp.route('/factura/<id_venta>')
@login_required
def factura(id_venta):
    user_id = session['user_id']
    # cambio mínimo: siempre minúsculas
    rol = (session.get('user_role') or "").lower()

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


@admin_bp.route("/descargar_factura/<int:invoice_id>")
@login_required
def descargar_factura(invoice_id):
    user_id = session.get("user_id")
    if not user_id:
        return "No autenticado", 401

    cursor = mysql.connection.cursor()
    rol = (session.get("user_role") or "").lower()

    if rol == "admin":
        cursor.execute('''
            SELECT Num_venta, Fecha, Nombre_Cliente, Apellido_Cliente, N_Documento,
                   Producto, Precio_Original, Descuento, Precio_Final,
                   Cantidad_p, SubTotal_Final, Total_Venta
            FROM reporte
            WHERE Num_venta = %s
        ''', (invoice_id,))
    else:
        cursor.execute('''
            SELECT Num_venta, Fecha, Nombre_Cliente, Apellido_Cliente, N_Documento,
                   Producto, Precio_Original, Descuento, Precio_Final,
                   Cantidad_p, SubTotal_Final, Total_Venta
            FROM reporte
            WHERE Num_venta = %s AND ID_Cliente = %s
        ''', (invoice_id, user_id))

    datos = cursor.fetchall()
    cursor.close()

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
    elements.append(Paragraph(f"Factura N.º {invoice_id}", title_style))
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

    nombre_archivo = f"Factura_{invoice_id}_{fecha}.pdf"
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
    user_id = session['user_id']
    # cambio mínimo: minúsculas
    rol = (session.get('user_role') or "").lower()

    if user_id and rol == 'cliente':
        flash('El Nombre, el Apellido y el N° de Documento no pueden ser editados', 'info')

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM usuarios WHERE ID_Usuario = %s', (user_id,))
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

    nombre = None  # Inicializar la variable
    if user_id:
        cur.execute(
            "SELECT Nombre FROM usuarios WHERE ID_Usuario = %s", (user_id,))
        row = cur.fetchone()
        nombre = row[0] if row else None
    cur.close()

    if rol == 'admin':
        return render_template('Vistas_admin/configuracion.html', usuario=usuario)
    elif rol == 'cliente':
        return render_template('Vista_usuario/perfil.html', usuario=usuario, user=user_id, nombre=nombre)
    else:
        flash('Rol no reconocido', 'error')
        return redirect(url_for('auth_bp.login'))


@admin_bp.route('/actualizar_usuario/<int:user_id>', methods=['POST'])
@login_required
def actualizar_usuario(user_id):
    usuario_id = session['user_id']
    # cambio mínimo: minúsculas
    rol = (session.get('user_role') or "").lower()

    if rol == 'cliente' and usuario_id != user_id:
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
        """, (nombre, apellido, documento, correo, telefono, direccion, ciudad, clave_hash, user_id))
    else:
        cur.execute("""
            UPDATE usuarios 
            SET Nombre=%s, Apellido=%s, N_Documento=%s, Correo=%s, Telefono=%s, Direccion=%s, Ciudad=%s
            WHERE ID_Usuario=%s
        """, (nombre, apellido, documento, correo, telefono, direccion, ciudad, user_id))

    mysql.connection.commit()
    cur.close()

    flash('Usuario actualizado correctamente', 'success')
    return redirect(url_for('admin_bp.configuracion'))

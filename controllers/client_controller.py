from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app import mysql
from functools import wraps

client_bp = Blueprint('client_bp', __name__)

# -------------------------------------------------------------------------------------------------------
#                                      CONEXIÓN VISTAS DEL CLIENTE
# -------------------------------------------------------------------------------------------------------


@client_bp.route('/')
def index_cliente():
    user_id = session.get("user_id")   # ID del usuario en sesión
    user_name = session.get("user_name")

    cur = mysql.connection.cursor()
    # Productos (máximo 8)
    cur.execute(
        'SELECT ID_Producto, Nombre, Precio, Imagen, Marca FROM Productos LIMIT 8')
    data = cur.fetchall()

    favoritos = []
    nombre = None

    if user_id:
        cur.execute(
            "SELECT Nombre FROM Usuarios WHERE ID_Usuario = %s", (user_id,))
        row = cur.fetchone()
        nombre = row[0] if row else None

        cur.execute(
            "SELECT ID_ProductoFK FROM favoritos WHERE ID_UsuarioFK = %s", (user_id,))
        favoritos = [row[0] for row in cur.fetchall()]

    cur.close()

    return render_template('Vista_usuario/index_usuario.html',
                           productos2=data,
                           user=user_name,
                           favoritos=favoritos,
                           nombre=nombre)

# -------------------------------------- MARCAS -----------------------------------------


@client_bp.route('/epa_colombia')
def epa_colombia():
    return render_marca("EPA Colombia", "Vista_usuario/epa-colombia.html", "productosepa")


@client_bp.route('/anyeluz')
def anyeluz():
    return render_marca("Anyeluz", "Vista_usuario/anyeluz.html", "productosanyeluz", "productosanyeluzlim")


@client_bp.route('/milagros')
def milagros():
    return render_marca("Milagros", "Vista_usuario/milagros.html", "productosmilagros")


@client_bp.route('/dluchi')
def dluchi():
    return render_marca("D’Luchi", "Vista_usuario/dluchi.html", "productosdluchi")


@client_bp.route('/kaba')
def kaba():
    return render_marca("Kaba", "Vista_usuario/kaba.html", "productoskaba", "productoskabalim")


@client_bp.route('/la_receta')
def la_receta():
    return render_marca("La Receta", "Vista_usuario/lareceta.html", "productosreceta", "productosrecetalim")


@client_bp.route('/magic_hair')
def magic_hair():
    return render_marca("Magic Hair", "Vista_usuario/magic-hair.html", "productosmagic")


@client_bp.route('/OMG')
def OMG():
    return render_marca("OMG", "Vista_usuario/OMG.html", "productosOMG")


@client_bp.route('/la_pocion')
def la_pocion():
    return render_marca("La Poción", "Vista_usuario/la-pocion.html", "productospocion", "productospocionlim")


@client_bp.route('/conocenos')
def conocenos():
    return render_template('Vista_usuario/conocenos.html')

# -------------------------------------- FAVORITOS -----------------------------------------


@client_bp.route("/toggle_favorito/<int:producto_id>", methods=["POST"])
def toggle_favorito(producto_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "No autenticado"}), 401

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT * FROM favoritos WHERE ID_UsuarioFK = %s AND ID_ProductoFK = %s", (user_id, producto_id))
    favorito = cursor.fetchone()

    if favorito:
        cursor.execute(
            "DELETE FROM favoritos WHERE ID_UsuarioFK = %s AND ID_ProductoFK = %s", (user_id, producto_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True, "favorito": False})
    else:
        cursor.execute(
            "INSERT INTO favoritos (ID_UsuarioFK, ID_ProductoFK) VALUES (%s, %s)", (user_id, producto_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"success": True, "favorito": True})


@client_bp.route('/favoritos')
def favoritos():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()
    cur.execute('''SELECT p.ID_Producto, p.Nombre, p.Precio, p.Imagen, p.Marca 
                   FROM Productos p
                   INNER JOIN favoritos f ON p.ID_Producto = f.ID_ProductoFK 
                   AND f.ID_UsuarioFK = %s
                   ORDER BY p.Marca ASC''', (user_id,))
    data = cur.fetchall()

    cur.execute(
        'SELECT ID_productoFK FROM favoritos WHERE ID_UsuarioFK = %s', (user_id,))
    productosfav = [row[0] for row in cur.fetchall()]
    cur.close()

    return render_template("Vista_usuario/favoritos.html", favoritos=data, productosfav=productosfav)

# -------------------------------------- DETALLES PRODUCTO -----------------------------------------


@client_bp.route("/detallesproducto/<int:id>")
def detallesproducto(id):
    user_id = session.get("user_id")
    user_name = session.get("user_name")

    cur = mysql.connection.cursor()
    cur.execute("""SELECT ID_Producto, Nombre, Descripcion, Precio, Imagen, Marca 
                   FROM productos WHERE ID_Producto = %s""", (id,))
    productodetalles = cur.fetchone()

    cur.execute("""SELECT ID_Producto, Nombre, Precio, Imagen
                   FROM productos
                   WHERE ID_Producto != %s
                   AND Marca = (SELECT Marca FROM productos WHERE ID_Producto = %s)
                   ORDER BY RAND() LIMIT 4""", (id, id,))
    relacionados = cur.fetchall()

    cur.execute(
        'SELECT ID_Producto, Nombre, Precio, Imagen, Marca FROM productos ORDER BY RAND() LIMIT 6')
    caruseldetalles = cur.fetchall()

    favoritos = []
    if user_id:
        cur.execute(
            "SELECT ID_ProductoFK FROM favoritos WHERE ID_UsuarioFK = %s", (user_id,))
        favoritos = [row[0] for row in cur.fetchall()]

    cur.close()

    if not productodetalles:
        return "Producto no encontrado", 404

    return render_template("Vista_usuario/info_producto.html",
                           productodetalles=productodetalles,
                           relacionados=relacionados,
                           caruseldetalles=caruseldetalles,
                           user=user_name,
                           favoritos=favoritos)

# -------------------------------------- CARRITO -----------------------------------------


@client_bp.route("/carrito_get")
def carrito_get():
    user_id = session.get("user_id")
    if user_id:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT ID_Carrito, Producto, Precio, Cantidad, Imagen FROM carrito_temp WHERE ID_UsuarioFK = %s", (user_id,))
        rows = cur.fetchall()
        cur.close()
        carrito = [{"id": r[0], "nombre": r[1], "precio": r[2],
                    "cantidad": r[3], "img": r[4]} for r in rows]
    else:
        carrito = session.get("carrito", [])
        for idx, item in enumerate(carrito):
            item["id"] = idx
    return jsonify(carrito)


@client_bp.route("/carrito_agregar", methods=["POST"])
def carrito_agregar():
    data = request.form
    producto = data["nombre"]
    precio = float(data["precio"])
    cantidad = int(data["cantidad"])
    img = data.get("img", "")
    user_id = session.get("user_id")

    if user_id:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT ID_Carrito, Cantidad FROM carrito_temp WHERE ID_UsuarioFK = %s AND Producto = %s", (user_id, producto))
        existente = cur.fetchone()
        if existente:
            cur.execute("UPDATE carrito_temp SET Cantidad = %s WHERE ID_Carrito = %s",
                        (existente[1] + cantidad, existente[0]))
        else:
            cur.execute("INSERT INTO carrito_temp (ID_UsuarioFK, Producto, Precio, Cantidad, Imagen) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, producto, precio, cantidad, img))
        mysql.connection.commit()
        cur.close()
    else:
        carrito = session.get("carrito", [])
        encontrado = False
        for item in carrito:
            if item["nombre"] == producto:
                item["cantidad"] += cantidad
                encontrado = True
                break
        if not encontrado:
            carrito.append({"nombre": producto, "precio": precio,
                           "cantidad": cantidad, "img": img})
        session["carrito"] = carrito

    flash("Producto agregado al carrito", "success")
    return redirect(url_for("client_bp.index_cliente"))


@client_bp.route("/carrito_actualizar", methods=["POST"])
def carrito_actualizar():
    data = request.form
    item_id = data.get("id")
    cantidad = max(1, int(data.get("cantidad", 1)))
    user_id = session.get("user_id")

    if user_id:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE carrito_temp SET Cantidad = %s WHERE ID_Carrito = %s AND ID_UsuarioFK = %s",
                    (cantidad, item_id, user_id))
        mysql.connection.commit()
        cur.close()
    else:
        carrito = session.get("carrito", [])
        item_id = int(item_id)
        if 0 <= item_id < len(carrito):
            carrito[item_id]["cantidad"] = cantidad
        session["carrito"] = carrito

    return jsonify({"success": True, "cantidad": cantidad})


@client_bp.route("/carrito_eliminar/<item_id>", methods=["POST"])
def carrito_eliminar(item_id):
    user_id = session.get("user_id")
    if user_id:
        cur = mysql.connection.cursor()
        cur.execute(
            "DELETE FROM carrito_temp WHERE ID_Carrito = %s AND ID_UsuarioFK = %s", (item_id, user_id))
        mysql.connection.commit()
        cur.close()
    else:
        item_id = int(item_id)
        carrito = session.get("carrito", [])
        if 0 <= item_id < len(carrito):
            carrito.pop(item_id)
        session["carrito"] = carrito

    return redirect(url_for("client_bp.index_cliente"))

# -------------------------------------- DECORADORES -----------------------------------------


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión para continuar.", "warning")
            return redirect(url_for("auth_bp.login"))
        return f(*args, **kwargs)
    return decorated_function


def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("user_role") != "cliente":
            flash("Debes iniciar sesión como cliente para continuar.", "warning")
            return redirect(url_for("auth_bp.login"))
        return f(*args, **kwargs)
    return decorated_function


@client_bp.route("/carrito_finalizar", methods=["POST"])
@login_required
def carrito_finalizar():
    user_id = session["user_id"]
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT Producto, Precio, Cantidad FROM carrito_temp WHERE ID_UsuarioFK = %s", (user_id,))
    carrito = cur.fetchall()

    if not carrito:
        carrito = session.get("carrito", [])
        if not carrito:
            flash("Tu carrito está vacío", "danger")
            return redirect(url_for("client_bp.index_cliente"))

    total = sum([item[1] * item[2] if isinstance(item, tuple)
                else item["precio"] * item["cantidad"] for item in carrito])
    cur.execute(
        "INSERT INTO ventas (ID_UsuarioFK, Fecha, Total) VALUES (%s, NOW(), %s)", (user_id, total))
    id_venta = cur.lastrowid

    for item in carrito:
        if isinstance(item, tuple):
            nombre, precio, cantidad = item
        else:
            nombre, precio, cantidad = item["nombre"], item["precio"], item["cantidad"]

        cur.execute(
            "SELECT ID_Producto FROM productos WHERE Nombre = %s", (nombre,))
        id_producto = cur.fetchone()[0]

        cur.execute("""INSERT INTO detalles_venta (ID_VentaFK, ID_ProductoFK, Cantidad_p, SubTotal)
                       VALUES (%s, %s, %s, %s)""", (id_venta, id_producto, cantidad, precio * cantidad))

    cur.execute("DELETE FROM carrito_temp WHERE ID_UsuarioFK = %s", (user_id,))
    session.pop("carrito", None)
    mysql.connection.commit()
    cur.close()

    flash("Compra finalizada con éxito", "success")
    return redirect(url_for("client_bp.index_cliente"))

# -------------------------------------- COMPRAS -----------------------------------------


@client_bp.route('/compras')
@cliente_required
def compras():
    user_id = session.get("user_id")
    cur = mysql.connection.cursor()
    cur.execute('''SELECT Num_venta, Fecha, SUM(SubTotal_Final) AS Total_Comprado, SUM(Cantidad_p) AS Total_Productos
                   FROM reporte WHERE ID_cliente = %s
                   GROUP BY Num_venta, Fecha ORDER BY Num_venta DESC''', (user_id,))
    data = cur.fetchall()
    cur.close()
    return render_template("Vista_usuario/compras.html", compras=data)

# -------------------------------------- BUSCAR -----------------------------------------


@client_bp.route('/buscar', methods=['GET'])
def buscar():
    user_id = session.get("user_id")
    user_name = session.get("user_name")
    query = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "")
    subcategoria = request.args.get("subcategoria", "")
    precio_min = request.args.get("precio_min", type=int)
    precio_max = request.args.get("precio_max", type=int)

    cur = mysql.connection.cursor()
    try:
        if not (query or categoria or subcategoria or precio_min or precio_max):
            cur.execute(
                "SELECT ID_Producto, Nombre, Precio, Imagen, Marca, Categoria FROM productos ORDER BY precio ASC")
            resultados = cur.fetchall()
        else:
            base_sql = "SELECT ID_Producto, Nombre, Precio, Imagen, Marca, Categoria FROM productos"
            where_conditions = []
            filtros = []

            if query:
                where_conditions.append(
                    "(LOWER(nombre) LIKE %s OR LOWER(categoria) LIKE %s OR LOWER(marca) LIKE %s OR LOWER(descripcion) LIKE %s)")
                query_param = f"%{query.lower()}%"
                filtros.extend([query_param] * 4)

            if categoria:
                where_conditions.append("categoria = %s")
                filtros.append(categoria)

            if subcategoria and subcategoria not in ["", "todas_las_subcategorías"]:
                subcategoria_mapping = {
                    "shampoo": ["shampoo", "champú"],
                    "acondicionador": ["acondicionador"],
                    "tratamiento": ["tratamiento", "mascarilla", "ampolla"],
                    "crema": ["crema", "loción"],
                    "bloqueador_solar": ["bloqueador", "protector solar", "SPF"],
                    "bronceador": ["bronceador", "autobronceante"],
                    "exfoliante": ["exfoliante", "scrub", "peeling"]
                }
                if subcategoria.lower() in subcategoria_mapping:
                    terms = subcategoria_mapping[subcategoria.lower()]
                    condition = " OR ".join(
                        ["LOWER(nombre) LIKE %s"] * len(terms))
                    where_conditions.append(f"({condition})")
                    filtros.extend([f"%{t}%" for t in terms])
                else:
                    where_conditions.append("LOWER(nombre) LIKE %s")
                    filtros.append(
                        f"%{subcategoria.lower().replace('_', ' ')}%")

            if precio_min is not None and precio_min > 0:
                where_conditions.append("precio >= %s")
                filtros.append(precio_min)
            if precio_max is not None and precio_max > 0:
                where_conditions.append("precio <= %s")
                filtros.append(precio_max)
            if precio_min and precio_max and precio_min > precio_max:
                flash("El precio mínimo no puede ser mayor al precio máximo", "error")
                precio_min, precio_max = precio_max, precio_min

            where_clause = " WHERE " + \
                " AND ".join(where_conditions) if where_conditions else ""
            final_sql = f"""{base_sql} {where_clause} ORDER BY CASE WHEN LOWER(nombre) LIKE %s THEN 1 ELSE 2 END, precio ASC"""
            filtros.append(f"%{query.lower()}%" if query else "%%")
            cur.execute(final_sql, filtros)
            resultados = cur.fetchall()

        productobusf = []
        if user_id:
            cur.execute(
                'SELECT ID_productoFK FROM favoritos WHERE ID_UsuarioFK = %s', (user_id,))
            productobusf = [row[0] for row in cur.fetchall()]

        total_productos = len(resultados)
        resultado_mensaje = "No se encontraron productos." if total_productos == 0 else (
            "Se encontró 1 producto." if total_productos == 1 else f"Se encontraron {total_productos} productos.")

        return render_template("Vista_usuario/buscar.html", resultados=resultados, query=query,
                               categoria=categoria, subcategoria=subcategoria,
                               precio_min=precio_min, precio_max=precio_max,
                               productobusf=productobusf, user=user_name,
                               total_productos=total_productos,
                               resultado_mensaje=resultado_mensaje)
    except Exception as e:
        flash("Error al realizar la búsqueda. Por favor, inténtalo de nuevo.", "error")
        return render_template("Vista_usuario/buscar.html", resultados=[], query=query,
                               categoria=categoria, subcategoria=subcategoria,
                               productobusf=[], total_productos=0,
                               resultado_mensaje="Error en la búsqueda.")
    finally:
        cur.close()

# -------------------------------------- FUNCIÓN AUXILIAR -----------------------------------------


def render_marca(nombre_marca, template, var_name, var_name_lim=None):
    user_id = session.get("user_id")
    user_name = session.get("user_name")
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT ID_Producto, Nombre, Precio, Imagen, Marca FROM Productos WHERE Marca = %s", (nombre_marca,))
    data = cur.fetchall()

    data_lim = []
    if var_name_lim:
        cur.execute(
            "SELECT ID_Producto, Nombre, Precio, Imagen, Marca FROM Productos WHERE Marca = %s LIMIT 6", (nombre_marca,))
        data_lim = cur.fetchall()

    favoritos = []
    if user_id:
        cur.execute(
            "SELECT ID_ProductoFK FROM favoritos WHERE ID_UsuarioFK = %s", (user_id,))
        favoritos = [row[0] for row in cur.fetchall()]

    cur.close()
    return render_template(template, **{var_name: data}, **({var_name_lim: data_lim} if var_name_lim else {}),
                           user=user_name, favoritos=favoritos)

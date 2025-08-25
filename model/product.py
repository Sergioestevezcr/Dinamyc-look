from model.database import get_db

def get_all_products():
    """
    Obtiene todos los productos de la base de datos.

    Returns:
        Una lista de tuplas, donde cada tupla representa un producto.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos')
    data = cur.fetchall()
    cur.close()
    return data

def add_product(nombre, descripcion, precio, marca, stock):
    """
    Agrega un nuevo producto a la base de datos.

    Args:
        nombre: Nombre del producto.
        descripcion: Descripción del producto.
        precio: Precio del producto.
        marca: Marca del producto.
        stock: Stock disponible del producto.

    Returns:
        None
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO productos (Nombre, Descripcion, Precio, Marca, Stock) VALUES (%s, %s, %s, %s, %s)',
                (nombre, descripcion, precio, marca, stock))
    mysql.connection.commit()
    cur.close()

def get_product_by_id(product_id):
    """
    Obtiene un producto de la base de datos por su ID.

    Args:
        product_id: El ID del producto a buscar.

    Returns:
        Una tupla con los datos del producto si se encuentra, o None si no.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM productos WHERE id_producto = %s', (product_id,))
    data = cur.fetchone()
    cur.close()
    return data

def update_product(product_id, nombre, descripcion, precio, marca, stock):
    """
    Actualiza un producto existente en la base de datos.

    Args:
        product_id: El ID del producto a actualizar.
        nombre: Nuevo nombre del producto.
        descripcion: Nueva descripción del producto.
        precio: Nuevo precio del producto.
        marca: Nueva marca del producto.
        stock: Nuevo stock disponible del producto.

    Returns:
        None
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('''UPDATE productos
                    SET Nombre = %s, Descripcion = %s, Precio = %s,
                        Marca = %s, Stock = %s
                    WHERE id_producto = %s''',
                (nombre, descripcion, precio, marca, stock, product_id))
    mysql.connection.commit()
    cur.close()

def get_product_price_and_stock(product_id):
    """
    Obtiene el precio y stock de un producto por su ID.

    Args:
        product_id: El ID del producto.

    Returns:
        Una tupla con el precio y stock (precio, stock) o None si no se encuentra.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('SELECT Precio, Stock FROM productos WHERE ID_Producto = %s', (product_id,))
    data = cur.fetchone()
    cur.close()
    return data

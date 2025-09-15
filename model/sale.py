from model.database import get_db
from model import product  # Necesitamos product para actualizar el stock


def get_sales_report():
    """
    Obtiene el informe de ventas desde la base de datos.

    Returns:
        Una lista de tuplas con los datos del reporte de ventas.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
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
    cur.close()
    return data


def add_new_sale(id_usuario, productos_venta):
    """
    Agrega una nueva venta y sus detalles a la base de datos, y actualiza el stock de productos.

    Args:
        id_usuario: El ID del usuario que realiza la compra.
        productos_venta: Una lista de diccionarios, donde cada diccionario
                        representa un producto en la venta con 'id', 'cantidad',
                        'precio', y 'subtotal'.

    Returns:
        El ID de la venta recién creada si tiene éxito, o None si hay un error.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    try:
        total_venta = sum(item['subtotal'] for item in productos_venta)

        # Insertar registro principal de la venta
        cur.execute('''INSERT INTO ventas (ID_UsuarioFK, Fecha, Total)
                        VALUES (%s, NOW(), %s)''',
                    (id_usuario, total_venta))

        venta_id = cur.lastrowid

        # Insertar cada detalle de producto vendido y actualizar stock
        for producto in productos_venta:
            cur.execute('''INSERT INTO detalles_venta (ID_VentaFK, ID_ProductoFK, Cantidad_p)
                            VALUES (%s, %s, %s)''',
                        (venta_id, producto['id'], producto['cantidad']))

            # Actualizar el stock del producto vendido usando la función del modelo product
            # Restamos la cantidad vendida
            product.update_product_stock(producto['id'], -producto['cantidad'])

        mysql.connection.commit()
        return venta_id

    except Exception as e:
        mysql.connection.rollback()
        # Considerar loggear en lugar de imprimir
        print(f"Error en add_new_sale: {e}")
        return None
    finally:
        cur.close()


def get_invoice_data(id_venta):
    """
    Obtiene los datos para generar una factura de una venta específica.

    Args:
        id_venta: El ID de la venta.

    Returns:
        Una lista de tuplas con los datos de la factura, o una lista vacía si no se encuentra.
    """
    mysql = get_db()
    cur = mysql.connection.cursor()
    cur.execute('''
        SELECT Num_venta, Fecha, Nombre_Cliente, Apellido_Cliente,
                Producto, Precio_Original, Descuento, Precio_Final,
                Cantidad_p, SubTotal_Final, Total_Venta
        FROM reporte
        WHERE Num_venta = %s
    ''', (id_venta,))
    factura_data = cur.fetchall()
    cur.close()
    return factura_data

# Función auxiliar para actualizar stock en model/product.py (si no la creaste antes)
# Deberías agregar esta función en model/product.py si no existe
# def update_product_stock(product_id, quantity_change):
#     """
#     Actualiza el stock de un producto.
#
#     Args:
#         product_id: El ID del producto.
#         quantity_change: La cantidad a sumar (positiva) o restar (negativa) del stock.
#     """
#     mysql = get_db()
#     cur = mysql.connection.cursor()
#     cur.execute('UPDATE productos SET Stock = Stock + %s WHERE ID_Producto = %s',
#                 (quantity_change, product_id))
#     mysql.connection.commit()
#     cur.close()

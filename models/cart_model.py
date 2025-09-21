from database import mysql


class CartModel:

    @staticmethod
    def get_cart_items(user_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT ID_Carrito, Producto, Precio, Cantidad, Imagen FROM carrito_temp WHERE ID_UsuarioFK = %s", (user_id,))
        rows = cur.fetchall()
        cur.close()
        return [{"id": r[0], "nombre": r[1], "precio": r[2], "cantidad": r[3], "img": r[4]} for r in rows]

    @staticmethod
    def add_to_cart(user_id, nombre, precio, cantidad, img):
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT ID_Carrito, Cantidad FROM carrito_temp WHERE ID_UsuarioFK = %s AND Producto = %s", (user_id, nombre))
        existente = cur.fetchone()

        if existente:
            nuevo_total = existente[1] + cantidad
            cur.execute("UPDATE carrito_temp SET Cantidad = %s WHERE ID_Carrito = %s",
                        (nuevo_total, existente[0]))
        else:
            cur.execute("INSERT INTO carrito_temp (ID_UsuarioFK, Producto, Precio, Cantidad, Imagen) VALUES (%s, %s, %s, %s, %s)",
                        (user_id, nombre, precio, cantidad, img))

        mysql.connection.commit()
        cur.close()

    @staticmethod
    def update_cart_item(user_id, item_id, cantidad):
        cur = mysql.connection.cursor()
        cur.execute("UPDATE carrito_temp SET Cantidad = %s WHERE ID_Carrito = %s AND ID_UsuarioFK = %s",
                    (cantidad, item_id, user_id))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def remove_from_cart(user_id, item_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "DELETE FROM carrito_temp WHERE ID_Carrito = %s AND ID_UsuarioFK = %s", (item_id, user_id))
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def finalize_purchase(user_id):
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT Producto, Precio, Cantidad FROM carrito_temp WHERE ID_UsuarioFK = %s", (user_id,))
        carrito = cur.fetchall()

        if not carrito:
            return None

        total = sum([item[1] * item[2] for item in carrito])
        cur.execute(
            "INSERT INTO ventas (ID_UsuarioFK, Fecha, Total) VALUES (%s, NOW(), %s)", (user_id, total))
        id_venta = cur.lastrowid

        for nombre, precio, cantidad in carrito:
            cur.execute(
                "SELECT ID_Producto FROM productos WHERE Nombre = %s", (nombre,))
            id_producto = cur.fetchone()[0]
            cur.execute("INSERT INTO detalles_venta (ID_VentaFK, ID_ProductoFK, Cantidad_p, SubTotal) VALUES (%s, %s, %s, %s)",
                        (id_venta, id_producto, cantidad, precio * cantidad))

        cur.execute(
            "DELETE FROM carrito_temp WHERE ID_UsuarioFK = %s", (user_id,))
        mysql.connection.commit()
        cur.close()
        return id_venta

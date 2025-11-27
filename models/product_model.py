from database import mysql


class ProductModel:

    @staticmethod
    def get_products_by_brand(brand):
        cur = mysql.connection.cursor()
        cur.execute(
            'SELECT ID_Producto, Nombre, Precio, Imagen, Marca FROM Productos WHERE Marca = %s', (brand,))
        data = cur.fetchall()
        cur.close()
        return data

    @staticmethod
    def get_related_products(product_id, brand):
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT ID_Producto, Nombre, Precio, Imagen
            FROM productos
            WHERE ID_Producto != %s
            AND Marca = %s
            ORDER BY RAND()
            LIMIT 4
        """, (product_id, brand))
        related = cur.fetchall()
        cur.close()
        return related

    @staticmethod
    def get_carousel_products():
        cur = mysql.connection.cursor()
        cur.execute(
            'SELECT ID_Producto, Nombre, Precio, Imagen, Marca FROM productos ORDER BY RAND() LIMIT 6')
        carousel = cur.fetchall()
        cur.close()
        return carousel

    @staticmethod
    def search_products(query, categoria, subcategoria, precio_min, precio_max):
        cur = mysql.connection.cursor()
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
                condition = " OR ".join(["LOWER(nombre) LIKE %s"] * len(terms))
                where_conditions.append(f"({condition})")
                filtros.extend([f"%{t}%" for t in terms])
            else:
                where_conditions.append("LOWER(nombre) LIKE %s")
                filtros.append(f"%{subcategoria.lower().replace('_', ' ')}%")

        if precio_min is not None and precio_min > 0:
            where_conditions.append("precio >= %s")
            filtros.append(precio_min)

        if precio_max is not None and precio_max > 0:
            where_conditions.append("precio <= %s")
            filtros.append(precio_max)

        where_clause = ""
        if where_conditions:
            where_clause = " WHERE " + " AND ".join(where_conditions)

        final_sql = f"{base_sql} {where_clause} ORDER BY CASE WHEN LOWER(nombre) LIKE %s THEN 1 ELSE 2 END, precio ASC"

        if query:
            filtros.append(f"%{query.lower()}%")
        else:
            filtros.append("%%")

        cur.execute(final_sql, filtros)
        resultados = cur.fetchall()
        cur.close()
        return resultados

    @staticmethod
    def get_all_products_admin():
        cur = mysql.connection.cursor()
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
        data = cur.fetchall()
        cur.close()
        return data

    @staticmethod
    def get_product_by_id(product_id):
        cur = mysql.connection.cursor()
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
        ''', (product_id,))
        data = cur.fetchone()
        cur.close()
        return data

    @staticmethod
    def add_product(nombre, descripcion, categoria, precio, stock, filename, idmarca, id_promocion):
        cur = mysql.connection.cursor()
        cur.execute(
            '''INSERT INTO productos 
               (Nombre, Descripcion, Categoria, Precio, Stock, Imagen, ID_ProveedorFK, ID_PromocionFK) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (nombre, descripcion, categoria, precio, stock, filename, idmarca, id_promocion)
        )
        mysql.connection.commit()
        cur.close()

    @staticmethod
    def update_product(product_id, nombre, descripcion, categoria, precio, stock, idmarca, id_promocion, filename=None):
        cur = mysql.connection.cursor()
        if filename:
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
                (nombre, descripcion, categoria, precio, stock, filename, idmarca, id_promocion, product_id)
            )
        else:
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
                (nombre, descripcion, categoria, precio, stock, idmarca, id_promocion, product_id)
            )
        mysql.connection.commit()
        cur.close()

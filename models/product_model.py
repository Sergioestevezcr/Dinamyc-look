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

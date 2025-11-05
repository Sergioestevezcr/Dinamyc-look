from database import mysql


class SaleModel:

    @staticmethod
    def get_user_purchases(user_id):
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT
                Num_venta,
                Fecha,
                SUM(SubTotal_Final) AS Total_Comprado,
                SUM(Cantidad_p) AS Total_Productos
            FROM reporte
            WHERE ID_cliente = %s
            GROUP BY Num_venta, Fecha
            ORDER BY Num_venta DESC
        ''', (user_id,))
        data = cur.fetchall()
        cur.close()
        return data

    @staticmethod
    def get_admin_dashboard_data():
        cur = mysql.connection.cursor()
        cur.execute('SELECT COUNT(ID_Venta) AS pedidos_Totales, SUM(Total) AS Ingresos_Totales FROM pedidos WHERE MONTH(Fecha) = MONTH(CURDATE()) AND YEAR(Fecha) = YEAR(CURDATE())')
        data_pedidos = cur.fetchone()
        pedidos = data_pedidos[0] or 0
        ingresos = data_pedidos[1] or 0

        cur.execute('''SELECT SUM(detalles_venta.Cantidad_p) AS Total_Cantidad_Mes_Actual FROM Detalles_venta JOIN pedidos ON detalles_venta.ID_VentaFK = pedidos.ID_Venta WHERE MONTH(pedidos.Fecha) = MONTH(CURDATE()) AND YEAR(pedidos.Fecha) = YEAR(CURDATE())''')
        productos_totales = cur.fetchone()[0]

        cur.execute(
            'SELECT Producto, Marca, Total_pedidos FROM masvendido ORDER BY masvendido.Total_pedidos DESC LIMIT 10')
        mas_vendidos = cur.fetchall()

        cur.execute(
            'SELECT * FROM prductosxacabar ORDER BY prductosxacabar.Stock DESC LIMIT 10')
        por_acabar = cur.fetchall()

        cur.close()
        return pedidos, ingresos, productos_totales, mas_vendidos, por_acabar

    @staticmethod
    def get_monthly_sales_data():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT MONTH(Fecha) AS mes, SUM(Total) AS total_ingresos, COUNT(*) AS total_pedidos
            FROM pedidos
            GROUP BY mes
            ORDER BY mes
        """)
        resultados = cur.fetchall()
        cur.close()
        return resultados

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
        cur.execute('SELECT COUNT(ID_Venta) AS Ventas_Totales, SUM(Total) AS Ingresos_Totales FROM ventas WHERE MONTH(Fecha) = MONTH(CURDATE()) AND YEAR(Fecha) = YEAR(CURDATE())')
        data_ventas = cur.fetchone()
        ventas = data_ventas[0] or 0
        ingresos = data_ventas[1] or 0

        cur.execute('''SELECT SUM(detalles_venta.Cantidad_p) AS Total_Cantidad_Mes_Actual FROM Detalles_venta JOIN ventas ON detalles_venta.ID_VentaFK = ventas.ID_Venta WHERE MONTH(ventas.Fecha) = MONTH(CURDATE()) AND YEAR(ventas.Fecha) = YEAR(CURDATE())''')
        productos_totales = cur.fetchone()[0]

        cur.execute(
            'SELECT Producto, Marca, Total_Ventas FROM mas_vendidos ORDER BY mas_vendidos.Total_Ventas DESC LIMIT 10')
        mas_vendidos = cur.fetchall()

        cur.execute(
            'SELECT * FROM prductosxacabar ORDER BY prductosxacabar.Stock DESC LIMIT 10')
        por_acabar = cur.fetchall()

        cur.close()
        return ventas, ingresos, productos_totales, mas_vendidos, por_acabar

    @staticmethod
    def get_monthly_sales_data():
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT MONTH(Fecha) AS mes, SUM(Total) AS total_ingresos, COUNT(*) AS Total_Vendido
            FROM ventas
            GROUP BY mes
            ORDER BY mes
        """)
        resultados = cur.fetchall()
        cur.close()
        return resultados

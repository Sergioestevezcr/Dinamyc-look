# controllers/payment_controller.py

import uuid
import json
import hashlib
import hmac

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    current_app,
    redirect,
    url_for
)

from database import mysql
from decorators import login_required, cliente_required
import mercadopago


payment_bp = Blueprint('payment_bp', __name__, template_folder='../templates')


def _carrito_resumen(user_id: int):
    """
    Lee el carrito del usuario desde la tabla carrito_temp.
    Esta tabla en tu BD tiene estas columnas:
        ID_Carrito
        ID_UsuarioFK
        Producto
        Precio
        Cantidad
        Imagen

    OJO: acá NO hacemos JOIN porque ya guardas nombre, precio e imagen directo.
    """
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            ID_Carrito,                    -- 0
            Producto,                      -- 1
            Precio,                        -- 2
            Cantidad,                      -- 3
            (Precio * Cantidad) AS Subtotal, -- 4
            Imagen                         -- 5
        FROM carrito_temp
        WHERE ID_UsuarioFK = %s
    """, (user_id,))
    rows = cur.fetchall()

    total_pesos = sum(r[4] for r in rows)      # r[4] = Subtotal
    total_cents = int(total_pesos * 100)       # Mercado Pago usa centavos

    return rows, total_pesos, total_cents


@payment_bp.route("/checkout", methods=["GET"])
@login_required
@cliente_required
def checkout_view():
    """
    Paso que se abre cuando el usuario le da "Finalizar Compra"
    en el carrito lateral del frontend.

    Flujo:
    1. Leer el carrito del usuario.
    2. Crear una referencia única de la orden.
    3. Insertar la orden en la tabla pagos como pendiente.
    4. Renderizar la página checkout.html con las dos opciones:
       - Pagar con Mercado Pago
       - Pago contraentrega (requiere dirección)
    """
    user_id = session["user_id"]

    carrito_rows, total_pesos, total_cents = _carrito_resumen(user_id)

    # referencia única que usaremos para identificar esta orden
    reference = uuid.uuid4().hex

    # Guardar la orden en la tabla pagos
    # La tabla pagos debe tener al menos:
    #   referencia (VARCHAR UNIQUE)
    #   user_id (INT)
    #   total_cents (INT)
    #   estado (VARCHAR)
    #   metodo (VARCHAR)  -> "MP" o "COD"
    #   direccion_entrega (NULL al inicio)
    #   mp_preference_id (NULL al inicio)
    #   mp_payment_id (NULL al inicio)
    #   raw_json (TEXT)
    #   created_at, updated_at
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO pagos (referencia, user_id, total_cents, estado, metodo, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (
        reference,
        user_id,
        total_cents,
        "PENDING",   # estado inicial: pendiente de método
        "MP"         # asumimos MP por defecto, si elige COD luego lo actualizamos
    ))
    mysql.connection.commit()

    return render_template(
        "pagos/checkout.html",
        carrito_rows=carrito_rows,
        total_pesos=total_pesos,
        reference=reference
    )


@payment_bp.route("/checkout/pagar", methods=["POST"])
@login_required
@cliente_required
def checkout_pagar():
    """
    El usuario eligió "Pagar con Mercado Pago".
    Aquí:
    1. Reconstruimos el carrito para armar la preferencia.
    2. Creamos la preferencia en Mercado Pago.
    3. Guardamos mp_preference_id en la tabla pagos.
    4. Redirigimos al usuario a init_point (Checkout Pro).
    """
    user_id = session["user_id"]
    reference = request.form.get("reference")

    carrito_rows, total_pesos, total_cents = _carrito_resumen(user_id)

    # Armamos la lista de items en el formato que Mercado Pago espera.
    # Cada item necesita title, quantity, unit_price, currency_id.
    # Vamos a usar:
    #   title       = Producto
    #   quantity    = Cantidad
    #   unit_price  = Precio (unitario)
    # currency_id: "COP"
    items_mp = []
    for row in carrito_rows:
        # row = (ID_Carrito, Producto, Precio, Cantidad, Subtotal, Imagen)
        items_mp.append({
            "id": str(row[0]),
            "title": row[1],
            "quantity": int(row[3]),
            "currency_id": "COP",
            "unit_price": float(row[2])
        })

    # Inicializamos el SDK de Mercado Pago con tu access token
    sdk = mercadopago.SDK(current_app.config["MP_ACCESS_TOKEN"])

    preference_data = {
        "items": items_mp,
        "external_reference": reference,  # así sabremos qué orden es en el webhook
        "back_urls": {
            "success": current_app.config["MP_SUCCESS_URL"],
            "failure": current_app.config["MP_FAILURE_URL"],
            "pending": current_app.config["MP_PENDING_URL"]
        },
        "auto_return": "approved",
        "notification_url": current_app.config["MP_NOTIFICATION_URL"]
    }

    pref_response = sdk.preference().create(preference_data)
    pref = pref_response["response"]

    mp_preference_id = pref.get("id")
    init_point = pref.get("init_point")  # URL de pago (producción)

    # Guardamos ese preference_id en la orden
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE pagos
        SET mp_preference_id=%s,
            updated_at=NOW()
        WHERE referencia=%s
          AND user_id=%s
    """, (
        mp_preference_id,
        reference,
        user_id
    ))
    mysql.connection.commit()

    # Mandamos al usuario al Checkout Pro de Mercado Pago
    return redirect(init_point)


@payment_bp.route("/checkout/contraentrega", methods=["POST"])
@login_required
@cliente_required
def checkout_contraentrega():
    """
    El usuario eligió pago contraentrega.
    Flujo:
    1. Recibimos la reference de la orden y la dirección de entrega.
    2. Actualizamos esa orden en pagos:
        - metodo = 'COD'
        - estado = 'COD_PENDIENTE_ENVIO'
        - direccion_entrega = la que puso el cliente
    3. Lo mandamos a una página de confirmación tipo "Listo, te lo llevamos".
    """
    user_id = session["user_id"]
    reference = request.form.get("reference")
    direccion_entrega = request.form.get("direccion_entrega")

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE pagos
        SET metodo=%s,
            estado=%s,
            direccion_entrega=%s,
            updated_at=NOW()
        WHERE referencia=%s
          AND user_id=%s
    """, (
        "COD",
        "COD_PENDIENTE_ENVIO",
        direccion_entrega,
        reference,
        user_id
    ))
    mysql.connection.commit()

    # OJO: aquí también podrías crear la venta final en tus tablas de historial de compras,
    # descontar stock, mandar correo al admin, etc.

    return redirect(url_for('payment_bp.contraentrega_confirmado', reference=reference))


@payment_bp.route("/pago/contraentrega_confirmado", methods=["GET"])
@login_required
@cliente_required
def contraentrega_confirmado():
    """
    Pantalla de gracias cuando elige contraentrega.
    """
    reference = request.args.get("reference")
    return render_template("pagos/pago_contraentrega.html", reference=reference)


@payment_bp.route("/pago/exitoso", methods=["GET"])
def pago_exitoso():
    return render_template("pagos/pago_exitoso.html")


@payment_bp.route("/pago/fallido", methods=["GET"])
def pago_fallido():
    return render_template("pagos/pago_fallido.html")


@payment_bp.route("/pago/pendiente", methods=["GET"])
def pago_pendiente():
    return render_template("pagos/pago_pendiente.html")


@payment_bp.route("/webhook/mercadopago", methods=["POST"])
def mp_webhook():
    """
    Mercado Pago manda aquí notificaciones cuando cambia el estado de un pago.
    Paso:
    - Validamos firma básica (si quieres).
    - Sacamos el payment_id.
    - Le pedimos a MP los detalles finales del pago.
    - Actualizamos la tabla pagos con estado final.
    """
    body_raw = request.get_data(as_text=True)
    signature_header = request.headers.get("x-signature")

    # Validación opcional HMAC con tu secreto:
    if current_app.config.get("MP_WEBHOOK_SECRET"):
        digest = hmac.new(
            current_app.config["MP_WEBHOOK_SECRET"].encode("utf-8"),
            body_raw.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        # Si quisieras bloquear notifs falsas:
        # if digest != signature_header:
        #     return ("bad signature", 400)

    data = request.get_json() or {}

    # Mercado Pago normalmente manda { "type": "payment", "data": { "id": <payment_id> }, ... }
    topic = data.get("type")
    payment_id = None
    if topic == "payment" and "data" in data:
        payment_id = data["data"].get("id")

    if payment_id:
        sdk = mercadopago.SDK(current_app.config["MP_ACCESS_TOKEN"])
        payment_info = sdk.payment().get(payment_id)
        payment_body = payment_info["response"]

        status = payment_body.get("status")  # "approved", "rejected", "in_process", etc.
        external_ref = payment_body.get("external_reference")

        # convertimos status de MP a nuestro estado interno
        if status == "approved":
            estado_local = "APPROVED"
        elif status == "rejected":
            estado_local = "REJECTED"
        elif status in ("in_process", "pending"):
            estado_local = "PENDING_MP"
        else:
            estado_local = "PENDING"

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE pagos
            SET estado=%s,
                mp_payment_id=%s,
                raw_json=%s,
                updated_at=NOW()
            WHERE referencia=%s
        """, (
            estado_local,
            str(payment_id),
            json.dumps(payment_body),
            external_ref
        ))
        mysql.connection.commit()

        # Si estado_local == "APPROVED":
        #   Aquí puedes generar la venta final, factura PDF, etc.

    # Importante: siempre responde 200 para que MP no siga reenviando infinito
    return ("", 200)

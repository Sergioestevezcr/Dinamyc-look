# decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash
from fpdf import FPDF, HTMLMixin


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


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #  Compara insensible a mayúsculas
        if "user_id" not in session or session.get("user_role", "").lower() != "admin":
            flash("Debes iniciar sesión como administrador para continuar.", "warning")
            return redirect(url_for("client_bp.index_cliente"))
        return f(*args, **kwargs)
    return decorated_function


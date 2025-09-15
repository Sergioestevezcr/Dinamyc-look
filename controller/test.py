from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from model import product, user, sale
from model.database import get_db
import sys
from functools import wraps  # Importamos wraps para crear decoradores

# Creamos un Blueprint para las rutas principales
main_bp = Blueprint('test', __name__)


@app.route("/testdb")
def testdb():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DATABASE();")
    db = cur.fetchone()
    cur.close()
    return f"Conectado a la base: {db}"

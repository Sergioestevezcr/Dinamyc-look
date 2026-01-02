#!/usr/bin/env python3
# wsgi.py - Archivo de entrada para servidores WSGI (Apache, Gunicorn, etc.)

import sys
import os

# Añadir el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(__file__))

# Importar la aplicación Flask
from app import create_app

# Crear la instancia de la aplicación
application = create_app()

if __name__ == "__main__":
    application.run()

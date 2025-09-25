# controllers/__init__.py
"""
Paquete controllers: contiene los Blueprints de la aplicación.
"""

from .auth_controller import auth_bp
from .client_controller import client_bp
from .admin_controller import admin_bp
from .diagnostic_controller import diagnostic_bp

__all__ = ["auth_bp", "client_bp", "admin_bp", "diagnostic_bp"]

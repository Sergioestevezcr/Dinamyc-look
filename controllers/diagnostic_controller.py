from flask import Blueprint, jsonify, current_app
import os

diagnostic_bp = Blueprint('diagnostic', __name__)


@diagnostic_bp.route('/verificar_templates')
def verificar_templates():
    BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    template_dir = current_app.template_folder

    resultado = {
        'cwd': os.getcwd(),
        'ruta_absoluta': template_dir,
        'template_folder': current_app.template_folder
    }

    if os.path.exists(template_dir):
        resultado['template_dir_existe'] = True
        resultado['contenido_template_dir'] = os.listdir(template_dir)

        vistas_admin_path = os.path.join(template_dir, 'Vistas_admin')

        if os.path.exists(vistas_admin_path):
            resultado['vistas_admin_existe'] = True
            resultado['contenido_vistas_admin'] = os.listdir(vistas_admin_path)
        else:
            resultado['vistas_admin_existe'] = False
    else:
        resultado['template_dir_existe'] = False

    return jsonify(resultado)


@diagnostic_bp.route('/verificar_static')
def verificar_static():
    BASE_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
    static_dir = os.path.join(BASE_DIR, 'static')
    return jsonify({
        "static_dir": static_dir,
        "static_existe": os.path.exists(static_dir),
        "contenido_static": os.listdir(static_dir) if os.path.exists(static_dir) else []
    })

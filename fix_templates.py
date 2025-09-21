import os
import re

# Carpeta raíz del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Carpetas de plantillas
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
USER_DIR = "Vista_usuario"
ADMIN_DIR = "Vistas_admin"

# Expresión regular para capturar render_template("archivo.html", ...)
pattern = re.compile(r"render_template\(\s*['\"]([^'\"]+)['\"]")


def fix_render_template(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    changed = False
    matches = pattern.findall(content)

    for match in matches:
        if "/" not in match:  # si no tiene carpeta, lo corregimos
            if os.path.exists(os.path.join(TEMPLATES_DIR, USER_DIR, match)):
                new_path = f"{USER_DIR}/{match}"
            elif os.path.exists(os.path.join(TEMPLATES_DIR, ADMIN_DIR, match)):
                new_path = f"{ADMIN_DIR}/{match}"
            else:
                continue  # si no está en ninguna carpeta, lo dejamos igual

            content = content.replace(
                f"render_template('{match}'", f"render_template('{new_path}'")
            content = content.replace(
                f"render_template(\"{match}\"", f"render_template(\"{new_path}\"")
            changed = True
            print(f"✅ Corregido en {path}: {match} → {new_path}")

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def scan_project():
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".py") and file not in ["fix_templates.py"]:
                fix_render_template(os.path.join(root, file))


if __name__ == "__main__":
    print("🔍 Buscando y corrigiendo rutas de render_template...")
    scan_project()
    print("✨ Proceso completado.")

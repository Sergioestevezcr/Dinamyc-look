#!/bin/bash
# Script para forzar tablas a minúsculas en todo el proyecto Flask
# Úsalo desde la raíz del proyecto

echo "🔎 Buscando referencias a tablas con mayúsculas..."

# Lista de tablas que quieres normalizar
TABLES=("Productos" "Usuarios" "Tokens" "Ventas" "Pedidos" "Categorias" "Clientes")

for T in "${TABLES[@]}"; do
    LOWER=$(echo "$T" | tr '[:upper:]' '[:lower:]')
    echo "➡️  Reemplazando $T -> $LOWER ..."
    grep -R --color=always "$T" . || true
    find . -type f -name "*.py" -exec sed -i "s/$T/$LOWER/g" {} +
done

echo "✅ Reemplazo completado."
echo "⚠️ Revisa manualmente si alguna consulta SQL necesita ajustes de columnas también."

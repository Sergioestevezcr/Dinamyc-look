# deploy.ps1 - Script de despliegue para Windows PowerShell

# Variables - AJUSTA ESTOS VALORES
$SERVER_USER = "tu_usuario"
$SERVER_IP = "tu_ip_del_servidor"
$REMOTE_PATH = "/home/$SERVER_USER/public_html/dinamyclook.com"

Write-Host "🚀 Iniciando despliegue de Dinamyc Look..." -ForegroundColor Green

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "❌ ERROR: Archivo .env no encontrado." -ForegroundColor Red
    Write-Host "Copia .env.example a .env y configúralo antes de desplegar." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Archivo .env encontrado" -ForegroundColor Green

# Crear archivo comprimido
Write-Host "📦 Creando archivo comprimido..." -ForegroundColor Cyan

$excludeFiles = @(
    ".git",
    ".venv",
    "__pycache__",
    "*.pyc",
    ".gitignore",
    "deploy.sh",
    "deploy.ps1",
    "*.zip"
)

# Crear lista de archivos a incluir
$files = Get-ChildItem -Path . -Recurse | Where-Object {
    $item = $_
    $exclude = $false
    foreach ($pattern in $excludeFiles) {
        if ($item.FullName -like "*$pattern*") {
            $exclude = $true
            break
        }
    }
    -not $exclude
}

# Comprimir archivos
Compress-Archive -Path * -DestinationPath "dinamyc-look-deploy.zip" -Force -CompressionLevel Optimal

Write-Host "✓ Archivo comprimido creado" -ForegroundColor Green

# Subir archivo al servidor usando SCP
Write-Host "📤 Subiendo archivos al servidor..." -ForegroundColor Cyan

scp dinamyc-look-deploy.zip "${SERVER_USER}@${SERVER_IP}:~/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al subir archivos" -ForegroundColor Red
    Remove-Item "dinamyc-look-deploy.zip"
    exit 1
}

Write-Host "✓ Archivos subidos" -ForegroundColor Green

# Ejecutar comandos en el servidor
Write-Host "⚙️ Configurando en el servidor..." -ForegroundColor Cyan

$sshCommands = @"
mkdir -p ~/public_html/dinamyclook.com
unzip -o ~/dinamyc-look-deploy.zip -d ~/public_html/dinamyclook.com/
cd ~/public_html/dinamyclook.com
if [ ! -d '.venv' ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p tmp
chmod +x wsgi.py
chmod -R 755 static
touch tmp/restart.txt
rm ~/dinamyc-look-deploy.zip
echo '✅ Despliegue completado en el servidor'
"@

ssh "${SERVER_USER}@${SERVER_IP}" $sshCommands

# Limpiar archivo local
Remove-Item "dinamyc-look-deploy.zip"

Write-Host ""
Write-Host "🎉 ¡Despliegue completado exitosamente!" -ForegroundColor Green
Write-Host "Visita tu sitio en: https://dinamyclook.com" -ForegroundColor Cyan

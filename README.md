# Dinamyc Look

![Status](https://img.shields.io/badge/status-completed-success)
![Academic Project](https://img.shields.io/badge/project-academic-blue)
![Institution](https://img.shields.io/badge/institution-SENA-red)
![Location](https://img.shields.io/badge/location-Bogotá%2C%20Colombia-lightgrey)

## Sistema Web de Gestión de Ventas y Divulgación Empresarial

**Dinamyc Look** es una plataforma web desarrollada para la **gestión de ventas, administración de productos y divulgación de información empresarial** de la empresa Dinamyc Look.

El sistema fue desarrollado como **proyecto final del programa Técnico en Programación de Software del SENA**, durante el periodo **enero de 2024 a noviembre de 2025**.

Debido a su impacto, calidad técnica y funcionalidad, el proyecto fue **reconocido y premiado como uno de los mejores proyectos de formación técnica a nivel distrital en Bogotá**.

---

# Tabla de Contenidos

- Descripción del Proyecto
- Objetivos
- Características del Sistema
- Arquitectura del Sistema
- Tecnologías Utilizadas
- Instalación
- Estructura del Proyecto
- Contexto Académico
- Impacto del Proyecto
- Autores
- Control de Versiones
- Licencia

---

# Descripción del Proyecto

El objetivo principal del sistema es **digitalizar procesos comerciales y administrativos**, permitiendo a la empresa organizar su información y mejorar la interacción con clientes a través de una plataforma web.

La aplicación facilita:

- gestión de productos
- registro de ventas
- visualización de información empresarial
- divulgación digital de servicios

Este proyecto representa la aplicación práctica de conocimientos en:

- desarrollo de software
- desarrollo web
- gestión de bases de datos
- arquitectura básica de sistemas
- control de versiones

---

# Objetivos

## Objetivo General

Desarrollar una plataforma web que permita a la empresa **Dinamyc Look gestionar sus ventas y divulgar información empresarial mediante una solución digital eficiente.**

## Objetivos Específicos

- Implementar un sistema de **gestión de productos**.
- Crear una plataforma de **gestión de ventas**.
- Facilitar la **divulgación de información empresarial**.
- Optimizar la organización de procesos comerciales.
- Aplicar conocimientos adquiridos durante la formación en programación de software.

---

# Características del Sistema

El sistema cuenta con funcionalidades orientadas a la gestión empresarial:

- Gestión de productos
- Gestión de ventas
- Visualización de información empresarial
- Interfaz web para usuarios
- Organización de datos comerciales
- Plataforma digital para divulgación de servicios

---

# Arquitectura del Sistema

El sistema sigue una arquitectura básica de aplicaciones web dividiendo el sistema en tres capas principales.

```
                Usuario
                   │
                   ▼
            Interfaz Web
              (Frontend)
                   │
                   ▼
            Lógica del Sistema
              (Backend)
                   │
                   ▼
              Base de Datos
```

### Frontend

Responsable de la interacción con el usuario y la visualización de la información.

### Backend

Gestiona la lógica del sistema, las operaciones de ventas y el control de datos.

### Base de Datos

Almacena de forma estructurada la información comercial del sistema.

---

# Tecnologías Utilizadas

El proyecto fue desarrollado utilizando tecnologías comunes en el desarrollo web:

- HTML5
- CSS3
- JavaScript
- Python
- Frameworks de desarrollo web
- Base de datos relacional
- Git
- GitHub

---

# Instalación

Para ejecutar el proyecto en un entorno local:

## 1 Clonar el repositorio

```bash
git clone https://github.com/Sergioestevezcr/Dinamyc-look.git
```

## 2 Entrar al directorio del proyecto

```bash
cd Dinamyc-look
```

## 3 Ejecutar el sistema

Dependiendo de la configuración del proyecto, iniciar el servidor correspondiente.

---

# Estructura del Proyecto

```
Dinamyc-look/
├── app.py
│     # Archivo principal de la aplicación Flask
│     # Inicializa la app, registra los blueprints y configura la conexión con MySQL.
│
├── config.py
│     # Configuración general: Base de datos, correo, claves, rutas de subida, etc.
│
├── controllers/           # Controladores (Blueprints)
│   ├── __init__.py
│   ├── admin_controller.py       # Rutas del panel administrador
│   ├── auth_controller.py        # Login, registro, recuperación de contraseña
│   ├── client_controller.py      # Rutas del cliente y navegación de productos
│   ├── diagnostic_controller.py  # Verificación de templates y estáticos
│   └── payment_controller.py     # (Si está en uso) Gestión de pagos
│
├── forms/
│   ├── __init__.py
│   ├── admin_form.py      # Formularios usados por el admin
│   └── auth_forms.py       # Formularios de autenticación
│
├── models/                # Modelos (interacción con MySQL)
│   ├── __init__.py
│   ├── user_model.py      # Usuarios y manejo de tokens
│   ├── product_model.py   # Productos y promociones
│   ├── sale_model.py      # Ventas, reportes, facturación
│   └── entity.py          # Clases base o entidades (si aplica)
│
├── services/
│   ├── __init__.py
│   └── email_service.py   # Servicio de envío de correos
│
├── static/
│   ├── css/               # Hojas de estilo
│   │   ├── style_admin.css
│   │   ├── style_index_admin.css
│   │   ├── style_lareceta.css
│   │   ├── style_Anyeluz.css
│   │   ├── style_Dluchi.css
│   │   ├── style_EPA_Colombia.css
│   │   ├── style_Kaba.css
│   │   ├── style_Magic-Hair.css
│   │   ├── style_Milagros.css
│   │   ├── style_OMG.css
│   │   └── (demás archivos CSS por marca)
│   │
│   ├── js/                # Scripts JavaScript
│   │   ├── script_alert.js
│   │   ├── script_carrito.js
│   │   ├── script_carrusel_productos.js
│   │   └── (otros scripts)
│   │
│   └── imagenes/          # Imágenes organizadas por marcas
│       ├── Anyeluz/
│       ├── Dluchi/
│       ├── EPA Colombia/
│       ├── Kaba/
│       ├── La Receta/
│       ├── Magic Hair/
│       ├── Milagros/
│       ├── OMG/
│       ├── La Pocion/
│       └── Logo dinamyc sin fondo.png
│
├── templates/
│   ├── errors/            # Páginas de error
│   │   ├── 404.html
│   │   └── 500.html
│   │
│   ├── paginas/           # Páginas generales (landing, etc.)
│   │   ├── chaceux.html
│   │   ├── pag_entrega.html
│   │   ├── pag_datos.html
│   │   ├── pag_pedidorealizado.html
│   │   └── (otras páginas generales)
│   │
│   ├── Vista_usuario/     # Plantillas del cliente
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── perfil.html
│   │   ├── factura.html
│   │   ├── compras.html
│   │   ├── favoritos.html
│   │   ├── buscar.html
│   │   ├── info_producto.html
│   │   ├── anyeluz.html
│   │   ├── dluchi.html
│   │   ├── milagros.html
│   │   ├── epa-colombia.html
│   │   ├── kaba.html
│   │   ├── lareceta.html
│   │   ├── la-pocion.html
│   │   ├── magic-hair.html
│   │   ├── OMG.html
│   │   └── clave_olvidada.html / clave_nueva.html
│   │
│   └── Vistas_admin/      # Plantillas del panel admin
│       ├── index-admin.html
│       ├── productos.html
│       ├── ventas.html
│       ├── usuarios.html
│       ├── reportes.html
│       ├── descuentos.html
│       ├── configuracion.html
│       ├── factura.html
│       └── token_status.html
│
├── venv/                  # Entorno virtual (no se sube a GitHub)
│
├── database.py            # Conexión a la base de datos (si separado)
├── decorators.py          # Decoradores: login_required, admin_required…
├── requirements.txt       # Dependencias del proyecto
├── Organizacion.txt       # Este archivo
└── run.py                 # Archivo alternativo de ejecución
---

# Contexto Académico

Este proyecto fue desarrollado como **trabajo final del programa Técnico en Programación de Software del Servicio Nacional de Aprendizaje (SENA)**.

Periodo de desarrollo:

**Enero 2024 — Noviembre 2025**

El proyecto fue **reconocido a nivel distrital en Bogotá como uno de los mejores proyectos técnicos**, destacándose por su implementación funcional y su aplicación en un contexto empresarial real.

---

# Impacto del Proyecto

La plataforma permite a la empresa Dinamyc Look:

- Organizar su información comercial
- Digitalizar procesos de ventas
- Mejorar la presentación de productos y servicios
- Contar con una plataforma digital para interacción con clientes

---

# Autores

### Sergio Andrés Soriano Cruz
Desarrollador del proyecto

Áreas de interés:

- Desarrollo de software
- Desarrollo web
- Ciberseguridad
- Sistemas informáticos

---

### Laura Valentina Vargas Ruiz
Desarrolladora del proyecto

---

# Control de Versiones

El proyecto utiliza **Git y GitHub** para el control de versiones, permitiendo:

- seguimiento de cambios
- organización del desarrollo
- colaboración en el proyecto

---

# Licencia

Este proyecto fue desarrollado con fines **académicos y educativos** como parte del proceso de formación del **Servicio Nacional de Aprendizaje (SENA)**.

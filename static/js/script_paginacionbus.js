// ==================== VARIABLES GLOBALES ====================

// Página actual (empieza en 1)
let currentPage = 1;

// Número de productos que se muestran por página
let itemsPerPage = 24;

// Total de productos (lo pasa Flask al HTML con window.TOTAL_PRODUCTOS)
let totalItems = window.TOTAL_PRODUCTOS || 0;

// Selecciona todos los productos (tarjetas con clase "product-card")
const productos = document.querySelectorAll('.product-card');

// Contenedor principal donde están los productos
const container = document.getElementById('productos-container');

// Contenedor de la paginación (los botones << < 1 2 3 > >>)
const paginationContainer = document.getElementById('paginacion');

// Elemento donde se mostrará el texto de "Mostrando X–Y de Z productos"
const paginaInfo = document.getElementById('pagina-info');

// Selector desplegable para elegir cuántos productos mostrar por página
const itemsPerPageSelect = document.getElementById('items-por-pagina');


// ==================== FUNCIONES DE PAGINACIÓN ====================

// Devuelve el número total de páginas según la cantidad de productos
function getTotalPages() {
    return Math.ceil(totalItems / itemsPerPage); // Redondea hacia arriba
}


// Muestra los productos de la página actual y oculta los demás
function updateDisplay() {
    // Calcula el índice inicial y final de los productos que se deben mostrar
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;

    // Recorre todos los productos
    productos.forEach((producto, index) => {
        // Si el producto está dentro del rango de la página → mostrar
        if (index >= startIndex && index < endIndex) {
            producto.classList.remove('hidden'); 
        } 
        // Si no → ocultar
        else {
            producto.classList.add('hidden');
        }
    });

    // Actualiza el texto de "Mostrando X–Y de Z productos"
    updatePageInfo();
}


// Actualiza la información de la página en el texto debajo de la búsqueda
function updatePageInfo() {
    if (totalItems === 0) return; // Si no hay productos, no hace nada

    // Producto inicial de la página actual
    const startItem = (currentPage - 1) * itemsPerPage + 1;
    // Producto final (puede ser menor al total si es la última página)
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);
    // Número total de páginas
    const totalPages = getTotalPages();

    // Inserta el texto en el elemento HTML correspondiente
    if (paginaInfo) {
        paginaInfo.textContent = 
            `Mostrando ${startItem}-${endItem} de ${totalItems} productos`;
    }
}


// Crea los botones de la paginación (<< < 1 2 3 > >>)
function createPagination() {
    // Si no hay paginación necesaria → ocultar el contenedor
    if (!paginationContainer || getTotalPages() <= 1) {
        if (paginationContainer) paginationContainer.style.display = 'none';
        return;
    }

    // Si hay varias páginas → mostrar el contenedor
    paginationContainer.style.display = 'flex';
    // Vaciar el contenido actual (para regenerarlo desde cero)
    paginationContainer.innerHTML = '';

    const totalPages = getTotalPages();

    // Botón para ir a la primera página
    paginationContainer.appendChild(createButton('<<', 1, currentPage === 1));

    // Botón para ir a la página anterior
    paginationContainer.appendChild(createButton('<', currentPage - 1, currentPage === 1));

    // Botones numéricos (1, 2, 3, …, totalPages)
    for (let i = 1; i <= totalPages; i++) {
        paginationContainer.appendChild(createButton(i, i, false, i === currentPage));
    }

    // Botón para ir a la página siguiente
    paginationContainer.appendChild(createButton('>', currentPage + 1, currentPage === totalPages));

    // Botón para ir a la última página
    paginationContainer.appendChild(createButton('>>', totalPages, currentPage === totalPages));
}


// Función que crea un botón de paginación
function createButton(text, page, disabled, active = false) {
    const button = document.createElement('button'); // Crea un <button>
    button.textContent = text;                       // Texto del botón (ej: "1", ">>")
    button.disabled = disabled;                      // Lo desactiva si corresponde

    // Si es la página actual → darle estilo activo
    if (active) button.classList.add('active');

    // Si el botón no está deshabilitado → añadir evento de click
    if (!disabled) {
        button.addEventListener('click', () => goToPage(page));
    }

    return button;
}


// Cambiar de página
function goToPage(page) {
    // Evitar que se salga de los límites
    if (page < 1 || page > getTotalPages()) return;

    // Guardar la página actual
    currentPage = page;

    // Actualizar los productos mostrados y los botones de paginación
    updateDisplay();
    createPagination();

    // Guardar la página en la URL (sin recargar la página)
    const url = new URL(window.location.href);
    url.searchParams.set('page_js', page);
    window.history.replaceState(null, '', url.toString());
}


// ==================== INICIALIZACIÓN ====================

// Cuando el DOM esté listo...
document.addEventListener("DOMContentLoaded", function () {
    // Si hay productos → inicializar la paginación
    if (totalItems > 0) {
        updateDisplay();
        createPagination();
    }

    // Escuchar cuando cambie el select de "productos por página"
    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', (e) => {
            // Guardar nuevo valor
            itemsPerPage = parseInt(e.target.value);
            // Reiniciar a la página 1
            currentPage = 1;
            // Volver a mostrar y actualizar
            updateDisplay();
            createPagination();
        });
    }

    // Revisar si hay una página guardada en la URL (ej: ?page_js=2)
    const urlParams = new URLSearchParams(window.location.search);
    const savedPage = urlParams.get('page_js');

    // Si existe, restaurar esa página
    if (savedPage) {
        currentPage = parseInt(savedPage);
        updateDisplay();
        createPagination();
    }
});
// ==================== FUNCIONES EXTRA ====================

// Función para limpiar todos los filtros de búsqueda
function limpiarFiltros() {
    // Crear un objeto URL con la ruta actual
    const url = new URL(window.location.href);

    // Elimina TODOS los parámetros de la URL (q, categoria, precio, etc.)
    url.search = "";

    // Redirigir al usuario a la URL limpia
    window.location.href = url.toString();
}
// ==================== MANEJO DE SUBCATEGORÍAS DINÁMICAS ====================

// Definir las subcategorías para cada categoría
const subcategoriasPorCategoria = {
    "Cuidado capilar": [
        { value: "shampoo", text: "Shampoo" },
        { value: "acondicionador", text: "Acondicionador" },
        { value: "tratamiento", text: "Tratamiento" }
    ],
    "Cuidado de la piel": [
        { value: "crema", text: "Crema" },
        { value: "bloqueador_solar", text: "Bloqueador Solar" },
        { value: "bronceador", text: "Bronceador" },
        { value: "exfoliante", text: "Exfoliante" }
    ]
};

// Función para actualizar las subcategorías
function actualizarSubcategorias() {
    const categoriaSelect = document.getElementById('categoria');
    const subcategoriaSelect = document.getElementById('subcategoria');
    
    if (!categoriaSelect || !subcategoriaSelect) return;
    
    const categoriaSeleccionada = categoriaSelect.value;
    const subcategoriaActual = subcategoriaSelect.value; // Guardar la selección actual
    
    // Limpiar subcategorías actuales
    subcategoriaSelect.innerHTML = '<option value="">Todas</option>';
    
    // Si hay categoría seleccionada, agregar sus subcategorías
    if (categoriaSeleccionada && subcategoriasPorCategoria[categoriaSeleccionada]) {
        const subcategorias = subcategoriasPorCategoria[categoriaSeleccionada];
        
        subcategorias.forEach(sub => {
            const option = document.createElement('option');
            option.value = sub.value;
            option.textContent = sub.text;
            
            // Mantener la selección si coincide
            if (sub.value === subcategoriaActual) {
                option.selected = true;
            }
            
            subcategoriaSelect.appendChild(option);
        });
    }
}

// Función para remover filtros individuales
function removeFilter(filterName) {
    const url = new URL(window.location.href);
    url.searchParams.delete(filterName);
    window.location.href = url.toString();
}

// ==================== INTEGRACIÓN CON EL CÓDIGO EXISTENTE ====================

// Extender la inicialización existente
document.addEventListener("DOMContentLoaded", function () {
    // ===== CÓDIGO EXISTENTE DE PAGINACIÓN =====
    if (totalItems > 0) {
        updateDisplay();
        createPagination();
    }

    if (itemsPerPageSelect) {
        itemsPerPageSelect.addEventListener('change', (e) => {
            itemsPerPage = parseInt(e.target.value);
            currentPage = 1;
            updateDisplay();
            createPagination();
        });
    }

    const urlParams = new URLSearchParams(window.location.search);
    const savedPage = urlParams.get('page_js');

    if (savedPage) {
        currentPage = parseInt(savedPage);
        updateDisplay();
        createPagination();
    }

    // ===== NUEVO CÓDIGO PARA SUBCATEGORÍAS =====
    const categoriaSelect = document.getElementById('categoria');
    
    if (categoriaSelect) {
        // Actualizar subcategorías al cargar la página
        actualizarSubcategorias();
        
        // Escuchar cambios en la categoría
        categoriaSelect.addEventListener('change', function() {
            actualizarSubcategorias();
        });
    }
});
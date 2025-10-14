// ==================== BARRA DE BÚSQUEDA RESPONSIVE ====================

document.addEventListener('DOMContentLoaded', () => {
	const toggleBtn = document.querySelector('.toggle-search');
	const barraBusqueda = document.querySelector('.barra-de-busqueda');

	// Alterna el dropdown
	if (toggleBtn && barraBusqueda) {
		toggleBtn.addEventListener('click', (e) => {
			e.stopPropagation();
			barraBusqueda.classList.toggle('active');
		});
	}

	// Cierra si se hace click fuera
	document.addEventListener('click', (e) => {
		if (barraBusqueda && !barraBusqueda.contains(e.target)) {
			barraBusqueda.classList.remove('active');
		}
	});

	// Restaura si la pantalla se agranda
	window.addEventListener('resize', () => {
		if (barraBusqueda && window.innerWidth > 980) {
			barraBusqueda.classList.remove('active');
		}
	});
});


// ==================== PAGINACIÓN Y FILTROS ====================

// Página actual
let currentPage = 1;
// Productos por página
let itemsPerPage = 24;
// Total de productos (viene del backend)
let totalItems = window.TOTAL_PRODUCTOS || 0;

// Elementos del DOM
const productos = document.querySelectorAll('.product-card');
const container = document.getElementById('productos-container');
const paginationContainer = document.getElementById('paginacion');
const paginaInfo = document.getElementById('pagina-info');
const itemsPerPageSelect = document.getElementById('items-por-pagina');


// === FUNCIONES DE PAGINACIÓN ===
function getTotalPages() {
	return Math.ceil(totalItems / itemsPerPage);
}

function updateDisplay() {
	const startIndex = (currentPage - 1) * itemsPerPage;
	const endIndex = startIndex + itemsPerPage;

	productos.forEach((producto, index) => {
		if (index >= startIndex && index < endIndex) {
			producto.classList.remove('hidden');
		} else {
			producto.classList.add('hidden');
		}
	});

	updatePageInfo();
}

function updatePageInfo() {
	if (!paginaInfo || totalItems === 0) return;

	const startItem = (currentPage - 1) * itemsPerPage + 1;
	const endItem = Math.min(currentPage * itemsPerPage, totalItems);
	const totalPages = getTotalPages();

	paginaInfo.textContent = `Mostrando ${startItem}-${endItem} de ${totalItems} productos`;
}

function createPagination() {
	if (!paginationContainer || getTotalPages() <= 1) {
		if (paginationContainer) paginationContainer.style.display = 'none';
		return;
	}

	paginationContainer.style.display = 'flex';
	paginationContainer.innerHTML = '';

	const totalPages = getTotalPages();

	paginationContainer.appendChild(createButton('<<', 1, currentPage === 1));
	paginationContainer.appendChild(createButton('<', currentPage - 1, currentPage === 1));

	for (let i = 1; i <= totalPages; i++) {
		paginationContainer.appendChild(createButton(i, i, false, i === currentPage));
	}

	paginationContainer.appendChild(createButton('>', currentPage + 1, currentPage === totalPages));
	paginationContainer.appendChild(createButton('>>', totalPages, currentPage === totalPages));
}

function createButton(text, page, disabled, active = false) {
	const button = document.createElement('button');
	button.textContent = text;
	button.disabled = disabled;
	if (active) button.classList.add('active');

	if (!disabled) {
		button.addEventListener('click', () => goToPage(page));
	}

	return button;
}

function goToPage(page) {
	if (page < 1 || page > getTotalPages()) return;

	currentPage = page;
	updateDisplay();
	createPagination();

	const url = new URL(window.location.href);
	url.searchParams.set('page_js', page);
	window.history.replaceState(null, '', url.toString());
}


// === LIMPIAR FILTROS ===
function limpiarFiltros() {
	const url = new URL(window.location.href);
	url.search = '';
	window.location.href = url.toString();
}


// === SUBCATEGORÍAS DINÁMICAS ===
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

function actualizarSubcategorias() {
	const categoriaSelect = document.getElementById('categoria');
	const subcategoriaSelect = document.getElementById('subcategoria');
	if (!categoriaSelect || !subcategoriaSelect) return;

	const categoriaSeleccionada = categoriaSelect.value;
	const subcategoriaActual = subcategoriaSelect.value;

	subcategoriaSelect.innerHTML = '<option value="">Todas</option>';

	if (categoriaSeleccionada && subcategoriasPorCategoria[categoriaSeleccionada]) {
		subcategoriasPorCategoria[categoriaSeleccionada].forEach(sub => {
			const option = document.createElement('option');
			option.value = sub.value;
			option.textContent = sub.text;
			if (sub.value === subcategoriaActual) option.selected = true;
			subcategoriaSelect.appendChild(option);
		});
	}
}

function removeFilter(filterName) {
	const url = new URL(window.location.href);
	url.searchParams.delete(filterName);
	window.location.href = url.toString();
}


// === INICIALIZACIÓN GENERAL ===
document.addEventListener("DOMContentLoaded", () => {
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

	const categoriaSelect = document.getElementById('categoria');
	if (categoriaSelect) {
		actualizarSubcategorias();
		categoriaSelect.addEventListener('change', actualizarSubcategorias);
	}
});

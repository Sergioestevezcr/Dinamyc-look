class TablePagination {
    constructor(tableSelector, options = {}) {
        this.table = document.querySelector(tableSelector);
        this.tbody = this.table.querySelector('tbody');
        this.originalRows = Array.from(this.tbody.querySelectorAll('tr'));
        
        // Configuración por defecto
        this.config = {
            itemsPerPage: options.itemsPerPage || 10,
            maxVisiblePages: options.maxVisiblePages || 5,
            showInfo: options.showInfo !== false,
            showItemsPerPageSelector: options.showItemsPerPageSelector !== false,
            itemsPerPageOptions: options.itemsPerPageOptions || [5, 10, 25, 50],
            searchSelector: options.searchSelector || null,
            noDataMessage: options.noDataMessage || 'No hay datos disponibles'
        };
        
        this.currentPage = 1;
        this.filteredRows = [...this.originalRows];
        
        this.init();
    }
    
    init() {
        this.createPaginationContainer();
        this.bindSearchFunctionality();
        this.updateDisplay();
    }
    
    createPaginationContainer() {
        // Crear el contenedor de paginación
        const paginationHTML = `
            <div class="pagination-container">
                <div class="pagination-info">
                    <div class="items-info">
                        <span id="pagination-showing">Mostrando 0 a 0 de 0 elementos</span>
                    </div>
                    <div class="items-per-page">
                        <label for="items-per-page">Elementos por página:</label>
                        <select id="items-per-page">
                            ${this.config.itemsPerPageOptions.map(option => 
                                `<option value="${option}" ${option === this.config.itemsPerPage ? 'selected' : ''}>${option}</option>`
                            ).join('')}
                        </select>
                    </div>
                </div>
                <div class="pagination-controls">
                    <button class="pagination-btn" id="first-page" title="Primera página">«</button>
                    <button class="pagination-btn" id="prev-page" title="Página anterior">‹</button>
                    <div class="page-numbers" id="page-numbers"></div>
                    <button class="pagination-btn" id="next-page" title="Página siguiente">›</button>
                    <button class="pagination-btn" id="last-page" title="Última página">»</button>
                </div>
            </div>
        `;
        
        // Insertar después de la tabla
        this.table.insertAdjacentHTML('afterend', paginationHTML);
        
        // Agregar estilos CSS
        this.addPaginationStyles();
        
        // Bind eventos
        this.bindPaginationEvents();
    }
    
    addPaginationStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .pagination-container {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 20px;
                padding: 15px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                flex-wrap: wrap;
                gap: 15px;
            }
            
            .pagination-info {
                display: flex;
                align-items: center;
                gap: 20px;
                flex-wrap: wrap;
            }
            
            .items-per-page {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .items-per-page label {
                font-size: 14px;
                color: #666;
                font-weight: 500;
            }
            
            #items-per-page {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
                cursor: pointer;
                color: #333;
            }
            
            #items-per-page:focus {
                outline: none;
                border-color: #A63054;
                box-shadow: 0 0 0 2px rgba(166, 48, 84, 0.2);
            }
            
            .items-info {
                font-size: 14px;
                color: #666;
                font-weight: 500;
            }
            
            .pagination-controls {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            
            .pagination-btn {
                padding: 8px 12px;
                border: 1px solid #ddd;
                background-color: white;
                cursor: pointer;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                color: #333;
                transition: all 0.3s ease;
                min-width: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .pagination-btn:hover:not(:disabled) {
                background-color: #A63054;
                color: white;
                border-color: #A63054;
            }
            
            .pagination-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                background-color: #f5f5f5;
            }
            
            .pagination-btn.active {
                background-color: #A63054;
                color: white;
                border-color: #A63054;
            }
            
            .page-numbers {
                display: flex;
                gap: 5px;
            }
            
            .no-data-message {
                text-align: center;
                padding: 40px;
                color: #666;
                font-style: italic;
            }
            
            @media screen and (max-width: 768px) {
                .pagination-container {
                    flex-direction: column;
                    gap: 15px;
                    padding: 10px;
                }
                
                .pagination-info {
                    flex-direction: column;
                    gap: 10px;
                    text-align: center;
                }
                
                .pagination-controls {
                    flex-wrap: wrap;
                    justify-content: center;
                }
                
                .pagination-btn {
                    padding: 6px 10px;
                    font-size: 12px;
                    min-width: 35px;
                }
                
                #items-per-page {
                    padding: 6px 10px;
                    font-size: 12px;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    bindPaginationEvents() {
        // Selector de elementos por página
        document.getElementById('items-per-page').addEventListener('change', (e) => {
            this.config.itemsPerPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.updateDisplay();
        });
        
        // Botones de navegación
        document.getElementById('first-page').addEventListener('click', () => {
            this.currentPage = 1;
            this.updateDisplay();
        });
        
        document.getElementById('prev-page').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.updateDisplay();
            }
        });
        
        document.getElementById('next-page').addEventListener('click', () => {
            const totalPages = Math.ceil(this.filteredRows.length / this.config.itemsPerPage);
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.updateDisplay();
            }
        });
        
        document.getElementById('last-page').addEventListener('click', () => {
            const totalPages = Math.ceil(this.filteredRows.length / this.config.itemsPerPage);
            this.currentPage = totalPages;
            this.updateDisplay();
        });
    }
    
    bindSearchFunctionality() {
        if (this.config.searchSelector) {
            const searchInput = document.querySelector(this.config.searchSelector);
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    this.filterRows(e.target.value);
                });
            }
        }
    }
    
    filterRows(searchTerm) {
        const term = searchTerm.toLowerCase().trim();
        
        if (term === '') {
            this.filteredRows = [...this.originalRows];
        } else {
            this.filteredRows = this.originalRows.filter(row => {
                const text = row.textContent.toLowerCase();
                return text.includes(term);
            });
        }
        
        this.currentPage = 1;
        this.updateDisplay();
    }
    
    updateDisplay() {
        const totalItems = this.filteredRows.length;
        const totalPages = Math.ceil(totalItems / this.config.itemsPerPage);
        
        // Asegurar que currentPage esté en rango válido
        if (this.currentPage > totalPages && totalPages > 0) {
            this.currentPage = totalPages;
        }
        
        // Mostrar filas de la página actual
        this.displayCurrentPageRows();
        
        // Actualizar información de paginación
        this.updatePaginationInfo(totalItems);
        
        // Actualizar controles de paginación
        this.updatePaginationControls(totalPages);
    }
    
    displayCurrentPageRows() {
        // Limpiar tbody
        this.tbody.innerHTML = '';
        
        if (this.filteredRows.length === 0) {
            // Mostrar mensaje de no datos
            const colCount = this.table.querySelector('thead tr').children.length;
            const noDataRow = document.createElement('tr');
            noDataRow.innerHTML = `<td colspan="${colCount}" class="no-data-message">${this.config.noDataMessage}</td>`;
            this.tbody.appendChild(noDataRow);
            return;
        }
        
        // Calcular índices de inicio y fin
        const startIndex = (this.currentPage - 1) * this.config.itemsPerPage;
        const endIndex = startIndex + this.config.itemsPerPage;
        
        // Mostrar filas de la página actual
        const currentPageRows = this.filteredRows.slice(startIndex, endIndex);
        currentPageRows.forEach(row => {
            this.tbody.appendChild(row.cloneNode(true));
        });
        
        // CRÍTICO: Restaurar eventos en las filas clonadas
        this.restoreRowEvents();
    }
    
    restoreRowEvents() {
        // Restaurar eventos para los enlaces "Ver Más" en la columna btn-mas
        const verMasLinks = this.tbody.querySelectorAll('.btn-mas a');
        verMasLinks.forEach(link => {
            // Los enlaces <a> con href funcionan nativamente, 
            // pero nos aseguramos de que no tengan eventos bloqueados
            link.style.pointerEvents = 'auto';
        });

        // Restaurar eventos de edición si existen (para otras tablas)
        const editButtons = this.tbody.querySelectorAll('.edit-btn');
        editButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                // Disparar evento personalizado que puede ser capturado por otros scripts
                const editEvent = new CustomEvent('rowEdit', {
                    detail: {
                        button: btn,
                        data: btn.dataset
                    }
                });
                document.dispatchEvent(editEvent);
            });
        });
    }
    
    updatePaginationInfo(totalItems) {
        const startItem = totalItems === 0 ? 0 : (this.currentPage - 1) * this.config.itemsPerPage + 1;
        const endItem = Math.min(this.currentPage * this.config.itemsPerPage, totalItems);
        
        const infoText = `Mostrando ${startItem} a ${endItem} de ${totalItems} elementos`;
        document.getElementById('pagination-showing').textContent = infoText;
    }
    
    updatePaginationControls(totalPages) {
        const firstBtn = document.getElementById('first-page');
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const lastBtn = document.getElementById('last-page');
        
        // Habilitar/deshabilitar botones
        firstBtn.disabled = this.currentPage === 1;
        prevBtn.disabled = this.currentPage === 1;
        nextBtn.disabled = this.currentPage === totalPages || totalPages === 0;
        lastBtn.disabled = this.currentPage === totalPages || totalPages === 0;
        
        // Generar números de página
        this.generatePageNumbers(totalPages);
    }
    
    generatePageNumbers(totalPages) {
        const pageNumbersContainer = document.getElementById('page-numbers');
        pageNumbersContainer.innerHTML = '';
        
        if (totalPages <= 1) return;
        
        const maxVisible = this.config.maxVisiblePages;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);
        
        // Ajustar el rango si es necesario
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }
        
        // Agregar puntos suspensivos al inicio si es necesario
        if (startPage > 1) {
            this.createPageButton(1, pageNumbersContainer);
            if (startPage > 2) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.padding = '8px 4px';
                dots.style.color = '#666';
                pageNumbersContainer.appendChild(dots);
            }
        }
        
        // Agregar números de página
        for (let i = startPage; i <= endPage; i++) {
            this.createPageButton(i, pageNumbersContainer);
        }
        
        // Agregar puntos suspensivos al final si es necesario
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const dots = document.createElement('span');
                dots.textContent = '...';
                dots.style.padding = '8px 4px';
                dots.style.color = '#666';
                pageNumbersContainer.appendChild(dots);
            }
            this.createPageButton(totalPages, pageNumbersContainer);
        }
    }
    
    createPageButton(pageNumber, container) {
        const button = document.createElement('button');
        button.className = 'pagination-btn';
        button.textContent = pageNumber;
        
        if (pageNumber === this.currentPage) {
            button.classList.add('active');
        }
        
        button.addEventListener('click', () => {
            this.currentPage = pageNumber;
            this.updateDisplay();
        });
        
        container.appendChild(button);
    }
    
    // Métodos públicos para interactuar con la paginación
    goToPage(page) {
        const totalPages = Math.ceil(this.filteredRows.length / this.config.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.updateDisplay();
        }
    }
    
    refresh() {
        this.originalRows = Array.from(this.tbody.querySelectorAll('tr'));
        this.filteredRows = [...this.originalRows];
        this.currentPage = 1;
        this.updateDisplay();
    }
    
    destroy() {
        const paginationContainer = document.querySelector('.pagination-container');
        if (paginationContainer) {
            paginationContainer.remove();
        }
        
        // Restaurar todas las filas originales
        this.tbody.innerHTML = '';
        this.originalRows.forEach(row => {
            this.tbody.appendChild(row);
        });
    }
}

// Inicialización automática cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Buscar todas las tablas con clase 'orders-table' y aplicar paginación
    const tables = document.querySelectorAll('.orders-table');
    const tables2 = document.querySelectorAll('.orders-table2');
    
    tables.forEach(table => {
        new TablePagination(`.orders-table`, {
            itemsPerPage: 10,
            maxVisiblePages: 5,
            itemsPerPageOptions: [5, 10, 25, 50],
            searchSelector: '.buscar',
            noDataMessage: 'No se encontraron resultados'
        });
    });

    tables2.forEach(table => {
        new TablePagination(`.orders-table2`, {
            itemsPerPage: 10,
            maxVisiblePages: 5,
            itemsPerPageOptions: [5, 10, 25, 50],
            searchSelector: '.buscar',
            noDataMessage: 'No se encontraron resultados'
        });
    });
});

// Escuchar eventos de edición para mantener la funcionalidad existente
document.addEventListener('rowEdit', function(e) {
    const { button, data } = e.detail;
    
    // Simular clic en el botón original para mantener la funcionalidad
    if (window.openEditModal) {
        window.openEditModal(data);
    }
});

// Exportar la clase para uso manual si es necesario
window.TablePagination = TablePagination;
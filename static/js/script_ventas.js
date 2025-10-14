// Espera a que todo el contenido del DOM esté cargado antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM que se usan en el formulario de ventas
    const addBtn = document.querySelector('.add-btn');
    const addModal = document.getElementById('addModal');
    const cancelAddBtn = document.getElementById('cancelAddBtn');
    const addForm = document.getElementById('addForm');
    const addProductoBtn = document.getElementById('add-producto-btn');
    const productosContainer = document.getElementById('productos-container');

    // ================== CLIENTE (datalist nombre → ID oculto) ==================
    const inputNombre = document.getElementById("usuario-nombre");
    const inputId = document.getElementById("usuario-id");
    const dataListUsuarios = document.getElementById("usuarios-list");

    if (inputNombre) {
        inputNombre.addEventListener("input", function() {
            const valor = inputNombre.value;
            const opcion = Array.from(dataListUsuarios.options).find(opt => opt.value === valor);

            if (opcion) {
                inputId.value = opcion.dataset.id;
            } else {
                inputId.value = "";
            }
        });
    }

    // ----------------- Abrir modal -----------------
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            addModal.style.display = 'flex';
        });
    }

    // ----------------- Cerrar modal -----------------
    if (cancelAddBtn) {
        cancelAddBtn.addEventListener('click', function() {
            addModal.style.display = 'none';
            resetForm();
        });
    }

    window.addEventListener('click', function(event) {
        if (event.target === addModal) {
            addModal.style.display = 'none';
            resetForm();
        }
    });

    // ----------------- Agregar nueva fila de producto -----------------
    if (addProductoBtn) {
        addProductoBtn.addEventListener('click', function() {
            addProductoRow();
        });
    }

    // ----------------- Validar formulario antes de enviar -----------------
    if (addForm) {
        addForm.addEventListener('submit', function(event) {
            if (!validateVentaForm()) {
                event.preventDefault();
                return;
            }
            addModal.style.display = 'none';
        });
    }

    // ----------------- Configurar event listeners iniciales -----------------
    setupProductEventListeners();

    // =================== FUNCIONES AUXILIARES ===================

    // Configura los event listeners para todos los productos
    function setupProductEventListeners() {
        const productoSelects = document.querySelectorAll('.producto-select');
        const cantidadInputs = document.querySelectorAll('.cantidad-input');

        productoSelects.forEach(select => {
            // Usar 'change' en lugar de 'input' para mejor compatibilidad con datalist
            select.addEventListener('change', function() {
                updatePrice(this);
            });
            
            // Añadir blur para capturar cuando el usuario sale del campo
            select.addEventListener('blur', function() {
                updatePrice(this);
            });
        });

        cantidadInputs.forEach(input => {
            input.addEventListener('input', function() {
                updateSubtotal(this);
            });
            
            input.addEventListener('change', function() {
                updateSubtotal(this);
            });
        });
    }

    // Restablece el formulario
    function resetForm() {
        addForm.reset();
        const productosItems = productosContainer.querySelectorAll('.producto-item');
        for (let i = 1; i < productosItems.length; i++) {
            productosItems[i].remove();
        }
        // Limpiar campos calculados de la primera fila
        const firstRow = productosContainer.querySelector('.producto-item');
        if (firstRow) {
            firstRow.querySelector('.precio-display').value = '';
            firstRow.querySelector('.subtotal-display').value = '';
        }
        updateTotal();
    }

    // Duplica la primera fila de producto
    function addProductoRow() {
        const firstProductoItem = productosContainer.querySelector('.producto-item');
        const newProductoItem = firstProductoItem.cloneNode(true);
        
        const inputs = newProductoItem.querySelectorAll('input');
        inputs.forEach(input => {
            input.value = '';
        });
        
        productosContainer.appendChild(newProductoItem);
        setupProductEventListenersForRow(newProductoItem);
    }

    // Configura event listeners para una fila específica
    function setupProductEventListenersForRow(row) {
        const productoSelect = row.querySelector('.producto-select');
        const cantidadInput = row.querySelector('.cantidad-input');

        if (productoSelect) {
            productoSelect.addEventListener('change', function() {
                updatePrice(this);
            });
            
            productoSelect.addEventListener('blur', function() {
                updatePrice(this);
            });
        }

        if (cantidadInput) {
            cantidadInput.addEventListener('input', function() {
                updateSubtotal(this);
            });
            
            cantidadInput.addEventListener('change', function() {
                updateSubtotal(this);
            });
        }
    }

    // Valida los datos del formulario
    function validateVentaForm() {
        const usuarioId = document.getElementById('usuario-id');
        const usuarioNombre = document.getElementById('usuario-nombre');

        if (!usuarioId.value) {
            alert('Por favor, selecciona un cliente válido de la lista');
            usuarioNombre.focus();
            return false;
        }

        const productoSelects = document.querySelectorAll('.producto-select');
        const cantidadInputs = document.querySelectorAll('.cantidad-input');

        let hasValidProduct = false;
        const productosSeleccionados = new Set();

        for (let i = 0; i < productoSelects.length; i++) {
            const producto = productoSelects[i].value;
            const cantidad = cantidadInputs[i].value;

            if (producto && cantidad && parseInt(cantidad) > 0) {
                hasValidProduct = true;

                // Extraer solo el nombre del producto (antes del guión)
                const nombreProducto = producto.split(' - ')[0].trim();
                
                if (productosSeleccionados.has(nombreProducto)) {
                    alert('Este producto ya fue seleccionado. Modifique la cantidad si desea más');
                    productoSelects[i].focus();
                    return false;
                }

                productosSeleccionados.add(nombreProducto);
            }
        }

        if (!hasValidProduct) {
            alert('Por favor, selecciona al menos un producto con cantidad válida');
            return false;
        }

        for (let i = 0; i < productoSelects.length; i++) {
            const producto = productoSelects[i].value;
            const cantidad = cantidadInputs[i].value;

            if (cantidad && parseInt(cantidad) > 0 && !producto) {
                alert('Por favor, selecciona un producto para la cantidad ingresada');
                productoSelects[i].focus();
                return false;
            }

            if (producto && (!cantidad || parseInt(cantidad) <= 0)) {
                alert('Por favor, ingresa una cantidad válida para el producto seleccionado');
                cantidadInputs[i].focus();
                return false;
            }
        }

        return true;
    }

    // =================== FUNCIONES GLOBALES ===================

    // Actualiza el precio cuando se selecciona un producto
    window.updatePrice = function(selectElement) {
    const inputValue = selectElement.value.trim();
    if (!inputValue) return;

    const productoItem = selectElement.closest('.producto-item');
    const precioDisplay = productoItem.querySelector('.precio-display');
    const datalist = document.getElementById('productos-list');
    const options = datalist.querySelectorAll('option');
    
    let precio = null;
    let descuento = 0;
    
    // Buscar coincidencia exacta o parcial
    for (let option of options) {
        const optionValue = option.value.trim();
        if (optionValue === inputValue || optionValue.startsWith(inputValue.split(' - ')[0])) {
            precio = parseFloat(option.getAttribute('data-precio'));
            descuento = parseFloat(option.getAttribute('data-descuento')) || 0;
            
            // Actualizar el input con el valor completo del option si no coincide exactamente
            if (optionValue !== inputValue) {
                selectElement.value = optionValue;
            }
            break;
        }
    }

    if (precio !== null) {
        let precioFinal = precio;

        // Aplicar descuento si existe
        if (descuento > 0) {
            precioFinal = precio - (precio * descuento / 100);
            precioDisplay.value = `$${precioFinal.toLocaleString('es-CO')}`;
        } else {
            precioDisplay.value = `$${precio.toLocaleString('es-CO')}`;
        }

    } else {
        precioDisplay.value = '';
    }

    updateSubtotal(selectElement);
}


    // Calcula y muestra el subtotal
    window.updateSubtotal = function(element) {
    const productoItem = element.closest('.producto-item');
    const productoSelect = productoItem.querySelector('.producto-select');
    const cantidadInput = productoItem.querySelector('.cantidad-input');
    const subtotalDisplay = productoItem.querySelector('.subtotal-display');
    
    const inputValue = productoSelect.value.trim();
    const cantidad = cantidadInput.value;
    
    if (!inputValue || !cantidad || parseInt(cantidad) <= 0) {
        subtotalDisplay.value = '';
        updateTotal();
        return;
    }
    
    const datalist = document.getElementById('productos-list');
    const options = datalist.querySelectorAll('option');
    let precio = null;
    let descuento = 0;
    
    for (let option of options) {
        const optionValue = option.value.trim();
        if (optionValue === inputValue || optionValue.startsWith(inputValue.split(' - ')[0])) {
            precio = parseFloat(option.getAttribute('data-precio'));
            descuento = parseFloat(option.getAttribute('data-descuento')) || 0;
            break;
        }
    }

    if (precio !== null) {
        // Aplica el descuento al subtotal
        const precioFinal = precio - (precio * descuento / 100);
        const subtotal = precioFinal * parseInt(cantidad);
        subtotalDisplay.value = '$' + subtotal.toLocaleString('es-CO');
    } else {
        subtotalDisplay.value = '';
    }

    updateTotal();
}


    // Calcula el total de la venta
    window.updateTotal = function() {
        const subtotalDisplays = document.querySelectorAll('.subtotal-display');
        const totalVentaInput = document.getElementById('total-venta');
        let total = 0;

        subtotalDisplays.forEach(subtotalDisplay => {
            let subtotalValue = subtotalDisplay.value.replace('$', '').trim();
            subtotalValue = subtotalValue.replace(/\./g, '');
            if (subtotalValue && !isNaN(subtotalValue)) {
                total += parseFloat(subtotalValue);
            }
        });

        totalVentaInput.value = '$' + total.toLocaleString('es-CO');
    }

    // Elimina una fila de producto
    window.removeProducto = function(button) {
        const productosItems = document.querySelectorAll('.producto-item');
        if (productosItems.length > 1) {
            const productoItem = button.closest('.producto-item');
            productoItem.remove();
            updateTotal();
        } else {
            alert('Debe mantener al menos una fila de producto');
        }
    }
});
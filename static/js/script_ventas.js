// Espera a que todo el contenido del DOM esté cargado antes de ejecutar el código
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM que se usan en el formulario de ventas
    const addBtn = document.querySelector('.add-btn');           // Botón para abrir el modal
    const addModal = document.getElementById('addModal');        // Contenedor modal
    const cancelAddBtn = document.getElementById('cancelAddBtn');// Botón para cerrar el modal
    const addForm = document.getElementById('addForm');          // Formulario para agregar venta
    const addProductoBtn = document.getElementById('add-producto-btn'); // Botón para añadir filas de productos
    const productosContainer = document.getElementById('productos-container'); // Contenedor de filas de productos

        // ================== CLIENTE (datalist nombre → ID oculto) ==================
    const inputNombre = document.getElementById("usuario-nombre"); // visible
    const inputId = document.getElementById("usuario-id"); // oculto (se envía)
    const dataListUsuarios = document.getElementById("usuarios-list");

    if (inputNombre) {
        inputNombre.addEventListener("input", function() {
            const valor = inputNombre.value;
            const opcion = Array.from(dataListUsuarios.options).find(opt => opt.value === valor);

            if (opcion) {
                // Copiar el ID real al campo oculto
                inputId.value = opcion.dataset.id;
            } else {
                // Si escriben algo no válido, limpiar el hidden
                inputId.value = "";
            }
        });
    }


    // ----------------- Abrir modal al hacer clic en "Agregar" -----------------
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            addModal.style.display = 'flex'; // Muestra el modal
        });
    }

    // ----------------- Cerrar modal al hacer clic en "Cancelar" -----------------
    if (cancelAddBtn) {
        cancelAddBtn.addEventListener('click', function() {
            addModal.style.display = 'none'; // Oculta el modal
            resetForm(); // Restablece el formulario a su estado inicial
        });
    }

    // ----------------- Cerrar modal al hacer clic fuera de su contenido -----------------
    window.addEventListener('click', function(event) {
        if (event.target === addModal) {
            addModal.style.display = 'none';
            resetForm();
        }
    });

    // ----------------- Agregar una nueva fila de producto al formulario -----------------
    if (addProductoBtn) {
        addProductoBtn.addEventListener('click', function() {
            addProductoRow();
        });
    }

    // ----------------- Validar formulario antes de enviar -----------------
    if (addForm) {
        addForm.addEventListener('submit', function(event) {
            // Si la validación falla, detener el envío y mantener el modal abierto
            if (!validateVentaForm()) {
                event.preventDefault();
                return;
            }
        
            // Solo si pasa la validación, cerrar el modal
            addModal.style.display = 'none';
        });
    }

    // ----------------- Configurar event listeners para productos existentes -----------------
    setupProductEventListeners();

    // =================== FUNCIONES AUXILIARES ===================

    // Configura los event listeners para los productos
    function setupProductEventListeners() {
        const productoSelects = document.querySelectorAll('.producto-select');
        const cantidadInputs = document.querySelectorAll('.cantidad-input');

        productoSelects.forEach(select => {
            // Event listener para cuando se selecciona del datalist
            select.addEventListener('input', function() {
                updatePrice(this);
            });
            
            // Event listener para cuando cambia el valor
            select.addEventListener('change', function() {
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

    // Restablece el formulario a su estado inicial
    function resetForm() {
        addForm.reset(); // Limpia los valores de todos los inputs
        // Deja solamente una fila de producto
        const productosItems = productosContainer.querySelectorAll('.producto-item');
        for (let i = 1; i < productosItems.length; i++) {
            productosItems[i].remove(); // Elimina filas extras
        }
        updateTotal(); // Actualiza el total a cero
    }

    // Duplica la primera fila de producto para agregar una nueva
    function addProductoRow() {
        const firstProductoItem = productosContainer.querySelector('.producto-item');
        const newProductoItem = firstProductoItem.cloneNode(true); // Clona la fila
        
        // Limpia los valores del nuevo elemento
        const inputs = newProductoItem.querySelectorAll('input');
        inputs.forEach(input => {
            input.value = ''; // Borra valores de los inputs
        });
        
        productosContainer.appendChild(newProductoItem); // Agrega la fila al contenedor
        
        // Configurar event listeners para la nueva fila
        setupProductEventListenersForRow(newProductoItem);
    }

    // Configura event listeners para una fila específica
    function setupProductEventListenersForRow(row) {
        const productoSelect = row.querySelector('.producto-select');
        const cantidadInput = row.querySelector('.cantidad-input');

        if (productoSelect) {
            productoSelect.addEventListener('input', function() {
                updatePrice(this);
            });
            
            productoSelect.addEventListener('change', function() {
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

    // Valida los datos del formulario de venta antes de enviarlo
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

                // Validar productos duplicados
                if (productosSeleccionados.has(producto)) {
                    alert('Este producto ya fue seleccionado. Modifique la cantidad si desea más');
                    productoSelects[i].focus();
                    return false;
                }

                productosSeleccionados.add(producto);
            }
        }

        if (!hasValidProduct) {
            alert('Por favor, selecciona al menos un producto con cantidad válida');
            return false;
        }

        // Validaciones cruzadas: cantidad sin producto o producto sin cantidad válida
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

        return true; // Si pasó todas las validaciones
    }

    // =================== FUNCIONES GLOBALES ===================

    // Actualiza el precio cuando se selecciona un producto
    window.updatePrice = function(selectElement) {
        const inputValue = selectElement.value;
        const productoItem = selectElement.closest('.producto-item');
        const precioDisplay = productoItem.querySelector('.precio-display');
        
        // Buscar en el datalist el precio correspondiente
        const datalist = document.getElementById('productos-list');
        const options = datalist.querySelectorAll('option');
        let precio = null;
        
        for (let option of options) {
            if (option.value === inputValue) {
                precio = option.getAttribute('data-precio');
                break;
            }
        }
        
        // Muestra el precio en el campo correspondiente
        if (precio) {
            const precioFormateado = parseFloat(precio).toLocaleString('es-CO');
            precioDisplay.value = '$' + precioFormateado;
        } else {
            precioDisplay.value = '';
        }

        updateSubtotal(selectElement); // Actualiza el subtotal al cambiar producto
    }

    // Calcula y muestra el subtotal para la fila
    window.updateSubtotal = function(element) {
        const productoItem = element.closest('.producto-item');
        const productoSelect = productoItem.querySelector('.producto-select');
        const cantidadInput = productoItem.querySelector('.cantidad-input');
        const subtotalDisplay = productoItem.querySelector('.subtotal-display');
        
        const inputValue = productoSelect.value;
        const cantidad = cantidadInput.value;
        
        // Buscar el precio en el datalist
        const datalist = document.getElementById('productos-list');
        const options = datalist.querySelectorAll('option');
        let precio = null;
        
        for (let option of options) {
            if (option.value === inputValue) {
                precio = option.getAttribute('data-precio');
                break;
            }
        }
        
        // Calcula subtotal solo si hay precio y cantidad válida
        if (precio && cantidad && parseInt(cantidad) > 0) {
            const subtotal = parseFloat(precio) * parseInt(cantidad);
            subtotalDisplay.value = '$' + subtotal.toLocaleString('es-CO');
        } else {
            subtotalDisplay.value = '';
        }
        
        updateTotal(); // Recalcula el total general
    }

    // Calcula y muestra el total de la venta sumando todos los subtotales
    window.updateTotal = function() {
        const subtotalDisplays = document.querySelectorAll('.subtotal-display');
        const totalVentaInput = document.getElementById('total-venta');
        let total = 0;

        subtotalDisplays.forEach(subtotalDisplay => {
            let subtotalValue = subtotalDisplay.value.replace('$', '').trim();
            subtotalValue = subtotalValue.replace(/\./g, ''); // quitar separadores de miles
            if (subtotalValue && !isNaN(subtotalValue)) {
                total += parseFloat(subtotalValue);
            }
        });

        totalVentaInput.value = '$' + total.toLocaleString('es-CO');
    }

    // Elimina una fila de producto, dejando al menos una
    window.removeProducto = function(button) {
        const productosItems = document.querySelectorAll('.producto-item');
        if (productosItems.length > 1) {
            const productoItem = button.closest('.producto-item');
            productoItem.remove();
            updateTotal(); // Actualiza el total tras eliminar
        } else {
            alert('Debe mantener al menos una fila de producto');
        }
    }
});
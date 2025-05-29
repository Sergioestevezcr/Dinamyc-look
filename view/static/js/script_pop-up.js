// INICIALIZACIÓN DEL SCRIPT
// Espera a que el contenido del DOM esté completamente cargado antes de ejecutar cualquier código
document.addEventListener('DOMContentLoaded', function() {

    // SELECCIÓN DE ELEMENTOS DEL DOM
    // Botones y controles de interacción
    const addBtn = document.querySelector('.add-btn');            // Botón para agregar nuevo cliente
    const editBtns = document.querySelectorAll('.edit-icon');     // Iconos de edición para cada cliente existente
    
    // Contenedores de modales
    const addModal = document.getElementById('addModal');         // Modal para agregar cliente
    const editModal = document.getElementById('editModal');       // Modal para editar cliente
    
    // Botones de cancelar dentro de los modales
    const cancelAddBtn = document.getElementById('cancelAddBtn'); // Botón cancelar en el modal de agregar
    const cancelEditBtn = document.getElementById('cancelEditBtn'); // Botón cancelar en el modal de editar
    
    // Formularios de los modales
    const addForm = document.getElementById('addForm');           // Formulario para agregar cliente
    const editForm = document.getElementById('editForm');         // Formulario para editar cliente

    // EVENTOS PARA ABRIR MODALES
    // Configuración para abrir el modal de agregar cliente
    addBtn.addEventListener('click', function() {
        addModal.style.display = 'flex';   // Muestra el modal con display flex para centrarlo
    });

    // Configuración para abrir el modal de editar cliente
    // Se aplica a cada botón de edición en la tabla
    editBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Obtiene la fila (tr) que contiene el botón de edición que se clickeó
            const row = this.closest('tr');

            // Extrae los datos de las celdas de la fila seleccionada
            const nombre = row.cells[0].textContent;    // Primera columna: nombre
            const correo = row.cells[1].textContent;    // Segunda columna: correo
            const telefono = row.cells[2].textContent;  // Tercera columna: teléfono
            const password = row.cells[3].textContent;  // Cuarta columna: contraseña

            // Rellena el formulario de edición con los datos existentes
            document.getElementById('edit-nombre').value = nombre;
            document.getElementById('edit-correo').value = correo;
            document.getElementById('edit-telefono').value = telefono;
            document.getElementById('edit-password').value = password;

            // Muestra el modal de edición
            editModal.style.display = 'flex';
        });
    });

    // EVENTOS PARA CERRAR MODALES
    // Cierra el modal de agregar al hacer clic en el botón de cancelar
    cancelAddBtn.addEventListener('click', function() {
        addModal.style.display = 'none';  // Oculta el modal
        addForm.reset();                  // Reinicia el formulario para eliminar datos ingresados
    });

    // Cierra el modal de editar al hacer clic en el botón de cancelar
    cancelEditBtn.addEventListener('click', function() {
        editModal.style.display = 'none';  // Oculta el modal
        editForm.reset();                  // Reinicia el formulario para eliminar cambios no guardados
    });

    // CIERRE DE MODALES HACIENDO CLIC FUERA DEL CONTENIDO
    // Detecta clics en cualquier parte de la ventana
    window.addEventListener('click', function(event) {
        // Si el clic fue directamente en el fondo del modal (no en su contenido)
        if (event.target === addModal) {
            addModal.style.display = 'none';  // Cierra el modal de agregar
            addForm.reset();                  // Limpia el formulario
        }
        if (event.target === editModal) {
            editModal.style.display = 'none';  // Cierra el modal de editar
            editForm.reset();                  // Limpia el formulario
        }
    });
    // ESTO GEERA UN ERROR EN EL EVIO DE LA INFORMACION (LO SOLUCIONO MÁS TARDE JEJEJE)
    // GESTIÓN DE ENVÍO DE FORMULARIOS
    // Maneja el envío del formulario de agregar cliente
    addForm.addEventListener('submit', function(event) {
        event.preventDefault();  // Evita que el formulario se envíe de forma tradicional
                                // y que la página se recargue
    
        // Aquí normalmente iría el código para:
        // 1. Validar los datos ingresados
        // 2. Enviar los datos al servidor mediante una petición AJAX/fetch
        // 3. Actualizar la tabla con el nuevo cliente sin recargar la página

        // Por ahora solo muestra una alerta de éxito simulado
        alert('¡Usuario agregado con éxito!');
        
        // Cierra el modal y limpia el formulario después de "guardar"
        addModal.style.display = 'none';
        addForm.reset();
    });

});
document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.querySelector('.add-btn');
    const addModal = document.getElementById('addModal');
    const editModal = document.getElementById('editModal');
    const cancelAddBtn = document.getElementById('cancelAddBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    const addForm = document.getElementById('addForm');
    const editForm = document.getElementById('editForm');

    // MANEJAR CLICS EN BOTONES DE EDITAR
    document.addEventListener('click', function(event) {
        // Verificar si se hizo clic en un botón de editar
        if (event.target.closest('.edit-btn')) {
            event.preventDefault(); // Prevenir navegación
            
            const editBtn = event.target.closest('.edit-btn');
            
            // Obtener datos de los atributos data-
            const id = editBtn.dataset.id;
            const nombre = editBtn.dataset.nombre;
            const apellido = editBtn.dataset.apellido;
            const correo = editBtn.dataset.correo;
            const telefono = editBtn.dataset.telefono;
            const direccion = editBtn.dataset.direccion;
            const ciudad = editBtn.dataset.ciudad;
            const password = editBtn.dataset.password;
            
            // Llenar el formulario
            document.getElementById('edit-nombre').value = nombre || '';
            document.getElementById('edit-apellido').value = apellido || '';
            document.getElementById('edit-correo').value = correo || '';
            document.getElementById('edit-telefono').value = telefono || '';
            document.getElementById('edit-direccion').value = direccion || '';
            document.getElementById('edit-ciudad').value = ciudad || '';
            document.getElementById('edit-password').value = password || '';
            
            // CORRECCIÓN: Establecer la acción correcta con ID en la URL
            editForm.action = `/update_contact/${id}`;
            
            console.log('ID a actualizar:', id);
            console.log('Acción del formulario:', editForm.action);
            
            // Mostrar el modal
            editModal.style.display = 'flex';
        }
    });

    // EVENTO PARA ABRIR MODAL DE AGREGAR
    addBtn.addEventListener('click', function() {
        addModal.style.display = 'flex';
    });

    // EVENTOS PARA CERRAR MODALES
    cancelAddBtn.addEventListener('click', function() {
        addModal.style.display = 'none';
        addForm.reset();
    });

    cancelEditBtn.addEventListener('click', function() {
        editModal.style.display = 'none';
        editForm.reset();
    });

    // CIERRE DE MODALES HACIENDO CLIC FUERA DEL CONTENIDO
    window.addEventListener('click', function(event) {
        if (event.target === addModal) {
            addModal.style.display = 'none';
            addForm.reset();
        }
        if (event.target === editModal) {
            editModal.style.display = 'none';
            editForm.reset();
        }
    });

    // VALIDACIONES
    addForm.addEventListener('submit', function(event) {
        const nombre = document.getElementById('add-nombre').value.trim();
        const apellido = document.getElementById('add-apellido').value.trim();
        const correo = document.getElementById('add-correo').value.trim();
        const telefono = document.getElementById('add-telefono').value.trim();
        const direccion = document.getElementById('add-direccion').value.trim();
        const ciudad = document.getElementById('add-ciudad').value.trim();
        const clave = document.getElementById('add-password').value.trim();

        if (!nombre || !apellido || !correo || !telefono || !direccion || !ciudad || !clave) {
            event.preventDefault();
            alert('Por favor, completa todos los campos obligatorios');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(correo)) {
            event.preventDefault();
            alert('Por favor, ingresa un correo electrónico válido');
            return;
        }

        addModal.style.display = 'none';
    });

    editForm.addEventListener('submit', function(event) {
        const nombre = document.getElementById('edit-nombre').value.trim();
        const apellido = document.getElementById('edit-apellido').value.trim();
        const correo = document.getElementById('edit-correo').value.trim();
        const telefono = document.getElementById('edit-telefono').value.trim();
        const direccion = document.getElementById('edit-direccion').value.trim();
        const ciudad = document.getElementById('edit-ciudad').value.trim();
        const clave = document.getElementById('edit-password').value.trim();

        if (!nombre || !apellido || !correo || !telefono || !direccion || !ciudad || !clave) {
            event.preventDefault();
            alert('Por favor, completa todos los campos obligatorios');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(correo)) {
            event.preventDefault();
            alert('Por favor, ingresa un correo electrónico válido');
            return;
        }

        console.log('Enviando formulario de edición...');
        editModal.style.display = 'none';
    });
});
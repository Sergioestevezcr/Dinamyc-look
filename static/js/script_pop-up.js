// Espera a que el contenido del DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {

    // Referencias a elementos del DOM que se utilizan en el formulario
    const addBtn = document.querySelector('.add-btn'); // Botón para abrir el modal de agregar
    const addModal = document.getElementById('addModal'); // Modal para agregar nuevos datos
    const editModal = document.getElementById('editModal'); // Modal para editar datos existentes
    const cancelAddBtn = document.getElementById('cancelAddBtn'); // Botón para cancelar el formulario de agregar
    const cancelEditBtn = document.getElementById('cancelEditBtn'); // Botón para cancelar el formulario de editar
    const addForm = document.getElementById('addForm'); // Formulario de agregar
    const editForm = document.getElementById('editForm'); // Formulario de edición

    // FUNCIÓN PARA OBTENER TODOS LOS CAMPOS DE UN FORMULARIO
    function getFormFields(form) {
        const fields = {};
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            // Excluye botones y solo procesa campos válidos
            if (input.type !== 'submit' && input.type !== 'button') {
                // Quita los prefijos 'add-' o 'edit-' del id para obtener el nombre del campo
                const fieldName = input.id.replace(/^(add-|edit-)/, '');
                fields[fieldName] = input; // Guarda el input en el objeto con clave simple
            }
        });

        return fields; // Devuelve un objeto con todos los campos del formulario
    }

    // FUNCIÓN DE VALIDACIÓN DE FORMULARIOS
    function validateForm(form, requiredFields = []) {
        const fields = getFormFields(form); // Obtiene todos los campos del formulario

        // Si no se especificaron campos requeridos, se consideran todos como requeridos
        if (requiredFields.length === 0) {
            requiredFields = Object.keys(fields);
        }

        // Revisa que los campos requeridos no estén vacíos
        for (const fieldName of requiredFields) {
            const field = fields[fieldName];
            if (field && !field.value.trim()) {
                alert(`Por favor, completa el campo: ${fieldName}`);
                field.focus();
                return false;
            }
        }

        // Verifica los campos que parecen ser correos electrónicos
        const emailFields = Object.keys(fields).filter(name => 
            name.includes('correo') || name.includes('email')
        );
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        for (const fieldName of emailFields) {
            const field = fields[fieldName];
            if (field && field.value.trim() && !emailRegex.test(field.value.trim())) {
                alert(`Por favor, ingresa un correo electrónico válido en: ${fieldName}`);
                field.focus();
                return false;
            }
        }

        return true; // Si pasa todas las validaciones, retorna verdadero
    }

    // EVENTO PARA ABRIR EL MODAL DE EDICIÓN AL HACER CLIC EN UN BOTÓN CON LA CLASE .edit-btn
    document.addEventListener('click', function(event) {
        if (event.target.closest('.edit-btn')) {
            event.preventDefault(); // Evita el comportamiento por defecto del enlace o botón
            
            const editBtn = event.target.closest('.edit-btn');
            const editFields = getFormFields(editForm); // Obtiene campos del formulario de edición

            // Llena los campos del formulario con los valores desde los atributos data-
            Object.keys(editFields).forEach(fieldName => {
                const field = editFields[fieldName];
                const dataValue = editBtn.dataset[fieldName]; // Lee valor desde data-fieldname

                if (field && dataValue !== undefined) {
                    field.value = dataValue || ''; // Asigna valor al campo
                }
            });

            // Define dinámicamente la acción del formulario usando el ID y tipo de entidad
            const id = editBtn.dataset.id;
            const baseAction = editForm.dataset.baseAction || '/update'; // Acción base
            const entityType = editForm.dataset.entityType || 'contact'; // Tipo de entidad (por defecto)

            editForm.action = `${baseAction}_${entityType}/${id}`; // Ej: /update_contact/5

            console.log('ID a actualizar:', id);
            console.log('Acción del formulario:', editForm.action);

            editModal.style.display = 'flex'; // Muestra el modal de edición
        }
    });

    // ABRE EL MODAL DE AGREGAR AL HACER CLIC EN EL BOTÓN DE AGREGAR
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            addModal.style.display = 'flex'; // Muestra el modal
        });
    }

    // CIERRA EL MODAL DE AGREGAR Y LIMPIA EL FORMULARIO
    if (cancelAddBtn) {
        cancelAddBtn.addEventListener('click', function() {
            addModal.style.display = 'none'; // Oculta el modal
            addForm.reset(); // Limpia todos los campos del formulario
        });
    }

    // CIERRA EL MODAL DE EDICIÓN Y LIMPIA EL FORMULARIO
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', function() {
            editModal.style.display = 'none';
            editForm.reset();
        });
    }

    // CIERRA LOS MODALES AL HACER CLIC FUERA DEL CONTENIDO DEL MODAL
    window.addEventListener('click', function(event) {
        if (addModal && event.target === addModal) {
            addModal.style.display = 'none';
            addForm.reset();
        }
        if (editModal && event.target === editModal) {
            editModal.style.display = 'none';
            editForm.reset();
        }
    });

    // VALIDACIÓN Y ENVÍO DEL FORMULARIO DE AGREGAR
    if (addForm) {
        addForm.addEventListener('submit', function(event) {
            // Obtiene campos requeridos desde un atributo data en el HTML
            const requiredFields = JSON.parse(addForm.dataset.requiredFields || '[]');

            if (!validateForm(addForm, requiredFields)) {
                event.preventDefault(); // Evita envío si hay errores
                return;
            }

            addModal.style.display = 'none'; // Oculta el modal si todo está correcto
        });
    }

    // VALIDACIÓN Y ENVÍO DEL FORMULARIO DE EDICIÓN
    if (editForm) {
        editForm.addEventListener('submit', function(event) {
            const requiredFields = JSON.parse(editForm.dataset.requiredFields || '[]');

            if (!validateForm(editForm, requiredFields)) {
                event.preventDefault(); // Evita el envío si falla la validación
                return;
            }

            console.log('Enviando formulario de edición...');
            editModal.style.display = 'none'; // Oculta el modal después del envío
        });
    }

});

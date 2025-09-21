document.addEventListener('DOMContentLoaded', function() {

    // --- REFERENCIAS A BOTONES Y MODALES ---
    const addBtn = document.querySelector('.add-btn'); // primer botón "Agregar"
    const addModal = document.getElementById('addModal'); // modal para agregar
    const editModal = document.getElementById('editModal'); // modal para editar
    const asigModal = document.getElementById('asigModal'); // modal para asignar productos/promociones

    // Botones cancelar
    const cancelAddBtn = document.getElementById('cancelAddBtn');
    const cancelEditBtn = document.getElementById('cancelEditBtn');

    // Formularios
    const addForm = document.getElementById('addForm');
    const editForm = document.getElementById('editForm');
    const promoForm = document.getElementById('promoForm'); // nuevo form de asignar

    // Segundo botón de la página: "Seleccionar producto"
    const selectProdBtn = document.querySelectorAll('.add-btn')[1]; 


    // --- FUNCIONES COMUNES ---

    // Extrae los campos de un formulario en un objeto
    function getFormFields(form) {
        const fields = {};
        const inputs = form.querySelectorAll('input, select, textarea');

        inputs.forEach(input => {
            if (input.type !== 'submit' && input.type !== 'button') {
                const fieldName = input.id.replace(/^(add-|edit-)/, '');
                fields[fieldName] = input;
            }
        });

        return fields;
    }

    // Valida campos obligatorios y correos electrónicos
    function validateForm(form, requiredFields = []) {
        const fields = getFormFields(form);

        if (requiredFields.length === 0) {
            requiredFields = Object.keys(fields);
        }

        for (const fieldName of requiredFields) {
            const field = fields[fieldName];
            if (field && !field.value.trim()) {
                alert(`Por favor, completa el campo: ${fieldName}`);
                field.focus();
                return false;
            }
        }

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

        return true;
    }

    // Previsualización de imágenes en inputs tipo "file"
    function previewImage(input, previewId) {
        const preview = document.getElementById(previewId);
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.style.display = "block";
            };
            reader.readAsDataURL(input.files[0]);
        }
    }


    // --- ABRIR MODAL EDITAR ---
    document.addEventListener('click', function(event) {
        if (event.target.closest('.edit-btn')) {
            event.preventDefault();

            const editBtn = event.target.closest('.edit-btn');
            const editFields = getFormFields(editForm);

            Object.keys(editFields).forEach(fieldName => {
                const field = editFields[fieldName];
                const dataValue = editBtn.dataset[fieldName];
                if (field) {
                    if (field.type === "file") {
                        const preview = document.getElementById(`preview-edit-${fieldName}`);
                        if (preview && dataValue) {
                            preview.src = dataValue;
                            preview.style.display = "block";
                        }
                    } else {
                        field.value = dataValue || '';
                    }
                }
            });

            const id = editBtn.dataset.id;
            const baseAction = editForm.dataset.baseAction || '/update';
            editForm.action = `${baseAction}/${id}`;
            editModal.style.display = 'flex';
        }
    });


    // --- ABRIR OTROS MODALES ---
    if (addBtn) {
        addBtn.addEventListener('click', function() {
            addModal.style.display = 'flex';
        });
    }

    if (selectProdBtn) {
        selectProdBtn.addEventListener('click', function() {
            asigModal.style.display = 'flex';
        });
    }


    // --- CERRAR MODALES ---
    function closeModal(modal, form) {
        if (modal) modal.style.display = 'none';
        if (form) {
            form.reset();
            form.querySelectorAll("img.preview").forEach(img => img.style.display = "none");
        }
    }

    if (cancelAddBtn) cancelAddBtn.addEventListener('click', () => closeModal(addModal, addForm));
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', () => closeModal(editModal, editForm));

    window.addEventListener('click', function(event) {
        if (event.target === addModal) closeModal(addModal, addForm);
        if (event.target === editModal) closeModal(editModal, editForm);
        if (event.target === asigModal) closeModal(asigModal, promoForm);
    });


    // --- SUBMIT FORMS (validaciones) ---
    if (addForm) {
        addForm.addEventListener('submit', function(event) {
            const requiredFields = JSON.parse(addForm.dataset.requiredFields || '[]');
            if (!validateForm(addForm, requiredFields)) {
                event.preventDefault();
            }
        });
    }

    if (editForm) {
        editForm.addEventListener('submit', function(event) {
            const requiredFields = JSON.parse(editForm.dataset.requiredFields || '[]');
            if (!validateForm(editForm, requiredFields)) {
                event.preventDefault();
            }
        });
    }


    // --- FORMULARIO DE ASIGNAR (promoForm) ---
    if (promoForm) {
        promoForm.addEventListener('submit', function(event) {
            const promocion = document.getElementById('edit-promocion').value;

            const productosIds = Array.from(document.querySelectorAll('.producto-id'))
                .map(input => input.value)
                .filter(val => val.trim() !== '');

            if (productosIds.length === 0) {
                alert("Debes seleccionar al menos un producto válido.");
                event.preventDefault();
                return;
            }

            if (!promocion) {
                if (!confirm("No has seleccionado ninguna promoción. ¿Deseas continuar sin asignar promoción?")) {
                    event.preventDefault();
                    return;
                }
            }
        });

        // ✅ Corregido: id correcto del botón "Agregar Producto"
        document.getElementById('add-producto-btn').addEventListener('click', function() {
            const container = document.getElementById('productos-container');
            const item = container.querySelector('.producto-item');
            const clone = item.cloneNode(true);

            clone.querySelector('.producto-select').value = '';
            clone.querySelector('.producto-id').value = '';

            container.appendChild(clone);
        });

        // ✅ Corregido: usar la clase real del botón eliminar
        document.getElementById('productos-container').addEventListener('click', function(e) {
            if (e.target.closest('.btn-remove-producto')) {
                const items = document.querySelectorAll('.producto-item');
                if (items.length > 1) {
                    e.target.closest('.producto-item').remove();
                } else {
                    alert("Debe haber al menos un producto.");
                }
            }
        });

        // Sincronizar input visible con input hidden
        document.getElementById('productos-container').addEventListener('input', function(e) {
            if (e.target.classList.contains('producto-select')) {
                const input = e.target;
                const option = Array.from(document.getElementById('productos-list').options)
                    .find(opt => opt.value === input.value);
                const hidden = input.closest('.producto-item').querySelector('.producto-id');
                hidden.value = option ? option.dataset.id : '';
            }
        });
    }


    // --- PREVISUALIZAR ARCHIVOS ---
    document.querySelectorAll("input[type='file']").forEach(input => {
        input.addEventListener("change", function() {
            const previewId = `preview-${this.id}`;
            previewImage(this, previewId);
        });
    });

});

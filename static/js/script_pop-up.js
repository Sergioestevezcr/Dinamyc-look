// Ejecuta todo el código solo cuando el DOM ya esté cargado
document.addEventListener('DOMContentLoaded', function () {

    // --- REFERENCIAS A ELEMENTOS DEL DOM ---
    var addBtn = document.querySelector('.add-btn'); // Botón principal para abrir el modal de agregar
    var addModal = document.getElementById('addModal'); // Modal de agregar producto
    var editModal = document.getElementById('editModal'); // Modal de editar producto
    var asigModal = document.getElementById('asigModal'); // Modal de asignar promociones
    var cancelAddBtn = document.getElementById('cancelAddBtn'); // Botón de cancelar en modal de agregar
    var cancelEditBtn = document.getElementById('cancelEditBtn'); // Botón de cancelar en modal de editar
    var addForm = document.getElementById('addForm'); // Formulario de agregar
    var editForm = document.getElementById('editForm'); // Formulario de editar
    var promoForm = document.getElementById('promoForm'); // Formulario de asignar promociones
    var selectProdBtn = document.querySelectorAll('.add-btn')[1]; // Segundo botón "Agregar", usado para asignar productos

    // --- FUNCIONES DE UTILIDAD ---
    function getFormFields(form) {
        // Devuelve un objeto con los campos del formulario indexados por nombre
        var fields = {};
        if (!form) return fields; // Si no existe el form, devolver vacío
        var inputs = form.querySelectorAll('input, select, textarea'); // Selecciona todos los inputs
        for (var i = 0; i < inputs.length; i++) {
            var input = inputs[i];
            if (input.type === 'submit' || input.type === 'button') continue; // Omite botones
            var raw = input.id || input.name || ''; // Usa id o name como referencia
            var fieldName = raw.replace(/^(add-|edit-)/, ''); // Limpia prefijos "add-" o "edit-"
            fields[fieldName] = input; // Guarda el campo en el objeto
        }
        return fields;
    }

    function validateForm(form, requiredFields) {
        // Valida que todos los campos requeridos estén llenos
        var fields = getFormFields(form);
        requiredFields = requiredFields || [];
        if (requiredFields.length === 0) requiredFields = Object.keys(fields); // Si no se pasa lista, toma todos
        for (var i = 0; i < requiredFields.length; i++) {
            var name = requiredFields[i];
            var f = fields[name];
            if (f && !String(f.value || '').trim()) { // Campo vacío
                alert('Por favor, completa el campo: ' + name);
                f.focus();
                return false; // Cancela validación
            }
        }
        return true; // Todo válido
    }

    function previewImage(input, previewId) {
        // Muestra una previsualización de imagen seleccionada
        var preview = document.getElementById(previewId);
        if (!preview) return;
        if (input.files && input.files[0]) {
            var reader = new FileReader(); // Lector de archivos
            reader.onload = function (e) {
                preview.src = e.target.result; // Asigna la imagen cargada
                preview.style.display = 'block'; // Muestra el elemento
            };
            reader.readAsDataURL(input.files[0]); // Lee el archivo como URL
        }
    }

    function collectDataAttributes(el) {
        // Extrae todos los atributos "data-*" de un elemento y devuelve un mapa
        var map = {};
        if (!el || !el.attributes) return map;
        for (var i = 0; i < el.attributes.length; i++) {
            var attr = el.attributes[i];
            if (!attr.name || attr.name.indexOf('data-') !== 0) continue; // Solo procesa data-*
            var keyRaw = attr.name.slice(5); // Elimina "data-"
            var val = attr.value;
            map[keyRaw] = val; // Original
            map[keyRaw.replace(/-/g, '_')] = val; // Variante con guiones bajos
            map[keyRaw.replace(/_/g, '-')] = val; // Variante con guiones
            map[keyRaw.toLowerCase()] = val; // Variante minúscula
            // Generar clave en camelCase
            var parts = keyRaw.split(/[-_]/);
            var camel = '';
            for (var j = 0; j < parts.length; j++) {
                camel += (j === 0) ? parts[j] : parts[j].charAt(0).toUpperCase() + parts[j].slice(1);
            }
            map[camel] = val;
        }
        return map;
    }

    function setSelectValue(select, value) {
        // Intenta seleccionar una opción en un <select> dado un valor
        if (!select || value === undefined || value === null || value === '') return false;
        var opts = select.options || [];

        // Busca por value exacto
        for (var i = 0; i < opts.length; i++) {
            var o = opts[i];
            if (o.value == value) { select.value = o.value; select.dispatchEvent(new Event('change')); return true; }
        }

        // Busca por atributo data-id
        for (var i2 = 0; i2 < opts.length; i2++) {
            var o2 = opts[i2];
            if (o2.dataset && o2.dataset.id == value) { select.value = o2.value; select.dispatchEvent(new Event('change')); return true; }
        }

        // Busca por texto exacto
        for (var i3 = 0; i3 < opts.length; i3++) {
            var o3 = opts[i3];
            if ((o3.textContent || '').trim() === String(value).trim()) { select.value = o3.value; select.dispatchEvent(new Event('change')); return true; }
        }

        // Busca por coincidencia parcial en el texto
        for (var i4 = 0; i4 < opts.length; i4++) {
            var o4 = opts[i4];
            if ((o4.textContent || '').trim().indexOf(String(value).trim()) !== -1) { select.value = o4.value; select.dispatchEvent(new Event('change')); return true; }
        }

        console.warn('No match select', select.id || select.name, value);
        return false;
    }

    // --- ABRIR MODAL DE EDICIÓN ---
    document.addEventListener('click', function (event) {
        if (!event.target || !event.target.closest) return;
        var btn = event.target.closest('.edit-btn'); // Botón que abre modal editar
        if (!btn) return;
        event.preventDefault();

        if (!editForm) { console.error('editForm no existe'); return; }

        var fields = getFormFields(editForm); // Campos del form editar
        var data = collectDataAttributes(btn); // Datos en atributos data-*
        console.log('edit btn data:', data);

        // Intenta asignar valores a los campos
        var keys = Object.keys(fields);
        for (var i = 0; i < keys.length; i++) {
            var key = keys[i];
            var field = fields[key];
            if (!field) continue;

            // Posibles claves relacionadas al campo
            var candKeys = [
                key.toLowerCase(),
                (field.id || '').replace(/^(add-|edit-)/, '').toLowerCase(),
                (field.name || '').toLowerCase(),
                'id_proveedor', 'id-proveedor', 'idproveedor', 'proveedor', 'marca',
                'id_promocion', 'id-promocion', 'idpromocion', 'promocion'
            ];

            var found;
            for (var k = 0; k < candKeys.length; k++) {
                var ck = candKeys[k];
                if (!ck) continue;
                if (data.hasOwnProperty(ck)) { found = data[ck]; break; }
                var cku = ck.replace(/-/g, '_');
                if (data.hasOwnProperty(cku)) { found = data[cku]; break; }
                var ckd = ck.replace(/_/g, '-');
                if (data.hasOwnProperty(ckd)) { found = data[ckd]; break; }
            }

            if (found === undefined && data.hasOwnProperty(key)) found = data[key];

            // Dependiendo del tipo de campo
            if (field.type === 'file') {
                var preview = document.getElementById('preview-' + (field.id || '')) || document.getElementById('preview-edit-' + key);
                if (preview && found) { preview.src = found; preview.style.display = 'block'; }
            } else if (field.tagName === 'SELECT') {
                if (found) { setSelectValue(field, found); } else { field.value = ''; }
            } else {
                field.value = (found !== undefined && found !== null) ? found : '';
            }

            console.log('campo -> ' + key + ': asignado ->', found);
        }

        // Validaciones especiales para selects de proveedor y promoción
        var proveedorSelect = document.getElementById('edit-proveedor') || editForm.querySelector("select[name='ID_ProveedorFK']");
        var promoSelect = document.getElementById('edit-promocion') || editForm.querySelector("select[name='ID_PromocionFK']");

        var posibleProveedor = data.id_proveedor || data['id-proveedor'] || data.idproveedor || data.proveedor || data.marca || data.ID_ProveedorFK || data.idProveedor;
        if (proveedorSelect && posibleProveedor) {
            var okProv = setSelectValue(proveedorSelect, posibleProveedor);
            if (!okProv) console.warn('Proveedor no se pudo seleccionar con:', posibleProveedor);
        }

        var posiblePromocion = data.id_promocion || data['id-promocion'] || data.idpromocion || data.promocion || data.ID_PromocionFK || data.idPromocion;
        if (promoSelect && posiblePromocion) {
            var okPromo = setSelectValue(promoSelect, posiblePromocion);
            if (!okPromo) console.warn('Promoción no se pudo seleccionar con:', posiblePromocion);
        }

        // Ajusta la acción del formulario
        var idFromBtn = data.id || btn.getAttribute('data-id');
        var baseAction = editForm.dataset.baseAction || '/update';
        if (idFromBtn) { editForm.action = baseAction + '/' + idFromBtn; }

        // Muestra el modal de edición
        editModal.style.display = 'flex';
    });

    // --- APERTURA Y CIERRE DE OTROS MODALES ---
    if (addBtn) addBtn.addEventListener('click', function () { addModal.style.display = 'flex'; });
    if (selectProdBtn) selectProdBtn.addEventListener('click', function () { asigModal.style.display = 'flex'; });

    function closeModal(modal, form) {
        // Cierra un modal y resetea su formulario
        if (modal) modal.style.display = 'none';
        if (form) {
            form.reset();
            var imgs = form.querySelectorAll('img.preview'); // Oculta previews
            for (var i = 0; i < imgs.length; i++) imgs[i].style.display = 'none';
        }
    }
    if (cancelAddBtn) cancelAddBtn.addEventListener('click', function () { closeModal(addModal, addForm); });
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', function () { closeModal(editModal, editForm); });

    window.addEventListener('click', function (event) {
        // Cierra los modales al hacer clic fuera
        if (event.target === addModal) closeModal(addModal, addForm);
        if (event.target === editModal) closeModal(editModal, editForm);
        if (event.target === asigModal) closeModal(asigModal, promoForm);
    });

    // --- VALIDACIÓN DE SUBMIT EN FORMULARIOS ---
    if (addForm) {
        addForm.addEventListener('submit', function (event) {
            var requiredFields = JSON.parse(addForm.dataset.requiredFields || '[]');
            if (!validateForm(addForm, requiredFields)) event.preventDefault();
        });
    }
    if (editForm) {
        editForm.addEventListener('submit', function (event) {
            var requiredFields = JSON.parse(editForm.dataset.requiredFields || '[]');
            if (!validateForm(editForm, requiredFields)) event.preventDefault();
        });
    }

    // --- FORMULARIO DE ASIGNAR PROMOCIÓN ---
    if (promoForm) {
        promoForm.addEventListener('submit', function (event) {
            var promocion = document.getElementById('edit-promocion') ? document.getElementById('edit-promocion').value : null;
            var productosIds = Array.prototype.slice.call(document.querySelectorAll('.producto-id'))
                .map(function (i) { return i.value; })
                .filter(function (v) { return v.trim() !== ''; });
            if (productosIds.length === 0) { alert('Debes seleccionar al menos un producto válido.'); event.preventDefault(); return; }
            if (!promocion) { if (!confirm('No has seleccionado ninguna promoción. ¿Deseas continuar sin asignar promoción?')) { event.preventDefault(); return; } }
        });

        // Lógica para añadir y eliminar productos en el formulario de asignar
        var addProductoBtn = document.getElementById('add-producto-btn');
        var productosContainer = document.getElementById('productos-container');
        if (addProductoBtn && productosContainer) {
            addProductoBtn.addEventListener('click', function () {
                var item = productosContainer.querySelector('.producto-item'); // Toma un ítem de producto
                var clone = item.cloneNode(true); // Lo clona
                var select = clone.querySelector('.producto-select'); // Select del producto
                var hidden = clone.querySelector('.producto-id'); // Input hidden del ID
                if (select) select.value = '';
                if (hidden) hidden.value = '';
                productosContainer.appendChild(clone); // Agrega el clon
            });

            productosContainer.addEventListener('click', function (e) {
                if (e.target.closest('.btn-remove-producto')) {
                    var items = productosContainer.querySelectorAll('.producto-item');
                    if (items.length > 1) e.target.closest('.producto-item').remove(); else alert('Debe haber al menos un producto.');
                }
            });

            productosContainer.addEventListener('input', function (e) {
                if (e.target.classList && e.target.classList.contains('producto-select')) {
                    var input = e.target;
                    var option = Array.prototype.slice.call(document.getElementById('productos-list').options)
                        .find(function (opt) { return opt.value === input.value; });
                    var hidden = input.closest('.producto-item').querySelector('.producto-id');
                    if (hidden) hidden.value = option ? option.dataset.id : '';
                }
            });
        }
    }

    // --- PREVISUALIZACIÓN DE ARCHIVOS ---
    var fileInputs = document.querySelectorAll('input[type="file"]');
    for (var fi = 0; fi < fileInputs.length; fi++) {
        fileInputs[fi].addEventListener('change', function () {
            var previewId = 'preview-' + this.id; // Crea id para la imagen preview
            previewImage(this, previewId); // Llama función preview
        });
    }

        // --- VER MÁS / VER MENOS EN DESCRIPCIONES ---
    const botonesVerMas = document.querySelectorAll('.ver-mas-btn');

    botonesVerMas.forEach((btn) => {
        btn.addEventListener('click', function () {
            const descripcionCompleta = this.previousElementSibling;
            const descripcionCorta = descripcionCompleta.previousElementSibling;

            if (descripcionCompleta.classList.contains('mostrar')) {
                descripcionCompleta.classList.remove('mostrar');
                descripcionCorta.style.display = 'block';
                this.textContent = 'Ver más';
            } else {
                descripcionCompleta.classList.add('mostrar');
                descripcionCorta.style.display = 'none';
                this.textContent = 'Ver menos';
            }
        });
    });

}); // Fin de DOMContentLoaded

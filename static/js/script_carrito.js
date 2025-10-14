// ==================== Carrito de compras con Flask ====================

// Selecciona el ícono del carrito en la página
const carritoIcon = document.querySelector(".bxs-shopping-bags");

// Crea un contenedor <div> para el carrito
const carrito = document.createElement("div");
carrito.id = "carrito"; // Asigna un id para poder manipularlo con CSS y JS

// Define el contenido HTML del carrito
carrito.innerHTML = `
    <div id="carrito-header">
        <h2>Carrito de Compras</h2>
        <button id="cerrar-carrito">&times;</button> <!-- Botón para cerrar -->
    </div>
    <div id="carrito-items"></div> <!-- Aquí se agregarán los productos -->
    <div id="carrito-footer">
        <p>Total: $<span id="carrito-total">0</span></p> <!-- Total dinámico -->
        <form id="form-finalizar" method="POST" action="/carrito_finalizar">
            <button type="submit" id="finalizar-compra">Finalizar Compra</button>
        </form>
    </div>
`;

// Agrega el carrito al body de la página
document.body.appendChild(carrito);

// Crea un badge para mostrar la cantidad de productos en el carrito
const carritoBadge = document.createElement("span");
carritoBadge.classList.add("carrito-badge");
carritoIcon.parentElement.style.position = "relative";
carritoIcon.parentElement.appendChild(carritoBadge);

// Referencias a elementos dentro del carrito
const cerrarCarritoBtn = document.getElementById("cerrar-carrito");
const carritoItems = document.getElementById("carrito-items");
const carritoTotal = document.getElementById("carrito-total");

// Array para almacenar los productos del carrito
let carritoData = [];

// ==================== FUNCIONES ====================

// Actualiza el badge que muestra la cantidad de productos
function actualizarBadge(total) {
    carritoBadge.style.display = total > 0 ? "block" : "none";
    carritoBadge.textContent = total;
}

// Carga los productos del carrito desde el backend
async function cargarCarrito() {
    const resp = await fetch("/carrito_get");
    const data = await resp.json();
    carritoData = data;
    renderCarrito();
}

// Renderiza los productos en el carrito
function renderCarrito() {
    carritoItems.innerHTML = "";
    let total = 0;

    carritoData.forEach(item => {
        const subtotal = item.precio * item.cantidad;
        total += subtotal;

        const div = document.createElement("div");
        div.classList.add("carrito-item");
        div.innerHTML = `
            <img src="${item.img}" alt="${item.nombre}">
            <div class="datos">
                <h4>${item.nombre}</h4>
                <input type="number" class="cantidad-item" min="1" value="${item.cantidad}" data-id="${item.id}">
            </div>
            <p class="subtotal">$${subtotal.toLocaleString("es-CO")}</p>
            <form method="POST" action="/carrito_eliminar/${item.id}">
                <button type="submit"><i class="fas fa-trash"></i></button>
            </form>
        `;
        carritoItems.appendChild(div);

        const inputCantidad = div.querySelector(".cantidad-item");
        const pSubtotal = div.querySelector(".subtotal");

        // Evento para actualizar subtotal y total en front-end
        inputCantidad.addEventListener("input", () => {
            let nuevaCantidad = parseInt(inputCantidad.value);
            if (isNaN(nuevaCantidad) || nuevaCantidad < 1) nuevaCantidad = 1;
            inputCantidad.value = nuevaCantidad;

            const nuevoSubtotal = item.precio * nuevaCantidad;
            pSubtotal.textContent = `$${nuevoSubtotal.toLocaleString("es-CO")}`;

            let totalTemp = 0;
            carritoData.forEach(dataItem => {
                totalTemp += dataItem.precio * dataItem.cantidad;
            });
            carritoTotal.textContent = totalTemp.toLocaleString("es-CO");
        });

        // Evento para actualizar cantidad exacta en el backend
        inputCantidad.addEventListener("change", async () => {
            let nuevaCantidad = parseInt(inputCantidad.value);
            if (isNaN(nuevaCantidad) || nuevaCantidad < 1) nuevaCantidad = 1;

            // Enviar la cantidad exacta al backend
            await fetch("/carrito_actualizar", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({
                    id: item.id,
                    cantidad: nuevaCantidad
                })
            });

            // Actualiza localmente
            item.cantidad = nuevaCantidad;
            renderCarrito(); // Re-renderiza para asegurar consistencia
        });
    });

    carritoTotal.textContent = total.toLocaleString("es-CO");
    actualizarBadge(carritoData.length);
}

// ==================== EVENTOS ====================

// Mostrar carrito al hacer click en el ícono
carritoIcon.addEventListener("click", async () => {
    carrito.classList.add("active");
    // Siempre cargar carrito al abrir para sincronizar con servidor
    await cargarCarrito();
});

// Cerrar carrito
cerrarCarritoBtn.addEventListener("click", () => {
    carrito.classList.remove("active");
});

// Función para agregar producto al carrito
async function agregarAlCarrito(nombre, precio, img, cantidad = 1) {
    try {
        const response = await fetch("/carrito_agregar", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ nombre, precio, cantidad, img })
        });
        
        if (response.ok) {
            // Actualizar carrito localmente sin recargar desde servidor
            const productoExistente = carritoData.find(item => item.nombre === nombre);
            if (productoExistente) {
                productoExistente.cantidad += cantidad;
            } else {
                carritoData.push({
                    id: Date.now(), // ID temporal
                    nombre: nombre,
                    precio: precio,
                    img: img,
                    cantidad: cantidad
                });
            }
            renderCarrito();
        }
    } catch (error) {
        console.error("Error al agregar al carrito:", error);
    }
}

// Botones para agregar productos en otras páginas
document.querySelectorAll(".btn-add").forEach(btn => {
    btn.addEventListener("click", async (e) => {
        e.preventDefault();

        const card = e.target.closest(".text-card, .text-card2, .text-card4");
        if (card) {
            const nombre = card.querySelector("h3").textContent;
            const precioElement = card.querySelector(".text-precio");
            
            // Verificar si hay precio con descuento
            let precio;
            const precioDescuento = precioElement.querySelector(".precio-descuento");
            
            if (precioDescuento) {
                // Si hay descuento, tomar el precio final (con descuento)
                precio = parseInt(precioDescuento.textContent.replace(/\D/g, ""));
            } else {
                // Si no hay descuento, tomar el precio normal
                precio = parseInt(precioElement.textContent.replace(/\D/g, ""));
            }
            
            const img = card.parentElement.querySelector("img").src;
            await agregarAlCarrito(nombre, precio, img, 1);
        }
    });
});

// ==================== EVENTOS PÁGINA DETALLES ====================

function configurarBotonesCantidad() {
    const cantidadInput = document.getElementById("cantidad");
    if (!cantidadInput) return;

    const botonesAcciones = document.querySelectorAll(".cantidad button");
    botonesAcciones.forEach((btn, index) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            let cantidad = parseInt(cantidadInput.value);
            if (index === 0) cantidad = Math.max(1, cantidad - 1);
            else cantidad++;
            cantidadInput.value = cantidad;
        });
    });
}

function configurarBotonPrincipal() {
    const btnPrincipal = document.querySelector(".btn-principal");
    if (!btnPrincipal) return;

    btnPrincipal.addEventListener("click", async (e) => {
        e.preventDefault();
        const nombre = document.querySelector(".detalle-info h1").textContent;
        const precioElement = document.querySelector(".precio");
        
        // Verificar si hay precio con descuento
        let precio;
        const precioDescuento = precioElement.querySelector(".precio-descuento");
        
        if (precioDescuento) {
            // Si hay descuento, tomar el precio final (con descuento)
            precio = parseInt(precioDescuento.textContent.replace(/\D/g, ""));
        } else {
            // Si no hay descuento, tomar el precio normal
            precio = parseInt(precioElement.textContent.replace(/\D/g, ""));
        }
        
        const img = document.querySelector(".detalle-imagen img").src;
        const cantidad = parseInt(document.getElementById("cantidad").value) || 1;
        await agregarAlCarrito(nombre, precio, img, cantidad);
    });
}

function configurarBotonesRelacionados() {
    const botonesRel = document.querySelectorAll("#btn-add-rel");
    botonesRel.forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const cardRel = e.target.closest(".card-rel");
            if (cardRel) {
                const nombre = cardRel.querySelector("h3").textContent;
                const precioElement = cardRel.querySelector(".price");
                
                // Verificar si hay precio con descuento
                let precio;
                const precioDescuento = precioElement.querySelector(".precio-descuento");
                
                if (precioDescuento) {
                    // Si hay descuento, tomar el precio final (con descuento)
                    precio = parseInt(precioDescuento.textContent.replace(/\D/g, ""));
                } else {
                    // Si no hay descuento, tomar el precio normal
                    precio = parseInt(precioElement.textContent.replace(/\D/g, ""));
                }
                
                const img = cardRel.querySelector("img").src;
                await agregarAlCarrito(nombre, precio, img, 1);
            }
        });
    });
}

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
    configurarBotonesCantidad();
    configurarBotonPrincipal();
    configurarBotonesRelacionados();
});
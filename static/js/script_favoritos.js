function initializeFavoriteButtons() {
    document.querySelectorAll(".btn-fav").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            const productId = this.dataset.id;
            const icon = this.querySelector("i");

            // Detectar tipo de ícono
            let baseIcon = "star";
            if (icon.className.includes("heart")) baseIcon = "heart";
            if (icon.className.includes("leaf")) baseIcon = "leaf";

            fetch(`/toggle_favorito/${productId}`, {
                method: "POST"
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    const contentType = response.headers.get("content-type") || "";
                    if (!contentType.includes("application/json")) {
                        throw new Error("Respuesta no JSON");
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        if (data.favorito) {
                            // AÑADIR favorito - solo cambiar clase
                            icon.className = `bx bxs-${baseIcon}`;
                        } else {
                            // QUITAR favorito - solo cambiar clase
                            icon.className = `bx bx-${baseIcon}`;

                            // Si estamos en la vista de favoritos, remover la tarjeta al quitar.
                            const productCard = this.closest(".product-card") || this.closest(".product-card4");
                            if (productCard && window.location.pathname.includes("/favoritos")) {
                                productCard.remove();
                            }
                        }
                        // ✅ El CSS se encarga del color automáticamente
                    }
                })
                .catch(error => {
                    console.error("Error:", error);
                    alert("No se pudo actualizar favoritos. Intenta de nuevo.");
                });
        });
    });
}

// Ejecutar cuando carga la página
document.addEventListener('DOMContentLoaded', initializeFavoriteButtons);
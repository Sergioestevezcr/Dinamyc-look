function initializeFavoriteButtons() {
    document.querySelectorAll(".btn-fav").forEach(button => {
        button.addEventListener("click", function(event) {
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
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.favorito) {
                        // AÑADIR favorito - solo cambiar clase
                        icon.className = `bx bxs-${baseIcon}`;
                    } else {
                        // QUITAR favorito - solo cambiar clase
                        icon.className = `bx bx-${baseIcon}`;
                    }
                    // ✅ El CSS se encarga del color automáticamente
                }
            })
            .catch(error => console.error("Error:", error));
        });
    });
}

// Ejecutar cuando carga la página
document.addEventListener('DOMContentLoaded', initializeFavoriteButtons);
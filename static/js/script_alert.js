const alerts = document.querySelectorAll('.alert');

alerts.forEach(alert => {
    // Progreso automático
    const progressBar = alert.querySelector('.alert-progress');
    if (progressBar) {
        progressBar.style.width = '100%';
        progressBar.style.transition = 'width 4s linear';

        setTimeout(() => {
            closeAlert(alert);
        }, 4000);
    }

    // Cerrar al hacer click en la X
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            closeAlert(alert);
        });
    }
});

// Función para cerrar alerta
function closeAlert(alert) {
    alert.style.opacity = '0';
    alert.style.transform = 'translateX(100%)';
    alert.style.transition = 'all 0.3s ease';

    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 300);
}

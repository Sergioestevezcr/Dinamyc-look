// SELECCIÓN DE ELEMENTOS DEL DOM
// Selecciona los principales elementos HTML que forman el carrusel
const carousel = document.querySelector('.carousel-product4');     // Contenedor principal del carrusel
const slides = document.querySelectorAll('.product-card4');        // Todas las tarjetas de productos
const prevBtn = document.querySelector('.btn-left-prd');           // Botón para ir al slide anterior
const nextBtn = document.querySelector('.btn-right-prd');          // Botón para ir al siguiente slide
const dotsContainer = document.querySelector('.carousel-dots');    // Contenedor de los puntos indicadores

// VARIABLES DE CONTROL
// Variables que controlan el estado y comportamiento del carrusel
let currentIndex = 0;      // Índice actual (posición del primer slide visible)
let slideWidth = 0;        // Ancho de cada slide (incluye tarjeta + espacio)
let slidesToShow = 1;      // Número de slides visibles a la vez (cambia según responsive)
let totalGroups = 1;       // Número total de grupos de slides
let gapSize = 30;          // Espacio entre tarjetas (30px por defecto en desktop)

// CÁLCULO DE DIMENSIONES
// Calcula el ancho de las tarjetas y el espacio entre ellas según el viewport
function calculateDimensions() {
    // Obtener el ancho actual de una tarjeta
    const cardWidth = slides[0].offsetWidth;
    
    // Determinar el tamaño del gap según el ancho de la ventana
    if (window.innerWidth <= 430) {
        gapSize = 20;      // Gap más pequeño (20px) en móviles pequeños
    } else if (window.innerWidth <= 580) {
        gapSize = 20;      // Gap de 20px en móviles medianos
    } else {
        gapSize = 30;      // Gap de 30px en desktop
    }
    
    // Actualizar el ancho total de cada slide (tarjeta + gap)
    slideWidth = cardWidth + gapSize;
    
    return { cardWidth, gapSize };
}

// CÁLCULO DE SLIDES VISIBLES
// Determina cuántos slides se muestran a la vez según el tamaño de pantalla
function calculateSlidesPerView() {
    const { cardWidth, gapSize } = calculateDimensions();
    const containerWidth = carousel.parentElement.clientWidth;  // Ancho del contenedor padre
    
    // Ajusta el padding del contenedor según el tamaño de pantalla
    // 40px total en móviles (20px a cada lado), 100px total en desktop (50px a cada lado)
    let containerPadding = window.innerWidth <= 430 ? 40 : 100;
    
    // Calcula cuántas tarjetas caben en el contenedor considerando gap y padding
    slidesToShow = Math.max(1, Math.floor((containerWidth - containerPadding) / slideWidth));
    
    // Limita el número de slides a mostrar al número total disponible
    slidesToShow = Math.min(slidesToShow, slides.length);
    
    // Calcula el número total de grupos de slides para la navegación por puntos
    totalGroups = Math.ceil(slides.length / slidesToShow);
    
    // Si el índice actual queda fuera de rango después de recalcular, lo ajusta
    if (currentIndex > slides.length - slidesToShow) {
        currentIndex = Math.max(0, slides.length - slidesToShow);
    }
    
    // Actualiza los puntos indicadores y la posición del carrusel
    generateDots();
    updateCarousel();
}

// GENERACIÓN DE PUNTOS INDICADORES
// Crea los puntos que indican la posición actual en el carrusel
function generateDots() {
    // Limpia el contenedor de puntos antes de regenerarlos
    dotsContainer.innerHTML = '';
    
    // Crea un punto por cada grupo de slides
    for (let i = 0; i < totalGroups; i++) {
        const dot = document.createElement('div');
        dot.classList.add('carousel-dot');
        
        // Marca como activo el punto correspondiente al grupo actual
        if (i === Math.floor(currentIndex / slidesToShow)) {
            dot.classList.add('active');
        }
        
        // Añade evento de clic para navegar directamente a ese grupo
        dot.addEventListener('click', () => {
            goToGroup(i);
        });
        
        dotsContainer.appendChild(dot);
    }
}

// NAVEGACIÓN A GRUPO ESPECÍFICO
// Permite saltar directamente a un grupo de slides específico
function goToGroup(groupIndex) {
    // Calcula el índice del primer slide del grupo seleccionado
    currentIndex = groupIndex * slidesToShow;
    
    // Asegura que no sobrepase el límite de slides
    if (currentIndex > slides.length - slidesToShow) {
        currentIndex = slides.length - slidesToShow;
    }
    
    // Actualiza la visualización del carrusel
    updateCarousel();
}

// INICIALIZACIÓN
// Configura el carrusel al cargar la página
calculateSlidesPerView();

// EVENTOS DE NAVEGACIÓN
// Configura los eventos para los botones de navegación
prevBtn.addEventListener('click', () => {
    // Retrocede un grupo completo de slides (mínimo 0)
    currentIndex = Math.max(currentIndex - slidesToShow, 0);
    updateCarousel();
});

nextBtn.addEventListener('click', () => {
    // Avanza un grupo completo de slides (máximo último grupo)
    currentIndex = Math.min(currentIndex + slidesToShow, slides.length - slidesToShow);
    updateCarousel();
});

// ACTUALIZACIÓN DEL CARRUSEL
// Actualiza la posición y estados visuales del carrusel
function updateCarousel() {
    // Recalcula dimensiones para asegurar valores actualizados
    calculateDimensions();
    
    // Desplaza el carrusel a la posición correspondiente con animación suave
    carousel.scrollTo({
        left: currentIndex * slideWidth,
        behavior: 'smooth'
    });
    
    // Actualiza el punto indicador activo
    const activeDotIndex = Math.floor(currentIndex / slidesToShow);
    const dots = document.querySelectorAll('.carousel-dot');
    dots.forEach((dot, index) => {
        dot.classList.toggle('active', index === activeDotIndex);
    });
    
    // Controla el estado visual y funcional de los botones
    // Desactiva el botón anterior si estamos en el primer grupo
    prevBtn.style.opacity = currentIndex === 0 ? '0.5' : '1';
    prevBtn.style.pointerEvents = currentIndex === 0 ? 'none' : 'auto';
    
    // Desactiva el botón siguiente si estamos en el último grupo
    const lastIndex = slides.length - slidesToShow;
    nextBtn.style.opacity = currentIndex >= lastIndex ? '0.5' : '1';
    nextBtn.style.pointerEvents = currentIndex >= lastIndex ? 'none' : 'auto';
}

// MANEJO DE REDIMENSIONAMIENTO
// Responde al cambio de tamaño de la ventana
let resizeTimeout;
window.addEventListener('resize', () => {
    // Utiliza debounce para limitar la frecuencia de ejecución durante el resize
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        calculateSlidesPerView();
    }, 250);  // Espera 250ms después del último evento de resize para ejecutar
});

// FUNCIONALIDAD TÁCTIL
// Implementa navegación táctil para dispositivos móviles
let touchStartX = 0;  // Posición X inicial del toque
let touchEndX = 0;    // Posición X final del toque

// Registra la posición inicial del toque
carousel.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
}, { passive: true });  // Passive true mejora el rendimiento

// Registra la posición final del toque y procesa el gesto
carousel.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}, { passive: true });

// PROCESAMIENTO DE GESTOS TÁCTILES
// Analiza el gesto de deslizamiento para determinar la dirección
function handleSwipe() {
    // Define un umbral mínimo de deslizamiento según el tamaño de pantalla
    const swipeThreshold = window.innerWidth <= 430 ? 30 : 50;
    
    if (touchStartX - touchEndX > swipeThreshold) {
        // Deslizamiento hacia la izquierda → avanzar al siguiente grupo
        if (currentIndex < slides.length - slidesToShow) {
            currentIndex += slidesToShow;
            updateCarousel();
        }
    } else if (touchEndX - touchStartX > swipeThreshold) {
        // Deslizamiento hacia la derecha → retroceder al grupo anterior
        if (currentIndex > 0) {
            currentIndex -= slidesToShow;
            updateCarousel();
        }
    }
}

// PREVENCIÓN DE ARRASTRE
// Evita comportamientos no deseados al intentar arrastrar elementos
carousel.addEventListener('dragstart', (e) => {
    e.preventDefault();
});
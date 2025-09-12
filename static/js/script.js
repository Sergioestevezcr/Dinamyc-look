// SELECCIÓN DE ELEMENTOS DEL DOM
// Variables que almacenan referencias a los elementos HTML que componen el slider
const btnLeft = document.querySelector(".btn-left")           // Botón para navegar a la izquierda
const btnRight= document.querySelector(".btn-right")          // Botón para navegar a la derecha
const slider = document.querySelector("#slider")              // Contenedor principal que se desplazará
const sliderSection = document.querySelectorAll(".slider-section"); // Todas las secciones (imágenes) del slider

// CONFIGURACIÓN DE EVENTOS DE NAVEGACIÓN
// Asigna eventos de clic a los botones de navegación
btnRight.addEventListener("click", e => moveToRight())       // Al hacer clic en botón derecho, mueve a la derecha
btnLeft.addEventListener("click", e => moveToLeft())         // Al hacer clic en botón izquierdo, mueve a la izquierda

// DESPLAZAMIENTO AUTOMÁTICO
// Configura un temporizador para cambiar imágenes automáticamente cada 5 segundos
setInterval(() => {
    moveToRight()     // Llama a la función de movimiento hacia la derecha cada 5000ms (5 segundos)
}, 5000);

// VARIABLES DE CONTROL
// Variables que controlan la posición y el movimiento del slider
let operacion = 0;                         // Almacena el porcentaje de desplazamiento actual
let counter = 0;                           // Contador que lleva el registro de la imagen actual
let widthimg = 100 / sliderSection.length; // Calcula el ancho en porcentaje de cada sección del slider

// FUNCIÓN DE DESPLAZAMIENTO HACIA LA DERECHA
// Controla el movimiento del slider hacia la derecha (muestra la siguiente imagen)
function moveToRight(){
    // Verifica si hemos llegado a la última imagen
    if (counter >= sliderSection.length-1){
        counter = 0;              // Vuelve a la primera imagen (índice 0)
        operacion = 0;            // Reinicia la posición de desplazamiento
        slider.style.transform = `translate(-${operacion}%)`; // Mueve el slider a la posición inicial
        slider.style.transition = "none"    // Desactiva la transición para un reinicio instantáneo
        return;                   // Sale de la función después de reiniciar
    }
    
    counter++;                    // Incrementa el contador para ir a la siguiente imagen
    operacion = operacion + widthimg;  // Aumenta el valor de desplazamiento según el ancho de la imagen
    
    // Aplica la transformación para mover el slider
    slider.style.transform = `translate(-${operacion}%)`;  // Desplaza el slider horizontalmente
    slider.style.transition = "all ease .6s"               // Aplica transición suave de 0.6 segundos
}

// FUNCIÓN DE DESPLAZAMIENTO HACIA LA IZQUIERDA
// Controla el movimiento del slider hacia la izquierda (muestra la imagen anterior)
function moveToLeft(){
    counter--                     // Decrementa el contador para ir a la imagen anterior
    
    // Verifica si estamos antes de la primera imagen
    if (counter < 0){
        counter = sliderSection.length-1;            // Va a la última imagen
        operacion = widthimg * (sliderSection.length-1)  // Calcula la posición de la última imagen
        slider.style.transform = `translate(-${operacion}%)`;  // Mueve el slider a la última imagen
        slider.style.transition = "none"             // Desactiva la transición para un salto instantáneo
        return;                                      // Sale de la función después de reiniciar
    }
    
    operacion = operacion - widthimg;                // Reduce el valor de desplazamiento
    
    // Aplica la transformación para mover el slider
    slider.style.transform = `translate(-${operacion}%)`;  // Desplaza el slider horizontalmente
    slider.style.transition = "all ease .6s"               // Aplica transición suave de 0.6 segundos
}
// variables para traer las clases al archivo y poder animarlas
const btnLeft = document.querySelector(".btn-left")
	  btnRight= document.querySelector(".btn-right")
	  slider = document.querySelector("#slider")
	  sliderSection = document.querySelectorAll(".slider-section");

// definen las acciones que se producen al hacer click encima de los botones
btnRight.addEventListener ("click", e => moveToRight())
btnLeft.addEventListener ("click", e => moveToLeft())
// define el tiempo en el que las imagenes van a cambiar automaticamente y en el sentido en el que lo van a hacer
setInterval (() => {
	moveToRight()
}, 5000);

// variables con las que se define cuanto vale cada movimiento 
let operacion = 0;
	counter = 0;
	widthimg = 100 / sliderSection.length;
// es la funcion que define como y hacia donde se mueve el container grande cuando se oprime el botos de desplzamiento hacia la derecha 
function moveToRight(){
	if (counter >= sliderSection.length-1){
		counter= 0;
		operacion = 0;
		slider.style.transform = `translate(-${operacion}%)`;
		slider.style.transition = "none"
		return;
	}
	counter++;
	operacion = operacion + widthimg;
	slider.style.transform = `translate(-${operacion}%)`;
	slider.style.transition = "all ease .6s"
// es la funcion que define como y hacia donde se mueve el container grande cuando se oprime el botos de desplzamiento hacia la izquierda	
}
function moveToLeft(){
	counter--
	if (counter < 0 ){
		counter= sliderSection.length-1;
		operacion = widthimg * (sliderSection.length-1)
		slider.style.transform = `translate(-${operacion}%)`;
		slider.style.transition = "none"
		return;
	}
	operacion = operacion - widthimg
	slider.style.transform = `translate(-${operacion}%)`;
	slider.style.transition = "all ease .6s"

	
}
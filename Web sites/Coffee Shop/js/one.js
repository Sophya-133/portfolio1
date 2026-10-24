let imageIndex = 0;
let images = ['images/splash1.png', 'images/splash2.png', 'images/splash3.png']; // ваш массив изображений

function updateCarousel() {
  document.getElementById('carousel-image').src = images[imageIndex];
  let indicators = document.getElementsByClassName('indicator');
  for (let i = 0; i < indicators.length; i++) {
    if (i === imageIndex) {
      indicators[i].classList.add('indicator-active');
    } else {
      indicators[i].classList.remove('indicator-active');
    }
  }
  let nextButton = document.getElementById('next-button');
  if (imageIndex === images.length - 1) {
    nextButton.innerText = 'Начать';
    nextButton.addEventListener('click', function() {
      window.location.href = 'login.html'; // замените на URL вашей следующей страницы
    });
  } else {
    nextButton.innerText = 'Следующий';
    nextButton.removeEventListener('click', function() {
      window.location.href = 'login.html';
    });
  }
}

document.getElementById('prev-button').addEventListener('click', function() {
  imageIndex = (imageIndex - 1 + images.length) % images.length;
  updateCarousel();
});

document.getElementById('next-button').addEventListener('click', function() {
  imageIndex = (imageIndex + 1) % images.length;
  updateCarousel();
});

updateCarousel();

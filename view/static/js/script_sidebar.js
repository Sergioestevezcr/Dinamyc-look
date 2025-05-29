
document.getElementById('open_btn').addEventListener('click', function() {
  document.querySelector('.sidebar').classList.add('active');
});

document.querySelector('.close-btn').addEventListener('click', function() {
  document.querySelector('.sidebar').classList.remove('active');
});

// admin-enhancements.js

document.addEventListener('DOMContentLoaded', function() {
  // Resaltar enlace activo del sidebar
  const currentPath = window.location.pathname;
  document.querySelectorAll('#sidebar li a').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.style.fontWeight = 'bold';
    }
  });

  // Mensaje en consola para confirmar carga
  console.log('✨ Admin enhancements cargados');
});

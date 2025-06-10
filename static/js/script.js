document.addEventListener('DOMContentLoaded', function() {
    const collapsibles = document.getElementsByClassName('collapsible-btn');
    for (let i = 0; i < collapsibles.length; i++) {
        collapsibles[i].addEventListener('click', function() {
            this.classList.toggle('active');
            const content = this.nextElementSibling;
            if (content.style.display === 'block') {
                content.style.display = 'none';
            } else {
                content.style.display = 'block';
            }
        });
    }

    // Manejo del formulario de búsqueda por año en partidos
    const yearForm = document.getElementById('year-filter-form');
    if (yearForm) {
        yearForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const year = document.getElementById('year-filter').value;
            window.location.href = `/partidos/?year=${year}`;
        });
    }
});
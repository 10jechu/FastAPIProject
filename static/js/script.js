document.addEventListener('DOMContentLoaded', function() {
    const rows = document.querySelectorAll('.data-table tbody tr:not(.detail-row)');
    rows.forEach(row => {
        row.addEventListener('click', function() {
            const detailRow = this.nextElementSibling;
            if (detailRow && detailRow.classList.contains('detail-row')) {
                detailRow.classList.toggle('active');
            }
        });
    });

    const deleteLinks = document.querySelectorAll('.btn-delete');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            if (!confirm('¿Estás seguro de eliminar este elemento?')) {
                event.preventDefault();
            }
        });
    });

    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const inputs = this.querySelectorAll('input[required]');
            let isValid = true;
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    alert(`El campo ${input.name} es obligatorio.`);
                }
            });
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
});
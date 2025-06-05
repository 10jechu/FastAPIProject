async function loadStats() {
    const year = document.getElementById('year') ? document.getElementById('year').value : '';
    const statsDiv = document.getElementById('stats');
    if (!statsDiv) return;

    const url = year ? `/estadisticas/completa/json?anio=${year}` : '/estadisticas/completa/json';

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Error en la respuesta del servidor');
        const data = await response.json();
        if (data.total_partidos === 0 || data.message) {
            statsDiv.innerHTML = `<p>${data.message || "No se encontraron datos para este año."}</p>`;
        } else {
            statsDiv.innerHTML = `
                <p><strong>Total Partidos:</strong> ${data.total_partidos}</p>
                <p><strong>Goles Anotados:</strong> ${data.goles_anotados}</p>
                <p><strong>Goles Recibidos:</strong> ${data.goles_recibidos}</p>
                <p><strong>Promedio Goles por Partido:</strong> ${data.promedio_goles_por_partido}</p>
                <p><strong>Victorias:</strong> ${data.victorias}</p>
                <p><strong>Empates:</strong> ${data.empates}</p>
                <p><strong>Derrotas:</strong> ${data.derrotas}</p>
                <p><strong>Tarjetas Amarillas:</strong> ${data.tarjetas_amarillas}</p>
                <p><strong>Tarjetas Rojas:</strong> ${data.tarjetas_rojas}</p>
                <p><strong>Partidos Eliminados:</strong> ${data.partidos_eliminados}</p>
                <p><strong>Porcentaje de Eliminaciones:</strong> ${data.porcentaje_eliminaciones}%</p>
            `;
        }
    } catch (error) {
        statsDiv.innerHTML = `<p>Error al cargar las estadísticas: ${error.message}</p>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadStats();

    const deleteForms = document.querySelectorAll('form[action$="/"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const method = form.querySelector('input[name="method"]')?.value;
            if (method === 'DELETE' && !confirm('¿Estás seguro de que deseas eliminar este registro?')) {
                e.preventDefault();
            }
        });
    });

    const collapsibles = document.querySelectorAll('.collapsible-btn');
    collapsibles.forEach(button => {
        button.addEventListener('click', function() {
            const content = this.nextElementSibling;
            const isActive = content.classList.contains('active');
            document.querySelectorAll('.collapsible-content').forEach(item => {
                item.classList.remove('active');
            });
            if (!isActive) {
                content.classList.add('active');
            }
        });
    });

    const yearSelect = document.getElementById('year');
    if (yearSelect) {
        yearSelect.addEventListener('change', loadStats);
    }
});
async function loadStats() {
    const year = document.getElementById('year').value;
    const statsDiv = document.getElementById('stats');
    const url = `https://fastapiproject-dap2.onrender.com/estadisticas/completa/?ano=${year}`;

    try {
        const response = await fetch(url);
        const data = await response.json();
        if (data.total_partidos === 0) {
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
            `;
        }
    } catch (error) {
        statsDiv.innerHTML = `<p>Error al cargar las estadísticas: ${error.message}</p>`;
    }
}

// Cargar estadísticas al iniciar
loadStats();
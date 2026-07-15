// ==========================================
// CONFIGURACIÓN DE LA API Y SEGURIDAD
// ==========================================
const API_BASE = "http://127.0.0.1:8000/api/v1";
const API_TOKEN = "admin123";
let miGrafico = null;

// ==========================================
// ANIMACIÓN DE CÓDIGO EN EL FONDO
// ==========================================
function iniciarFondoAnimado() {
    const canvas = document.getElementById('bg-codigo');
    const ctx = canvas.getContext('2d');

    // Ajustar el canvas al tamaño de la pantalla
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Caracteres que se mostrarán (Bits, Hex y símbolos matemáticos)
    const caracteres = '01XYZ0123456789$%^&*<>{}[]/\\+=~';
    const arregloCaracteres = caracteres.split('');

    const tamañoFuente = 14;
    const columnas = canvas.width / tamañoFuente;

    // Un arreglo para guardar la coordenada Y de cada columna
    const gotas = [];
    for (let x = 0; x < columnas; x++) {
        gotas[x] = 1;
    }

    function dibujarFrames() {
        // Fondo negro con opacidad para crear el efecto de estela/desvanecimiento
        ctx.fillStyle = 'rgba(10, 10, 10, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Color del texto (Tu verde Cyber/Neón)
        ctx.fillStyle = '#CCFF00';
        ctx.font = tamañoFuente + 'px monospace';

        for (let i = 0; i < gotas.length; i++) {
            // Elegir un caracter aleatorio
            const texto = arregloCaracteres[Math.floor(Math.random() * arregloCaracteres.length)];

            // Dibujar el caracter
            ctx.fillText(texto, i * tamañoFuente, gotas[i] * tamañoFuente);

            // Reiniciar la gota a la parte superior de forma aleatoria
            if (gotas[i] * tamañoFuente > canvas.height && Math.random() > 0.975) {
                gotas[i] = 0;
            }
            // Mover la gota hacia abajo
            gotas[i]++;
        }
    }

    // Velocidad a la que cae el código (en milisegundos)
    setInterval(dibujarFrames, 35);

    // Ajustar si el usuario cambia el tamaño de la ventana del navegador
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}
// ==========================================
// MANEJO DE EXCEPCIONES Y UI
// ==========================================
function mostrarError(codigo, mensaje) {
    const colores = {
        400: 'border-yellow-500 text-yellow-400',
        401: 'border-red-500 text-red-400', // Agregado para el token inválido
        404: 'border-orange-500 text-orange-400',
        500: 'border-red-500 text-red-400',
        501: 'border-purple-500 text-purple-400'
    };
    const colorClass = colores[codigo] || 'border-red-500 text-red-400';

    const toast = document.createElement('div');
    toast.className = `bg-[#44475A] border-l-4 ${colorClass} p-4 rounded-r shadow-2xl max-w-sm toast-enter relative overflow-hidden`;
    toast.innerHTML = `
        <div class="flex items-start gap-3">
            <span class="text-xl font-bold text-[#F8F8F2]">Error ${codigo}</span>
            <p class="text-sm text-[#F8F8F2] leading-tight">${mensaje}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="absolute top-2 right-2 text-[#6272A4] hover:text-white">&times;</button>
    `;
    document.getElementById('toast-container').appendChild(toast);
    setTimeout(() => toast.remove(), 7000);
}

async function manejarRespuesta(response) {
    if (!response.ok) {
        let errorMsg = "Error desconocido del servidor.";
        try {
            const dataError = await response.json();
            errorMsg = dataError.detail || errorMsg;
        } catch (e) {}
        mostrarError(response.status, errorMsg);
        throw new Error(`HTTP Error ${response.status}`);
    }
    return response.json();
}

// ==========================================
// CARGA DE ESTADÍSTICAS Y GRÁFICOS
// ==========================================
async function cargarEstadisticas() {
    document.getElementById('loader').classList.remove('hidden');

    const anio = document.getElementById('filtro-anio').value;
    const exp = document.getElementById('filtro-exp').value;
    const empresa = document.getElementById('filtro-empresa').value;
    const modalidad = document.getElementById('filtro-modalidad').value;
    const empleo = document.getElementById('filtro-empleo').value;

    const url = `${API_BASE}/salarios?anio=${anio}&experiencia=${exp}&tamano_empresa=${empresa}&modalidad=${modalidad}&tipo_empleo=${empleo}`;

    try {
        // FETCH CON BEARER TOKEN EN EL ENCABEZADO
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await manejarRespuesta(response);

        const formaterTotal = new Intl.NumberFormat('en-US');
        document.getElementById('kpi-total').innerText = `${formaterTotal.format(data.total)} registros`;

        let promedio = 0;
        if (data.salarios.length > 0) {
            const suma = data.salarios.reduce((acc, curr) => acc + Number(curr.salary_in_usd), 0);
            promedio = suma / data.salarios.length;
        }
        const formateador = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
        document.getElementById('kpi-promedio').innerText = formateador.format(promedio);

        const conteoPuestos = data.salarios.reduce((acc, item) => {
            const puesto = item.job_title;
            if (!acc[puesto]) acc[puesto] = [];
            acc[puesto].push(Number(item.salary_in_usd));
            return acc;
        }, {});

        const topPuestos = Object.keys(conteoPuestos)
            .sort((a, b) => conteoPuestos[b].length - conteoPuestos[a].length)
            .slice(0, 5);

        const labels = topPuestos.length > 0 ? topPuestos : ["Sin Datos"];
        const promediosPorPuesto = labels.map(puesto => {
            if(puesto === "Sin Datos") return 0;
            const salarios = conteoPuestos[puesto];
            return salarios.reduce((a, b) => a + b, 0) / salarios.length;
        });

        const ctx = document.getElementById('chartSalarios').getContext('2d');
        if (miGrafico) miGrafico.destroy();

        miGrafico = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Salario Promedio USD',
                    data: promediosPorPuesto,
                    backgroundColor: '#CCFF00', // Verde Neón Cyber
                    borderWidth: 0,
                    borderRadius: 4, // Bordes un poco más cuadrados y serios
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        // Verificamos si estamos en modo claro para oscurecer la grilla
                        grid: { color: document.body.classList.contains('light-mode') ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: document.body.classList.contains('light-mode') ? '#6B7280' : '#888888', font: { family: 'system-ui' } }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: document.body.classList.contains('light-mode') ? '#6B7280' : '#888888', maxRotation: 15, minRotation: 15, font: { family: 'system-ui' } }
                    }
                }
            }
        });

    } catch (error) {
        document.getElementById('kpi-total').innerText = "0 registros";
        document.getElementById('kpi-promedio').innerText = "$0";
        if (miGrafico) miGrafico.destroy();
    } finally {
        document.getElementById('loader').classList.add('hidden');
    }
}

// ==========================================
// PREDICCIÓN DE SALARIO
// ==========================================
async function realizarPrediccion() {
    const exp = document.getElementById('experience').value;
    const size = document.getElementById('company_size').value;
    const remote = document.getElementById('remote').value;

    const url = `${API_BASE}/predecir?experience_level=${exp}&company_size=${size}&remote_ratio=${remote}`;

    try {
        // FETCH CON BEARER TOKEN EN EL ENCABEZADO
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${API_TOKEN}`,
                'Content-Type': 'application/json'
            }
        });

        const data = await manejarRespuesta(response);

        const formateador = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
        document.getElementById('salario-valor').innerText = formateador.format(data.salario_predicho_usd);
        document.getElementById('resultado').classList.remove('hidden');
    } catch (error) {
        document.getElementById('resultado').classList.add('hidden');
    }
}

// ==========================================
// EVENT LISTENERS INICIALES
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    // 1. Iniciamos la animación de fondo
    iniciarFondoAnimado();

    // 2. Cargamos las estadísticas del dashboard
    cargarEstadisticas();

    // Escuchar el botón de calcular
    document.getElementById('btn-calcular').addEventListener('click', realizarPrediccion);

    // Escuchar cambios en los selects
    const filtros = document.querySelectorAll('.filtros-dashboard');
    filtros.forEach(select => select.addEventListener('change', cargarEstadisticas));

    // Evento para el botón de Modo Claro
    document.getElementById('btn-theme').addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        cargarEstadisticas(); // Recargamos la gráfica para que cambie de color
    });
});
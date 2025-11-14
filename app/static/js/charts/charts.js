// app/static/js/charts/charts.js

// Namespace globale per memorizzare i dati e le istanze dei grafici
window._playerChartData = window._playerChartData || {};
window._miniCharts = window._miniCharts || {};

/**
 * Legge i dati dei giocatori (passati da Jinja) e li
 * memorizza nel namespace globale per un facile accesso.
 * @param {Array<Object>} playersData - L'array 'players' serializzato da tojson.
 */
export function buildChartDataMap(playersData) {
  if (!playersData) return;

  playersData.forEach(data => {
    if (!data || !data.player) return;

    window._playerChartData[data.player.id] = {
      labels: data.chart_labels || [],
      values: data.profit_history || [],
      names: data.tournament_names || [],
      tournament_ids: data.tournament_ids || [], // Salva gli ID
      netProfit: data.player.net_profit || 0 
    };
  });
}

/**
 * Scansiona il DOM alla ricerca di <canvas> e disegna i grafici.
 */
export function createMiniCharts() {
  document.querySelectorAll('canvas[id^="chart-player-"]').forEach(canvas => {
    const id = canvas.id;
    const playerId = canvas.dataset.playerId;

    // Distrugge il grafico precedente se esiste (necessario per il cambio tema)
    if (window._miniCharts[id]) {
      try {
        window._miniCharts[id].destroy();
      } catch (e) {
        console.warn("Impossibile distruggere il vecchio grafico:", id, e);
      }
    }

    const chartData = (window._playerChartData && window._playerChartData[playerId]) || null;

    // Gestione se non ci sono dati
    if (!chartData || !chartData.values || !chartData.values.length === 0) {
      canvas.style.display = 'none';
      const holder = canvas.closest('.chart-holder');
      if (holder && !holder.querySelector('.no-chart-data')) {
        const noDataEl = document.createElement('div');
        noDataEl.className = 'alert alert-light text-center small no-chart-data p-2';
        noDataEl.innerText = 'Nessuno storico profitti disponibile.';
        const oldAlert = holder.querySelector('.alert');
        if (oldAlert) oldAlert.remove(); 
        holder.appendChild(noDataEl);
      }
      return;
    }
    
    // Calcolo dinamico con padding di 5 e numeri interi
    const dataValues = chartData.values.length > 0 ? chartData.values : [0];
    const dataMin = Math.min(...dataValues);
    const dataMax = Math.max(...dataValues);
    const paddedMin = dataMin - 5;
    const paddedMax = dataMax + 5;
    const finalMin = Math.floor(paddedMin > 0 ? 0 : paddedMin);
    const finalMax = Math.ceil(paddedMax < 0 ? 0 : paddedMax);

    const tournamentNames = chartData.names || [];
    const tournamentIds = chartData.tournament_ids || []; // Recupera gli ID

    try {
      const style = getComputedStyle(document.documentElement);

      // --- Colori Grafico ---
      const colorSuccess = style.getPropertyValue('--bs-success').trim() || '#198754';
      const colorDanger = style.getPropertyValue('--bs-danger').trim() || '#dc3545';
      const colorSuccessRGB = style.getPropertyValue('--bs-success-rgb').trim() || '25, 135, 84';
      const colorDangerRGB = style.getPropertyValue('--bs-danger-rgb').trim() || '220, 53, 69';

      // La linea è neutra (colore body)
      const lineFinalColor = style.getPropertyValue('--bs-body-color').trim() || '#212529';
      
      const gridColor = style.getPropertyValue('--bs-border-color-translucent').trim() || '#ccc';

      // Crea un array di colori (rosso/verde) basato su ogni singolo valore
      const pointColors = chartData.values.map(value => {
        return value >= 0 ? colorSuccess : colorDanger;
      });

      const ctx = canvas.getContext('2d');

      // --- FUNZIONE PER GRADIENTE DINAMICO (Rosso/Verde per il fill) ---
      function createFillGradient(context) {
        const chart = context.chart;
        const { ctx, chartArea } = chart;

        if (!chartArea) {
          return null;
        }
        const yZero = chart.scales.y.getPixelForValue(0);
        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        const height = chartArea.bottom - chartArea.top;
        const stop = (yZero - chartArea.top) / height;
        const clampedStop = Math.max(0, Math.min(1, stop));
        const alpha = '0.25'; 

        gradient.addColorStop(0, `rgba(${colorSuccessRGB}, ${alpha})`);
        gradient.addColorStop(clampedStop, `rgba(${colorSuccessRGB}, ${alpha})`);
        gradient.addColorStop(clampedStop, `rgba(${colorDangerRGB}, ${alpha})`);
        gradient.addColorStop(1, `rgba(${colorDangerRGB}, ${alpha})`);

        return gradient;
      }
      // --- FINE FUNZIONE ---

      const cfg = {
        type: 'line',
        data: {
          labels: (tournamentNames.length > 0) ? tournamentNames : chartData.labels,
          datasets: [{
            data: chartData.values,
            borderColor: lineFinalColor, // Linea neutra (nera/bianca)
            
            // Fill dinamico (rosso/verde)
            backgroundColor: createFillGradient, 
            fill: 'origin',

            borderWidth: 2,
            tension: 0.2,

            // Colori PUNTI dinamici
            pointBackgroundColor: pointColors,
            pointBorderColor: pointColors,
            pointRadius: 2,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: pointColors,
            pointHoverBorderColor: pointColors
          }]
        },
        options: {
          // --- Gestione Clic sul Grafico ---
          onClick: (event, elements, chart) => {
            if (elements.length > 0) {
              const dataIndex = elements[0].index;
              // Controlla se abbiamo un ID valido per quel punto
              if (tournamentIds.length > dataIndex && tournamentIds[dataIndex] != null) {
                
                const tournamentId = tournamentIds[dataIndex];
                
                // Pulisce l'ID (es. da caratteri invisibili se ci fossero)
                const cleanId = parseInt(tournamentId); 
                
                if (!isNaN(cleanId)) {
                  // --- MODIFICA: Rimosso /detail/ dall'URL ---
                  window.location.href = `/tournaments/${cleanId}`;
                } else {
                  console.warn("Tentativo di reindirizzamento con ID non valido:", tournamentId);
                }
              }
            }
          },
          
          // Cambia cursore in 'pointer' (manina)
          onHover: (event, chartElement) => {
            const canvas = event.native.target;
            if (chartElement.length > 0) {
              canvas.style.cursor = 'pointer'; // Manina
            } else {
              canvas.style.cursor = 'default'; // Freccia standard
            }
          },

          plugins: {
            legend: { display: false },
            tooltip: {
              enabled: true,
              displayColors: false, // Rimuove il quadratino colorato
              backgroundColor: function (context) {
                // Il tooltip rimane dinamico (rosso/verde)
                const value = context.tooltip.dataPoints[0].parsed.y;
                return value >= 0 ? colorSuccess : colorDanger;
              },
              callbacks: {
                title: function (context) {
                  const dataIndex = context[0].dataIndex;
                  if (tournamentNames.length > dataIndex && tournamentNames[dataIndex]) {
                    return tournamentNames[dataIndex];
                  }
                  return "Torneo " + chartData.labels[dataIndex];
                },
                label: function (context) {
                  let label = 'Profitto: ';
                  if (context.parsed.y !== null) {
                    const value = context.parsed.y;
                    label += new Intl.NumberFormat('it-IT', {
                      style: 'currency',
                      currency: 'EUR',
                      signDisplay: 'exceptZero'
                    }).format(value);
                  }
                  return label;
                }
              }
            }
          },
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              border: { display: false },
              grid: { display: false },
              ticks: {
                display: true,
                font: { size: 9 },
                maxRotation: 70,
                minRotation: 70
              }
            },
            y: {
              min: finalMin,
              max: finalMax,
              border: { display: false },
              grid: {
                color: function (context) {
                  const zeroLineColor = style.getPropertyValue('--bs-body-color').trim() || '#212525';
                  // La linea della griglia a 0 rimane evidenziata
                  if (context.tick.value === 0) {
                    return zeroLineColor; 
                  }
                  return gridColor;
                },
                lineWidth: function (context) {
                  return (context.tick.value === 0) ? 2 : 1;
                },
                drawBorder: false
              },
              ticks: {
                display: true,
                font: { size: 9 },
                callback: function (value, index, ticks) {
                  if (Math.abs(value) >= 1000) {
                    return (value / 1000) + 'k €';
                  }
                  return value + ' €';
                }
              }
            }
          }
        }
      };
      window._miniCharts[id] = new Chart(ctx, cfg);
    } catch (err) {
      console.error('Errore creazione grafico:', id, err);
    }
  });
}
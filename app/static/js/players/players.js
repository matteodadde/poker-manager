// static/js/players/players.js
(() => {
  const LOG = '[players.js]';

  // --- Utility: aspetta che jQuery + DataTables siano disponibili ---
  const waitForDataTables = (maxRetries = 30, interval = 100) => new Promise((resolve, reject) => {
    let tries = 0;
    const id = setInterval(() => {
      if (window.jQuery && jQuery.fn && jQuery.fn.DataTable) {
        clearInterval(id);
        return resolve();
      }
      tries += 1;
      if (tries >= maxRetries) {
        clearInterval(id);
        return reject(new Error('jQuery/DataTables not available'));
      }
    }, interval);
  });

  // --- Costruzione lista per il modal ---
  const buildListHtml = rows => rows.map(cells => `
    <li class="mb-2">
      <strong>Data:</strong> ${cells[0]}<br>
      <strong>Buy-in (€):</strong> ${cells[1]}<br>
      <strong>Rebuy:</strong> ${cells[2]}<br>
      <strong>Posizione:</strong> ${cells[3]}<br>
      <strong>Vincita (€):</strong> ${cells[4]}
    </li>
  `).join('');

  // --- Mostra dettagli giocatore nel modal Bootstrap ---
  const showPlayerDetails = () => {
    const rowEls = document.querySelectorAll('#players-table tbody tr');
    const rows = Array.from(rowEls).map(row => Array.from(row.cells).map(c => c.textContent.trim()));
    if (!rows.length) return;

    const modalBody = document.querySelector('#player-details-modal .modal-body');
    if (!modalBody) {
      console.warn(LOG, 'Modal markup non trovato. Aggiungi il modal nel DOM prima di usare showPlayerDetails().');
      return;
    }
    modalBody.innerHTML = `<ul class="list-unstyled">${buildListHtml(rows)}</ul>`;

    // usa API bootstrap
    if (!window.__playersModalInstance) {
      window.__playersModalInstance = new bootstrap.Modal('#player-details-modal', { keyboard: true });
    }
    window.__playersModalInstance.show();
  };

  // --- Inizializza / Re-init sicura di DataTable ---
  const initDataTable = () => {
    const $table = $('#players-table');
    if (!$table.length) {
      // niente tabella, niente inizializzazione
      return;
    }

    // Se DataTable è già attivo ma non abbiamo il nostro flag, distruggi prima
    try {
      if ($.fn.DataTable.isDataTable($table.get(0)) && !$table.data('dtInitialized')) {
        console.info(LOG, 'Trovata istanza DataTable senza flag: la distruggo per prevenire duplicati.');
        $table.DataTable().clear().destroy();
        // rimuovi eventuali wrapper lasciati da DataTables
        $table.removeAttr('style');
        $table.find('.dataTables_wrapper').remove();
      }
    } catch (err) {
      console.warn(LOG, 'Errore durante controllo/destroy di DataTable:', err);
    }

    // Se flag impostata, salta l'inizializzazione
    if ($table.data('dtInitialized')) {
      // già inizializzata da questa istanza dello script
      return;
    }

    // Inizializza DataTable in modo idempotente
    const dt = $table.DataTable({
      paging: true,
      searching: true,
      ordering: true,
      responsive: true,
      // ordina per profitto netto se presente nella colonna 3 (0-index)
      order: [[3, 'desc']],
      language: {
        url: "//cdn.datatables.net/plug-ins/1.13.6/i18n/it-IT.json"
      }
    });

    // Flag per evitare reinits futuri
    $table.data('dtInitialized', true);
    // Salva l'istanza per debug/uso futuro
    window.__playersDataTable = dt;
    console.info(LOG, 'DataTable inizializzato correttamente.');
  };

  // --- Debug helpers esposti su window (opzionali) ---
  window.__playersHelpers = {
    isDataTableInitialized: () => {
      const t = document.querySelector('#players-table');
      return !!(t && window.jQuery && jQuery.fn && jQuery.fn.DataTable && $.fn.DataTable.isDataTable(t));
    },
    listScriptTagsForPlayers: () => Array.from(document.scripts).filter(s => s.src && s.src.includes('players')).map(s => s.src)
  };

  // --- Boot: attendi DataTables e init (evita doppia init) ---
  document.addEventListener('DOMContentLoaded', () => {
    // attiva listener click delegato per button che apre modal
    document.body.addEventListener('click', (ev) => {
      const btn = ev.target.closest && ev.target.closest('#show-details-btn');
      if (btn) {
        ev.preventDefault();
        showPlayerDetails();
      }
    });

    // tenta inizializzare DataTables in modo sicuro
    waitForDataTables().then(() => {
      initDataTable();
    }).catch(err => {
      console.warn(LOG, 'jQuery/DataTables non trovati, inizializzazione saltata:', err);
      // prova comunque a chiamare init dopo 500ms (per casi CDN lenti)
      setTimeout(() => {
        try { initDataTable(); } catch(e) { console.error(LOG, 'Init retry fail', e); }
      }, 500);
    });
  });
})();

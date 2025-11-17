$(document).ready(function () {
    $('#players-table').DataTable({
        language: {
            url: 'https://cdn.datatables.net/plug-ins/1.13.6/i18n/it-IT.json'
        },
        pageLength: 10,
        order: [[5, 'desc']], // Ordinamento predefinito per Profitto Netto (colonna 5) decrescente
        columnDefs: [
            {
                targets: [1, 2, 3, 4, 5, 12, 14], // Colonne monetarie: Vincite, Spese Totali, Buy-in Spesi, Rebuy Spesi, Profitto Netto, Profitto Medio, Premio Medio ITM
                type: 'num',
                render: function (data, type, row) {
                    if (type === 'display' || type === 'filter') {
                        return parseFloat(data).toFixed(2) + ' €';
                    }
                    return parseFloat(data) || 0;
                }
            },
            {
                targets: [8, 10], // Colonne percentuali: Win Rate, ITM Rate
                type: 'num',
                render: function (data, type, row) {
                    if (type === 'display' || type === 'filter') {
                        return (parseFloat(data) * 100).toFixed(1) + '%';
                    }
                    return parseFloat(data) || 0;
                }
            },
            {
                targets: [13, 15], // Colonne numeriche decimali: Rebuy Medio, Rapporto Vittorie/ITM
                type: 'num',
                render: function (data, type, row) {
                    if (type === 'display' || type === 'filter') {
                        return parseFloat(data).toFixed(2);
                    }
                    return parseFloat(data) || 0;
                }
            },
            {
                targets: [6, 7, 9, 11, 16], // Colonne intere: Tornei, Vittorie, ITM, Rebuys, Tornei senza Rebuy
                type: 'num',
                render: function (data, type, row) {
                    return parseInt(data) || 0;
                }
            },
            {
                targets: 0, // Colonna Giocatore
                type: 'string'
            }
        ]
    });
});
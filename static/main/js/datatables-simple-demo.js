window.addEventListener('DOMContentLoaded', event => {
    // Simple-DataTables
    // https://github.com/fiduswriter/Simple-DataTables/wiki

    const datatablesSimple = document.getElementById('datatablesSimple');
    if (datatablesSimple) {
        new simpleDatatables.DataTable(datatablesSimple, {
            columns: [
                { select: 0, sortable: true },
                { select: 1, sortable: true },
                { select: 2, sortable: true },  
                { select: 3, sortable: false },
                { select: 4, sortable: true },
                { select: 5, sortable: false },
                { select: 6, sortable: false },
                { select: 7, sortable: false },
                { select: 8, sortable: false },
            ]
        });
    }
});

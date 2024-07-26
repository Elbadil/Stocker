window.addEventListener('DOMContentLoaded', event => {
    // Simple-DataTables
    // https://github.com/fiduswriter/Simple-DataTables/wiki

    const datatablesSimple = document.getElementById('datatablesSimple');
    if (datatablesSimple) {
        const table = new simpleDatatables.DataTable(datatablesSimple, {
            columns: [
                { select: 0, sortable: true },
                { select: 1, sortable: true },
                { select: 2, sortable: true },  
                { select: 3, sortable: false },
                { select: 4, sortable: true },
                { select: 5, sortable: false },
                { select: 6, sortable: false },
                { select: 7, sortable: false },
                { select: 8, sortable: true },
                { select: 9, sortable: true },
                { select: 10, sortable: false },
            ]
        });

        // Function to perform custom actions after search
        function performCustomActions() {
            let visibleRows;
            const searchQuery = document.querySelector('.datatable-input').value;
            const searchTitle = document.getElementById('search_title');
            if (!searchQuery) {
                searchTitle.textContent = 'All Items';
            } else {
                searchTitle.innerHTML = `<b>Search: </b>${searchQuery}`;
            }
            const itemsNumber = document.getElementById('item_num');
            console.log(`Search query: ${searchQuery}`);
            console.log(`Visible rows: ${visibleRows}`);
        }

        // Attach event listener to the automatically generated search input
        document.querySelector('.datatable-input').addEventListener('input', function() {
            // Perform custom actions
            performCustomActions();
        });
    }
});

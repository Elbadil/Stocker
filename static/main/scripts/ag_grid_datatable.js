window.addEventListener('DOMContentLoaded', event => {

    const gridOptions = {
        // Row Data: The data to be displayed.
        rowData: [
            { make: "Tesla", model: "Model Y", price: 64950, electric: true },
            { make: "Ford", model: "F-Series", price: 33850, electric: false },
            { make: "Toyota", model: "Corolla", price: 29600, electric: false },
        ],
        defaultColDef: {
            minWidth: 110,
            filter: true
        },
        // Column Definitions: Defines the columns to be displayed.
        columnDefs: [
            { field: "Name", flex: 3, minWidth: 120 },
            { field: "Quantity", flex: 1.5 },
            { field: "price", flex: 1.5 },
            { field: "Variants", flex: 2.5 },
            { field: "T. Price", headerName: "T. Price", flex: 2 },
            { field: "Category", flex: 2 },
            { field: "Supplier", flex: 2 },
            { field: "Picture", flex: 2, filter: false },
            { field: "Created", flex: 1.5 },
            { field: "Updated", flex: 1.5 , resizable: false }
        ]
    };

    const myGridElement = document.querySelector('#myGrid');
    agGrid.createGrid(myGridElement, gridOptions);
});
document.addEventListener('DOMContentLoaded', async () => {
    const userId = document.getElementById('user_id').value;
    const categoryId = document.getElementById('category_id').value;
    const supplierId = document.getElementById('supplier_id').value;
    let itemsUrl;

    if (categoryId) {
        itemsUrl = `/api/inventory/category_items/${categoryId}/`
    } else if (supplierId) {
        itemsUrl = `/api/inventory/supplier_items/${supplierId}/`
    } else {
        itemsUrl = `/api/inventory/items/${userId}/`
    }

    const fetchUserItems = async (itemsUrl) => {
        try {
            const userItemsUrl = itemsUrl;
            const res = await fetch(userItemsUrl, {
                method: "GET",
            });
            let data = await res.json();
            if (res.status === 200) {
                return data;
            } else {
                console.log(`Error: ${data.error}`);
            }
        } catch (err) {
            console.log(`Error: ${err}`);
        }
    };

    const userItemsData = await fetchUserItems(itemsUrl);
    console.log(userItemsData);  // Verify data in the console
    userItemsData.forEach(item => {
        if (!item.updated) {
            item.updated_at = null;
        }
    });

    const filterParams = {
        comparator: (filterLocalDateAtMidnight, cellValue) => {
            if (cellValue == null) return -1;

            const dateParts = cellValue.split('/');
            const month = Number(dateParts[0]) - 1;
            const day = Number(dateParts[1]);
            const year = Number(dateParts[2]);

            const cellDate = new Date(year, month, day);
            if (cellDate < filterLocalDateAtMidnight) {
                return -1;
            } else if (cellDate > filterLocalDateAtMidnight) {
                return 1;
            } else {
                return 0;
            }
        },
        browserDatePicker: true
    };

    const tableOptions = {
        // Table Height
        domLayout: 'autoHeight',
        //  Row Data
        rowData: userItemsData,
        // Row Selection Mode
        rowSelection: 'multiple',
        // Default Column Definition
        defaultColDef: {
            minWidth: 120,
            filter: true,
            autoHeight: true,
        },
        // Pagination
        pagination: true,
        //  Page Size
        paginationPageSize: 20,
        // Cell Data(text) Selection
        enableCellTextSelection: true,
        // Row Colors
        rowClassRules: {
            'ag-row-odd': params => params.node.rowIndex % 2 !== 0,
            'ag-row-even': params => params.node.rowIndex % 2 === 0,
        },
        // Columns Definition
        columnDefs: [
            { 
                field: "name",
                headerCheckboxSelection: true,
                checkboxSelection: true,
                flex: 3,
                minWidth: 150
            },
            {
                field: "quantity",
                flex: 1.5
            },
            { 
                field: "price",
                flex: 1,
                valueFormatter: params => params.value.toFixed(2)
            },
            { 
                field: "variants",
                valueGetter: (params) => {
                    let variants = [];
                    if (params.data && params.data.variants && Array.isArray(params.data.variants)) {
                        params.data.variants.forEach((variant) => {
                            const variantOptions = variant.options.join(', ');
                            variants.push(`${variant.name}: ${variantOptions}`);
                        });
                        return variants;
                    }
                },
                cellRenderer: (params) => {
                    const variants = params.value;
                    if (variants && Array.isArray(variants)) {
                        let variantsCell = "<div>";
                        variants.forEach((variant, index) => {
                            const variantName = variant.split(': ')[0];
                            const variantOptions = variant.split(': ')[1];
                            if (index > 0) {
                                variantsCell += `<div style="border-top: 1px solid #DCDCDC;"><b>${variantName}:</b> ${variantOptions}</div>`;
                            } else {
                                variantsCell += `<div><b>${variantName}:</b> ${variantOptions}</div>`;
                            }
                        });
                        variantsCell += "</div>";
                        return variantsCell;
                    }
                    return "";
                }, 
                flex: 2.5,
                minWidth: 140,
                filter: "agTextColumnFilter"
            },
            { 
                field: "total_price",
                headerName: "T. Price",
                valueFormatter: params => params.value.toFixed(2),
                flex: 1.5
            },
            { 
                field: "category",
                valueGetter: params => params.data.category,
                cellRenderer: (params) => {
                    if (params.data.category) {
                        return `<a class="table_links" data-category="${params.value}">${params.value}</a>`;
                    }
                },
                flex: 2
            },
            { 
                field: "supplier",
                valueGetter: params => params.data.supplier,
                cellRenderer: (params) => {
                    if (params.data.supplier) {
                        return `<a class="table_links" data-supplier="${params.value}">${params.value}</a>`;
                    }
                },
                flex: 2
            },
            {
                field: "picture",
                cellRenderer: (params) => {
                    if (params.value) {
                        return `<img class="img-thumbnail"
                                     style="width: 100px;
                                     margin-top: 4px;
                                     margin-bottom: 4px;"
                                     src="${params.value}"></img>`;
                    }
                },
                minWidth: 140,
                flex: 2,
                filter: false
            },
            { 
                field: "created_at",
                headerName: "Created",
                filter: "agDateColumnFilter",
                filterParams: filterParams,
                minWidth: 130,
                flex: 1.5
            },
            { 
                field: "updated_at",
                headerName: "Updated",
                filter: "agDateColumnFilter",
                filterParams: filterParams,
                minWidth: 130,
                flex: 1.5 ,
                resizable: false
            }
        ]
    };
      
    const inventoryTable = document.querySelector('#inventoryTable');
    const gridApi = agGrid.createGrid(inventoryTable, tableOptions);

    inventoryTable.addEventListener('click', (event) => {
        const target = event.target;
        if (target.classList.contains('table_links')) {
            event.preventDefault();
            const category = target.getAttribute('data-category');
            const supplier = target.getAttribute('data-supplier');

            filterData(category, supplier);
        }
    });

    const filterData = (category, supplier) => {
        console.log('Filtering Data')
        const filteredData = tableOptions.rowData.filter(item => {
            let categoryMatches = true;
            let supplierMatches = true;
            if (category) {
                categoryMatches = item.category === category;
            }
            if (supplier) {
                supplierMatches = item.supplier === supplier;
            }
            return categoryMatches && supplierMatches;
        });
        gridApi.setGridOption("rowData", filteredData);
    }

    // Initial data load
    filterData();

});
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

console.log(`userId: ${userId}`);

const fetchUserItems = async (itemsUrl) => {
    try {
        const userItemsUrl = itemsUrl
        const res = await fetch(userItemsUrl, {
            method: "GET",
        });
        let data = await res.json();
        if (res.status === 200) {
            return data;
        } else {
            console.log(`Error: ${data.error}`)
        }
    } catch (err) {
        console.log(`Error: ${err}`);
    }
};  

async function initTableWithUserItems(itemsUrl) {
    const userItemsData = await fetchUserItems(itemsUrl);
    userItemsData.forEach(item => {
        if (!item.updated) {
            item.updated_at = null;
        }
    });

    // Handling Date Filtering
    const filterParams = {
        comparator: (filterLocalDateAtMidnight, cellValue) => {
            if (cellValue == null) return -1;
    
            // Assuming date format is MM/DD/YYYY
            const dateParts = cellValue.split('/');
            const month = Number(dateParts[0]) - 1; // Months are zero-based in JavaScript Date
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
        // Row Data: The data to be displayed.
        rowData: userItemsData,
        // Column Default Definition
        defaultColDef: {
            minWidth: 120,
            filter: true,
            autoHeight: true,
        },
        // Pagination
        pagination: true,
        paginationPageSize: 20,
        // Cell Selection
        enableCellTextSelection: true,
        // ensureDomOrder: true,
        // Column Definitions: Defines the columns to be displayed.
        columnDefs: [
            { field: "name", flex: 3, minWidth: 130 },
            { field: "quantity", flex: 1.5 },
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
                                variantsCell += `<div style="border-top: 1px solid #E8E8E8;"><b>${variantName}:</b> ${variantOptions}</div>`;
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
                filter: "agTextColumnFilter",
                filterParams: {
                    caseSensitive: false
                }
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
                cellRenderer: params => `<a href="/inventory/category_items/${params.value}/">${params.value}</a>`,
                flex: 2
            },
            { 
                field: "supplier",
                valueGetter: params => params.data.supplier,
                cellRenderer: params => `<a href="/inventory/supplier_items/${params.value}/">${params.value}</a>`,
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
                resizable: false }
        ]
    };
    document.addEventListener('DOMContentLoaded', () => {
        const inventoryTable = document.querySelector('#inventoryTable');
        agGrid.createGrid(inventoryTable, tableOptions);
    });
};

initTableWithUserItems(itemsUrl);

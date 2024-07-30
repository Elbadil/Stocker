const userId = document.getElementById('user_id').value;
console.log(`userId: ${userId}`);

const fetchUserItems = async (userId) => {
    try {
        const userItemsUrl = `/api/inventory/items/${userId}/`
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

async function initTableWithUserItems(userId) {
    const userItemsData = await fetchUserItems(userId);
    userItemsData.forEach(item => {
        if (!item.updated) {
            item.updated_at = null;
        }
        item.total_price = item.total_price.toFixed(2);
        item.price = item.price.toFixed(2);
    });
    const tableOptions = {
        // Row Data: The data to be displayed.
        domLayout: 'autoHeight',
        rowData: userItemsData,
        defaultColDef: {
            minWidth: 120,
            filter: true,
            autoHeight: true,
        },
        pagination: true,
        paginationPageSize: 20,
        // Column Definitions: Defines the columns to be displayed.
        columnDefs: [
            { field: "name", flex: 3, minWidth: 130 },
            { field: "quantity", flex: 1.5 },
            { field: "price", flex: 1, filter: "agNumberColumnFilter" },
            { 
                field: "variants",
                cellRenderer: (params) => {
                    const variants = params.value;
                    if (variants && Array.isArray(variants)) {
                        let variantsCell = "<div>";
                        variants.forEach((variant, index) => {
                            const variantOptions = variant.options.join(', ');
                            if (index > 0) {
                                variantsCell += `<div style="border-top: 1px solid #E8E8E8;"><b>${variant.name}:</b> ${variantOptions}</div>`;
                            } else {
                                variantsCell += `<div><b>${variant.name}:</b> ${variantOptions}</div>`;
                            }
                        });
                        variantsCell += "</div>";
                        return variantsCell;
                    }
                    return "";
                }, 
                flex: 2.5,
                minWidth: 140,
            },
            { field: "total_price", headerName: "T. Price", filter: "agNumberColumnFilter", flex: 1.5 },
            { field: "category", flex: 2 },
            { field: "supplier", flex: 2 },
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
                minWidth: 130,
                flex: 2,
                filter: false
            },
            { field: "created_at", headerName: "Created", filter: "agDateColumnFilter", minWidth: 130, flex: 1.5 },
            { field: "updated_at", headerName: "Updated", minWidth: 130, flex: 1.5 , resizable: false }
        ]
    };
    document.addEventListener('DOMContentLoaded', () => {
        const inventoryTable = document.querySelector('#inventoryTable');
        agGrid.createGrid(inventoryTable, tableOptions);
    });
};

initTableWithUserItems(userId);

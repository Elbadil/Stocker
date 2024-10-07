import { AgGridReact, CustomCellRendererProps } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { useEffect, useState, useMemo } from 'react';
import Loader from '../../common/Loader';
import Breadcrumb from '../../components/Breadcrumbs/Breadcrumb';
import { api } from '../../api/axios';
import { useInventory } from '../../contexts/InventoryContext';
import { useAlert } from '../../contexts/AlertContext';
import {
  ColDef,
  GridOptions,
  RowSelectionOptions,
  IDateFilterParams,
  ITextFilterParams,
  INumberFilterParams,
} from 'ag-grid-community';

export interface Item {
  name: string;
  quantity: number;
  price: number;
  total_price: number;
  category: string | null;
  supplier: string | null;
  variants: { name: string; options: string[] }[] | null;
  picture: string | null;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

const Items = () => {
  const { loading } = useInventory();
  const { isDarkMode } = useAlert();
  const [itemsLoading, setItemsLoading] = useState<boolean>(true);

  const VariantsRenderer = (props: CustomCellRendererProps) => {
    const variants = props.value;
    return variants ? (
      <div className="grid divide-y">
        {variants.map((variant: string, index: number) => (
          <div
            key={index}
            className="whitespace-nowrap overflow-hidden text-ellipsis"
          >
            {variant.split(': ')[0]}: {variant.split(': ')[1]}
          </div>
        ))}
      </div>
    ) : (
      <></>
    );
  };

  const PictureRenderer = (props: CustomCellRendererProps) => {
    return props.value ? (
      <div className="mt-2.5 mb-2.5 h-20 w-20 rounded-full">
        <img
          src={props.value}
          className="w-full h-full object-cover rounded-full"
          alt="Item Picture"
        />
      </div>
    ) : (
      <></>
    );
  };

  const filterParams: IDateFilterParams = {
    comparator: (filterLocalDateAtMidnight: Date, cellValue: string) => {
      var dateAsString = cellValue;
      if (dateAsString == null) return -1;
      var dateParts = dateAsString.split('/');
      var cellDate = new Date(
        Number(dateParts[2]),
        Number(dateParts[1]) - 1,
        Number(dateParts[0]),
      );
      if (filterLocalDateAtMidnight.getTime() === cellDate.getTime()) {
        return 0;
      }
      if (cellDate < filterLocalDateAtMidnight) {
        return -1;
      }
      if (cellDate > filterLocalDateAtMidnight) {
        return 1;
      }
      return 0;
    },
    inRangeFloatingFilterDateFormat: 'Do MMM YYYY',
  };

  const [rowData, setRowData] = useState<Item[]>([]);
  const [colDefs] = useState<ColDef<Item>[]>([
    {
      field: 'name',
      flex: 3,
      minWidth: 150,
    },
    {
      field: 'quantity',
      flex: 1.2,
      minWidth: 115,
    },
    {
      field: 'price',
      valueFormatter: (params) => params.value.toFixed(2),
      flex: 1.5,
      minWidth: 115,
    },
    {
      field: 'total_price',
      headerName: 'T. Price',
      valueFormatter: (params) => params.value.toFixed(2),
      flex: 1.5,
      minWidth: 120,
    },
    {
      field: 'variants',
      valueGetter: (params) => {
        let variants: string[] = [];
        if (
          params.data &&
          params.data?.variants &&
          Array.isArray(params.data?.variants)
        ) {
          params.data.variants.forEach((variant) => {
            variants.push(`${variant.name}: ${variant.options.join(', ')}`);
          });
          return variants;
        }
      },
      cellRenderer: VariantsRenderer,
      flex: 2.5,
      minWidth: 140,
    },
    {
      field: 'picture',
      cellRenderer: PictureRenderer,
      minWidth: 120,
      flex: 1.5,
      filter: false,
    },
    { field: 'category', flex: 2 },
    { field: 'supplier', flex: 2 },
    {
      field: 'created_at',
      headerName: 'Created',
      filter: 'agDateColumnFilter',
      filterParams: filterParams,
      minWidth: 120,
      flex: 1,
    },
    {
      field: 'updated_at',
      headerName: 'Updated',
      valueFormatter: (params) => (params.data?.updated ? params.value : ''),
      filter: 'agDateColumnFilter',
      filterParams: filterParams,
      minWidth: 120,
      flex: 1,
      resizable: false,
    },
  ]);

  const defaultColDef = useMemo(() => {
    return {
      flex: 1,
      minWidth: 130,
      filterParams: {
        buttons: ['apply', 'reset'],
        closeOnApply: true,
      } as ITextFilterParams | INumberFilterParams | IDateFilterParams,
      filter: true,
      autoHeight: true,
      headerClass: 'text-base font-medium',
      cellClass: 'font-medium',
    };
  }, []);

  const rowSelection = useMemo<
    RowSelectionOptions | 'single' | 'multiple'
  >(() => {
    return {
      mode: 'multiRow',
    };
  }, []);

  const gridOptions: GridOptions<Item> = {
    domLayout: 'autoHeight',
    pagination: true,
    paginationPageSize: 20,
    enableCellTextSelection: true,
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get('/inventory/user/items/');
        console.log(res.data);
        setRowData(res.data);
      } catch (err) {
        console.log('Error getting user items', err);
      } finally {
        setItemsLoading(false);
      }
    };

    loadData();
  }, []);

  return (
    <>
      <div className="mx-auto max-w-full">
        <Breadcrumb main="Inventory" pageName="Items" />
        <div className="col-span-5 xl:col-span-3">
          {loading || itemsLoading ? (
            <Loader />
          ) : (
            <div
              className={`ag-theme-${
                isDarkMode ? 'quartz-dark' : 'quartz'
              } w-full h-full font-satoshi`}
              style={{ height: 500 }}
            >
              <AgGridReact
                rowData={rowData}
                columnDefs={colDefs}
                rowSelection={rowSelection}
                defaultColDef={defaultColDef}
                gridOptions={gridOptions}
              />
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Items;

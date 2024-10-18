import { AgGridReact, CustomCellRendererProps } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import React, {
  useEffect,
  useState,
  useMemo,
  useRef,
  useCallback,
} from 'react';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import Item, { ItemProps } from './Item';
import AddItem from './AddItem';
import EditItem from './EditItem';
import DeleteItem from './DeleteItem';
import Loader from '../../common/Loader';
import ModalOverlay from '../../components/ModalOverlay';
import Breadcrumb from '../../components/Breadcrumbs/Breadcrumb';
import { api } from '../../api/axios';
import { useInventory } from '../../contexts/InventoryContext';
import { useAlert } from '../../contexts/AlertContext';
import { Alert } from '../UiElements/Alert';
import {
  ColDef,
  GridOptions,
  RowSelectionOptions,
  IDateFilterParams,
  ITextFilterParams,
  INumberFilterParams,
  GetRowIdParams,
} from 'ag-grid-community';
import { handleItemExport, handleBulkExport } from './utils';

const Items = () => {
  const { loading, totalItems, totalQuantity, totalValue } = useInventory();
  const { alert, isDarkMode } = useAlert();
  const [itemsLoading, setItemsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<ItemProps | null>(null);
  const [openItem, setOpenItem] = useState<boolean>(false);
  const [openAddItem, setOpenAddItem] = useState<boolean>(false);
  const [openEditItem, setOpenEditItem] = useState<boolean>(false);
  const [openDeleteItem, setOpenDeleteItem] = useState<boolean>(false);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const NameRenderer = (props: CustomCellRendererProps) => {
    return (
      <button
        className="hover:underline"
        onClick={() => {
          setOpenItem(true);
          setSelectedItem(props.data);
        }}
      >
        {props.value}
      </button>
    );
  };

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

  const dateFilterParams: IDateFilterParams = {
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

  const gridRef = useRef<AgGridReact>(null);
  const [rowData, setRowData] = useState<ItemProps[]>([]);
  const [selectedRows, setSelectedRows] = useState<ItemProps[] | undefined>(
    undefined,
  );
  const [colDefs] = useState<ColDef<ItemProps>[]>([
    {
      field: 'name',
      cellRenderer: NameRenderer,
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
      getQuickFilterText: (params) => params.value.toFixed(2),
      flex: 1.5,
      minWidth: 115,
    },
    {
      field: 'total_price',
      headerName: 'T. Price',
      valueFormatter: (params) => params.value.toFixed(2),
      getQuickFilterText: (params) => params.value.toFixed(2),
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
      getQuickFilterText: () => '',
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
      filterParams: dateFilterParams,
      minWidth: 120,
      flex: 1,
    },
    {
      field: 'updated_at',
      headerName: 'Updated',
      valueFormatter: (params) => (params.data?.updated ? params.value : ''),
      filter: 'agDateColumnFilter',
      filterParams: dateFilterParams,
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
      selectAll: 'currentPage',
      enableSelectionWithoutKeys: true,
      // enableClickSelection: true,
    };
  }, []);

  const gridOptions: GridOptions<ItemProps> = {
    domLayout: 'autoHeight',
    pagination: true,
    paginationPageSize: 20,
    enableCellTextSelection: true,
  };

  const getAndSetSelectRows = () => {
    const selectedItems: ItemProps[] | undefined =
      gridRef.current?.api.getSelectedRows();
    setSelectedRows(selectedItems);
  };

  const getRowNode = (rowId: string) => {
    return gridRef.current?.api.getRowNode(rowId);
  };

  const getRowId = useCallback(
    (params: GetRowIdParams) => String(params.data.id),
    [],
  );

  useEffect(() => {
    getAndSetSelectRows();
  }, [openEditItem]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get('/inventory/user/items/');
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
        <Breadcrumb main="Inventory" pageName="Inventory Items" />
        {loading || itemsLoading ? (
          <Loader />
        ) : (
          <>
            {alert && <Alert {...alert} />}
            <div className="col-span-5 xl:col-span-3 relative">
              <div className="w-full flex flex-col border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
                <div className="p-5 flex-grow">
                  {/* Search | Item CRUD */}
                  <div className="flex flex-col gap-3 sm:flex-row justify-between sm:items-center">
                    {/* Search */}
                    <div className="max-w-md relative">
                      <label
                        htmlFor="default-search"
                        className="mb-2 text-sm font-medium text-gray-900 sr-only dark:text-white"
                      >
                        Search
                      </label>
                      <div>
                        <div className="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
                          <SearchRoundedIcon />
                        </div>
                        <input
                          id="default-search"
                          value={searchTerm}
                          onChange={handleSearchInputChange}
                          className="block max-w-sm p-3 ps-11 text-sm text-black border border-stroke rounded-lg bg-white focus:border-blue-500 focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:placeholder-slate-300 dark:text-white dark:focus:border-primary"
                          placeholder="Search Items..."
                          required
                        />
                        {searchTerm && (
                          <button
                            type="button"
                            className="absolute inset-y-0 end-1 flex items-center pr-3"
                            onClick={() => setSearchTerm('')}
                          >
                            <span className="text-slate-400 hover:text-slate-700 dark:text-white dark:hover:text-slate-300">
                              ✖
                            </span>
                          </button>
                        )}
                      </div>
                    </div>
                    {/* Bulk Export */}
                    <div>
                      <button
                        className="flex font-medium items-center hover:text-primary"
                        onClick={handleBulkExport}
                      >
                        <FileDownloadOutlinedIcon sx={{ marginRight: '2px' }} />
                        Bulk Export
                      </button>
                    </div>
                    {/* Read Add | Edit | Delete | Export Item */}
                    <div>
                      {/* Read Item Modal */}
                      {selectedItem && (
                        <ModalOverlay
                          isOpen={openItem}
                          onClose={() => setOpenItem(false)}
                        >
                          <Item
                            item={selectedItem}
                            setItem={setSelectedItem}
                            itemRowNode={getRowNode(selectedItem.id)}
                            setOpen={setOpenItem}
                            rowData={rowData}
                            setRowData={setRowData}
                          />
                        </ModalOverlay>
                      )}
                      {/* Export item(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-slate-200 text-black'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => handleItemExport(selectedRows)}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <FileDownloadOutlinedIcon />
                      </button>

                      {/* Delete item(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-red-500 text-white'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenDeleteItem(true)}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <DeleteOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows.length >= 1 && (
                        <ModalOverlay
                          isOpen={openDeleteItem}
                          onClose={() => setOpenDeleteItem(false)}
                        >
                          <DeleteItem
                            items={selectedRows}
                            open={openDeleteItem}
                            setOpen={setOpenDeleteItem}
                            rowData={rowData}
                            setRowData={setRowData}
                          />
                        </ModalOverlay>
                      )}
                      {/* Edit item */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          selectedRows && selectedRows.length === 1
                            ? 'bg-primary text-white'
                            : 'text-slate-400 bg-gray dark:bg-meta-4'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenEditItem(true)}
                        disabled={!selectedRows || selectedRows.length !== 1}
                      >
                        <ModeEditOutlineOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows[0] && (
                        <ModalOverlay
                          isOpen={openEditItem}
                          onClose={() => setOpenEditItem(false)}
                        >
                          <EditItem
                            open={openEditItem}
                            setOpen={setOpenEditItem}
                            rowNode={getRowNode(selectedRows[0].id)}
                            item={selectedRows[0]}
                          />
                        </ModalOverlay>
                      )}
                      {/* Add item */}
                      <button
                        className="inline-flex items-center justify-center rounded-full bg-meta-3 py-2 px-3 text-center font-medium text-white hover:bg-opacity-90 lg:px-3 xl:px-3"
                        onClick={() => setOpenAddItem(true)}
                        aria-hidden={false}
                      >
                        <AddCircleOutlinedIcon sx={{ marginRight: '3px' }} />
                        New
                      </button>
                      <ModalOverlay
                        isOpen={openAddItem}
                        onClose={() => setOpenAddItem(false)}
                      >
                        <AddItem
                          open={openAddItem}
                          setOpen={setOpenAddItem}
                          setRowData={setRowData}
                        />
                      </ModalOverlay>
                    </div>
                  </div>

                  {/* Inventory Info: Items | Quantity | Value */}
                  <div className="mx-auto mt-3.5 mb-3.5 grid grid-cols-3 rounded-md border bg-gray border-stroke py-2.5 shadow-1 dark:border-strokedark dark:bg-[#37404F]">
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">Items:</span>
                      <span className="font-semibold text-black dark:text-white">
                        {totalItems}
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">
                        Total Quantity:
                      </span>
                      <span className="font-semibold text-black dark:text-white">
                        {totalQuantity}
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 xsm:flex-row">
                      <span className="text-base font-medium">
                        Total Value:
                      </span>
                      <span className="font-semibold text-black dark:text-white">
                        {totalValue.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* AG Grid DataTable */}
                  <div
                    className={`ag-theme-${
                      isDarkMode ? 'quartz-dark' : 'quartz'
                    } w-full flex-grow font-satoshi`}
                  >
                    <AgGridReact
                      ref={gridRef}
                      rowData={rowData}
                      columnDefs={colDefs}
                      rowSelection={rowSelection}
                      onRowSelected={getAndSetSelectRows}
                      defaultColDef={defaultColDef}
                      gridOptions={gridOptions}
                      quickFilterText={searchTerm}
                      getRowId={getRowId}
                    />
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default Items;

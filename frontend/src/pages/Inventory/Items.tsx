import { AgGridReact, CustomCellRendererProps } from '@ag-grid-community/react';
import AgGridTable, {
  dateFilterParams,
} from '../../components/Tables/AgGridTable';
import React, { useEffect, useState, useRef } from 'react';
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
import { ColDef } from '@ag-grid-community/core';
import { handleItemExport, handleBulkExport } from './utils';

const Items = () => {
  const { loading, totalItems, totalQuantity, totalValue } = useInventory();
  const { alert } = useAlert();
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
      <div
        className="hover:underline whitespace-nowrap overflow-hidden text-ellipsis cursor-pointer"
        onClick={() => {
          setOpenItem(true);
          setSelectedItem(props.data);
        }}
      >
        {props.value}
      </div>
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
      valueGetter: (params) => {
        if (params.data?.updated_at && params.data?.updated) {
          return params.data?.updated_at;
        }
        return null;
      },
      filter: 'agDateColumnFilter',
      filterParams: dateFilterParams,
      minWidth: 120,
      flex: 1,
      resizable: false,
    },
  ]);

  const getAndSetSelectRows = () => {
    const selectedItems: ItemProps[] | undefined =
      gridRef.current?.api.getSelectedRows();
    setSelectedRows(selectedItems);
  };

  const getRowNode = (rowId: string) => {
    return gridRef.current?.api.getRowNode(rowId);
  };

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
                            selectedItems={selectedRows}
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
                            setRowData={setRowData}
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
                  <AgGridTable
                    ref={gridRef}
                    rowData={rowData}
                    colDefs={colDefs}
                    searchTerm={searchTerm}
                    onRowSelected={getAndSetSelectRows}
                  />
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

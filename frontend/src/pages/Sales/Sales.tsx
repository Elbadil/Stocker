import React, { useState, useEffect, useRef } from 'react';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import AgGridTable, {
  AddressRenderer,
  StatusRenderer,
  dateFilterParams,
} from '../../components/Tables/AgGridTable';
import MultiNumberFilter from '../../components/AgGridFilters/MultiNumberFilter';
import MultiTextFilter from '../../components/AgGridFilters/MultiTextFilter';
import Loader from '../../common/Loader';
import ModalOverlay from '../../components/ModalOverlay';
import { useAlert } from '../../contexts/AlertContext';
import { Alert } from '../UiElements/Alert';
import { Location } from '../ClientOrders/Clients/Client';
import { api } from '../../api/axios';
import { AgGridReact, CustomCellRendererProps } from '@ag-grid-community/react';
import {
  ColDef,
  GetQuickFilterTextParams,
  ValueGetterParams,
} from '@ag-grid-community/core';
import Breadcrumb from '../../components/Breadcrumbs/Breadcrumb';
import { handleSaleExport, handleSalesBulkExport } from './utils';

export interface SoldItem {
  id: string;
  created_by: string;
  item: string;
  sold_quantity: number;
  sold_price: number;
  total_price: number;
}

export interface SaleProps {
  id: string;
  reference_id: string;
  created_by: string;
  client: string;
  sold_items: SoldItem[];
  delivery_status: string;
  payment_status: string;
  shipping_address?: Location | null;
  shipping_cost: number;
  net_profit: number;
  source?: string | null;
  from_order: boolean;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

const Sales = () => {
  const { alert } = useAlert();
  const [salesLoading, setSalesLoading] = useState<boolean>(false);
  const loading = false;
  const [selectedSale, setSelectedSale] = useState<SaleProps | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [openSale, setOpenSale] = useState<boolean>(false);
  const [openAddSale, setOpenAddSale] = useState<boolean>(false);
  const [openEditSale, setOpenEditSale] = useState<boolean>(false);
  const [openDeleteSale, setOpenDeleteSale] = useState<boolean>(false);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const RefRenderer = (params: CustomCellRendererProps) => {
    return params.value;
  };

  const soldItemValueGetter = (
    params: ValueGetterParams<SaleProps, SoldItem[]>,
    key: keyof SoldItem,
  ) => {
    if (!params.data?.sold_items) return [];
    return params.data.sold_items.map((soldItem) => soldItem[key]);
  };

  const SoldItemRenderer = (
    params: CustomCellRendererProps,
    key: keyof SoldItem,
  ) => {
    if (!params.value) return null;
    const decimalFields = ['sold_price', 'total_price'];
    return (
      <>
        {params.value.map((prop: string | number, index: number) => (
          <div
            key={index}
            className="whitespace-nowrap overflow-hidden text-ellipsis"
          >
            {decimalFields.includes(key) && typeof prop === 'number'
              ? prop.toFixed(2)
              : prop}
          </div>
        ))}
      </>
    );
  };

  const numberGetQuickFilterText = (
    params: GetQuickFilterTextParams<SaleProps, number[]>,
  ) => {
    if (!params.value) return '';
    return params.value.map((value) => value.toFixed(2)).join(', ');
  };

  const gridRef = useRef<AgGridReact>(null);
  const [selectedRows, setSelectedRows] = useState<SaleProps[] | undefined>(
    undefined,
  );
  const [rowData, setRowData] = useState<SaleProps[]>([]);
  const [colDefs] = useState<ColDef<SaleProps>[]>([
    {
      field: 'created_at',
      headerName: 'Created',
      filter: 'agDateColumnFilter',
      filterParams: dateFilterParams,
      minWidth: 120,
      flex: 1,
    },
    {
      field: 'reference_id',
      headerName: 'Ref',
      cellRenderer: RefRenderer,
      sortable: false,
      minWidth: 120,
      flex: 1,
    },
    {
      field: 'client',
      minWidth: 120,
      flex: 1,
    },
    {
      field: 'sold_items',
      headerName: 'Item',
      valueGetter: (params) => soldItemValueGetter(params, 'item'),
      cellRenderer: (params: CustomCellRendererProps) =>
        SoldItemRenderer(params, 'item'),
      filter: MultiTextFilter,
      flex: 3,
      minWidth: 150,
    },
    {
      field: 'sold_items',
      headerName: 'Quantity',
      valueGetter: (params) => soldItemValueGetter(params, 'sold_quantity'),
      cellRenderer: (params: CustomCellRendererProps) =>
        SoldItemRenderer(params, 'sold_quantity'),
      filter: MultiNumberFilter,
      flex: 1.5,
      minWidth: 115,
    },
    {
      field: 'sold_items',
      headerName: 'Price',
      valueGetter: (params) => soldItemValueGetter(params, 'sold_price'),
      cellRenderer: (params: CustomCellRendererProps) =>
        SoldItemRenderer(params, 'sold_price'),
      getQuickFilterText: numberGetQuickFilterText,
      filter: MultiNumberFilter,
      flex: 1.5,
      minWidth: 123,
    },
    {
      field: 'sold_items',
      headerName: 'T. Price',
      valueGetter: (params) => soldItemValueGetter(params, 'total_price'),
      cellRenderer: (params: CustomCellRendererProps) =>
        SoldItemRenderer(params, 'total_price'),
      getQuickFilterText: numberGetQuickFilterText,
      filter: MultiNumberFilter,
      flex: 1.5,
      minWidth: 123,
    },
    {
      field: 'delivery_status',
      headerName: 'Delivery Status',
      cellRenderer: StatusRenderer,
      flex: 3,
      minWidth: 160,
      sortable: false,
    },
    {
      field: 'payment_status',
      headerName: 'Payment Status',
      cellRenderer: StatusRenderer,
      flex: 3,
      minWidth: 167,
      sortable: false,
    },
    {
      field: 'shipping_address',
      headerName: 'Address',
      valueGetter: (params: ValueGetterParams<SaleProps, Location>) => {
        if (!params.data?.shipping_address) return null;
        return Object.values(params.data.shipping_address).join(', ');
      },
      cellRenderer: AddressRenderer,
    },
    {
      field: 'shipping_cost',
      headerName: 'Shipping Cost',
      valueGetter: (params) => {
        if (!params.data?.shipping_cost) return null;
        console.log(params.data.shipping_cost);
        return Number(params.data.shipping_cost);
      },
      valueFormatter: (params) =>
        !params.value ? '' : params.value.toFixed(2),
      filter: 'agNumberColumnFilter',
      getQuickFilterText: numberGetQuickFilterText,
      flex: 3,
      minWidth: 155,
    },
    {
      field: 'net_profit',
      headerName: 'Net Profit',
      valueFormatter: (params) => {
        if (!params.value) return null;
        return params.value.toFixed(2);
      },
      filter: 'agNumberColumnFilter',
      getQuickFilterText: numberGetQuickFilterText,
      flex: 1.5,
      minWidth: 123,
    },
    {
      field: 'source',
      headerName: 'Source',
      flex: 2,
      minWidth: 130,
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
    },
  ]);

  const getAndSetSelectedRows = () => {
    const selectedOrders: SaleProps[] | undefined =
      gridRef.current?.api.getSelectedRows();
    setSelectedRows(selectedOrders);
  };

  const getRowNode = (rowId: string) => {
    return gridRef.current?.api.getRowNode(rowId);
  };

  useEffect(() => {
    const loadData = async () => {
      setSalesLoading(true);
      try {
        const res = await api.get('/sales/');
        setRowData(res.data);
      } catch (error: any) {
        console.log('Error getting sales data', error);
      } finally {
        setSalesLoading(false);
      }
    };

    loadData();
  }, []);

  return (
    <>
      <div className="mx-auto max-w-full">
        <Breadcrumb main="Sales" pageName="Sales" />
        {loading || salesLoading ? (
          <Loader />
        ) : (
          <>
            {alert && <Alert {...alert} />}
            <div className="col-span-5 xl:col-span-3 relative">
              <div className="w-full flex flex-col border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
                <div className="p-5 flex-grow">
                  {/* Search | Sales CRUD */}
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
                          placeholder="Search Orders..."
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
                        onClick={handleSalesBulkExport}
                      >
                        <FileDownloadOutlinedIcon sx={{ marginRight: '2px' }} />
                        Bulk Export
                      </button>
                    </div>
                    {/* Read Add | Edit | Delete | Export Sale */}
                    <div>
                      {/* Read Sale Modal */}
                      {/* {selectedOrder && (
                        <ModalOverlay
                          isOpen={openOrder}
                          onClose={() => setOpenOrder(false)}
                        >
                          <SupplierOrder
                            order={selectedOrder}
                            setOrder={setSelectedOrder}
                            rowNode={getRowNode(selectedOrder.id)}
                            setOpen={setOpenOrder}
                            rowData={rowData}
                            setRowData={setRowData}
                          />
                        </ModalOverlay>
                      )} */}
                      {/* Export Sale(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-slate-200 text-black'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={handleSaleExport}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <FileDownloadOutlinedIcon />
                      </button>

                      {/* Delete Sale(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-red-500 text-white'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenDeleteSale(true)}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <DeleteOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows.length >= 1 && (
                        <ModalOverlay
                          isOpen={openDeleteSale}
                          onClose={() => setOpenDeleteSale(false)}
                        >
                          <div>Hi</div>
                          {/* <DeleteSupplierOrder
                            orders={selectedRows}
                            open={openDeleteSale}
                            setOpen={setOpenDeleteSale}
                            rowData={rowData}
                            setRowData={setRowData}
                          /> */}
                        </ModalOverlay>
                      )}
                      {/* Edit Sale */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          selectedRows && selectedRows.length === 1
                            ? 'bg-primary text-white'
                            : 'text-slate-400 bg-gray dark:bg-meta-4'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenEditSale(true)}
                        disabled={!selectedRows || selectedRows.length !== 1}
                      >
                        <ModeEditOutlineOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows[0] && (
                        <ModalOverlay
                          isOpen={openEditSale}
                          onClose={() => setOpenEditSale(false)}
                        >
                          <div>Hi</div>
                          {/* <EditSupplierOrder
                            supplierOrder={selectedRows[0]}
                            open={openEditSale}
                            setOpen={setOpenEditSale}
                            rowNode={getRowNode(selectedRows[0].id)}
                            setRowData={setRowData}
                          /> */}
                        </ModalOverlay>
                      )}
                      {/* Add Sale */}
                      <button
                        className="inline-flex items-center justify-center rounded-full bg-meta-3 py-2 px-3 text-center font-medium text-white hover:bg-opacity-90 lg:px-3 xl:px-3"
                        onClick={() => setOpenAddSale(true)}
                        aria-hidden={false}
                      >
                        <AddCircleOutlinedIcon sx={{ marginRight: '3px' }} />
                        New
                      </button>
                      <ModalOverlay
                        isOpen={openAddSale}
                        onClose={() => setOpenAddSale(false)}
                      >
                        <div>Hi</div>
                        {/* <AddSupplierOrder
                          open={openAddSale}
                          setOpen={setOpenAddSale}
                          setRowData={setRowData}
                        /> */}
                      </ModalOverlay>
                    </div>
                  </div>
                  {/* Orders Info | Orders Count | Orders status */}
                  <div className="mx-auto mt-3.5 mb-3.5 grid grid-cols-4 rounded-md border bg-gray border-stroke py-2.5 shadow-1 dark:border-strokedark dark:bg-[#37404F]">
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">
                        Total Sales:
                      </span>
                      <span className="font-semibold text-black dark:text-white">
                        {/* {ordersCount} */}0
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">Active:</span>
                      <span className="font-semibold text-black dark:text-white">
                        {/* {orderStatus.active} */}0
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">Completed:</span>
                      <span className="font-semibold text-black dark:text-white">
                        {/* {orderStatus.completed} */}0
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 px-4 xsm:flex-row">
                      <span className="text-base font-medium">Failed:</span>
                      <span className="font-semibold text-black dark:text-white">
                        {/* {orderStatus.failed} */}0
                      </span>
                    </div>
                  </div>
                  {/* AG Grid DataTable */}
                  <AgGridTable
                    ref={gridRef}
                    rowData={rowData}
                    colDefs={colDefs}
                    searchTerm={searchTerm}
                    onRowSelected={getAndSetSelectedRows}
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

export default Sales;

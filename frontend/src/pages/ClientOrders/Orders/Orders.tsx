import { useState, useEffect, useRef } from 'react';
import {
  ColDef,
  ValueGetterParams,
  ModuleRegistry,
  GetQuickFilterTextParams,
} from '@ag-grid-community/core';
import { AgGridReact, CustomCellRendererProps } from '@ag-grid-community/react';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import AgGridTable, {
  dateFilterParams,
} from '../../../components/Tables/AgGridTable';
import ModalOverlay from '../../../components/ModalOverlay';
import Breadcrumb from '../../../components/Breadcrumbs/Breadcrumb';
import Loader from '../../../common/Loader';
import { api } from '../../../api/axios';
import { useAlert } from '../../../contexts/AlertContext';
import { Alert } from '../../UiElements/Alert';
import { useClientOrders } from '../../../contexts/ClientOrdersContext';
import { handleBulkExport, handleOrderExport } from './utils';
import { Location } from '../Clients/Client';
import MultiNumberFilter from '../../../components/AgGridFilters/MultiNumberFilter';
import MultiTextFilter from '../../../components/AgGridFilters/MultiTextFilter';
import { ClientSideRowModelModule } from '@ag-grid-community/client-side-row-model';
import Order, { OrderProps, OrderedItem } from './Order';
import AddOrder from './AddOrder';
import EditOrder from './EditOrder';
import DeleteOrder from './DeleteOrder';

ModuleRegistry.registerModules([ClientSideRowModelModule]);

const Orders = () => {
  const { alert } = useAlert();
  const { loading, clients, ordersCount } = useClientOrders();
  const [ordersLoading, setOrdersLoading] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedRows, setSelectedRows] = useState<OrderProps[] | undefined>(
    undefined,
  );
  const [selectedOrder, setSelectedOrder] = useState<OrderProps | null>(null);
  const [openOrder, setOpenOrder] = useState<boolean>(false);
  const [openAddOrder, setOpenAddOrder] = useState<boolean>(false);
  const [openEditOrder, setOpenEditOrder] = useState<boolean>(false);
  const [openDeleteOrder, setOpenDeleteOrder] = useState<boolean>(false);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const RefRenderer = (params: CustomCellRendererProps) => {
    if (!params.value) return null;
    return (
      <div
        className="hover:underline cursor-pointer"
        onClick={() => {
          setSelectedOrder(params.data);
          setOpenOrder(true);
        }}
      >
        {params.value}
      </div>
    );
  };

  const OrderedItemRenderer = (
    params: CustomCellRendererProps,
    key: keyof OrderedItem,
  ) => {
    if (!params.value) return null;
    const decimalFields = ['ordered_price', 'total_profit', 'total_price'];
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

  const StatusRenderer = (params: CustomCellRendererProps) => {
    if (!params.value) return null;

    const status = params.value;
    const success = ['Paid', 'Delivered'];
    const fail = ['Failed', 'Canceled'];

    const statusStyle = () => {
      if (success.includes(status)) {
        return 'bg-lime-500';
      } else if (fail.includes(status)) {
        return 'bg-red-500';
      }
      return 'bg-cyan-500';
    };

    return (
      <div className="whitespace-nowrap overflow-hidden text-ellipsis">
        <span
          className={`${statusStyle()} text-white p-1 font-semibold rounded-md`}
        >
          {params.value}
        </span>
      </div>
    );
  };

  const AddressRenderer = (params: CustomCellRendererProps) => {
    if (!params.value) return null;

    return (
      <div className="mb-1">
        {params.value.split(', ').map((prop: string, index: number) => (
          <div
            key={index}
            className="m-0 p-0 whitespace-nowrap overflow-hidden text-ellipsis"
            style={{ lineHeight: '2' }}
          >
            {prop}
          </div>
        ))}
      </div>
    );
  };

  const createValueGetter = (
    params: ValueGetterParams<OrderProps, OrderedItem[]>,
    key: keyof OrderedItem,
  ) => {
    if (!params.data?.ordered_items) return [];
    return params.data.ordered_items.map((item) => item[key]);
  };

  const numberGetQuickFilterText = (
    params: GetQuickFilterTextParams<OrderProps, number[]>,
  ) => {
    if (!params.value) return '';
    return params.value.map((value: number) => value.toFixed(2)).join(', ');
  };

  const gridRef = useRef<AgGridReact>(null);
  const [rowData, setRowData] = useState<OrderProps[]>([]);
  const [colDefs] = useState<ColDef<OrderProps>[]>([
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
      field: 'ordered_items',
      headerName: 'Item',
      valueGetter: (params) => createValueGetter(params, 'item'),
      cellRenderer: (params: CustomCellRendererProps) =>
        OrderedItemRenderer(params, 'item'),
      filter: MultiTextFilter,
      flex: 3,
      minWidth: 150,
    },
    {
      field: 'ordered_items',
      headerName: 'Quantity',
      valueGetter: (params) => createValueGetter(params, 'ordered_quantity'),
      cellRenderer: (params: CustomCellRendererProps) =>
        OrderedItemRenderer(params, 'ordered_quantity'),
      filter: MultiNumberFilter,
      getQuickFilterText: numberGetQuickFilterText,
      flex: 1.5,
      minWidth: 115,
    },
    {
      field: 'ordered_items',
      headerName: 'Price',
      valueGetter: (params) => createValueGetter(params, 'ordered_price'),
      cellRenderer: (params: CustomCellRendererProps) =>
        OrderedItemRenderer(params, 'ordered_price'),
      getQuickFilterText: numberGetQuickFilterText,
      filter: MultiNumberFilter,

      flex: 1,
      minWidth: 110,
    },
    {
      field: 'ordered_items',
      headerName: 'T. Price',
      valueGetter: (params) => createValueGetter(params, 'total_price'),
      cellRenderer: (params: CustomCellRendererProps) =>
        OrderedItemRenderer(params, 'total_price'),
      getQuickFilterText: numberGetQuickFilterText,
      filter: MultiNumberFilter,
      flex: 1,
      minWidth: 110,
    },
    {
      field: 'status',
      cellRenderer: StatusRenderer,
      flex: 1.8,
      minWidth: 115,
      sortable: false,
    },
    {
      field: 'shipping_address',
      headerName: 'Address',
      valueGetter: (params: ValueGetterParams<OrderProps, Location>) => {
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
        return Number(params.data.shipping_cost);
      },
      valueFormatter: (params) => {
        if (!params.value) return null;
        return params.value.toFixed(2);
      },
      filter: 'agNumberColumnFilter',
      flex: 3,
      minWidth: 155,
    },
    {
      field: 'net_profit',
      headerName: 'Net Profit',
      valueFormatter: (params) => params.value.toFixed(2),
      flex: 2,
      minWidth: 130,
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

  const getAndSetSelectRows = () => {
    const selectedOrders: OrderProps[] | undefined =
      gridRef.current?.api.getSelectedRows();
    setSelectedRows(selectedOrders);
  };

  const getRowNode = (rowId: string) => {
    return gridRef.current?.api.getRowNode(rowId);
  };

  useEffect(() => {
    const loadData = async () => {
      setOrdersLoading(true);
      try {
        const res = await api.get('/client_orders/orders/');
        setRowData(res.data);
      } catch (error: any) {
        console.log('Error getting orders list', error);
      } finally {
        setOrdersLoading(false);
      }
    };

    loadData();
  }, []);

  useEffect(() => {
    if (openEditOrder) getAndSetSelectRows();
  }, [openEditOrder]);

  return (
    <>
      <div className="mx-auto max-w-full">
        <Breadcrumb main="Client Orders" pageName="Orders" />
        {loading || ordersLoading ? (
          <Loader />
        ) : (
          <>
            {alert && <Alert {...alert} />}
            <div className="col-span-5 xl:col-span-3 relative">
              <div className="w-full flex flex-col border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
                <div className="p-5 flex-grow">
                  {/* Search | Order CRUD */}
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
                        onClick={handleBulkExport}
                      >
                        <FileDownloadOutlinedIcon sx={{ marginRight: '2px' }} />
                        Bulk Export
                      </button>
                    </div>
                    {/* Read Add | Edit | Delete | Export Order */}
                    <div>
                      {/* Read Order Modal */}
                      {selectedOrder && (
                        <ModalOverlay
                          isOpen={openOrder}
                          onClose={() => setOpenOrder(false)}
                        >
                          <Order
                            order={selectedOrder}
                            setOrder={setSelectedOrder}
                            orderRowNode={getRowNode(selectedOrder.id)}
                            setOpen={setOpenOrder}
                            rowData={rowData}
                            setRowData={setRowData}
                          />
                        </ModalOverlay>
                      )}
                      {/* Export Order(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-slate-200 text-black'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={handleOrderExport}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <FileDownloadOutlinedIcon />
                      </button>

                      {/* Delete Order(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-red-500 text-white'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenDeleteOrder(true)}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <DeleteOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows.length >= 1 && (
                        <ModalOverlay
                          isOpen={openDeleteOrder}
                          onClose={() => setOpenDeleteOrder(false)}
                        >
                          <DeleteOrder
                            orders={selectedRows}
                            open={openDeleteOrder}
                            setOpen={setOpenDeleteOrder}
                            rowData={rowData}
                            setRowData={setRowData}
                          />
                        </ModalOverlay>
                      )}
                      {/* Edit Order */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          selectedRows && selectedRows.length === 1
                            ? 'bg-primary text-white'
                            : 'text-slate-400 bg-gray dark:bg-meta-4'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenEditOrder(true)}
                        disabled={!selectedRows || selectedRows.length !== 1}
                      >
                        <ModeEditOutlineOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows[0] && (
                        <ModalOverlay
                          isOpen={openEditOrder}
                          onClose={() => setOpenEditOrder(false)}
                        >
                          <EditOrder
                            open={openEditOrder}
                            setOpen={setOpenEditOrder}
                            order={selectedRows[0]}
                            rowNode={getRowNode(selectedRows[0].id)}
                            setRowData={setRowData}
                          />
                        </ModalOverlay>
                      )}
                      {/* Add Order */}
                      <button
                        className="inline-flex items-center justify-center rounded-full bg-meta-3 py-2 px-3 text-center font-medium text-white hover:bg-opacity-90 lg:px-3 xl:px-3"
                        onClick={() => setOpenAddOrder(true)}
                        aria-hidden={false}
                      >
                        <AddCircleOutlinedIcon sx={{ marginRight: '3px' }} />
                        New
                      </button>
                      <ModalOverlay
                        isOpen={openAddOrder}
                        onClose={() => setOpenAddOrder(false)}
                      >
                        <AddOrder
                          open={openAddOrder}
                          setOpen={setOpenAddOrder}
                          setRowData={setRowData}
                        />
                      </ModalOverlay>
                    </div>
                  </div>
                  {/* Orders Info | Clients Count | Orders Count */}
                  <div className="mx-auto mt-3.5 mb-3.5 grid grid-cols-2 rounded-md border bg-gray border-stroke py-2.5 shadow-1 dark:border-strokedark dark:bg-[#37404F]">
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">Clients:</span>
                      <span className="font-semibold text-black dark:text-white">
                        {clients.count}
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 px-4 xsm:flex-row">
                      <span className="text-base font-medium">Orders:</span>
                      <span className="font-semibold text-black dark:text-white">
                        {ordersCount}
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

export default Orders;

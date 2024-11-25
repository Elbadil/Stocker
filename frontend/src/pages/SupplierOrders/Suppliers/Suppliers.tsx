import React, { useState, useEffect, useRef } from 'react';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import Loader from '../../../common/Loader';
import Breadcrumb from '../../../components/Breadcrumbs/Breadcrumb';
import AgGridTable, {
  AddressRenderer,
  dateFilterParams,
} from '../../../components/Tables/AgGridTable';
import ModalOverlay from '../../../components/ModalOverlay';
import { Location } from '../../ClientOrders/Clients/Client';
import { useAlert } from '../../../contexts/AlertContext';
import { Alert } from '../../UiElements/Alert';
import { api } from '../../../api/axios';
import { useSupplierOrders } from '../../../contexts/SupplierOrdersContext';
import { handleSupplierBulkExport, handleSupplierExport } from './utils';
import { AgGridReact } from '@ag-grid-community/react';
import { ColDef, ValueGetterParams } from '@ag-grid-community/core';
import AddSupplier from './AddSupplier';
import EditSupplier from './EditSupplier';

export interface SupplierProps {
  id: string;
  created_by: string;
  name: string;
  phone_number?: string | null;
  email?: string | null;
  location?: Location;
  total_orders: number;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

const Suppliers = () => {
  const { alert } = useAlert();
  const { loading, suppliers, ordersCount } = useSupplierOrders();
  const [suppliersLoading, setSuppliersLoading] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedSupplier, setSelectedSupplier] =
    useState<SupplierProps | null>(null);
  // Supplier Modals States
  const [openSupplier, setOpenSupplier] = useState<boolean>(false);
  const [openAddSupplier, setOpenAddSupplier] = useState<boolean>(false);
  const [openEditSupplier, setOpenEditSupplier] = useState<boolean>(false);
  const [openDeleteSupplier, setOpenDeleteSupplier] = useState<boolean>(false);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const gridRef = useRef<AgGridReact>(null);
  const [selectedRows, setSelectedRows] = useState<SupplierProps[] | undefined>(
    undefined,
  );

  const [rowData, setRowData] = useState<SupplierProps[]>([]);
  const [colDefs] = useState<ColDef<SupplierProps>[]>([
    {
      field: 'name',
      flex: 3,
      minWidth: 150,
    },
    {
      field: 'total_orders',
      headerName: 'Total Orders',
      flex: 3,
      minWidth: 150,
    },
    {
      field: 'phone_number',
      headerName: 'Phone Number',
      flex: 3,
      minWidth: 165,
    },
    {
      field: 'email',
      flex: 3,
      minWidth: 165,
    },
    {
      field: 'location',
      valueGetter: (params: ValueGetterParams<SupplierProps, Location>) => {
        if (!params.data?.location) return null;
        return Object.values(params.data.location).join(', ');
      },
      cellRenderer: AddressRenderer,
      flex: 3,
      minWidth: 165,
    },
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

  const getAndSetSelectRows = () => {
    const selectedSuppliers: SupplierProps[] | undefined =
      gridRef.current?.api.getSelectedRows();
    setSelectedRows(selectedSuppliers);
  };

  const getRowNode = (rowId: string) => {
    return gridRef.current?.api.getRowNode(rowId);
  };

  useEffect(() => {
    const loadData = async () => {
      setSuppliersLoading(true);
      try {
        const res = await api.get('/supplier_orders/suppliers/');
        setRowData(res.data);
      } catch (error) {
        console.log('Error fetching suppliers list', error);
      } finally {
        setSuppliersLoading(false);
      }
    };

    loadData();
  }, []);

  useEffect(() => {
    if (selectedRows) getAndSetSelectRows();
  }, [openEditSupplier]);

  return (
    <>
      <div className="mx-auto max-w-full">
        <Breadcrumb main="Supplier Orders" pageName="Suppliers" />
        {loading || suppliersLoading ? (
          <Loader />
        ) : (
          <>
            {alert && <Alert {...alert} />}
            <div className="col-span-5 xl:col-span-3 relative">
              <div className="w-full flex flex-col border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
                <div className="p-5 flex-grow">
                  {/* Search | Supplier CRUD */}
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
                          placeholder="Search Suppliers..."
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
                        onClick={handleSupplierBulkExport}
                      >
                        <FileDownloadOutlinedIcon sx={{ marginRight: '2px' }} />
                        Bulk Export
                      </button>
                    </div>
                    {/* Read Add | Edit | Delete | Export Supplier */}
                    <div>
                      {/* Read Supplier Modal */}
                      {selectedSupplier && (
                        <ModalOverlay
                          isOpen={openSupplier}
                          onClose={() => setOpenSupplier(false)}
                        >
                          <div>Hi</div>
                          {/* <Client
                            client={selectedClient}
                            setClient={setSelectedClient}
                            clientRowNode={getRowNode(selectedClient.id)}
                            setOpen={setOpenClient}
                            rowData={rowData}
                            setRowData={setRowData}
                          /> */}
                        </ModalOverlay>
                      )}
                      {/* Export Supplier(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-slate-200 text-black'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={handleSupplierExport}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <FileDownloadOutlinedIcon />
                      </button>

                      {/* Delete Supplier(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-red-500 text-white'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenDeleteSupplier(true)}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <DeleteOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows.length >= 1 && (
                        <ModalOverlay
                          isOpen={openDeleteSupplier}
                          onClose={() => setOpenDeleteSupplier(false)}
                        >
                          <div>Hi</div>
                          {/* <DeleteClient
                            clients={selectedRows}
                            open={openDeleteClient}
                            setOpen={setOpenDeleteClient}
                            rowData={rowData}
                            setRowData={setRowData}
                          /> */}
                        </ModalOverlay>
                      )}
                      {/* Edit Supplier */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          selectedRows && selectedRows.length === 1
                            ? 'bg-primary text-white'
                            : 'text-slate-400 bg-gray dark:bg-meta-4'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenEditSupplier(true)}
                        disabled={!selectedRows || selectedRows.length !== 1}
                      >
                        <ModeEditOutlineOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows[0] && (
                        <ModalOverlay
                          isOpen={openEditSupplier}
                          onClose={() => setOpenEditSupplier(false)}
                        >
                          <EditSupplier
                            supplier={selectedRows[0]}
                            open={openEditSupplier}
                            setOpen={setOpenEditSupplier}
                            rowNode={getRowNode(selectedRows[0].id)}
                            setRowData={setRowData}
                          />
                        </ModalOverlay>
                      )}
                      {/* Add Supplier */}
                      <button
                        className="inline-flex items-center justify-center rounded-full bg-meta-3 py-2 px-3 text-center font-medium text-white hover:bg-opacity-90 lg:px-3 xl:px-3"
                        onClick={() => setOpenAddSupplier(true)}
                        aria-hidden={false}
                      >
                        <AddCircleOutlinedIcon sx={{ marginRight: '3px' }} />
                        New
                      </button>
                      <ModalOverlay
                        isOpen={openAddSupplier}
                        onClose={() => setOpenAddSupplier(false)}
                      >
                        <AddSupplier
                          open={openAddSupplier}
                          setOpen={setOpenAddSupplier}
                          setRowData={setRowData}
                        />
                      </ModalOverlay>
                    </div>
                  </div>
                  {/* Supplier Info | Supplier Count | Orders Count */}
                  <div className="mx-auto mt-3.5 mb-3.5 grid grid-cols-2 rounded-md border bg-gray border-stroke py-2.5 shadow-1 dark:border-strokedark dark:bg-[#37404F]">
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">Suppliers:</span>
                      <span className="font-semibold text-black dark:text-white">
                        {suppliers.count}
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

export default Suppliers;

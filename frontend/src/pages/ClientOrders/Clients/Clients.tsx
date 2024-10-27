import { useEffect, useRef, useState } from 'react';
import { AgGridReact } from 'ag-grid-react';
import SearchRoundedIcon from '@mui/icons-material/SearchRounded';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import AgGridTable, {
  dateFilterParams,
} from '../../../components/Tables/AgGridTable';
import ModalOverlay from '../../../components/ModalOverlay';
import Loader from '../../../common/Loader';
import { ColDef } from 'ag-grid-community';
import { useAlert } from '../../../contexts/AlertContext';
import { Alert } from '../../UiElements/Alert';
import { api } from '../../../api/axios';
import Breadcrumb from '../../../components/Breadcrumbs/Breadcrumb';
import { handleBulkExport, handleClientExport } from './utils';
import AddClient from './AddClient';
import EditClient from './EditClient';
import { useClientOrders } from '../../../contexts/ClientOrdersContext';

export interface Location {
  country?: string | null;
  city?: string | null;
  street_address?: string | null;
}

export interface ClientProps {
  id: string;
  created_by: string;
  name: string;
  age?: number | null;
  phone_number?: string | null;
  email?: string | null;
  sex?: 'Male' | 'Female' | null;
  location?: Location;
  source?: string | null;
  total_orders: number;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

const Clients = () => {
  const { alert } = useAlert();
  const { loading } = useClientOrders();
  const [clientsLoading, setClientsLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedClient, setSelectedClient] = useState<ClientProps | null>(
    null,
  );
  const [openClient, setOpenClient] = useState<boolean>(false);
  const [openAddClient, setOpenAddClient] = useState<boolean>(false);
  const [openEditClient, setOpenEditClient] = useState<boolean>(false);
  const [openDeleteClient, setOpenDeleteClient] = useState<boolean>(false);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };

  const gridRef = useRef<AgGridReact>(null);
  const [selectedRows, setSelectedRows] = useState<ClientProps[] | undefined>(
    undefined,
  );
  const [rowData, setRowData] = useState<ClientProps[]>([]);
  const [colDefs] = useState<ColDef<ClientProps>[]>([
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
    const selectedClients: ClientProps[] | undefined =
      gridRef.current?.api.getSelectedRows();
    setSelectedRows(selectedClients);
  };

  const getRowNode = (rowId: string) => {
    return gridRef.current?.api.getRowNode(rowId);
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const res = await api.get('/client_orders/clients/');
        setRowData(res.data);
      } catch (err) {
        console.log('Error getting user items', err);
      } finally {
        setClientsLoading(false);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    getAndSetSelectRows();
  }, [openEditClient]);

  return (
    <>
      <div className="mx-auto max-w-full">
        <Breadcrumb main="Orders" pageName="Clients" />
        {loading || clientsLoading ? (
          <Loader />
        ) : (
          <>
            {alert && <Alert {...alert} />}
            <div className="col-span-5 xl:col-span-3 relative">
              <div className="w-full flex flex-col border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
                <div className="p-5 flex-grow">
                  {/* Search | Client CRUD */}
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
                          placeholder="Search Clients..."
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
                    {/* Read Add | Edit | Delete | Export Client */}
                    <div>
                      {/* Read Client Modal */}
                      {selectedClient && (
                        <ModalOverlay
                          isOpen={openClient}
                          onClose={() => setOpenClient(false)}
                        >
                          <div>Hi</div>
                          {/* <Item
                          item={selectedClient}
                          setItem={setSelectedClient}
                          itemRowNode={getRowNode(selectedClient.id)}
                          setOpen={setOpenClient}
                          rowData={rowData}
                          setRowData={setRowData}
                        /> */}
                        </ModalOverlay>
                      )}
                      {/* Export Client(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-slate-200 text-black'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={handleClientExport}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <FileDownloadOutlinedIcon />
                      </button>

                      {/* Delete Client(s) */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          !selectedRows || selectedRows.length < 1
                            ? 'text-slate-400 bg-gray dark:bg-meta-4'
                            : 'bg-red-500 text-white'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenDeleteClient(true)}
                        disabled={!selectedRows || selectedRows.length < 1}
                      >
                        <DeleteOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows.length >= 1 && (
                        <ModalOverlay
                          isOpen={openDeleteClient}
                          onClose={() => setOpenDeleteClient(false)}
                        >
                          <div>Hi</div>
                          {/* <DeleteItem
                          items={selectedRows}
                          open={openDeleteClient}
                          setOpen={setOpenDeleteClient}
                          rowData={rowData}
                          setRowData={setRowData}
                        /> */}
                        </ModalOverlay>
                      )}
                      {/* Edit Client */}
                      <button
                        type="button"
                        className={`mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark ${
                          selectedRows && selectedRows.length === 1
                            ? 'bg-primary text-white'
                            : 'text-slate-400 bg-gray dark:bg-meta-4'
                        } h-10 w-10.5 text-center font-medium hover:bg-opacity-90`}
                        onClick={() => setOpenEditClient(true)}
                        disabled={!selectedRows || selectedRows.length !== 1}
                      >
                        <ModeEditOutlineOutlinedIcon />
                      </button>
                      {selectedRows && selectedRows[0] && (
                        <ModalOverlay
                          isOpen={openEditClient}
                          onClose={() => setOpenEditClient(false)}
                        >
                          <EditClient
                            open={openEditClient}
                            setOpen={setOpenEditClient}
                            client={selectedRows[0]}
                            rowNode={getRowNode(selectedRows[0].id)}
                          />
                        </ModalOverlay>
                      )}
                      {/* Add Client */}
                      <button
                        className="inline-flex items-center justify-center rounded-full bg-meta-3 py-2 px-3 text-center font-medium text-white hover:bg-opacity-90 lg:px-3 xl:px-3"
                        onClick={() => setOpenAddClient(true)}
                        aria-hidden={false}
                      >
                        <AddCircleOutlinedIcon sx={{ marginRight: '3px' }} />
                        New
                      </button>
                      <ModalOverlay
                        isOpen={openAddClient}
                        onClose={() => setOpenAddClient(false)}
                      >
                        <AddClient
                          open={openAddClient}
                          setOpen={setOpenAddClient}
                          setRowData={setRowData}
                        />
                      </ModalOverlay>
                    </div>
                  </div>
                  {/* Clients Info */}
                  <div className="mx-auto mt-3.5 mb-3.5 grid grid-cols-3 rounded-md border bg-gray border-stroke py-2.5 shadow-1 dark:border-strokedark dark:bg-[#37404F]">
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">Items:</span>
                      <span className="font-semibold text-black dark:text-white">
                        4
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-500 px-4 dark:border-slate-400 xsm:flex-row">
                      <span className="text-base font-medium">
                        Total Quantity:
                      </span>
                      <span className="font-semibold text-black dark:text-white">
                        5
                      </span>
                    </div>
                    <div className="flex flex-col items-center justify-center gap-1 xsm:flex-row">
                      <span className="text-base font-medium">
                        Total Value:
                      </span>
                      <span className="font-semibold text-black dark:text-white">
                        7
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

export default Clients;

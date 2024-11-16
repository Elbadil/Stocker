import React, { useEffect, useMemo, useState } from 'react';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import { ClientProps } from './Client';
import { api } from '../../../api/axios';
import { useAlert } from '../../../contexts/AlertContext';
import ClipLoader from 'react-spinners/ClipLoader';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';
import { setClientOrders } from '../../../store/slices/clientOrdersSlice';

interface DeleteClientProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setClientOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  clients: ClientProps[];
  rowData: ClientProps[];
  setRowData: React.Dispatch<React.SetStateAction<ClientProps[]>>;
}

const DeleteClient = ({
  open,
  setOpen,
  setClientOpen,
  clients,
  rowData,
  setRowData,
}: DeleteClientProps) => {
  const { setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const [loading, setLoading] = useState<boolean>(false);
  const [deleteErrors, setDeleteErrors] = useState<string>('');

  const [clientsWithOrders, clientsWithoutOrders] = useMemo(() => {
    const withOrders: ClientProps[] = [];
    const withoutOrders: ClientProps[] = [];
    clients.forEach((client) => {
      if (client.total_orders > 0) {
        withOrders.push(client);
      } else {
        withoutOrders.push(client);
      }
    });
    return [withOrders, withoutOrders];
  }, [clients]);

  const clientsForDeletion = useMemo(
    () => ({
      ids: clientsWithoutOrders.map((client) => client.id),
      names: clientsWithoutOrders.map((client) => client.name),
    }),
    [clients, clientsWithoutOrders],
  );

  const removeDeletedClientsRows = () => {
    const clientsIds = new Set(clientsForDeletion.ids);
    const filteredRows = rowData.filter((row) => !clientsIds.has(row.id));
    setRowData(filteredRows);
  };

  const handleClientDeletion = async () => {
    setLoading(true);
    setDeleteErrors('');
    try {
      let res;
      if (clientsWithoutOrders.length > 1) {
        res = await api.delete(`/client_orders/clients/bulk_delete/`, {
          data: { ids: clientsForDeletion.ids },
        });
      } else {
        res = await api.delete(
          `/client_orders/clients/${clientsWithoutOrders[0].id}/`,
        );
      }
      console.log(res.data);
      removeDeletedClientsRows();
      dispatch((dispatch, getState) => {
        const { clientOrders } = getState();
        dispatch(
          setClientOrders({
            ...clientOrders,
            clients: {
              count: clientOrders.clients.count - clientsWithoutOrders.length,
              names: clientOrders.clients.names.filter(
                (name) => !new Set(clientsForDeletion.names).has(name),
              ),
            },
          }),
        );
      });
      setAlert({
        type: 'success',
        title:
          clientsWithoutOrders.length > 1
            ? `${clientsWithoutOrders.length} Clients Deleted`
            : 'Client Deleted',
        description: `You successfully deleted ${
          clientsWithoutOrders.length > 1
            ? `${clientsWithoutOrders.length} clients`
            : `client ${clientsWithoutOrders[0].name}`
        }.`,
      });
      setOpen(false);
      if (setClientOpen) setClientOpen(false);
    } catch (error: any) {
      console.log('Error during client deletion', error);
      setDeleteErrors('Something went wrong, please try again later');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) setDeleteErrors('');
  }, [open]);

  return (
    <div className="mx-auto max-w-sm min-w-80 border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          {clients.length > 1 ? 'Delete Clients' : 'Delete Client'}
        </h3>
        <div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-hidden={true}
          >
            <span className="text-slate-400 hover:text-slate-700 dark:text-white dark:hover:text-slate-300">
              ✖
            </span>
          </button>
        </div>
      </div>
      {/* Form Content */}
      <div className="max-w-full overflow-y-auto max-h-[85vh] text-black dark:text-white flex flex-col">
        <div className="p-5">
          <div className="mb-3  font-medium">
            Are you sure you want to delete:
          </div>
          <ol className="list-inside list-disc">
            {clients.map((client, index: number) => (
              <li className="mt-2" key={index}>
                {client.name}
                {client.total_orders > 0 && (
                  <WarningAmberOutlinedIcon
                    sx={{
                      color: '#f97316',
                      fontSize: '22px',
                      paddingBottom: '4px',
                      marginLeft: '1.5px',
                    }}
                  />
                )}
              </li>
            ))}
          </ol>
          {clientsWithOrders.length > 0 && (
            <div className="mt-3 text-sm text-orange-500 flex justify-start gap-0.5">
              <WarningAmberOutlinedIcon
                sx={{
                  fontSize: '17.5px',
                  paddingTop: '3px',
                }}
              />
              <p>
                {clientsWithOrders.length > 1
                  ? clientsWithOrders.length === clients.length
                    ? 'All selected clients are '
                    : 'Some selected clients are '
                  : `Client ${clientsWithOrders[0].name} is `}
                linked to existing orders and won't be deleted. Please manage
                their orders before deletion.
              </p>
            </div>
          )}
          {deleteErrors && (
            <p className="mt-2 text-red-500 font-medium text-sm italic">
              {deleteErrors}
            </p>
          )}
        </div>
      </div>
      {/* Form Submission */}
      <div className="flex justify-end gap-3 border-t border-stroke py-3 px-4 dark:border-strokedark">
        <button
          className="flex justify-center bg-slate-300	 hover:bg-opacity-90 rounded py-2 px-4 font-medium text-slate-700"
          type="button"
          onClick={() => setOpen(false)}
        >
          Cancel
        </button>
        <button
          className={
            'flex justify-center ' +
            (clientsWithOrders.length === clients.length
              ? 'cursor-not-allowed bg-red-400 '
              : 'bg-red-500 hover:bg-opacity-90 ') +
            'rounded py-2 px-6 font-medium text-gray'
          }
          type="submit"
          onClick={handleClientDeletion}
          disabled={clientsWithOrders.length === clients.length}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteClient;

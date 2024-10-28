import React, { useEffect, useState } from 'react';
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

  const clientsData = {
    ids: clients.map((client) => client.id),
    names: clients.map((client) => client.name),
  };

  const removeDeletedClientsRows = () => {
    const clientsIds = new Set(clientsData.ids);
    const filteredRows = rowData.filter((row) => !clientsIds.has(row.id));
    setRowData(filteredRows);
  };

  const handleClientDeletion = async () => {
    setLoading(true);
    setDeleteErrors('');
    try {
      let res;
      if (clients.length > 1) {
        res = await api.delete(`/client_orders/clients/bulk_delete/`, {
          data: { ids: clientsData.ids },
        });
      } else {
        res = await api.delete(`/client_orders/clients/${clients[0].id}/`);
      }
      console.log(res.data);
      removeDeletedClientsRows();
      dispatch((dispatch, getState) => {
        const { clientOrders } = getState();
        dispatch(
          setClientOrders({
            ...clientOrders,
            clients: {
              count: clientOrders.clients.count - clients.length,
              names: clientOrders.clients.names.filter(
                (name) => !new Set(clientsData.names).has(name),
              ),
            },
          }),
        );
      });
      setAlert({
        type: 'success',
        title:
          clients.length > 1
            ? `${clients.length} Clients Deleted`
            : 'Client Deleted',
        description: `You successfully deleted ${
          clients.length > 1
            ? `${clients.length} clients`
            : `client ${clients[0].name}`
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
              </li>
            ))}
          </ol>
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
          className="flex justify-center bg-red-500 hover:bg-opacity-90 rounded py-2 px-4 font-medium text-gray"
          type="submit"
          onClick={handleClientDeletion}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteClient;

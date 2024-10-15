import React, { useEffect, useState } from 'react';
import ClipLoader from 'react-spinners/ClipLoader';
import { Item } from './Items';
import { api } from '../../api/axios';
import { useDispatch } from 'react-redux';
import { setInventory } from '../../store/slices/inventorySlice';
import { AppDispatch } from '../../store/store';
import { useAlert } from '../../contexts/AlertContext';

export interface DeleteItemProps {
  items: Item[];
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowData: Item[];
  setRowData: React.Dispatch<React.SetStateAction<Item[]>>;
}

const DeleteItem = ({
  items,
  open,
  setOpen,
  rowData,
  setRowData,
}: DeleteItemProps) => {
  const dispatch = useDispatch<AppDispatch>();
  const { setAlert } = useAlert();
  const [loading, setLoading] = useState<boolean>(false);
  const [deleteErrors, setDeleteErrors] = useState<string>('');

  const itemsSummary = {
    ids: items.map((item) => item.id),
    totalQuantity: items.reduce(
      (prevQuantity, item) => prevQuantity + item.quantity,
      0,
    ),
    totalValue: items.reduce(
      (prevValue, item) => prevValue + item.total_price,
      0,
    ),
  };

  const removeDeletedRows = () => {
    const itemsIds = new Set(itemsSummary.ids);
    const filteredRows = rowData.filter((item: Item) => !itemsIds.has(item.id));
    setRowData(filteredRows);
  };

  const handleDelete = async () => {
    setLoading(true);
    setDeleteErrors('');
    try {
      if (items.length === 0) {
        throw new Error('No items to delete');
      }

      let res;
      if (items.length > 1) {
        console.log('items length', items.length);
        res = await api.delete('/inventory/items/bulk_delete/', {
          data: { ids: itemsSummary.ids },
        });
      } else {
        res = await api.delete(`/inventory/items/${items[0].id}/`);
      }
      console.log(res.status);
      dispatch((dispatch, getState) => {
        const { inventory } = getState();
        dispatch(
          setInventory({
            ...inventory,
            totalItems: inventory.totalItems - items.length,
            totalQuantity: inventory.totalQuantity - itemsSummary.totalQuantity,
            totalValue: inventory.totalValue - itemsSummary.totalValue,
          }),
        );
      });
      removeDeletedRows();
      // setTimeout(() => {
      setAlert({
        type: 'success',
        title:
          items.length > 1 ? `${items.length} Items Deleted` : 'Item Deleted',
        description:
          items.length > 1
            ? `You have successfully deleted ${items.length} items from your inventory.`
            : `You have successfully deleted ${items[0].name} from your inventory.`,
      });
      setOpen(false);
      // }, 1000);
    } catch (err) {
      console.log('Error deleting items', err);
      setDeleteErrors('Something went wrong. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) setDeleteErrors('');
  }, [open]);

  return (
    <div className="mx-auto max-w-md min-w-80 border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          {items.length > 1 ? 'Delete Items' : 'Delete Item'}
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
      <div className="max-w-full overflow-y-auto max-h-[80vh] text-black dark:text-white flex flex-col">
        <div className="p-5">
          <div className="mb-3  font-medium">
            Are you sure you want to delete:
          </div>
          <ol className="list-inside list-disc">
            {items.map((item, index: number) => (
              <li className="mt-2" key={index}>
                {item.name}
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
          onClick={handleDelete}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteItem;

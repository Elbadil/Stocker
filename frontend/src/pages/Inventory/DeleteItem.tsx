import React, { useEffect, useMemo, useState } from 'react';
import ClipLoader from 'react-spinners/ClipLoader';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import { ItemProps } from './Item';
import { api } from '../../api/axios';
import { useDispatch } from 'react-redux';
import { setInventory } from '../../store/slices/inventorySlice';
import { AppDispatch } from '../../store/store';
import { useAlert } from '../../contexts/AlertContext';
import { useInventory } from '../../contexts/InventoryContext';

export interface DeleteItemProps {
  selectedItems: ItemProps[];
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowData: ItemProps[];
  setRowData: React.Dispatch<React.SetStateAction<ItemProps[]>>;
  setItemOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}

const DeleteItem = ({
  selectedItems,
  open,
  setOpen,
  rowData,
  setRowData,
  setItemOpen,
}: DeleteItemProps) => {
  const dispatch = useDispatch<AppDispatch>();
  const { setAlert } = useAlert();
  const { items } = useInventory();
  const [loading, setLoading] = useState<boolean>(false);
  const [deleteErrors, setDeleteErrors] = useState<string>('');

  const itemsSummary = {
    ids: selectedItems.map((item) => item.id),
    names: selectedItems.map((item) => item.name),
    totalQuantity: selectedItems.reduce(
      (prevQuantity, item) => prevQuantity + item.quantity,
      0,
    ),
    totalValue: selectedItems.reduce(
      (prevValue, item) => prevValue + item.total_price,
      0,
    ),
  };

  const removeDeletedRows = () => {
    const itemsIds = new Set(itemsSummary.ids);
    const filteredRows = rowData.filter(
      (item: ItemProps) => !itemsIds.has(item.id),
    );
    setRowData(filteredRows);
  };

  const isItemOrdered = (selectedItem: ItemProps) => {
    const itemFound = items.find((item) => item.name === selectedItem.name);
    return itemFound ? itemFound.ordered : false;
  };

  const orderedItems = useMemo(() => {
    const itemsNames = new Set(itemsSummary.names);
    return items.filter((item) => itemsNames.has(item.name) && item.ordered);
  }, [items, selectedItems]);

  const handleDelete = async () => {
    setLoading(true);
    setDeleteErrors('');
    try {
      if (selectedItems.length === 0) {
        throw new Error('No items to delete');
      }

      let res;
      if (selectedItems.length > 1) {
        console.log('items length', selectedItems.length);
        res = await api.delete('/inventory/items/bulk_delete/', {
          data: { ids: itemsSummary.ids },
        });
      } else {
        res = await api.delete(`/inventory/items/${selectedItems[0].id}/`);
      }
      console.log(res.status);
      dispatch((dispatch, getState) => {
        const { inventory } = getState();
        dispatch(
          setInventory({
            ...inventory,
            items: items.filter(
              (item) => !itemsSummary.names.includes(item.name),
            ),
            totalItems: inventory.totalItems - selectedItems.length,
            totalQuantity: inventory.totalQuantity - itemsSummary.totalQuantity,
            totalValue: inventory.totalValue - itemsSummary.totalValue,
          }),
        );
      });
      removeDeletedRows();
      setAlert({
        type: 'success',
        title:
          selectedItems.length > 1
            ? `${selectedItems.length} Items Deleted`
            : 'Item Deleted',
        description:
          selectedItems.length > 1
            ? `You have successfully deleted ${selectedItems.length} items from your inventory.`
            : `You have successfully deleted ${selectedItems[0].name} from your inventory.`,
      });
      setOpen(false);
      if (setItemOpen) setItemOpen(false);
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
    <div className="mx-auto max-w-sm border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          {selectedItems.length > 1 ? 'Delete Items' : 'Delete Item'}
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
          <div className="mb-3 font-medium">
            Are you sure you want to delete:
          </div>
          <ol className="list-inside list-disc">
            {selectedItems.map((selectedItem, index: number) => (
              <li className="mt-2" key={index}>
                {selectedItem.name}
                {isItemOrdered(selectedItem) && (
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

          {/* Delete Errors */}
          {orderedItems.length > 0 && (
            <div className="mt-3 text-sm text-orange-500 flex justify-start gap-0.5">
              <WarningAmberOutlinedIcon
                sx={{
                  fontSize: '17.5px',
                  paddingTop: '3px',
                }}
              />
              <p>
                {orderedItems.length > 1
                  ? orderedItems.length === selectedItems.length
                    ? 'All selected items are '
                    : 'Some selected items are '
                  : `${orderedItems[0].name} is `}
                linked to existing orders. Please manage orders before deletion.
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
            (orderedItems.length > 0
              ? 'cursor-not-allowed bg-red-400 '
              : 'bg-red-500 hover:bg-opacity-90 ') +
            'rounded py-2 px-6 font-medium text-gray'
          }
          type="submit"
          onClick={handleDelete}
          disabled={orderedItems.length > 0}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteItem;

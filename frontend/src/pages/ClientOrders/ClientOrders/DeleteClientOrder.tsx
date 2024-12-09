import React, { useEffect, useState } from 'react';
import ClipLoader from 'react-spinners/ClipLoader';
import { ClientOrderProps } from './ClientOrder';
import { api } from '../../../api/axios';
import { useAlert } from '../../../contexts/AlertContext';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';
import { setClientOrders } from '../../../store/slices/clientOrdersSlice';
import { useClientOrders } from '../../../contexts/ClientOrdersContext';
import { setInventory } from '../../../store/slices/inventorySlice';
import { useInventory } from '../../../contexts/InventoryContext';
import { statusType } from '../../../utils/form';

interface DeleteClientOrderProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  orders: ClientOrderProps[];
  rowData: ClientOrderProps[];
  setRowData: React.Dispatch<React.SetStateAction<ClientOrderProps[]>>;
  setOrderOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}

const DeleteClientOrder = ({
  open,
  setOpen,
  orders,
  rowData,
  setRowData,
  setOrderOpen,
}: DeleteClientOrderProps) => {
  const { setAlert } = useAlert();
  const { ordersCount, orderStatus } = useClientOrders();
  const { items } = useInventory();
  const dispatch = useDispatch<AppDispatch>();
  const [loading, setLoading] = useState<boolean>(false);
  const [deleteErrors, setDeleteErrors] = useState<string>('');

  const ordersSummary = {
    ids: orders.map((order) => order.id),
    orderedItemsGrouped: orders.map((order) => order.ordered_items),
    delivery_status: orders.map((order) => order.delivery_status),

    flattenedOrderedItems() {
      const orderedItemsMap = new Map();

      this.orderedItemsGrouped.forEach((items) => {
        items.forEach((orderedItem) => {
          const itemName = orderedItem.item;
          if (orderedItemsMap.has(itemName)) {
            const prevValue = orderedItemsMap.get(itemName);
            orderedItemsMap.set(itemName, {
              ...prevValue,
              quantity: prevValue.quantity + orderedItem.ordered_quantity,
            });
          } else {
            orderedItemsMap.set(itemName, {
              name: orderedItem.item,
              quantity: orderedItem.ordered_quantity,
            });
          }
        });
      });

      return orderedItemsMap;
    },
  };

  const updateRowData = () => {
    const ordersIds = new Set(ordersSummary.ids);
    const filteredRows = rowData.filter((row) => !ordersIds.has(row.id));
    setRowData(filteredRows);
  };

  const updateOrderStatusState = () => {
    const newOrderStatus = structuredClone(orderStatus);
    ordersSummary.delivery_status.forEach((status) => {
      const delStatusType = statusType(status);
      newOrderStatus[delStatusType] = newOrderStatus[delStatusType] - 1;
    });
    return newOrderStatus;
  };

  const updateOrdersState = () => {
    dispatch((dispatch, getState) => {
      const { inventory, clientOrders } = getState();
      dispatch(
        setClientOrders({
          ...clientOrders,
          ordersCount: ordersCount - orders.length,
          orderStatus: updateOrderStatusState(),
        }),
      );
      dispatch(
        setInventory({
          ...inventory,
          items: items.map((item) => {
            const orderedItemsMap = ordersSummary.flattenedOrderedItems();
            const orderedItem = orderedItemsMap.get(item.name);
            return orderedItem
              ? { ...item, quantity: item.quantity + orderedItem.quantity }
              : item;
          }),
        }),
      );
    });
  };

  const handleOrderDeletion = async () => {
    setLoading(true);
    setDeleteErrors('');
    try {
      let res;
      if (orders.length > 1) {
        res = await api.delete('/client_orders/orders/bulk_delete/', {
          data: { ids: ordersSummary.ids },
        });
      } else {
        res = await api.delete(`/client_orders/orders/${orders[0].id}/`);
      }
      console.log(res.data);
      // Remove deleted order(s) from the orders table
      updateRowData();
      // Update ordersCount and items state
      updateOrdersState();
      // Set success Alert
      setAlert({
        type: 'success',
        title:
          orders.length > 1
            ? `${orders.length} Orders Deleted.`
            : `Order Deleted.`,
        description: `You successfully deleted ${
          orders.length > 1
            ? `${orders.length} orders`
            : `order ${orders[0].reference_id} by ${orders[0].client}`
        }.`,
      });
      // Close the delete order(s) modal
      setOpen(false);
      if (setOrderOpen) setOrderOpen(false);
    } catch (error: any) {
      console.log('Error during orders deletion', error);
      setDeleteErrors('Something went wrong, please try again later.');
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
          {orders.length > 1 ? 'Delete Orders' : 'Delete Order'}
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
          <div className="mb-2.5 font-medium">
            Are you sure you want to delete:
          </div>
          <ol className="list-inside list-disc">
            {orders.map((order, index: number) => (
              <li className="mt-2" key={index}>
                Order {order.reference_id} - by {order.client}
              </li>
            ))}
          </ol>
          <div className="mt-2 text-sm text-yellow-600 dark:text-yellow-500">
            * Deleting {orders.length > 1 ? 'these orders' : 'this order'} will
            automatically restore the linked ordered item quantities to the
            inventory.
          </div>
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
          onClick={handleOrderDeletion}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteClientOrder;

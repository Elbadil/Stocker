import React, { useEffect, useState } from 'react';
import ClipLoader from 'react-spinners/ClipLoader';
import { SupplierOrderProps } from './SupplierOrders';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';
import { setSupplierOrders } from '../../../store/slices/supplierOrdersSlice';
import { api } from '../../../api/axios';
import { useSupplierOrders } from '../../../contexts/SupplierOrdersContext';
import { statusType } from '../../../utils/form';
import { useAlert } from '../../../contexts/AlertContext';

interface DeleteSupplierOrder {
  orders: SupplierOrderProps[];
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setOrderOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  rowData: SupplierOrderProps[];
  setRowData: React.Dispatch<React.SetStateAction<SupplierOrderProps[]>>;
}

const DeleteSupplierOrder = ({
  orders,
  open,
  setOpen,
  setOrderOpen,
  rowData,
  setRowData,
}: DeleteSupplierOrder) => {
  const dispatch = useDispatch<AppDispatch>();
  const { setAlert } = useAlert();
  const { orderStatus, ordersCount } = useSupplierOrders();
  const [loading, setLoading] = useState<boolean>(false);
  const [deleteErrors, setDeleteErrors] = useState<string>('');

  const ordersSummary = {
    ids: orders.map((order) => order.id),
    deliveryStatus: orders.map((order) => order.delivery_status),
  };

  const removeDeletedOrdersRows = () => {
    const deletedOrdersIds = new Set(ordersSummary.ids);
    const filteredRows = rowData.filter((row) => !deletedOrdersIds.has(row.id));
    setRowData(filteredRows);
  };

  const updateOrderStatusState = () => {
    const newOrderStatus = structuredClone(orderStatus);
    ordersSummary.deliveryStatus.forEach((status) => {
      const delStatusType = statusType(status);
      newOrderStatus[delStatusType] -= 1;
    });
    return newOrderStatus;
  };

  const handleOrderDeletion = async () => {
    setLoading(true);
    setDeleteErrors('');
    try {
      let res;
      if (orders.length > 1) {
        res = await api.delete('/supplier_orders/orders/bulk_delete/', {
          data: { ids: ordersSummary.ids },
        });
      } else {
        res = await api.delete(`/supplier_orders/orders/${orders[0].id}/`);
      }
      console.log(res.data);
      // Remove deleted orders rows
      removeDeletedOrdersRows();
      // Update orderStatus and ordersCount states
      dispatch((dispatch, getState) => {
        const { supplierOrders } = getState();
        dispatch(
          setSupplierOrders({
            ...supplierOrders,
            orderStatus: updateOrderStatusState(),
            ordersCount: ordersCount - orders.length,
          }),
        );
      });
      // Set and display success Alert
      setAlert({
        type: 'success',
        title:
          orders.length > 1
            ? `${orders.length} Orders Deleted.`
            : `Order Deleted.`,
        description: `You successfully deleted ${
          orders.length > 1
            ? `${orders.length} orders`
            : `order ${orders[0].reference_id} from ${orders[0].supplier}`
        }.`,
      });
      // Close supplierOrder details modal if any
      if (setOrderOpen) setOrderOpen(false);
      // Close Delete Supplier Order(s) modal
      setOpen(false);
    } catch (error) {
      console.log('Error during orders deletion', error);
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
          <div className="mb-3  font-medium">
            Are you sure you want to delete:
          </div>
          <ol className="list-inside list-disc">
            {orders.map((order, index: number) => (
              <li className="mt-2" key={index}>
                Order {order.reference_id} - From {order.supplier}
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
          onClick={handleOrderDeletion}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteSupplierOrder;

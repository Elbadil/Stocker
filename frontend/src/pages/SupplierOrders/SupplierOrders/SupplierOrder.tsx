import React, { useState } from 'react';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import ModalOverlay from '../../../components/ModalOverlay';
import { handleSupplierOrderExport } from './utils';
import { IRowNode } from '@ag-grid-community/core';
import EditSupplierOrder from './EditSupplierOrder';
import DeleteSupplierOrder from './DeleteSupplierOrder';

export interface SupplierOrderedItem {
  id: string;
  order: string;
  created_by: string;
  item: string;
  supplier: string;
  ordered_quantity: number;
  ordered_price: number;
  total_price: number;
  in_inventory: boolean;
}

export interface SupplierOrderProps {
  id: string;
  reference_id: string;
  created_by: string;
  supplier: string;
  ordered_items: SupplierOrderedItem[];
  total_price: number;
  delivery_status: string;
  payment_status: string;
  tracking_number?: string | null;
  shipping_cost?: number | null;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

interface SupplierOrder {
  order: SupplierOrderProps;
  setOrder: React.Dispatch<React.SetStateAction<SupplierOrderProps | null>>;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowNode?: IRowNode<SupplierOrderProps>;
  rowData: SupplierOrderProps[];
  setRowData: React.Dispatch<React.SetStateAction<SupplierOrderProps[]>>;
}

const SupplierOrder = ({
  order,
  setOpen,
  setOrder,
  rowNode,
  rowData,
  setRowData,
}: SupplierOrder) => {
  const [openEditOrder, setOpenEditOrder] = useState<boolean>(false);
  const [openDeleteOrder, setOpenDeleteOrder] = useState<boolean>(false);

  const statusStyle = (status: string) => {
    const success = ['Paid', 'Delivered'];
    const failure = ['Failed', 'Canceled', 'Returned', 'Refunded'];

    if (success.includes(status)) {
      return 'bg-lime-500';
    } else if (failure.includes(status)) {
      return 'bg-red-500';
    }
    return 'bg-cyan-500';
  };

  return (
    <div className="mx-auto max-w-sm border rounded-md border-stroke bg-white dark:border-slate-700 dark:bg-boxdark">
      {/* Order Modal Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Order {order.reference_id} - From: {order.supplier}
        </h3>
        <div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-hidden={true}
          >
            <span className="ml-3 text-slate-400 hover:text-slate-700 dark:text-white dark:hover:text-slate-300">
              ✖
            </span>
          </button>
        </div>
      </div>

      {/* Order Details */}
      <div className="max-w-full overflow-y-auto max-h-[80vh] flex flex-col">
        {/* Export | Edit | Delete Buttons */}
        <div className="flex justify-end items-center">
          <div className="px-2.5 pt-2.5">
            {/* Export Order */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-black dark:hover:text-black hover:bg-slate-200 dark:hover:bg-slate-200"
              onClick={() => handleSupplierOrderExport([order])}
            >
              <FileDownloadOutlinedIcon />
            </button>
            {/* Edit Order */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-primary dark:hover:bg-primary"
              onClick={() => setOpenEditOrder(true)}
            >
              <ModeEditOutlineOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openEditOrder}
              onClose={() => setOpenEditOrder(false)}
            >
              <EditSupplierOrder
                open={openEditOrder}
                setOpen={setOpenEditOrder}
                supplierOrder={order}
                setSupplierOrder={setOrder}
                rowNode={rowNode}
                setRowData={setRowData}
              />
            </ModalOverlay>
            {/* Delete Order */}
            <button
              type="button"
              className="mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-red-500 dark:hover:bg-red-500"
              onClick={() => setOpenDeleteOrder(true)}
            >
              <DeleteOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openDeleteOrder}
              onClose={() => setOpenDeleteOrder(false)}
            >
              <DeleteSupplierOrder
                open={openDeleteOrder}
                setOpen={setOpenDeleteOrder}
                orders={[order]}
                rowData={rowData}
                setRowData={setRowData}
                setOrderOpen={setOpen}
              />
            </ModalOverlay>
          </div>
        </div>
        <div className="px-6 pb-6 pt-1">
          {/* Order Info */}
          <div className="divide-y divide-slate-200 dark:divide-slate-600">
            {/* Ref ID */}
            <div className="mb-2">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Ref
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {order.reference_id}
              </p>
            </div>
            {/* Created | Updated at */}
            <div className="mb-3 pt-3 flex flex-row gap-9.5">
              {/* Created at */}
              <div className="">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Created
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {order.created_at}
                </p>
              </div>
              {/* Updated at */}
              {order.updated && (
                <div className="">
                  <div className="mb-1 block text-base font-medium text-black dark:text-white">
                    Updated
                  </div>
                  <p className="text-base text-slate-900 truncate dark:text-slate-300">
                    {order.updated_at}
                  </p>
                </div>
              )}
            </div>
            {/* Supplier */}
            <div className="mb-2">
              <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                Supplier
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {order.supplier}
              </p>
            </div>
            {/* Ordered Items */}
            <div className="mb-2">
              <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                Ordered Items
              </div>
              <ol className="text-base text-slate-900 truncate dark:text-slate-300 space-y-1 list-inside list-disc">
                {order.ordered_items.map((orderedItem, index: number) => (
                  <li key={index}>
                    <span className="font-medium underline">
                      {orderedItem.item}:
                    </span>
                    <div className="flex justify-between items-center py-1.5">
                      <div className="flex justify-center flex-col">
                        <div className="font-medium">Quantity</div>
                        <div>{orderedItem.ordered_quantity}</div>
                      </div>
                      <div>
                        <div className="font-medium">Price</div>
                        <div>{orderedItem.ordered_price.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="font-medium">T. Price</div>
                        <div>{orderedItem.total_price.toFixed(2)}</div>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
            {/* Total Order Price */}
            <div className="mb-2">
              <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                Total Order Price
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {order.total_price.toFixed(2)}
              </p>
            </div>
            {/* Delivery | Payment Status */}
            <div className="mb-3 flex flex-row gap-9.5">
              {/* Delivery Status */}
              <div className="">
                <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                  Delivery Status
                </div>
                <p className="text-base py-1.5 text-slate-900 truncate dark:text-slate-300">
                  <span
                    className={`${statusStyle(
                      order.delivery_status,
                    )} text-white p-1.5 font-semibold rounded-md`}
                  >
                    {order.delivery_status}
                  </span>
                </p>
              </div>
              {/* Payment Status */}
              <div className="">
                <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                  Payment Status
                </div>
                <p className="text-base py-1.5 text-slate-900 truncate dark:text-slate-300">
                  <span
                    className={`${statusStyle(
                      order.payment_status,
                    )} text-white p-1.5 font-semibold rounded-md`}
                  >
                    {order.payment_status}
                  </span>
                </p>
              </div>
            </div>
            {/* Tracking Number */}
            {order.tracking_number && (
              <div className="mb-2 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Tracking Number
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {order.tracking_number}
                </p>
              </div>
            )}
            {/* Shipping cost */}
            {order.shipping_cost && (
              <div className="mb-2 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Shipping cost
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {order.shipping_cost}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupplierOrder;

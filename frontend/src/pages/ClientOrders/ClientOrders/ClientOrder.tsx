import React, { useState } from 'react';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import { IRowNode } from '@ag-grid-community/core';
import { handleOrderExport } from './utils';
import EditClientOrder from './EditClientOrder';
import DeleteClientOrder from './DeleteClientOrder';
import { Location } from '../Clients/Client';
import ModalOverlay from '../../../components/ModalOverlay';

export interface ClientOrderedItem {
  item: string;
  ordered_quantity: number;
  ordered_price: number;
  total_price: number;
  total_profit: number;
}

export interface ClientOrderProps {
  id: string;
  reference_id: string;
  created_by: string;
  client: string;
  ordered_items: ClientOrderedItem[];
  status: string;
  shipping_address: Location;
  shipping_cost?: number | null;
  net_profit: number;
  source?: string | null;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

interface ClientOrder {
  order: ClientOrderProps;
  setOrder: React.Dispatch<React.SetStateAction<ClientOrderProps | null>>;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  orderRowNode?: IRowNode<ClientOrderProps>;
  rowData: ClientOrderProps[];
  setRowData: React.Dispatch<React.SetStateAction<ClientOrderProps[]>>;
}

const ClientOrder = ({
  order,
  setOrder,
  setOpen,
  orderRowNode,
  rowData,
  setRowData,
}: ClientOrder) => {
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
          Order {order.reference_id} - By: {order.client}
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
              onClick={() => handleOrderExport([order])}
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
              <EditClientOrder
                open={openEditOrder}
                setOpen={setOpenEditOrder}
                order={order}
                setOrder={setOrder}
                rowNode={orderRowNode}
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
              <DeleteClientOrder
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
            {/* Client */}
            <div className="mb-2">
              <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                Client
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {order.client}
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
                      <div>
                        <div className="font-medium">Profit</div>
                        <div>{orderedItem.total_profit.toFixed(2)}</div>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
            {/* Status */}
            <div className="mb-2">
              <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                Status
              </div>
              <p className="text-base py-1.5 text-slate-900 truncate dark:text-slate-300">
                <span
                  className={`${statusStyle(
                    order.status,
                  )} text-white p-1.5 font-semibold rounded-md`}
                >
                  {order.status}
                </span>
              </p>
            </div>
            {/* Source of Acquisition */}
            {order.source && (
              <div className="mb-2">
                <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                  Source of Acquisition
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {order.source}
                </p>
              </div>
            )}
            {/* Address */}
            {order.shipping_address && (
              <div className="mb-2 pt-2">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Address
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {Object.values(order.shipping_address).reverse().join(', ')}.
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
            {/* Net Profit */}
            <div className="mb-2 pt-3">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Net Profit{' '}
                <span className="text-sm italic font-light ml-1">
                  total revenue - costs
                </span>
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {order.net_profit.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClientOrder;

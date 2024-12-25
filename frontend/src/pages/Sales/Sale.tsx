import React, { useState } from 'react';
import { IRowNode } from '@ag-grid-community/core';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import ModalOverlay from '../../components/ModalOverlay';
import { Location } from '../ClientOrders/Clients/Client';
import EditSale from './EditSale';
import DeleteSale from './DeleteSale';
import { handleSaleExport } from './utils';

export interface SoldItem {
  id: string;
  created_by: string;
  item: string;
  sold_quantity: number;
  sold_price: number;
  total_price: number;
  total_profit: number;
}

export interface SaleProps {
  id: string;
  reference_id: string;
  created_by: string;
  client: string;
  sold_items: SoldItem[];
  delivery_status: string;
  payment_status: string;
  shipping_address: Location | null;
  shipping_cost: number;
  net_profit: number;
  source?: string | null;
  tracking_number?: string | null;
  linked_order?: string | null; 
  created_at: string;
  updated_at: string;
  updated: boolean;
}

interface Sale {
  sale: SaleProps;
  setSale: React.Dispatch<React.SetStateAction<SaleProps | null>>;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowNode?: IRowNode<SaleProps>;
  rowData: SaleProps[];
  setRowData: React.Dispatch<React.SetStateAction<SaleProps[]>>;
}

const Sale = ({
  sale,
  setSale,
  setOpen,
  rowNode,
  rowData,
  setRowData,
}: Sale) => {
  const [openEditSale, setOpenEditSale] = useState<boolean>(false);
  const [openDeleteSale, setOpenDeleteSale] = useState<boolean>(false);

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
      {/* Sale Modal Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Sale {sale.reference_id} - Made by: {sale.client}
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

      {/* Sale Details */}
      <div className="max-w-full overflow-y-auto max-h-[80vh] flex flex-col">
        {/* Export | Edit | Delete Buttons */}
        <div className="flex justify-end items-center">
          <div className="px-2.5 pt-2.5">
            {/* Export Sale */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-black dark:hover:text-black hover:bg-slate-200 dark:hover:bg-slate-200"
              onClick={() => handleSaleExport([sale])}
            >
              <FileDownloadOutlinedIcon />
            </button>
            {/* Edit Sale */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-primary dark:hover:bg-primary"
              onClick={() => setOpenEditSale(true)}
            >
              <ModeEditOutlineOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openEditSale}
              onClose={() => setOpenEditSale(false)}
            >
              <EditSale
                open={openEditSale}
                setOpen={setOpenEditSale}
                sale={sale}
                setSale={setSale}
                rowNode={rowNode}
                setRowData={setRowData}
              />
            </ModalOverlay>
            {/* Delete Sale */}
            <button
              type="button"
              className="mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-red-500 dark:hover:bg-red-500"
              onClick={() => setOpenDeleteSale(true)}
            >
              <DeleteOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openDeleteSale}
              onClose={() => setOpenDeleteSale(false)}
            >
              <DeleteSale
                open={openDeleteSale}
                setOpen={setOpenDeleteSale}
                sales={[sale]}
                rowData={rowData}
                setRowData={setRowData}
                setSaleOpen={setOpen}
              />
            </ModalOverlay>
          </div>
        </div>
        <div className="px-6 pb-6 pt-1">
          {/* Sale Info */}
          <div className="divide-y divide-slate-200 dark:divide-slate-600">
            {/* Ref ID */}
            <div className="mb-2">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Ref
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {sale.reference_id}
              </p>
            </div>
            {/* Linked Order */}
            {sale.linked_order && (
              <div className="mb-2 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Linked Order Ref
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {sale.linked_order}
                </p>
              </div>
            )}
            {/* Created | Updated at */}
            <div className="mb-3 pt-3 flex flex-row gap-9.5">
              {/* Created at */}
              <div className="">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Created
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {sale.created_at}
                </p>
              </div>
              {/* Updated at */}
              {sale.updated && (
                <div className="">
                  <div className="mb-1 block text-base font-medium text-black dark:text-white">
                    Updated
                  </div>
                  <p className="text-base text-slate-900 truncate dark:text-slate-300">
                    {sale.updated_at}
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
                {sale.client}
              </p>
            </div>
            {/* Sold Items */}
            <div className="mb-2">
              <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                Sold Items
              </div>
              <ol className="text-base text-slate-900 truncate dark:text-slate-300 space-y-1 list-inside list-disc">
                {sale.sold_items.map((soldItem, index: number) => (
                  <li key={index}>
                    <span className="font-medium underline">
                      {soldItem.item}:
                    </span>
                    <div className="flex justify-between items-center py-1.5">
                      <div className="flex justify-center flex-col">
                        <div className="font-medium">Quantity</div>
                        <div>{soldItem.sold_quantity}</div>
                      </div>
                      <div>
                        <div className="font-medium">Price</div>
                        <div>{soldItem.sold_price.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="font-medium">T. Price</div>
                        <div>{soldItem.total_price.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="font-medium">Profit</div>
                        <div>{soldItem.total_profit.toFixed(2)}</div>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
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
                      sale.delivery_status,
                    )} text-white p-1.5 font-semibold rounded-md`}
                  >
                    {sale.delivery_status}
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
                      sale.payment_status,
                    )} text-white p-1.5 font-semibold rounded-md`}
                  >
                    {sale.payment_status}
                  </span>
                </p>
              </div>
            </div>
            {/* Source of Acquisition */}
            {sale.source && (
              <div className="mb-2">
                <div className="mb-1 pt-2 block text-base font-medium text-black dark:text-white">
                  Source of Acquisition
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {sale.source}
                </p>
              </div>
            )}
            {/* Address */}
            {sale.shipping_address && (
              <div className="mb-2 pt-2">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Address
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {Object.values(sale.shipping_address).reverse().join(', ')}.
                </p>
              </div>
            )}
            {/* Tracking Number */}
            {sale.tracking_number && (
              <div className="mb-2 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Tracking Number
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {sale.tracking_number}
                </p>
              </div>
            )}
            {/* Shipping cost */}
            {sale.shipping_cost && (
              <div className="mb-2 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Shipping cost
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {sale.shipping_cost}
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
                {sale.net_profit.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sale;

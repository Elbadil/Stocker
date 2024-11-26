import React, { useState } from 'react';
import { IRowNode } from '@ag-grid-community/core';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import ModalOverlay from '../../../components/ModalOverlay';
import { Location } from '../../ClientOrders/Clients/Client';
import { handleSupplierExport } from './utils';
import EditSupplier from './EditSupplier';
import DeleteSupplier from './DeleteSupplier';

export interface SupplierProps {
  id: string;
  created_by: string;
  name: string;
  phone_number?: string | null;
  email?: string | null;
  location?: Location;
  total_orders: number;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

interface Supplier {
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  supplier: SupplierProps;
  setSupplier: React.Dispatch<React.SetStateAction<SupplierProps | null>>;
  rowNode?: IRowNode<SupplierProps>;
  rowData: SupplierProps[];
  setRowData: React.Dispatch<React.SetStateAction<SupplierProps[]>>;
}

const Supplier = ({
  setOpen,
  supplier,
  setSupplier,
  rowNode,
  rowData,
  setRowData,
}: Supplier) => {
  const [openEditSupplier, setOpenEditSupplier] = useState<boolean>(false);
  const [openDeleteSupplier, setOpenDeleteSupplier] = useState<boolean>(false);

  return (
    <div className="mx-auto max-w-sm border rounded-md border-stroke bg-white dark:border-slate-700 dark:bg-boxdark">
      {/* Supplier Modal Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Supplier:{' '}
          {supplier.name.length > 25
            ? supplier.name.substring(0, 25) + '...'
            : supplier.name}
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
      {/* Supplier Details */}
      <div className="max-w-full overflow-y-auto max-h-[80vh] flex flex-col">
        {/* Export | Edit | Delete Buttons */}
        <div className="flex justify-end items-center">
          <div className="px-2.5 pt-2.5">
            {/* Export Supplier */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-black dark:hover:text-black hover:bg-slate-200 dark:hover:bg-slate-200"
              onClick={handleSupplierExport}
            >
              <FileDownloadOutlinedIcon />
            </button>
            {/* Edit Supplier */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-primary dark:hover:bg-primary"
              onClick={() => setOpenEditSupplier(true)}
            >
              <ModeEditOutlineOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openEditSupplier}
              onClose={() => setOpenEditSupplier(false)}
            >
              <EditSupplier
                supplier={supplier}
                setSupplier={setSupplier}
                open={openEditSupplier}
                setOpen={setOpenEditSupplier}
                rowNode={rowNode}
                setRowData={setRowData}
              />
            </ModalOverlay>

            {/* Delete Supplier */}
            <button
              type="button"
              className="mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-red-500 dark:hover:bg-red-500"
              onClick={() => setOpenDeleteSupplier(true)}
            >
              <DeleteOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openDeleteSupplier}
              onClose={() => setOpenDeleteSupplier(false)}
            >
              <DeleteSupplier
                suppliers={[supplier]}
                open={openDeleteSupplier}
                setOpen={setOpenDeleteSupplier}
                rowData={rowData}
                setRowData={setRowData}
                setSupplierOpen={setOpen}
              />
            </ModalOverlay>
          </div>
        </div>
        <div className="px-6 pb-6 pt-1">
          {/* Supplier Info */}
          <div className="divide-y divide-slate-200 dark:divide-slate-600">
            {/* Name */}
            <div className="mb-3">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Name
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {supplier.name}
              </p>
            </div>
            {/* Name */}
            <div className="mb-3 pt-3">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Total Orders
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {supplier.total_orders}
              </p>
            </div>
            {/* Phone Number */}
            {supplier.phone_number && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Phone Number
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {supplier.phone_number}
                </p>
              </div>
            )}
            {/* Email */}
            {supplier.email && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Email
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {supplier.email}
                </p>
              </div>
            )}

            {/* Location */}
            {supplier.location && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Location
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {Object.values(supplier.location).reverse().join(', ')}
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
                  {supplier.created_at}
                </p>
              </div>
              {/* Updated at */}
              {supplier.updated && (
                <div className="">
                  <div className="mb-1 block text-base font-medium text-black dark:text-white">
                    Updated
                  </div>
                  <p className="text-base text-slate-900 truncate dark:text-slate-300">
                    {supplier.updated_at}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Supplier;

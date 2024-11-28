import React, { useState } from 'react';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import { IRowNode } from '@ag-grid-community/core';
import ModalOverlay from '../../../components/ModalOverlay';
import { handleClientExport } from './utils';
import EditClient from './EditClient';
import DeleteClient from './DeleteClient';

export interface Location {
  country?: string | null;
  city?: string | null;
  street_address?: string | null;
}

export interface ClientProps {
  id: string;
  created_by: string;
  name: string;
  age?: number | null;
  phone_number?: string | null;
  email?: string | null;
  sex?: 'Male' | 'Female' | null;
  location: Location | null;
  source?: string | null;
  total_orders: number;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

interface Client {
  client: ClientProps;
  setClient: React.Dispatch<React.SetStateAction<ClientProps | null>>;
  clientRowNode?: IRowNode<ClientProps>;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowData: ClientProps[];
  setRowData: React.Dispatch<React.SetStateAction<ClientProps[]>>;
}

const Client = ({
  client,
  setClient,
  clientRowNode,
  setOpen,
  rowData,
  setRowData,
}: Client) => {
  const [openEditClient, setOpenEditClient] = useState<boolean>(false);
  const [openDeleteClient, setOpenDeleteClient] = useState<boolean>(false);

  return (
    <div className="mx-auto max-w-sm border rounded-md border-stroke bg-white dark:border-slate-700 dark:bg-boxdark">
      {/* Client Modal Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Client:{' '}
          {client.name.length > 25
            ? client.name.substring(0, 25) + '...'
            : client.name}
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
      {/* Client Details */}
      <div className="max-w-full overflow-y-auto max-h-[80vh] flex flex-col">
        {/* Export | Edit | Delete Buttons */}
        <div className="flex justify-end items-center">
          <div className="px-2.5 pt-2.5">
            {/* Export Item */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-black dark:hover:text-black hover:bg-slate-200 dark:hover:bg-slate-200"
              onClick={() => handleClientExport([client])}
            >
              <FileDownloadOutlinedIcon />
            </button>
            {/* Edit Item */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-primary dark:hover:bg-primary"
              onClick={() => setOpenEditClient(true)}
            >
              <ModeEditOutlineOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openEditClient}
              onClose={() => setOpenEditClient(false)}
            >
              <EditClient
                client={client}
                setClient={setClient}
                open={openEditClient}
                setOpen={setOpenEditClient}
                rowNode={clientRowNode}
                setRowData={setRowData}
              />
            </ModalOverlay>

            {/* Delete Item */}
            <button
              type="button"
              className="mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-red-500 dark:hover:bg-red-500"
              onClick={() => setOpenDeleteClient(true)}
            >
              <DeleteOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openDeleteClient}
              onClose={() => setOpenDeleteClient(false)}
            >
              <DeleteClient
                clients={[client]}
                open={openDeleteClient}
                setOpen={setOpenDeleteClient}
                rowData={rowData}
                setRowData={setRowData}
                setClientOpen={setOpen}
              />
            </ModalOverlay>
          </div>
        </div>
        <div className="px-6 pb-6 pt-1">
          {/* Client Info */}
          <div className="divide-y divide-slate-200 dark:divide-slate-600">
            {/* Name */}
            <div className="mb-3">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Name
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {client.name}
              </p>
            </div>
            {/* Name */}
            <div className="mb-3 pt-3">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Total Orders
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {client.total_orders}
              </p>
            </div>
            {/* Phone Number */}
            {client.phone_number && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Phone Number
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {client.phone_number}
                </p>
              </div>
            )}
            {/* Email */}
            {client.email && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Email
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {client.email}
                </p>
              </div>
            )}
            {/* Age */}
            {client.age && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Age
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {client.age}
                </p>
              </div>
            )}
            {/* Sex */}
            {client.sex && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Sex
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {client.sex}
                </p>
              </div>
            )}
            {/* Location */}
            {client.location && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Location
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {Object.values(client.location).reverse().join(', ')}
                </p>
              </div>
            )}
            {/* Source of Acquisition */}
            {client.source && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Source of Acquisition
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {client.source}
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
                  {client.created_at}
                </p>
              </div>
              {/* Updated at */}
              {client.updated && (
                <div className="">
                  <div className="mb-1 block text-base font-medium text-black dark:text-white">
                    Updated
                  </div>
                  <p className="text-base text-slate-900 truncate dark:text-slate-300">
                    {client.updated_at}
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

export default Client;

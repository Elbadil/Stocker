import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModeEditOutlineOutlinedIcon from '@mui/icons-material/ModeEditOutlineOutlined';
import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import { IRowNode } from 'ag-grid-community';
import { useState } from 'react';
import EditItem from './EditItem';
import DeleteItem from './DeleteItem';
import ModalOverlay from '../../components/ModalOverlay';
import { handleItemExport } from './utils';

export interface ItemProps {
  id: string;
  user: string;
  name: string;
  quantity: number;
  price: number;
  total_price: number;
  category: string | null;
  supplier: string | null;
  variants: { name: string; options: string[] }[] | null;
  picture: string | null;
  created_at: string;
  updated_at: string;
  updated: boolean;
}

export interface ItemComponentProps {
  item: ItemProps;
  setItem: React.Dispatch<React.SetStateAction<ItemProps | null>>;
  itemRowNode?: IRowNode<ItemProps>;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowData: ItemProps[];
  setRowData: React.Dispatch<React.SetStateAction<ItemProps[]>>;
}

const Item = ({
  item,
  setItem,
  itemRowNode,
  setOpen,
  rowData,
  setRowData,
}: ItemComponentProps) => {
  const [openEditItem, setOpenEditItem] = useState<boolean>(false);
  const [openDeleteItem, setOpenDeleteItem] = useState<boolean>(false);

  return (
    <div className="mx-auto max-w-sm border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Item Modal Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          {item.name.length > 27
            ? item.name.substring(0, 27) + '...'
            : item.name}
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
      {/* Item Details */}
      <div className="max-w-full overflow-y-auto max-h-[80vh] flex flex-col">
        {/* Export | Edit | Delete Buttons */}
        <div className="flex justify-end items-center">
          <div className="px-2.5 pt-2.5">
            {/* Export Item */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-black dark:hover:text-black hover:bg-slate-200 dark:hover:bg-slate-200"
              onClick={() => handleItemExport([item])}
            >
              <FileDownloadOutlinedIcon />
            </button>
            {/* Edit Item */}
            <button
              type="button"
              className="mr-1.5 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-primary dark:hover:bg-primary"
              onClick={() => setOpenEditItem(true)}
            >
              <ModeEditOutlineOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openEditItem}
              onClose={() => setOpenEditItem(false)}
            >
              <EditItem
                item={item}
                setItem={setItem}
                open={openEditItem}
                setOpen={setOpenEditItem}
                rowNode={itemRowNode}
              />
            </ModalOverlay>
            {/* Delete Item */}
            <button
              type="button"
              className="mr-2 inline-flex items-center justify-center rounded-full border-[0.5px] border-stroke dark:border-strokedark bg-gray dark:bg-meta-4 text-slate-500 dark:text-white h-10 w-10.5 text-center font-medium hover:text-white hover:bg-red-500 dark:hover:bg-red-500"
              onClick={() => setOpenDeleteItem(true)}
            >
              <DeleteOutlinedIcon />
            </button>
            <ModalOverlay
              isOpen={openDeleteItem}
              onClose={() => setOpenDeleteItem(false)}
            >
              <DeleteItem
                items={[item]}
                open={openDeleteItem}
                setOpen={setOpenDeleteItem}
                rowData={rowData}
                setRowData={setRowData}
                setItemOpen={setOpen}
              />
            </ModalOverlay>
          </div>
        </div>
        <div className="px-6 pb-6 pt-2">
          {/* Picture */}
          {item.picture && (
            <div className="mb-3 flex justify-center items-center">
              <div className="h-40 w-40 rounded-full overflow-hidden mr-1">
                <img
                  src={item.picture}
                  className="w-full h-full object-cover"
                  alt="Item"
                />
              </div>
            </div>
          )}
          {/* Item Info */}
          <div className="divide-y divide-slate-200 dark:divide-slate-600">
            {/* Name */}
            <div className="mb-3">
              <div className="mb-1 block text-base font-medium text-black dark:text-white">
                Name
              </div>
              <p className="text-base text-slate-900 truncate dark:text-slate-300">
                {item.name}
              </p>
            </div>
            {/* Price | Quantity | Total Price */}
            <div className="mb-3 pt-3 flex flex-row gap-9">
              {/* Price */}
              <div className="w-full sm:w-1/3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Price
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {item.price.toFixed(2)}
                </p>
              </div>
              {/* Quantity */}
              <div className="w-full sm:w-1/3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Quantity
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {item.quantity}
                </p>
              </div>
              {/* Total Price */}
              <div className="w-full sm:w-1/3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Total Price
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {item.total_price.toFixed(2)}
                </p>
              </div>
            </div>
            {/* Category */}
            {item.category && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Category
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {item.category}
                </p>
              </div>
            )}
            {/* Supplier */}
            {item.supplier && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Supplier
                </div>
                <p className="text-base text-slate-900 truncate dark:text-slate-300">
                  {item.supplier}
                </p>
              </div>
            )}
            {/* Variants */}
            {item.variants && (
              <div className="mb-3 pt-3">
                <div className="mb-1 block text-base font-medium text-black dark:text-white">
                  Variants
                </div>
                <ol className="text-base text-slate-900 truncate dark:text-slate-300 space-y-1 list-inside list-disc">
                  {item.variants.map((variant, index: number) => (
                    <li key={index}>
                      <span className="font-medium">{variant.name}:</span>{' '}
                      {variant.options.join(', ')}
                    </li>
                  ))}
                </ol>
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
                  {item.created_at}
                </p>
              </div>
              {/* Updated at */}
              {item.updated && (
                <div className="">
                  <div className="mb-1 block text-base font-medium text-black dark:text-white">
                    Updated
                  </div>
                  <p className="text-base text-slate-900 truncate dark:text-slate-300">
                    {item.updated_at}
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

export default Item;

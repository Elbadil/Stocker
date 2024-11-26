import React, { useEffect, useMemo, useState } from 'react';
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined';
import ClipLoader from 'react-spinners/ClipLoader';
import { SupplierProps } from './Supplier';
import { setSupplierOrders } from '../../../store/slices/supplierOrdersSlice';
import { api } from '../../../api/axios';
import { useAlert } from '../../../contexts/AlertContext';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';

interface DeleteSupplier {
  suppliers: SupplierProps[];
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowData: SupplierProps[];
  setRowData: React.Dispatch<React.SetStateAction<SupplierProps[]>>;
  setSupplierOpen?: React.Dispatch<React.SetStateAction<boolean>>;
}

const DeleteSupplier = ({
  suppliers,
  open,
  setOpen,
  rowData,
  setRowData,
  setSupplierOpen,
}: DeleteSupplier) => {
  const { setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const [deleteErrors, setDeleteErrors] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const [suppliersWithOrders, suppliersWithoutOrders] = useMemo(() => {
    const withOrders: SupplierProps[] = [];
    const withoutOrders: SupplierProps[] = [];

    suppliers.forEach((supplier) => {
      if (supplier.total_orders > 0) {
        withOrders.push(supplier);
      } else {
        withoutOrders.push(supplier);
      }
    });

    return [withOrders, withoutOrders];
  }, [suppliers]);

  const suppliersForDeletion = {
    ids: suppliersWithoutOrders.map((supplier) => supplier.id),
    names: suppliersWithoutOrders.map((supplier) => supplier.name),
  };

  const removeDeletedSuppliersRows = () => {
    const suppliersIds = new Set(suppliersForDeletion.ids);
    const filteredRows = rowData.filter((row) => !suppliersIds.has(row.id));
    setRowData(filteredRows);
  };

  const handleDelete = async () => {
    setDeleteErrors('');
    setLoading(true);
    try {
      let res;
      if (suppliersWithoutOrders.length > 1) {
        res = await api.delete('/supplier_orders/suppliers/bulk_delete/', {
          data: { ids: suppliersForDeletion.ids },
        });
      } else {
        res = await api.delete(
          `/supplier_orders/suppliers/${suppliersWithoutOrders[0].id}/`,
        );
      }
      console.log(res.data);
      // Remove deleted suppliers rows
      removeDeletedSuppliersRows();
      // Update suppliers state
      const supplierNamesSet = new Set(suppliersForDeletion.names);
      dispatch((dispatch, getState) => {
        const { supplierOrders } = getState();
        dispatch(
          setSupplierOrders({
            ...supplierOrders,
            suppliers: {
              count:
                supplierOrders.suppliers.count - suppliersWithoutOrders.length,
              names: supplierOrders.suppliers.names.filter(
                (supplierName) => !supplierNamesSet.has(supplierName),
              ),
            },
          }),
        );
      });
      // Set and display success alert
      setAlert({
        type: 'success',
        title:
          suppliersWithoutOrders.length > 1
            ? `${suppliersWithoutOrders.length} Suppliers Deleted`
            : 'Supplier Deleted',
        description: `You successfully deleted ${
          suppliersWithoutOrders.length > 1
            ? `${suppliersWithoutOrders.length} suppliers`
            : `supplier ${suppliersWithoutOrders[0].name}`
        }.`,
      });
      // Close delete supplier modal
      setOpen(false);
      // Close supplier modal if any
      if (setSupplierOpen) setSupplierOpen(false);
    } catch (error) {
      console.log('Error during supplier deletion', error);
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
          {suppliers.length > 1 ? 'Delete Suppliers' : 'Delete Supplier'}
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
            {suppliers.map((supplier, index: number) => (
              <li className="mt-2" key={index}>
                {supplier.name}
                {supplier.total_orders > 0 && (
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
          {suppliersWithOrders.length > 0 && (
            <div className="mt-3 text-sm text-orange-500 flex justify-start gap-0.5">
              <WarningAmberOutlinedIcon
                sx={{
                  fontSize: '17.5px',
                  paddingTop: '3px',
                }}
              />
              <p>
                {suppliersWithOrders.length > 1
                  ? suppliersWithOrders.length === suppliers.length
                    ? 'All selected suppliers are '
                    : 'Some selected suppliers are '
                  : `Supplier ${suppliersWithOrders[0].name} is `}
                linked to existing orders and won't be deleted. Please manage
                their orders before deletion.
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
            (suppliersWithOrders.length === suppliers.length
              ? 'cursor-not-allowed bg-red-400 '
              : 'bg-red-500 hover:bg-opacity-90 ') +
            'rounded py-2 px-6 font-medium text-gray'
          }
          type="submit"
          onClick={handleDelete}
          disabled={suppliersWithOrders.length === suppliers.length}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteSupplier;

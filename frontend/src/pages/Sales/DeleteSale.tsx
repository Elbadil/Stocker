import React, { useEffect, useState } from 'react';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ClipLoader from 'react-spinners/ClipLoader';
import { SaleProps } from './Sale';
import { useAlert } from '../../contexts/AlertContext';
import { useSales } from '../../contexts/SalesContext';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store/store';
import { statusType } from '../../utils/form';
import { setSales } from '../../store/slices/salesSlice';
import { useInventory } from '../../contexts/InventoryContext';
import { setInventory } from '../../store/slices/inventorySlice';
import { api } from '../../api/axios';

interface DeleteSale {
  sales: SaleProps[];
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setSaleOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  rowData: SaleProps[];
  setRowData: React.Dispatch<React.SetStateAction<SaleProps[]>>;
}

const DeleteSale = ({
  sales,
  open,
  setOpen,
  setSaleOpen,
  rowData,
  setRowData,
}: DeleteSale) => {
  const { setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const { salesCount, saleStatus } = useSales();
  const { items } = useInventory();
  const [loading, setLoading] = useState<boolean>(false);
  const [deleteErrors, setDeleteErrors] = useState<string>('');

  const salesSummary = {
    ids: sales.map((sale) => sale.id),
    deliveryStatus: sales.map((sale) => sale.delivery_status),
    soldItems: sales.map((sale) => sale.sold_items),
    flattenedSoldItems() {
      const soldItemsMap = new Map();

      this.soldItems.forEach((itemsList) => {
        itemsList.forEach((soldItem) => {
          const itemName = soldItem.item;
          if (soldItemsMap.has(itemName)) {
            const prevValue = soldItemsMap.get(itemName);
            soldItemsMap.set(itemName, {
              ...prevValue,
              quantity: prevValue.quantity + soldItem.sold_quantity,
            });
          } else {
            soldItemsMap.set(itemName, {
              name: soldItem.item,
              quantity: soldItem.sold_quantity,
            });
          }
        });
      });

      return soldItemsMap;
    },
  };

  const linkedSalesCount = sales.filter((sale) => sale.linked_order).length;

  const updateRowData = () => {
    const saleIds = new Set(salesSummary.ids);
    const filteredRows = rowData.filter((row) => !saleIds.has(row.id));
    setRowData(filteredRows);
  };

  const updateSalesState = () => {
    const newSalesStatus = structuredClone(saleStatus);
    salesSummary.deliveryStatus.forEach((status) => {
      const saleStatusType = statusType(status);
      newSalesStatus[saleStatusType] -= 1;
    });

    dispatch(
      setSales({
        salesCount: salesCount - sales.length,
        saleStatus: newSalesStatus,
      }),
    );
  };

  const updateItemsState = () => {
    const flattenedItems = salesSummary.flattenedSoldItems();
    dispatch((dispatch, getState) => {
      const { inventory } = getState();
      dispatch(
        setInventory({
          ...inventory,
          items: items.map((item) => {
            const soldItem = flattenedItems.get(item.name);
            return soldItem
              ? { ...item, quantity: item.quantity + soldItem.quantity }
              : item;
          }),
        }),
      );
    });
  };

  const handleSaleDelete = async () => {
    setLoading(true);
    setDeleteErrors('');
    try {
      let res;
      if (sales.length > 1) {
        res = await api.delete('/sales/bulk_delete', {
          data: { ids: salesSummary.ids },
        });
      } else {
        res = await api.delete(`/sales/${sales[0].id}/`);
      }
      console.log(res.data);
      // Update sales row data
      updateRowData();
      // Update sales state
      updateSalesState();
      // Update linked items state
      updateItemsState();
      // Set and display success alert
      setAlert({
        type: 'success',
        title:
          sales.length > 1 ? `${sales.length} Sales Deleted.` : `Sale Deleted.`,
        description: `You successfully deleted ${
          sales.length > 1
            ? `${sales.length} sales`
            : `sale ${sales[0].reference_id} made by ${sales[0].client}`
        }.`,
      });
      // Close Delete Sale Modal
      setOpen(false);
      // Close Sale Model if any
      if (setSaleOpen) setSaleOpen(false);
    } catch (error: any) {
      console.log('Error during sales deletion', error);
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
          {sales.length > 1 ? 'Delete Sales' : 'Delete Sale'}
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
            {sales.map((sale, index: number) => (
              <li className="mt-2" key={index}>
                Sale {sale.reference_id} - by {sale.client}
                {sale.linked_order && (
                  <InfoOutlinedIcon
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
          <div className="mt-2 text-sm text-yellow-600 dark:text-yellow-500">
            * Deleting non-linked sales will automatically update the inventory
            by restoring the quantities of the associated items.
          </div>
          {linkedSalesCount > 0 && (
            <div className="mt-2 text-sm text-orange-500 flex justify-start gap-0.5">
              <InfoOutlinedIcon
                sx={{
                  fontSize: '17.5px',
                  paddingTop: '3px',
                }}
              />
              <p>
                This sale is linked to an order. Deleting it won't affect the
                order but may impact data integrity.
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
          className="flex justify-center bg-red-500 hover:bg-opacity-90 rounded py-2 px-4 font-medium text-gray"
          type="submit"
          onClick={handleSaleDelete}
        >
          {loading ? <ClipLoader color="#ffffff" size={23} /> : 'Delete'}
        </button>
      </div>
    </div>
  );
};

export default DeleteSale;

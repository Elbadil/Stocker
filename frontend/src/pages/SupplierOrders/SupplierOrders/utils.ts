import React from 'react';
import { utils, writeFile } from 'xlsx';
import { setSupplierOrders } from '../../../store/slices/supplierOrdersSlice';
import { SelectOption } from '../../../types/form';
import { selectOptionsFromStrings, areFieldsEmpty } from '../../../utils/form';
import {
  FieldArrayWithId,
  UseFieldArrayAppend,
  UseFormGetValues,
  UseFormResetField,
  UseFormSetValue,
} from 'react-hook-form';
import {
  SupplierOrderSchema,
  SupplierOrderedItemSchema,
} from './AddSupplierOrder';
import { dispatch } from '../../../store/store';
import { SupplierOrderProps } from './SupplierOrder';
import toast from 'react-hot-toast';
import { api } from '../../../api/axios';
import { format } from 'date-fns';

type FlattenedOrderedItems = {
  [key: string]: string;
};

export const resetNewSupplier = () => {
  dispatch((dispatch, getState) => {
    const { supplierOrders } = getState();
    dispatch(
      setSupplierOrders({
        ...supplierOrders,
        newSupplier: null,
      }),
    );
  });
};

export const filterAndSetSupplierItems = (
  currentSupplier: string,
  noSupplierItems: string[],
  suppliersMap: Map<string, string[]>,
  setItemOptions: React.Dispatch<React.SetStateAction<SelectOption[]>>,
  getValues: UseFormGetValues<SupplierOrderSchema>,
  setValue: UseFormSetValue<SupplierOrderSchema>,
  resetField: UseFormResetField<SupplierOrderSchema>,
) => {
  const supplierItems = [
    ...(suppliersMap.get(currentSupplier) || []),
    ...noSupplierItems,
  ];

  console.log(currentSupplier);

  // Set item options for the select supplier
  const supplierItemsOptions = selectOptionsFromStrings(supplierItems);
  if (suppliersMap.get(currentSupplier)) {
    console.log('Supplier has items');
  } else {
    console.log('Supplier has no items');
  }
  setItemOptions(supplierItemsOptions);

  // Filter supplier items form fields
  const emptyItem: Partial<SupplierOrderedItemSchema> = {
    item: '',
    ordered_quantity: undefined,
    ordered_price: undefined,
  };

  const supplierItemsSet = new Set(supplierItems);
  const currentItemFields = getValues(`ordered_items`);

  const filteredItemFields = currentItemFields.filter(
    (field) => field && field.item && supplierItemsSet.has(field.item),
  );

  if (filteredItemFields.length === 0) {
    resetField('ordered_items', {
      defaultValue: [emptyItem as SupplierOrderedItemSchema],
    });
  } else {
    setValue('ordered_items', filteredItemFields);
  }
};

export const addNewOrderedItemField = (
  newOrderedItem: SupplierOrderedItemSchema,
  fields: FieldArrayWithId<SupplierOrderSchema, 'ordered_items'>[],
  append: UseFieldArrayAppend<SupplierOrderSchema>,
  getValues: UseFormGetValues<SupplierOrderSchema>,
  setValue: UseFormSetValue<SupplierOrderSchema>,
) => {
  if (!newOrderedItem) return;

  const fieldUpdated = fields.some((_, index) => {
    const currentItemFields = getValues(`ordered_items.${index}`);
    if (areFieldsEmpty(currentItemFields)) {
      setValue(`ordered_items.${index}`, newOrderedItem);
      return true; // Stop iterating once a field is updated
    }
    return false; // Continue checking other fields
  });
  if (!fieldUpdated) {
    append(newOrderedItem);
  }
};

export const resetNewOrderedItem = () => {
  dispatch((dispatch, getState) => {
    const { supplierOrders } = getState();
    dispatch(
      setSupplierOrders({
        ...supplierOrders,
        newOrderedItem: null,
      }),
    );
  });
};

export const orderedItemsDataFlattener = (order: SupplierOrderProps) => {
  return order.ordered_items.reduce<FlattenedOrderedItems>(
    (acc, orderedItem, index) => {
      acc[`ordered_item-${index + 1}`] = `${orderedItem.item} | Quantity: ${
        orderedItem.ordered_quantity
      } | Unit Price: ${orderedItem.ordered_price.toFixed(
        2,
      )} | Total Price: ${orderedItem.total_price.toFixed(2)}`;
      return acc;
    },
    {},
  );
};

export const orderDataFlattener = (orders: SupplierOrderProps[]) =>
  orders.map((order) => ({
    ...order,
    ordered_items: `${order.ordered_items.length} unique ${
      order.ordered_items.length > 1 ? 'items' : 'item'
    }`,
    ...orderedItemsDataFlattener(order),
    updated_at: order.updated ? order.updated_at : null,
  }));

export const createSheetFile = (orders: SupplierOrderProps[]) => {
  const flattenedData = orderDataFlattener(orders);
  const ws = utils.json_to_sheet(flattenedData);
  /* create workbook and append worksheet */
  const wb = utils.book_new();
  const dateNow = format(new Date(), 'dd-MM-yyyy');
  utils.book_append_sheet(wb, ws, `Clients ${dateNow}`);
  if (orders.length > 1) {
    writeFile(wb, `${orders[0].created_by}_orders_${dateNow}.xlsx`);
  } else {
    writeFile(wb, `order_${orders[0].reference_id}_${dateNow}.xlsx`);
  }
};

export const handleSupplierOrderExport = (selectedRows?: SupplierOrderProps[]) => {
  if (selectedRows) {
    createSheetFile(selectedRows);
  } else {
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

export const handleSupplierOrderBulkExport = async () => {
  try {
    const res = await api.get('/supplier_orders/orders/');
    const orders = res.data;
    createSheetFile(orders);
  } catch (error: any) {
    console.log('Error during orders export', error);
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

import React from 'react';
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

export const handleSupplierOrderExport = () => {};
export const handleSupplierOrderBulkExport = () => {};

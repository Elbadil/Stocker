import React, { useEffect, useState } from 'react';
import ClipLoader from 'react-spinners/ClipLoader';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import {
  useForm,
  useFieldArray,
  Controller,
  SubmitHandler,
} from 'react-hook-form';
import Select, { SingleValue } from 'react-select';
import { SupplierOrderProps } from './SupplierOrder';
import {
  schema,
  SupplierOrderSchema,
  SupplierOrderedItemSchema,
} from './AddSupplierOrder';
import { useAlert } from '../../../contexts/AlertContext';
import ModalOverlay from '../../../components/ModalOverlay';
import { zodResolver } from '@hookform/resolvers/zod';
import { IRowNode } from '@ag-grid-community/core';
import { useSupplierOrders } from '../../../contexts/SupplierOrdersContext';
import { SelectOption } from '../../../types/form';
import {
  selectOptionsFromObjects,
  selectOptionsFromStrings,
  customSelectStyles,
  statusType,
} from '../../../utils/form';
import {
  addNewOrderedItemField,
  filterAndSetSupplierItems,
  resetNewOrderedItem,
  resetNewSupplier,
} from './utils';
import AddItem from '../../Inventory/AddItem';
import AddSupplier from '../Suppliers/AddSupplier';
import { api } from '../../../api/axios';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';
import { setSupplierOrders } from '../../../store/slices/supplierOrdersSlice';
import toast from 'react-hot-toast';

interface EditSupplierOrder {
  supplierOrder: SupplierOrderProps;
  setSupplierOrder?: React.Dispatch<
    React.SetStateAction<SupplierOrderProps | null>
  >;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowNode?: IRowNode<SupplierOrderProps>;
  setRowData: React.Dispatch<React.SetStateAction<SupplierOrderProps[]>>;
}

const EditSupplierOrder = ({
  supplierOrder,
  setSupplierOrder,
  open,
  setOpen,
  rowNode,
  setRowData,
}: EditSupplierOrder) => {
  const { isDarkMode, setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const {
    suppliers,
    newSupplier,
    noSupplierItems,
    orderStatus,
    newOrderedItem,
  } = useSupplierOrders();
  const [openAddSupplier, setOpenAddSupplier] = useState<boolean>(false);
  const [openAddItem, setOpenAddItem] = useState<boolean>(false);
  const [isOrderDelivered, setIsOrderDelivered] = useState<boolean>(false);
  const [initialValues, setInitialValues] =
    useState<SupplierOrderSchema | null>(null);

  const emptyItem: Partial<SupplierOrderedItemSchema> = {
    item: '',
    ordered_quantity: undefined,
    ordered_price: undefined,
  };

  const {
    register,
    control,
    setError,
    setValue,
    getValues,
    resetField,
    reset,
    watch,
    clearErrors,
    handleSubmit,
    formState: { errors, dirtyFields, isSubmitting },
  } = useForm<SupplierOrderSchema>({
    resolver: zodResolver(schema),
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'ordered_items',
  });

  const currentValues = watch();
  const currentSupplier = watch('supplier');
  const currentDeliveryStatus = watch('delivery_status');
  const suppliersMap = new Map(
    suppliers.map((supplier) => [supplier.name, supplier.item_names]),
  );
  const supplierOptions = selectOptionsFromObjects(suppliers);
  const noSupplierItemsOptions = selectOptionsFromStrings(noSupplierItems);
  const [itemOptions, setItemOptions] = useState<SelectOption[]>([]);
  const deliveryStatusOptions = selectOptionsFromStrings(
    orderStatus.delivery_status,
  );
  const paymentStatusOptions = selectOptionsFromStrings(
    orderStatus.payment_status,
  );

  const handleSupplierChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<SelectOption>,
  ) => {
    // reset newSupplier if any
    if (newSupplier) {
      resetNewSupplier();
    }

    if (option) {
      onChange(option.value);
      filterAndSetSupplierItems(
        option.value,
        noSupplierItems,
        suppliersMap,
        setItemOptions,
        getValues,
        setValue,
        resetField,
      );
    } else {
      onChange('');
      setItemOptions(noSupplierItemsOptions);
    }
  };

  const handleItemChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<SelectOption>,
    index: number,
  ) => {
    if (option) {
      onChange(option.value);
    } else {
      onChange('');
    }
    clearErrors(`ordered_items.${index}`);
  };

  const updateOrderStatusState = (orderUpdate: SupplierOrderProps) => {
    const prevOrderStatusType = statusType(supplierOrder.delivery_status);
    const newOrderStatusType = statusType(orderUpdate.delivery_status);
    if (prevOrderStatusType !== newOrderStatusType) {
      return {
        ...orderStatus,
        [newOrderStatusType]: orderStatus[newOrderStatusType] + 1,
        [prevOrderStatusType]: orderStatus[prevOrderStatusType] - 1,
      };
    }
    return orderStatus;
  };

  const onSubmit: SubmitHandler<SupplierOrderSchema> = async (data) => {
    console.log(data);
    try {
      const res = await api.put(
        `/supplier_orders/orders/${supplierOrder.id}/`,
        data,
      );
      const orderUpdate = res.data;
      console.log(orderUpdate);
      // Set row node data
      rowNode?.setData(orderUpdate);
      // Update Order's state and display a toast notification
      if (setSupplierOrder) {
        setSupplierOrder(orderUpdate);
        toast.success(`Order ${orderUpdate.reference_id} updated!`, {
          duration: 4000,
        });
      }
      // Update rowData
      setRowData((prev) =>
        prev.map((row) => (row.id === orderUpdate.id ? orderUpdate : row)),
      );
      // Update orderStatus state
      dispatch((dispatch, getState) => {
        const { supplierOrders } = getState();
        dispatch(
          setSupplierOrders({
            ...supplierOrders,
            orderStatus: updateOrderStatusState(orderUpdate),
          }),
        );
      });
      // Set and display success Alert
      setAlert({
        type: 'success',
        title: 'Order Updated',
        description: `Order ${
          orderUpdate.reference_id
        } has been successfully updated.${
          supplierOrder.delivery_status !== 'Delivered' &&
          orderUpdate.delivery_status === 'Delivered'
            ? ' The ordered items have been added to the inventory. For existing items, the quantity has been updated, and the average price recalculated.'
            : ''
        }`,
      });
      // Close Edit Order Modal
      setOpen(false);
    } catch (error: any) {
      console.log('Error during form submission', error);
      if (error.response && error.response.status === 400) {
        const errorData = error.response.data;
        (Object.keys(errorData) as Array<keyof SupplierOrderSchema>).forEach(
          (field) => {
            setError(field, { message: errorData[field] });
          },
        );
      } else {
        setError('root', {
          message: 'Something went wrong, please try again later',
        });
      }
    }
  };

  const orderHasChanges = () => {
    if (!initialValues || !currentValues) return false;
    if (
      initialValues.ordered_items.length !== currentValues.ordered_items.length
    )
      return true;

    const numberFields = ['ordered_quantity', 'ordered_price', 'shipping_cost'];

    return (Object.keys(dirtyFields) as Array<keyof SupplierOrderSchema>).some(
      (key) => {
        if (numberFields.includes(key)) {
          return Number(initialValues[key]) !== Number(currentValues[key]);
        }
        if (key === 'ordered_items') {
          return initialValues.ordered_items.some((orderedItem, index) => {
            return (
              Object.keys(orderedItem) as Array<keyof SupplierOrderedItemSchema>
            ).some((orderedItemKey) => {
              if (numberFields.includes(orderedItemKey)) {
                return (
                  Number(initialValues[key][index][orderedItemKey]) !==
                  Number(currentValues[key][index][orderedItemKey])
                );
              }
              return (
                initialValues[key][index][orderedItemKey] !==
                currentValues[key][index][orderedItemKey]
              );
            });
          });
        }
        return initialValues[key] !== currentValues[key];
      },
    );
  };

  useEffect(() => {
    if (newSupplier) setValue('supplier', newSupplier);
  }, [newSupplier]);

  useEffect(() => {
    // Filter supplier items fields
    // Add new item to the current supplier's items options
    if (currentSupplier) {
      filterAndSetSupplierItems(
        currentSupplier,
        noSupplierItems,
        suppliersMap,
        setItemOptions,
        getValues,
        setValue,
        resetField,
      );
    }
    // Handle new Ordered Item field addition
    if (newOrderedItem) {
      addNewOrderedItemField(
        newOrderedItem,
        fields,
        append,
        getValues,
        setValue,
      );
      resetNewOrderedItem();
    }
  }, [openAddItem, openAddSupplier]);

  useEffect(() => {
    if (open) {
      if (supplierOrder.delivery_status === 'Delivered') {
        setIsOrderDelivered(true);
      } else {
        setIsOrderDelivered(false);
      }
      filterAndSetSupplierItems(
        supplierOrder.supplier,
        noSupplierItems,
        suppliersMap,
        setItemOptions,
        getValues,
        setValue,
        resetField,
      );
      setInitialValues(supplierOrder);
      reset(supplierOrder);
    }
  }, [open]);

  useEffect(() => {
    orderHasChanges();
  }, [initialValues, currentValues, supplierOrder]);

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Edit Order {supplierOrder.reference_id} - From{' '}
          {supplierOrder.supplier}
        </h3>
        <div>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              resetNewSupplier();
            }}
            aria-hidden={true}
          >
            <span className="text-slate-400 hover:text-slate-700 dark:text-white dark:hover:text-slate-300">
              ✖
            </span>
          </button>
        </div>
      </div>
      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Form Content */}
        <div className="max-w-full overflow-y-auto min-h-[60vh] max-h-[80vh] flex flex-col">
          <div className="p-6">
            {/* Delivered Order Note */}
            {isOrderDelivered && (
              <div className="text-sm font-medium mb-4 text-black dark:text-slate-300">
                * This order has been marked as Delivered. Please note that the
                supplier, ordered items, and delivery status cannot be modified
                to maintain data integrity.
              </div>
            )}

            {/* Supplier */}
            <div className="mb-4">
              <div className="flex items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="supplier_name"
                >
                  Supplier*
                </label>
                {!isOrderDelivered && (
                  <button
                    type="button"
                    onClick={() => setOpenAddSupplier(true)}
                    className="text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                  >
                    new supplier?
                  </button>
                )}
              </div>
              <div className="w-full">
                {open && (
                  <Controller
                    name="supplier"
                    control={control}
                    rules={{ required: true }}
                    render={({ field: { value, onChange, ...field } }) => (
                      <Select
                        {...field}
                        isClearable
                        value={
                          newSupplier
                            ? { value: newSupplier, label: newSupplier }
                            : value
                            ? supplierOptions.find(
                                (option) => option.value === value,
                              )
                            : null
                        }
                        onChange={(option) =>
                          handleSupplierChange(onChange, option)
                        }
                        options={supplierOptions}
                        styles={customSelectStyles(isDarkMode)}
                        isDisabled={isOrderDelivered}
                      />
                    )}
                  />
                )}
              </div>
              {errors.supplier && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.supplier.message}
                </p>
              )}
            </div>

            {/* Ordered Items */}
            <div className="mb-2 border-t border-b border-stroke dark:border-slate-600">
              <div className="flex pt-3 items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="ordered_items"
                >
                  Ordered Item(s)*
                </label>
                {!isOrderDelivered && (
                  <div className="flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => setOpenAddItem(true)}
                      disabled={!currentSupplier}
                      className={`text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline ${
                        !currentSupplier && 'cursor-not-allowed'
                      }`}
                    >
                      new item?{' '}
                    </button>
                    <span className="italic text-sm text-slate-400 dark:text-slate-400">
                      select a supplier first
                    </span>
                  </div>
                )}
              </div>
              {/* Ordered Items Note */}
              {!isOrderDelivered && (
                <div className="text-sm mb-2.5 text-black dark:text-slate-300">
                  * Note: You can select items already linked to this supplier,
                  items without a supplier (their supplier will be set to this
                  order's supplier after the order is placed), or create a new
                  item to add it to the item options.
                </div>
              )}
              {/* Ordered Items Fields List */}
              {fields.map((field, index) => (
                <div
                  className={`mt-1 mb-2 pb-1 ${
                    index >= 1 &&
                    'pt-2 border-t border-stroke dark:border-slate-700'
                  }`}
                  key={field.id}
                >
                  {/* Item Name */}
                  <div>
                    <label
                      className="mb-2 block text-sm font-medium text-black dark:text-white"
                      htmlFor="item_name"
                    >
                      Name*
                    </label>
                    <div className="flex items-center justify-start">
                      <div className="w-full">
                        {open && (
                          <Controller
                            name={`ordered_items.${index}.item`}
                            control={control}
                            rules={{ required: true }}
                            render={({
                              field: { value, onChange, ...field },
                            }) => (
                              <Select
                                {...field}
                                isClearable
                                value={
                                  value
                                    ? itemOptions.find(
                                        (option) => option.value === value,
                                      )
                                    : null
                                }
                                onChange={(option) =>
                                  handleItemChange(onChange, option, index)
                                }
                                noOptionsMessage={() =>
                                  currentSupplier
                                    ? 'No existing items for the selected supplier, please create new ones'
                                    : 'Select a supplier to get items suggestions'
                                }
                                options={itemOptions}
                                styles={customSelectStyles(isDarkMode)}
                                isDisabled={isOrderDelivered}
                              />
                            )}
                          />
                        )}
                      </div>
                      {/* Delete Item Field */}
                      {fields.length > 1 && !isOrderDelivered && (
                        <div>
                          <button
                            type="button"
                            className="ml-2 border border-slate-300 dark:border-slate-600 text-slate-400 py-2 px-2.5 rounded"
                            onClick={() => remove(index)}
                          >
                            <DeleteOutlinedIcon />
                          </button>
                        </div>
                      )}
                    </div>
                    {errors.ordered_items?.[index]?.item && (
                      <p className="text-red-500 font-medium text-sm italic mt-1">
                        {errors.ordered_items[index].item.message}
                      </p>
                    )}
                  </div>
                  {/* Item Quantity */}
                  <div className="mt-2.5">
                    <label
                      className="mb-2 block text-sm font-medium text-black dark:text-white"
                      htmlFor="item_quantity"
                    >
                      Quantity*
                    </label>
                    <input
                      className={`w-full rounded border ${
                        isOrderDelivered &&
                        'disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none'
                      } border-stroke bg-gray pl-3 py-2 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary`}
                      type="number"
                      placeholder="e.g. 1"
                      disabled={isOrderDelivered}
                      {...register(`ordered_items.${index}.ordered_quantity`)}
                    />
                    {errors.ordered_items?.[index]?.ordered_quantity && (
                      <p className="text-red-500 font-medium text-sm italic mt-1">
                        {errors.ordered_items[index].ordered_quantity.message}
                      </p>
                    )}
                  </div>
                  {/* Item Price Per Unit */}
                  <div className="mt-2.5">
                    <label
                      className="mb-2 block text-sm font-medium text-black dark:text-white"
                      htmlFor="item_price"
                    >
                      Price per unit*
                    </label>
                    <input
                      className={`w-full rounded border ${
                        isOrderDelivered &&
                        'disabled:pointer-events-none disabled:opacity-50 disabled:shadow-none'
                      } border-stroke bg-gray pl-3 py-2 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary`}
                      type="number"
                      placeholder="e.g. 19.99"
                      disabled={isOrderDelivered}
                      {...register(`ordered_items.${index}.ordered_price`)}
                    />
                    {errors.ordered_items?.[index]?.ordered_price && (
                      <p className="text-red-500 font-medium text-sm italic mt-1">
                        {errors.ordered_items[index].ordered_price.message}
                      </p>
                    )}
                  </div>
                  {/* Add Item Button */}
                  {index === fields.length - 1 && !isOrderDelivered && (
                    <button
                      type="button"
                      className="mt-3 text-sm inline-flex items-center justify-center rounded-md bg-meta-3 py-2 px-2 text-center font-medium text-white hover:bg-opacity-90"
                      onClick={() =>
                        append(emptyItem as SupplierOrderedItemSchema)
                      }
                    >
                      <AddCircleOutlinedIcon sx={{ marginRight: '0.2em' }} />
                      Add Item
                    </button>
                  )}
                </div>
              ))}
            </div>
            {/* Delivery Status */}
            <div className="mb-3 pb-4 border-b border-stroke dark:border-slate-600">
              <label
                className="block mb-2 text-base font-medium text-black dark:text-white"
                htmlFor="status"
              >
                Delivery status
              </label>
              <div className="w-full">
                {open && (
                  <Controller
                    name="delivery_status"
                    control={control}
                    rules={{ required: false }}
                    render={({ field: { value, onChange, ...field } }) => (
                      <Select
                        {...field}
                        isClearable
                        value={
                          value
                            ? deliveryStatusOptions.find(
                                (option) => option.value === value,
                              )
                            : null
                        }
                        onChange={(option) => onChange(option?.value || null)}
                        options={deliveryStatusOptions}
                        styles={customSelectStyles(isDarkMode)}
                        placeholder={<span>Select delivery status...</span>}
                        isDisabled={isOrderDelivered}
                      />
                    )}
                  />
                )}
              </div>
              {/* 'Delivered' delivery status note */}
              {!errors.delivery_status &&
                !isOrderDelivered &&
                currentDeliveryStatus === 'Delivered' && (
                  <div className="mt-2.5 p-2 text-sm text-yellow-600 dark:text-yellow-500 rounded border-l-4 border-yellow-500">
                    <p className="font-semibold">Important:</p>
                    <p>
                      Once you submit the order with the delivery status set to
                      <strong> "Delivered"</strong>, the following will occur:
                    </p>
                    <ul className="ml-4 list-disc">
                      <li>
                        Ordered items will be added to the inventory if they are
                        not already present.
                      </li>
                      <li>
                        If an item already exists in the inventory, its quantity
                        will be updated, and the average price will be
                        recalculated.
                      </li>
                    </ul>
                    <p className="mt-2">
                      Additionally, you will no longer be able to modify the
                      <strong> supplier</strong>,<strong> ordered items</strong>{' '}
                      or <strong>delivery status</strong> fields. Please ensure
                      all details are correct before submitting.
                    </p>
                  </div>
                )}

              {errors.delivery_status && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.delivery_status.message}
                </p>
              )}
            </div>
            {/* Payment Status */}
            <div className="mb-3 pb-4 border-b border-stroke dark:border-slate-600">
              <label
                className="block mb-2 text-base font-medium text-black dark:text-white"
                htmlFor="status"
              >
                Payment status
              </label>
              <div className="w-full">
                {open && (
                  <Controller
                    name="payment_status"
                    control={control}
                    rules={{ required: false }}
                    render={({ field: { value, onChange, ...field } }) => (
                      <Select
                        {...field}
                        isClearable
                        value={
                          value
                            ? paymentStatusOptions.find(
                                (option) => option.value === value,
                              )
                            : null
                        }
                        onChange={(option) => onChange(option?.value || null)}
                        options={paymentStatusOptions}
                        styles={customSelectStyles(isDarkMode)}
                        placeholder={<span>Select payment status...</span>}
                      />
                    )}
                  />
                )}
              </div>
              {errors.payment_status && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.payment_status.message}
                </p>
              )}
            </div>
            {/* Shipping Cost */}
            <div className="mb-3 pb-3 border-b border-stroke dark:border-slate-600">
              <label
                className="mb-2 block text-base font-medium text-black dark:text-white"
                htmlFor="shipping_cost"
              >
                Shipping Cost
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="number"
                placeholder="eg. 30.00"
                {...register('shipping_cost')}
              />
              {errors.shipping_cost && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.shipping_cost.message}
                </p>
              )}
            </div>
            {/* Tracking Number */}
            <div className="mb-3">
              <label
                className="mb-2 block text-base font-medium text-black dark:text-white"
                htmlFor="shipping_cost"
              >
                Tracking Number
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="Enter tracking number"
                {...register('tracking_number')}
              />
              {errors.tracking_number && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.tracking_number.message}
                </p>
              )}
            </div>
            {/* Root Errors */}
            {errors.root && (
              <p className="text-red-500 font-medium text-sm italic mt-2">
                {errors.root.message}
              </p>
            )}
          </div>
        </div>

        {/* Submit Form*/}
        <div className="flex justify-end gap-4 border-t border-stroke py-3 px-6 dark:border-strokedark">
          <button
            className={
              'flex justify-center ' +
              (!orderHasChanges()
                ? 'cursor-not-allowed bg-blue-400 '
                : 'bg-primary hover:bg-opacity-90 ') +
              'rounded py-2 px-6 font-medium text-gray'
            }
            type="submit"
            disabled={isSubmitting || !orderHasChanges()}
          >
            {isSubmitting ? <ClipLoader color="#ffffff" size={23} /> : 'Save'}
          </button>
        </div>
      </form>

      {/* Add Supplier Form Modal */}
      {!isOrderDelivered && (
        <ModalOverlay
          isOpen={openAddSupplier}
          onClose={() => setOpenAddSupplier(false)}
        >
          <AddSupplier open={openAddSupplier} setOpen={setOpenAddSupplier} />
        </ModalOverlay>
      )}

      {/* Add Item Form Modal */}
      {currentSupplier && !isOrderDelivered && (
        <ModalOverlay
          isOpen={openAddItem}
          onClose={() => setOpenAddItem(false)}
        >
          <AddItem
            open={openAddItem}
            setOpen={setOpenAddItem}
            supplier={currentSupplier}
          />
        </ModalOverlay>
      )}
    </div>
  );
};

export default EditSupplierOrder;

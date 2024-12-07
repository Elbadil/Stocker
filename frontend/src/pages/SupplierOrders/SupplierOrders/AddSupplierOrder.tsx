import React, { useEffect, useState } from 'react';
import {
  useForm,
  Controller,
  SubmitHandler,
  useFieldArray,
} from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import Select, { SingleValue } from 'react-select';
import ClipLoader from 'react-spinners/ClipLoader';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import { useSupplierOrders } from '../../../contexts/SupplierOrdersContext';
import { setSupplierOrders } from '../../../store/slices/supplierOrdersSlice';
import { SupplierOrderProps } from './SupplierOrder';
import AddSupplier from '../Suppliers/AddSupplier';
import AddItem from '../../Inventory/AddItem';
import { useAlert } from '../../../contexts/AlertContext';
import ModalOverlay from '../../../components/ModalOverlay';
import {
  orderedItemsField,
  requiredStringField,
  optionalStringField,
  optionalNumberField,
  customSelectStyles,
  selectOptionsFromObjects,
  selectOptionsFromStrings,
  statusType,
} from '../../../utils/form';
import { SelectOption } from '../../../types/form';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';
import { api } from '../../../api/axios';
import {
  filterAndSetSupplierItems,
  resetNewSupplier,
  addNewOrderedItemField,
  resetNewOrderedItem,
} from './utils';

export const schema = z.object({
  supplier: requiredStringField('Supplier'),
  ordered_items: orderedItemsField(),
  delivery_status: optionalStringField(),
  payment_status: optionalStringField(),
  shipping_cost: optionalNumberField(),
  tracking_number: optionalStringField(),
});

export type SupplierOrderSchema = z.infer<typeof schema>;
export type SupplierOrderedItemSchema =
  SupplierOrderSchema['ordered_items'][number];

interface AddSupplierOrder {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setRowData: React.Dispatch<React.SetStateAction<SupplierOrderProps[]>>;
}

const AddSupplierOrder = ({ open, setOpen, setRowData }: AddSupplierOrder) => {
  const { isDarkMode, setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const {
    suppliers,
    orderStatus,
    ordersCount,
    newSupplier,
    noSupplierItems,
    newOrderedItem,
  } = useSupplierOrders();
  const [openAddSupplier, setOpenAddSupplier] = useState<boolean>(false);
  const [openAddItem, setOpenAddItem] = useState<boolean>(false);

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
    handleSubmit,
    clearErrors,
    reset,
    resetField,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<SupplierOrderSchema>({
    resolver: zodResolver(schema),
    defaultValues: {
      supplier: '',
      ordered_items: [emptyItem as SupplierOrderedItemSchema],
      delivery_status: 'Pending',
      payment_status: 'Pending',
      tracking_number: '',
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'ordered_items',
  });

  const currentSupplier = watch('supplier');
  const currentDeliveryStatus = watch('delivery_status');
  const suppliersMap = new Map(
    suppliers.map((supplier) => [supplier.name, supplier.item_names]),
  );
  const noSupplierItemsOptions = selectOptionsFromStrings(noSupplierItems);
  const paymentStatusOptions = selectOptionsFromStrings(
    orderStatus.payment_status,
  );
  const [itemOptions, setItemOptions] = useState<SelectOption[]>(
    noSupplierItemsOptions,
  );
  const supplierOptions = selectOptionsFromObjects(suppliers);
  const deliveryStatusOptions = selectOptionsFromStrings(
    orderStatus.delivery_status,
  );

  const handleSupplierChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    // reset newSupplier if any
    if (newSupplier) {
      resetNewSupplier();
    }

    // Change value, filter ordered items fields and set Item options
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
    option: SingleValue<{ value: string; label: string }>,
    index: number,
  ) => {
    if (option) {
      onChange(option.value);
    } else {
      onChange('');
    }
    clearErrors(`ordered_items.${index}`);
  };

  const updateOrderStatusState = (newSupplierOrder: SupplierOrderProps) => {
    const orderStatusType = statusType(newSupplierOrder.delivery_status);
    return {
      ...orderStatus,
      [orderStatusType]: orderStatus[orderStatusType] + 1,
    };
  };

  const onSubmit: SubmitHandler<SupplierOrderSchema> = async (data) => {
    try {
      const res = await api.post('/supplier_orders/orders/', data);
      const newOrder = res.data;
      // Add new order to rowData
      setRowData((prev) => [newOrder, ...prev]);
      // Update supplierOrders state
      dispatch((dispatch, getState) => {
        const { supplierOrders } = getState();
        dispatch(
          setSupplierOrders({
            ...supplierOrders,
            ordersCount: ordersCount + 1,
            orderStatus: updateOrderStatusState(newOrder),
          }),
        );
      });
      // Set and display success Alert
      setAlert({
        type: 'success',
        title: 'New Order Created',
        description: `Order ${newOrder.reference_id} from ${
          newOrder.supplier
        } has been successfully added.${
          newOrder.delivery_status === 'Delivered'
            ? ' The ordered items have been added to the inventory. For existing items, the quantity has been updated, and the average price recalculated.'
            : ''
        }`,
      });
      // Close Add Supplier Order Modal
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

  useEffect(() => {
    if (open) reset();
  }, [open]);

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

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Create New Order
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
            {/* Supplier */}
            <div className="mb-4">
              <div className="flex items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="supplier_name"
                >
                  Supplier*
                </label>
                <button
                  type="button"
                  onClick={() => setOpenAddSupplier(true)}
                  className="text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                >
                  new supplier?
                </button>
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
              </div>
              {/* Ordered Items Note */}
              <div className="text-sm mb-2.5 text-black dark:text-slate-300">
                * Note: You can select items already linked to this supplier,
                items without a supplier (their supplier will be set to this
                order's supplier after the order is placed), or create a new
                item to add it to the item options.
              </div>
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
                              />
                            )}
                          />
                        )}
                      </div>
                      {/* Delete Item Field */}
                      {fields.length > 1 && (
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
                      className="w-full rounded border border-stroke bg-gray pl-3 py-2 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                      type="number"
                      placeholder="e.g. 1"
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
                      className="w-full rounded border border-stroke bg-gray pl-3 py-2 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                      type="number"
                      placeholder="e.g. 19.99"
                      {...register(`ordered_items.${index}.ordered_price`)}
                    />
                    {errors.ordered_items?.[index]?.ordered_price && (
                      <p className="text-red-500 font-medium text-sm italic mt-1">
                        {errors.ordered_items[index].ordered_price.message}
                      </p>
                    )}
                  </div>
                  {/* Add Item Button */}
                  {index === fields.length - 1 && (
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
                      />
                    )}
                  />
                )}
              </div>
              {/* 'Delivered' delivery status note */}
              {!errors.delivery_status &&
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
                      <strong> supplier</strong> or{' '}
                      <strong>ordered items</strong> fields. Please ensure all
                      details are correct before submitting.
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
            className="flex justify-center bg-primary hover:bg-opacity-90 rounded py-2 px-6 font-medium text-gray"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <ClipLoader color="#ffffff" size={23} />
            ) : (
              'Add new order'
            )}
          </button>
        </div>
      </form>

      {/* Add Supplier Form Modal */}
      <ModalOverlay
        isOpen={openAddSupplier}
        onClose={() => setOpenAddSupplier(false)}
      >
        <AddSupplier open={openAddSupplier} setOpen={setOpenAddSupplier} />
      </ModalOverlay>

      {/* Add Item Form Modal */}
      {currentSupplier && (
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

export default AddSupplierOrder;

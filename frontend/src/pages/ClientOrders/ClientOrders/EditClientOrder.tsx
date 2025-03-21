import React, { useState, useEffect } from 'react';
import {
  useForm,
  useFieldArray,
  Controller,
  SubmitHandler,
} from 'react-hook-form';
import { IRowNode } from '@ag-grid-community/core';
import { zodResolver } from '@hookform/resolvers/zod';
import Select, { SingleValue } from 'react-select';
import CreatableSelect from 'react-select/creatable';
import ClipLoader from 'react-spinners/ClipLoader';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import ModalOverlay from '../../../components/ModalOverlay';
import {
  customSelectStyles,
  selectOptionsFromStrings,
  selectOptionsFromObjects,
  statusType,
} from '../../../utils/form';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import AddClient from '../Clients/AddClient';
import AddItem from '../../Inventory/AddItem';
import { useClientOrders } from '../../../contexts/ClientOrdersContext';
import { useInventory } from '../../../contexts/InventoryContext';
import { setInventory } from '../../../store/slices/inventorySlice';
import { setClientOrders } from '../../../store/slices/clientOrdersSlice';
import {
  schema,
  ClientOrderSchema,
  ClientOrderedItemSchema,
} from './AddClientOrder';
import { ClientOrderProps } from './ClientOrder';
import { useAlert } from '../../../contexts/AlertContext';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';
import { findCountryAndSetCitiesForOrder, resetNewClient } from './utils';
import { api } from '../../../api/axios';
import toast from 'react-hot-toast';

interface EditClientOrderProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  order: ClientOrderProps;
  setOrder?: React.Dispatch<React.SetStateAction<ClientOrderProps | null>>;
  rowNode?: IRowNode<ClientOrderProps>;
  setRowData: React.Dispatch<React.SetStateAction<ClientOrderProps[]>>;
}

const EditClientOrder = ({
  open,
  setOpen,
  order,
  setOrder,
  rowNode,
  setRowData,
}: EditClientOrderProps) => {
  const { isDarkMode, setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const { clients, newClient, acqSources, countries, orderStatus } =
    useClientOrders();
  const { items } = useInventory();
  const [openAddClient, setOpenAddClient] = useState<boolean>(false);
  const [openAddItem, setOpenAddItem] = useState<boolean>(false);
  const [cityOptions, setCityOptions] = useState<
    { value: string; label: string }[]
  >([]);
  const [initialValues, setInitialValues] = useState<ClientOrderSchema | null>(
    null,
  );
  const [isOrderDelivered, setIsOrderDelivered] = useState<boolean>(false);

  const {
    register,
    handleSubmit,
    control,
    reset,
    watch,
    clearErrors,
    setValue,
    setError,
    formState: { errors, dirtyFields, isSubmitting },
  } = useForm<ClientOrderSchema>({
    resolver: zodResolver(schema),
  });

  const currentValues = watch();
  const currentDeliveryStatus = watch('delivery_status');

  const { fields, append, remove } = useFieldArray({
    name: 'ordered_items',
    control,
  });

  const emptyItem: Partial<ClientOrderedItemSchema> = {
    item: '',
    ordered_quantity: undefined,
    ordered_price: undefined,
  };

  const clientOptions = selectOptionsFromStrings(clients.names);
  const itemOptions = selectOptionsFromObjects(items);
  const sourceOptions = selectOptionsFromStrings(acqSources);
  const countryOptions = selectOptionsFromObjects(countries);
  const deliveryStatusOptions = selectOptionsFromStrings(
    orderStatus.delivery_status,
  );
  const paymentStatusOptions = selectOptionsFromStrings(
    orderStatus.payment_status,
  );

  const inventoryItemsMap = new Map(items.map((item) => [item.name, item]));

  const handleClientChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    if (newClient) {
      resetNewClient();
    }
    if (option) {
      onChange(option.value);
    } else {
      onChange('');
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
      clearErrors(`ordered_items.${index}`);
    }
  };

  const handleCountryChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    if (option) {
      onChange(option.value);
      findCountryAndSetCitiesForOrder(
        option.value,
        countries,
        setCityOptions,
        currentValues,
        setValue,
      );
    } else {
      onChange(null);
      setCityOptions([]);
      setValue('shipping_address.city', null);
    }
  };

  const validateItemQuantity = (orderedItems: ClientOrderedItemSchema[]) => {
    let quantityErrors = false;

    const setQuantityError = (index: number) => {
      setError(`ordered_items.${index}.ordered_quantity`, {
        message: 'The ordered quantity exceeds available stock.',
      });
      quantityErrors = true;
    };

    const previousItemsMap = new Map(
      order.ordered_items.map((orderedItem) => [orderedItem.item, orderedItem]),
    );

    orderedItems.forEach((orderedItem, index: number) => {
      const itemInInventory = inventoryItemsMap.get(orderedItem.item);
      const itemPrevOrdered = previousItemsMap.get(orderedItem.item);

      if (itemPrevOrdered) {
        if (
          itemInInventory &&
          itemPrevOrdered.ordered_quantity !== orderedItem.ordered_quantity &&
          itemInInventory.quantity + itemPrevOrdered.ordered_quantity <
            orderedItem.ordered_quantity
        ) {
          setQuantityError(index);
        }
      } else if (
        itemInInventory &&
        itemInInventory.quantity < orderedItem.ordered_quantity
      ) {
        setQuantityError(index);
      }
    });
    return quantityErrors;
  };

  const updateOrderStatusState = (newOrderDeliveryStatus: string) => {
    if (newOrderDeliveryStatus !== order.delivery_status) {
      const newStatusType = statusType(newOrderDeliveryStatus);
      const oldStatusType = statusType(order.delivery_status);
      return {
        ...orderStatus,
        [newStatusType]: orderStatus[newStatusType] + 1,
        [oldStatusType]: orderStatus[oldStatusType] - 1,
      };
    }
    return orderStatus;
  };

  const updateOrderedItemsState = (orderUpdate: ClientOrderProps) => {
    const updatedItemsMap = new Map(
      orderUpdate.ordered_items.map((orderedItem) => [
        orderedItem.item,
        orderedItem,
      ]),
    );
    const previousItemsMap = new Map(
      order.ordered_items.map((orderedItem) => [orderedItem.item, orderedItem]),
    );

    return items.map((item) => {
      const orderedItem = updatedItemsMap.get(item.name);
      const previousOrderedItem = previousItemsMap.get(item.name);

      if (orderedItem && previousOrderedItem) {
        // Calculate quantity difference for updated items
        const quantityDiff =
          orderedItem.ordered_quantity - previousOrderedItem.ordered_quantity;
        return {
          ...item,
          quantity: item.quantity - quantityDiff,
        };
      } else if (previousOrderedItem) {
        // Add removed ordered item's quantity to the item
        return {
          ...item,
          quantity: item.quantity + previousOrderedItem.ordered_quantity,
        };
      } else if (orderedItem) {
        // New ordered item quantity adjustment
        return {
          ...item,
          quantity: item.quantity - orderedItem.ordered_quantity,
        };
      }
      return item;
    });
  };

  const onSubmit: SubmitHandler<ClientOrderSchema> = async (data) => {
    const quantityErrors = validateItemQuantity(data.ordered_items);
    if (quantityErrors) return;
    console.log(data);
    try {
      const res = await api.put(`/client_orders/${order.id}/`, data);
      const orderUpdate = res.data;
      console.log('Order Update', orderUpdate);
      // Update rowNode
      rowNode?.setData(orderUpdate);
      // Update rowData
      setRowData((prev) =>
        prev.map((orderInstance) =>
          orderInstance.id === order.id ? orderUpdate : orderInstance,
        ),
      );
      // Update inventory's items state
      dispatch((dispatch, getState) => {
        const { inventory, clientOrders } = getState();
        dispatch(
          setClientOrders({
            ...clientOrders,
            orderStatus: updateOrderStatusState(orderUpdate.delivery_status),
          }),
        );
        dispatch(
          setInventory({
            ...inventory,
            items: updateOrderedItemsState(orderUpdate),
          }),
        );
      });
      // Set success Alert
      if (setOrder) {
        setOrder(orderUpdate);
        toast.success(`Order ${order.reference_id} updated!`, {
          duration: 4000,
        });
      } else {
        setAlert({
          type: 'success',
          title: 'Order Updated',
          description: `Order ${order.reference_id} has been successfully updated.`,
        });
      }
      // Close Edit Order Modal
      setOpen(false);
    } catch (error: any) {
      console.log('Error during form submission', error);
      if (error.response && error.response.status === 400) {
        const errorData = error.response.data;
        (Object.keys(errorData) as Array<keyof ClientOrderSchema>).forEach(
          (field) => {
            if (field === 'shipping_address') {
              const addressErrors = errorData[field];
              Object.keys(addressErrors).forEach((prop) => {
                const addressProp =
                  prop as keyof ClientOrderSchema['shipping_address'];
                setError(`${field}.${addressProp}`, {
                  message: addressErrors[addressProp],
                });
              });
            } else {
              setError(field, { message: errorData[field] });
            }
          },
        );
      } else {
        setError('root', {
          message: 'Something went wrong, please try again later.',
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

    return (Object.keys(dirtyFields) as Array<keyof ClientOrderSchema>).some(
      (key) => {
        if (numberFields.includes(key)) {
          return Number(initialValues[key]) !== Number(currentValues[key]);
        }
        if (key === 'ordered_items') {
          return initialValues.ordered_items.some((orderedItem, index) => {
            return (
              Object.keys(orderedItem) as Array<keyof ClientOrderedItemSchema>
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
        if (key === 'shipping_address') {
          return (
            JSON.stringify(initialValues[key]) !==
            JSON.stringify(currentValues[key])
          );
        }
        return initialValues[key] !== currentValues[key];
      },
    );
  };

  useEffect(() => {
    const loadData = () => {
      setInitialValues(order);
      reset(order);
      if (
        order.shipping_address &&
        order.shipping_address.country &&
        order.shipping_address.city
      ) {
        findCountryAndSetCitiesForOrder(
          order.shipping_address.country,
          countries,
          setCityOptions,
          currentValues,
          setValue,
        );
      }
      if (order.delivery_status === 'Delivered') setIsOrderDelivered(true);
    };

    if (open) loadData();
  }, [open]);

  useEffect(() => {
    if (newClient) setValue('client', newClient);
  }, [newClient]);

  useEffect(() => {
    orderHasChanges();
  }, [initialValues, currentValues]);

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Edit Order {order.reference_id} - By: {order.client}
        </h3>
        <div>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              resetNewClient();
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
                client, ordered items, and delivery status cannot be modified to
                maintain data integrity, and any changes made to the order
                record will be synchronized between both the order and the sale
                record.
              </div>
            )}

            {/* Client */}
            <div className="mb-4">
              <div className="flex items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="client_name"
                >
                  Client*
                </label>
                {!isOrderDelivered && (
                  <button
                    type="button"
                    onClick={() => setOpenAddClient(true)}
                    className="text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                  >
                    new client?
                  </button>
                )}
              </div>
              <div className="w-full">
                {open && (
                  <Controller
                    name="client"
                    control={control}
                    rules={{ required: true }}
                    render={({ field: { value, onChange, ...field } }) => (
                      <Select
                        {...field}
                        isClearable
                        value={
                          newClient
                            ? { value: newClient, label: newClient }
                            : value
                            ? clientOptions.find(
                                (option) => option.value === value,
                              )
                            : null
                        }
                        onChange={(option) =>
                          handleClientChange(onChange, option)
                        }
                        options={clientOptions}
                        styles={customSelectStyles(isDarkMode)}
                        isDisabled={isOrderDelivered}
                      />
                    )}
                  />
                )}
              </div>
              {errors.client && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.client.message}
                </p>
              )}
            </div>

            {/* Ordered Items */}
            <div className="mb-2 border-t border-b border-stroke dark:border-slate-600">
              <div className="flex pt-3 items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="client_name"
                >
                  Ordered Item(s)*
                </label>
                {!isOrderDelivered && (
                  <button
                    type="button"
                    onClick={() => setOpenAddItem(true)}
                    className="text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                  >
                    new item?
                  </button>
                )}
              </div>
              {/* Ordered Items Note */}
              {!isOrderDelivered && (
                <div className="text-sm mb-2.5 text-black dark:text-slate-300">
                  * Note: You can only select items that exist in the inventory
                  or create a new one. Ordered item quantities will be
                  automatically deducted from inventory upon order submission.
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
                        append(emptyItem as ClientOrderedItemSchema)
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
                      <CreatableSelect
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
                        A new sale record will be created and added to the sales
                        list, containing the order's details.
                      </li>
                      <li>
                        Any future changes made to the linked sale or order
                        record will be synchronized between both records.
                      </li>
                    </ul>
                    <p className="mt-2">
                      Additionally, you will no longer be able to modify the
                      <strong> client</strong>, <strong>ordered items</strong>{' '}
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
                      <CreatableSelect
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
            {/* Acquisition Source */}
            <div className="mb-3 pb-4 border-b border-stroke dark:border-slate-600">
              <label
                className="block mb-2 text-base font-medium text-black dark:text-white"
                htmlFor="source"
              >
                Source of Acquisition
              </label>
              <div className="w-full">
                {open && (
                  <Controller
                    name="source"
                    control={control}
                    rules={{ required: false }}
                    render={({ field: { value, onChange, ...field } }) => (
                      <CreatableSelect
                        {...field}
                        isClearable
                        value={
                          value
                            ? sourceOptions.find(
                                (option) => option.value === value,
                              )
                            : null
                        }
                        onChange={(option) => onChange(option?.value || null)}
                        options={sourceOptions}
                        styles={customSelectStyles(isDarkMode)}
                        placeholder={<span>Create or Select...</span>}
                      />
                    )}
                  />
                )}
              </div>
              {errors.source && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.source.message}
                </p>
              )}
            </div>
            {/* Shipping Address */}
            <div className="mb-3 pb-3 border-b border-stroke dark:border-slate-600">
              <label
                className="block  mb-2 text-base font-medium text-black dark:text-white"
                htmlFor="source"
              >
                Address
              </label>
              {/* Country & City */}
              <div className="mb-3 flex flex-col gap-5.5 sm:flex-row">
                {/* Country */}
                <div className="w-full sm:w-1/2">
                  <label
                    className="mb-2 block text-sm font-medium text-black dark:text-white"
                    htmlFor="country"
                  >
                    Country
                  </label>
                  {open && (
                    <Controller
                      name="shipping_address.country"
                      control={control}
                      rules={{ required: false }}
                      render={({ field: { value, onChange, ...field } }) => (
                        <Select
                          {...field}
                          isClearable
                          value={
                            value
                              ? countryOptions.find(
                                  (option) => option.value === value,
                                )
                              : null
                          }
                          onChange={(option) =>
                            handleCountryChange(onChange, option)
                          }
                          options={countryOptions}
                          styles={customSelectStyles(isDarkMode)}
                        />
                      )}
                    />
                  )}
                  {errors.shipping_address?.country && (
                    <p className="text-red-500 font-medium text-sm italic mt-2">
                      {errors.shipping_address.country.message}
                    </p>
                  )}
                </div>
                {/* City */}
                <div className="w-full sm:w-1/2">
                  <label
                    className="mb-2 block text-sm font-medium text-black dark:text-white"
                    htmlFor="city"
                  >
                    City
                  </label>
                  {open && (
                    <Controller
                      name="shipping_address.city"
                      control={control}
                      rules={{ required: false }}
                      render={({ field: { value, onChange, ...field } }) => (
                        <Select
                          {...field}
                          isClearable
                          value={
                            value
                              ? cityOptions.find(
                                  (option) => option.value === value,
                                )
                              : null
                          }
                          onChange={(option) => onChange(option?.value || null)}
                          options={cityOptions}
                          noOptionsMessage={() =>
                            'Choose a country for city options'
                          }
                          styles={customSelectStyles(isDarkMode)}
                        />
                      )}
                    />
                  )}
                  {errors.shipping_address?.city && (
                    <p className="text-red-500 font-medium text-sm italic mt-2">
                      {errors.shipping_address.city.message}
                    </p>
                  )}
                </div>
              </div>
              {/* Street Address */}
              <label
                className="mb-2 block text-sm font-medium text-black dark:text-white"
                htmlFor="address"
              >
                Street Address
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="eg. Oued Tansift Street N2"
                {...register('shipping_address.street_address')}
              />
              {errors.shipping_address?.street_address && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.shipping_address.street_address.message}
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

      {/* Add Client Form Modal */}
      <ModalOverlay
        isOpen={openAddClient}
        onClose={() => setOpenAddClient(false)}
      >
        <AddClient open={openAddClient} setOpen={setOpenAddClient} />
      </ModalOverlay>

      {/* Add Item Form Modal */}
      <ModalOverlay isOpen={openAddItem} onClose={() => setOpenAddItem(false)}>
        <AddItem open={openAddItem} setOpen={setOpenAddItem} />
      </ModalOverlay>
    </div>
  );
};

export default EditClientOrder;

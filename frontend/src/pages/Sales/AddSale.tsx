import React, { useEffect, useState } from 'react';
import {
  useForm,
  useFieldArray,
  Controller,
  SubmitHandler,
} from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import ClipLoader from 'react-spinners/ClipLoader';
import Select, { SingleValue } from 'react-select';
import CreatableSelect from 'react-select/creatable';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import { SaleProps, SoldItem } from './Sales';
import { useAlert } from '../../contexts/AlertContext';
import {
  locationField,
  optionalNumberField,
  optionalStringField,
  requiredStringField,
  selectOptionsFromObjects,
  selectOptionsFromStrings,
  customSelectStyles,
  soldItemsField,
  statusType,
} from '../../utils/form';
import ModalOverlay from '../../components/ModalOverlay';
import AddClient from '../ClientOrders/Clients/AddClient';
import AddItem from '../Inventory/AddItem';
import { resetNewClient } from '../ClientOrders/ClientOrders/utils';
import { useSales } from '../../contexts/SalesContext';
import { useClientOrders } from '../../contexts/ClientOrdersContext';
import { useInventory } from '../../contexts/InventoryContext';
import { SelectOption } from '../../types/form';
import { findCountryAndSetCitiesForSale } from './utils';
import { api } from '../../api/axios';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store/store';
import { setSales } from '../../store/slices/salesSlice';
import { setInventory } from '../../store/slices/inventorySlice';

export const schema = z.object({
  client: requiredStringField('Client'),
  sold_items: soldItemsField(),
  delivery_status: optionalStringField(),
  payment_status: optionalStringField(),
  source: optionalStringField(),
  shipping_address: locationField(),
  shipping_cost: optionalNumberField(),
  tracking_number: optionalStringField(),
});

export type SaleSchema = z.infer<typeof schema>;
export type SoldItemSchema = SaleSchema['sold_items'][number];

interface AddSale {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setRowData: React.Dispatch<React.SetStateAction<SaleProps[]>>;
}

const AddSale = ({ open, setOpen, setRowData }: AddSale) => {
  const { isDarkMode, setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const { saleStatus, salesCount } = useSales();
  const { clients, newClient, acqSources, countries } = useClientOrders();
  const { items } = useInventory();
  const [openAddClient, setOpenAddClient] = useState<boolean>(false);
  const [openAddItem, setOpenAddItem] = useState<boolean>(false);

  // Partial makes all properties of a type optional
  const emptyItem: Partial<SoldItemSchema> = {
    item: '',
    sold_quantity: undefined,
    sold_price: undefined,
  };

  const {
    register,
    control,
    reset,
    handleSubmit,
    setError,
    setValue,
    clearErrors,
    formState: { errors, isSubmitting },
  } = useForm<SaleSchema>({
    resolver: zodResolver(schema),
    defaultValues: {
      sold_items: [emptyItem as SoldItemSchema],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'sold_items',
  });

  const clientOptions = selectOptionsFromStrings(clients.names);
  const itemOptions = selectOptionsFromObjects(items);
  const deliveryStatusOptions = selectOptionsFromStrings(
    saleStatus.delivery_status,
  );
  const paymentStatusOptions = selectOptionsFromStrings(
    saleStatus.payment_status,
  );
  const sourceOptions = selectOptionsFromStrings(acqSources);
  const countryOptions = selectOptionsFromObjects(countries);
  const [cityOptions, setCityOptions] = useState<SelectOption[]>([]);
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
      clearErrors(`sold_items.${index}`);
    }
  };

  const handleCountryChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    if (option) {
      onChange(option.value);
      findCountryAndSetCitiesForSale(option.value, countries, setCityOptions);
    } else {
      onChange(null);
      setCityOptions([]);
      setValue('shipping_address.city', null);
    }
  };

  const validateItemQuantity = (soldItems: SoldItemSchema[]) => {
    let quantityErrors = false;

    soldItems.forEach((soldItem, index: number) => {
      const itemInInventory = inventoryItemsMap.get(soldItem.item);

      if (
        itemInInventory &&
        itemInInventory.quantity < soldItem.sold_quantity
      ) {
        setError(`sold_items.${index}.sold_quantity`, {
          message: 'The sold quantity exceeds available stock.',
        });
        quantityErrors = true;
      }
    });
    return quantityErrors;
  };

  const updateItemQuantities = (soldItems: SoldItemSchema[]) => {
    dispatch((dispatch, getState) => {
      const { inventory } = getState();
      dispatch(
        setInventory({
          ...inventory,
          items: items.map((item) => {
            const soldItemInInventory = soldItems.find(
              (soldItem) => soldItem.item === item.name,
            );
            return soldItemInInventory
              ? {
                  ...item,
                  quantity: item.quantity - soldItemInInventory.sold_quantity,
                }
              : item;
          }),
        }),
      );
    });
  };

  const updateSaleState = (newStatus: string) => {
    const newStatusType = statusType(newStatus);
    dispatch(
      setSales({
        salesCount: salesCount + 1,
        saleStatus: {
          ...saleStatus,
          [newStatusType]: saleStatus[newStatusType] + 1,
        },
      }),
    );
  };

  const onSubmit: SubmitHandler<SaleSchema> = async (data) => {
    const soldItems = data.sold_items;
    const quantityErrors = validateItemQuantity(soldItems);
    if (quantityErrors) return;
    try {
      const res = await api.post('/sales/', data);
      const newSale = res.data;
      console.log(newSale);
      // Update sales count
      dispatch((dispatch, getState) => {
        const { sales } = getState();
        dispatch(
          setSales({
            ...sales,
            salesCount: salesCount + 1,
          }),
        );
      });
      // Update sales state
      updateSaleState(newSale.delivery_status);
      // Update item inventory quantities
      updateItemQuantities(soldItems);
      // Append new sale to rowData
      setRowData((prev) => [newSale, ...prev]);
      // Display success alert
      setAlert({
        type: 'success',
        title: 'New Sale Created',
        description: `Sale ${newSale.reference_id} made by ${newSale.client} has been successfully added.`,
      });
      // Close Add Sale Modal
      setOpen(false);
    } catch (error: any) {
      console.log('Error during form submission', error);
      if (error.response && error.response.status === 400) {
        const errorData = error.response.data;
        (Object.keys(errorData) as Array<keyof SaleSchema>).forEach((field) => {
          if (field === 'shipping_address') {
            const addressErrors = errorData[field];
            Object.keys(addressErrors).forEach((prop) => {
              const addressProp = prop as keyof SaleSchema['shipping_address'];
              setError(`${field}.${addressProp}`, {
                message: addressErrors[addressProp],
              });
            });
          } else {
            setError(field, { message: errorData[field] });
          }
        });
      } else {
        setError('root', {
          message: 'Something went wrong, please try again later.',
        });
      }
    }
  };

  useEffect(() => {
    if (open) reset();
  }, [open]);

  useEffect(() => {
    if (newClient) setValue('client', newClient);
  }, [newClient]);

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Create New Sale
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
            {/* Client */}
            <div className="mb-4">
              <div className="flex items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="client_name"
                >
                  Client*
                </label>
                <button
                  type="button"
                  onClick={() => setOpenAddClient(true)}
                  className="text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                >
                  new client?
                </button>
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

            {/* Sold Items */}
            <div className="mb-2 border-t border-b border-stroke dark:border-slate-600">
              <div className="flex pt-3 items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="client_name"
                >
                  Sold Item(s)*
                </label>
                <button
                  type="button"
                  onClick={() => setOpenAddItem(true)}
                  className="text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                >
                  new item?
                </button>
              </div>
              {/* Sold Items Note */}
              <div className="text-sm mb-2.5 text-black dark:text-slate-300">
                * Note: You can only select items that exist in the inventory or
                create a new one. Sold item quantities will be automatically
                deducted from inventory upon sale submission.
              </div>
              {/* Sold Items Fields List */}
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
                            name={`sold_items.${index}.item`}
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
                    {errors.sold_items?.[index]?.item && (
                      <p className="text-red-500 font-medium text-sm italic mt-1">
                        {errors.sold_items[index].item.message}
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
                      {...register(`sold_items.${index}.sold_quantity`)}
                    />
                    {errors.sold_items?.[index]?.sold_quantity && (
                      <p className="text-red-500 font-medium text-sm italic mt-1">
                        {errors.sold_items[index].sold_quantity.message}
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
                      {...register(`sold_items.${index}.sold_price`)}
                    />
                    {errors.sold_items?.[index]?.sold_price && (
                      <p className="text-red-500 font-medium text-sm italic mt-1">
                        {errors.sold_items[index].sold_price.message}
                      </p>
                    )}
                  </div>
                  {/* Add Item Button */}
                  {index === fields.length - 1 && (
                    <button
                      type="button"
                      className="mt-3 text-sm inline-flex items-center justify-center rounded-md bg-meta-3 py-2 px-2 text-center font-medium text-white hover:bg-opacity-90"
                      onClick={() => append(emptyItem as SoldItemSchema)}
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
            className="flex justify-center bg-primary hover:bg-opacity-90 rounded py-2 px-6 font-medium text-gray"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <ClipLoader color="#ffffff" size={23} />
            ) : (
              'Add new sale'
            )}
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

export default AddSale;

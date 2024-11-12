import {
  SubmitHandler,
  useForm,
  useFieldArray,
  Controller,
} from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import Select, { SingleValue } from 'react-select';
import CreatableSelect from 'react-select/creatable';
import ClipLoader from 'react-spinners/ClipLoader';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import ModalOverlay from '../../../components/ModalOverlay';
import { api } from '../../../api/axios';
import AddClient from '../Clients/AddClient';
import AddItem from '../../Inventory/AddItem';
import {
  requiredStringField,
  requiredPositiveNumberField,
  customSelectStyles,
  selectOptionsFromStrings,
  selectOptionsFromObjects,
} from '../../../utils/form';
import { useClientOrders } from '../../../contexts/ClientOrdersContext';
import { setClientOrders } from '../../../store/slices/clientOrdersSlice';
import { useDispatch } from 'react-redux';
import React, { useEffect, useState } from 'react';
import { useAlert } from '../../../contexts/AlertContext';
import { useInventory } from '../../../contexts/InventoryContext';
import { setInventory } from '../../../store/slices/inventorySlice';
import { AppDispatch } from '../../../store/store';
import { OrderProps } from './Order';
import { findCountryAndSetCitiesForOrder } from './utils';

export const schema = z.object({
  client: requiredStringField('Client'),
  ordered_items: z
    .array(
      z.object({
        item: requiredStringField('Item name'),
        ordered_quantity: requiredPositiveNumberField('Quantity'),
        ordered_price: requiredPositiveNumberField('Price'),
      }),
    )
    .superRefine((orderedItems, ctx) => {
      // Collect all items names
      const itemNames = orderedItems.map((orderedItem) => orderedItem.item);
      const nameCount: { [key: string]: number } = {};
      itemNames.forEach((name: string, index: number) => {
        const nameLower = name.toLowerCase().trim();
        nameCount[nameLower] = (nameCount[nameLower] || 0) + 1;
        if (nameCount[nameLower] > 1) {
          ctx.addIssue({
            code: 'custom',
            path: [index, 'item'], // Point to the specific field in the array
            message: `Item "${name.trim()}" has already been selected.`,
          });
        }
      });
    }),
  status: z.string().optional().nullable(),
  source: z.string().optional().nullable(),
  shipping_address: z
    .object({
      country: z.string().optional().nullable(),
      city: z.string().optional().nullable(),
      street_address: z.preprocess(
        (val) => (val === '' ? undefined : val),
        z.string().optional().nullable(),
      ),
    })
    .transform((loc) => {
      // If all properties are null or undefined, return undefined
      return Object.values(loc).every(
        (val) => val === null || val === undefined || val === '',
      )
        ? undefined
        : loc;
    }),
  shipping_cost: z.preprocess(
    (val) => (val ? Number(val) : null),
    z.number().optional().nullable(),
  ),
});

export type OrderSchema = z.infer<typeof schema>;
// Adding [number] at the end to tell TypeScript to give you the
// type of a single item in that array
export type OrderedItemSchema = OrderSchema['ordered_items'][number];

interface AddOrderProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setRowData: React.Dispatch<React.SetStateAction<OrderProps[]>>;
}

const AddOrder = ({ open, setOpen, setRowData }: AddOrderProps) => {
  const { isDarkMode, setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const {
    clients,
    newClient,
    acqSources,
    countries,
    orderStatus,
    ordersCount,
  } = useClientOrders();
  const { items } = useInventory();
  const [openAddClient, setOpenAddClient] = useState<boolean>(false);
  const [openAddItem, setOpenAddItem] = useState<boolean>(false);
  const [cityOptions, setCityOptions] = useState<
    { value: string; label: string }[]
  >([]);

  // Partial makes all properties of a type optional
  const emptyItem: Partial<OrderedItemSchema> = {
    item: '',
    ordered_quantity: undefined,
    ordered_price: undefined,
  };

  const {
    register,
    control,
    handleSubmit,
    clearErrors,
    reset,
    setError,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<OrderSchema>({
    resolver: zodResolver(schema),
    defaultValues: {
      client: '',
      // "as" => trust me, I know what I'm doing
      ordered_items: [emptyItem as OrderedItemSchema],
      status: '',
      source: '',
      shipping_address: {
        country: '',
        city: '',
        street_address: '',
      },
    },
  });

  const { fields, append, remove } = useFieldArray({
    name: 'ordered_items',
    control,
  });

  const clientOptions = selectOptionsFromStrings(clients.names);
  const itemOptions = selectOptionsFromObjects(items);
  const sourceOptions = selectOptionsFromStrings(acqSources);
  const countryOptions = selectOptionsFromObjects(countries);
  const statusOptions = selectOptionsFromStrings(orderStatus.names);

  const handleClientChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    if (newClient) {
      dispatch((dispatch, getState) => {
        const { clientOrders } = getState();
        dispatch(
          setClientOrders({
            ...clientOrders,
            newClient: null,
          }),
        );
      });
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
      findCountryAndSetCitiesForOrder(option.value, countries, setCityOptions);
    } else {
      onChange(null);
      setCityOptions([]);
      setValue('shipping_address.city', null);
    }
  };

  const validateItemQuantity = (orderedItems: OrderedItemSchema[]) => {
    let quantityErrors = false;
    orderedItems.forEach((orderedItem, index: number) => {
      const itemInInventory = items.find(
        (item) => item.name === orderedItem.item,
      );
      if (
        itemInInventory &&
        itemInInventory.quantity < orderedItem.ordered_quantity
      ) {
        setError(`ordered_items.${index}.ordered_quantity`, {
          message: 'The ordered quantity exceeds available stock.',
        });
        quantityErrors = true;
      }
    });
    return quantityErrors;
  };

  const onSubmit: SubmitHandler<OrderSchema> = async (data) => {
    const quantityErrors = validateItemQuantity(data.ordered_items);
    if (quantityErrors) return;
    const orderedItems = data.ordered_items;
    console.log(data);
    try {
      const res = await api.post('/client_orders/orders/', data);
      const newOrder = res.data;
      console.log(newOrder);
      dispatch((dispatch, getState) => {
        const { clientOrders, inventory } = getState();
        dispatch(
          setClientOrders({
            ...clientOrders,
            ordersCount: ordersCount + 1,
          }),
        );
        dispatch(
          setInventory({
            ...inventory,
            items: items.map((item) => {
              const orderedItem = orderedItems.find(
                (orderedItem) => orderedItem.item === item.name,
              );
              return orderedItem
                ? {
                    name: item.name,
                    quantity: item.quantity - orderedItem.ordered_quantity,
                  }
                : item;
            }),
          }),
        );
      });
      setRowData((prev) => [newOrder, ...prev]);
      setAlert({
        type: 'success',
        title: 'New Order Created',
        description: `Order ${newOrder.reference_id} by ${newOrder.client} has been successfully added.`,
      });
      setOpen(false);
    } catch (error: any) {
      console.log('Error during form submission', error);
      if (error.response && error.response.status === 400) {
        const errorData = error.response.data;
        (Object.keys(errorData) as Array<keyof OrderSchema>).forEach(
          (field) => {
            if (field === 'shipping_address') {
              const addressErrors = errorData[field];
              Object.keys(addressErrors).forEach((prop) => {
                const addressProp =
                  prop as keyof OrderSchema['shipping_address'];
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
          message: 'Something went wrong, please try again later',
        });
      }
    }
  };

  useEffect(() => {
    if (open) {
      clearErrors();
      reset();
    }
  }, [open]);

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
            onClick={() => setOpen(false)}
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

            {/* Ordered Items */}
            <div className="mb-2 border-t border-b border-stroke dark:border-slate-600">
              <div className="flex pt-3 items-center gap-2.5 mb-2">
                <label
                  className="block text-base font-medium text-black dark:text-white"
                  htmlFor="client_name"
                >
                  Ordered Item(s)*
                </label>
                <button
                  type="button"
                  onClick={() => setOpenAddItem(true)}
                  className="text-sm font-medium text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                >
                  new item?
                </button>
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
                                options={itemOptions}
                                styles={customSelectStyles(isDarkMode)}
                              />
                            )}
                          />
                        )}
                      </div>
                      {/* Delete Item Field */}
                      {index >= 1 && (
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
                      onClick={() => append(emptyItem as OrderedItemSchema)}
                    >
                      <AddCircleOutlinedIcon sx={{ marginRight: '0.2em' }} />
                      Add Item
                    </button>
                  )}
                </div>
              ))}
            </div>
            {/* Status */}
            <div className="mb-3 pb-4 border-b border-stroke dark:border-slate-600">
              <label
                className="block mb-2 text-base font-medium text-black dark:text-white"
                htmlFor="status"
              >
                Status
              </label>
              <div className="w-full">
                {open && (
                  <Controller
                    name="status"
                    control={control}
                    rules={{ required: false }}
                    render={({ field: { value, onChange, ...field } }) => (
                      <CreatableSelect
                        {...field}
                        isClearable
                        value={
                          value
                            ? statusOptions.find(
                                (option) => option.value === value,
                              )
                            : null
                        }
                        onChange={(option) => onChange(option?.value || null)}
                        options={statusOptions}
                        styles={customSelectStyles(isDarkMode)}
                        placeholder={<span>Select order status...</span>}
                      />
                    )}
                  />
                )}
              </div>
              {errors.status && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.status.message}
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
            <div className="mb-3">
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

export default AddOrder;

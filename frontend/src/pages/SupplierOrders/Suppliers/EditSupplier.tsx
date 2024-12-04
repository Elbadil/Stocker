import React, { useEffect, useState } from 'react';
import { useForm, Controller, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Select, { SingleValue } from 'react-select';
import ClipLoader from 'react-spinners/ClipLoader';
import { customSelectStyles } from '../../../utils/form';
import { SupplierProps } from './Supplier';
import { SupplierSchema, schema } from './AddSupplier';
import { useAlert } from '../../../contexts/AlertContext';
import { useClientOrders } from '../../../contexts/ClientOrdersContext';
import { useSupplierOrders } from '../../../contexts/SupplierOrdersContext';
import { setSupplierOrders } from '../../../store/slices/supplierOrdersSlice';
import { selectOptionsFromObjects } from '../../../utils/form';
import { findCountryAndSetCitiesForSupplier } from './utils';
import { Location } from '../../ClientOrders/Clients/Client';
import { IRowNode } from '@ag-grid-community/core';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../../store/store';
import { api } from '../../../api/axios';
import toast from 'react-hot-toast';

interface EditSupplier {
  supplier: SupplierProps;
  setSupplier?: React.Dispatch<React.SetStateAction<SupplierProps | null>>;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  rowNode?: IRowNode<SupplierProps>;
  setRowData: React.Dispatch<React.SetStateAction<SupplierProps[]>>;
}

const EditSupplier = ({
  supplier,
  setSupplier,
  open,
  setOpen,
  rowNode,
  setRowData,
}: EditSupplier) => {
  const { isDarkMode, setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const { suppliers } = useSupplierOrders();
  const { countries } = useClientOrders();
  const [initialData, setInitialData] = useState<SupplierSchema | null>(null);

  const {
    register,
    handleSubmit,
    control,
    setError,
    reset,
    watch,
    setValue,
    formState: { errors, dirtyFields, isSubmitting },
  } = useForm<SupplierSchema>({
    resolver: zodResolver(schema),
  });

  const currentValues = watch();

  const countryOptions = selectOptionsFromObjects(countries);
  const [cityOptions, setCityOptions] = useState<
    { value: string; label: string }[]
  >([]);

  const handleCountryChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    if (option) {
      onChange(option.value);
      findCountryAndSetCitiesForSupplier(
        option.value,
        countries,
        setCityOptions,
        currentValues,
        setValue,
      );
    } else {
      onChange(null);
      setCityOptions([]);
      setValue('location.city', null);
    }
  };

  const updateSuppliersState = (supplierUpdate: SupplierProps) =>
    suppliers.map((existingSupplier) =>
      existingSupplier.name === supplier.name
        ? {
            name: supplierUpdate.name,
            item_names: existingSupplier.item_names,
          }
        : existingSupplier,
    );

  const onSubmit: SubmitHandler<SupplierSchema> = async (data) => {
    console.log(data);
    try {
      const res = await api.put(
        `/supplier_orders/suppliers/${supplier.id}/`,
        data,
      );
      const supplierUpdate = res.data;
      // Update SupplierOrders State
      dispatch((dispatch, getState) => {
        const { supplierOrders } = getState();
        dispatch(
          setSupplierOrders({
            ...supplierOrders,
            suppliers: updateSuppliersState(supplierUpdate),
          }),
        );
      });
      // Update Row Node
      rowNode?.setData(supplierUpdate);
      // Update Row Data
      setRowData((prev) =>
        prev.map((rowData) =>
          rowData.id === supplier.id ? supplierUpdate : rowData,
        ),
      );
      // Set and display success Alert
      if (setSupplier) {
        setSupplier(supplierUpdate);
        toast.success('Supplier has been successfully updated!', {
          duration: 5000,
        });
      }
      setAlert({
        type: 'success',
        title: 'Supplier Updated',
        description: `Supplier ${supplierUpdate.name} has been successfully updated.`,
      });
      // Close Edit supplier Modal
      setOpen(false);
    } catch (error: any) {
      console.log('Error during form submission', error);
      if (error.response && error.response.status === 400) {
        const errorData = error.response.data;
        (Object.keys(errorData) as Array<keyof SupplierSchema>).forEach(
          (field) => {
            if (field === 'location') {
              const locationErrors = errorData[field];
              (Object.keys(locationErrors) as Array<keyof Location>).forEach(
                (key) => {
                  const locationFieldError = locationErrors[key];
                  setError(`location.${key}`, { message: locationFieldError });
                },
              );
            } else {
              const errorMessage = errorData[field];
              setError(field, { message: errorMessage });
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

  const supplierHasChanges = () => {
    if (!initialData || !currentValues) return false;
    return (Object.keys(dirtyFields) as Array<keyof SupplierSchema>).some(
      (key) => {
        if (key === 'location') {
          return (
            JSON.stringify(initialData[key]) !==
            JSON.stringify(currentValues[key])
          );
        }
        return initialData[key] !== currentValues[key];
      },
    );
  };

  useEffect(() => {
    if (open) {
      if (
        supplier.location &&
        supplier.location.country &&
        supplier.location.city
      ) {
        // setValue('location.city', supplier.location.city);
        findCountryAndSetCitiesForSupplier(
          supplier.location.country,
          countries,
          setCityOptions,
          currentValues,
          setValue,
        );
      }
      setInitialData(supplier);
      reset(supplier);
    }
  }, [open, reset]);

  useEffect(() => {
    supplierHasChanges();
  }, [initialData, currentValues]);

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Edit Supplier:
          {supplier.name.length > 28
            ? supplier.name.substring(0, 28) + '...'
            : supplier.name}
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
        <div className="max-w-full overflow-y-auto max-h-[80vh] flex flex-col">
          <div className="p-6">
            {/* Name */}
            <div className="mb-4">
              <label
                className="mb-2 block text-sm font-medium text-black dark:text-white"
                htmlFor="name"
              >
                Name*
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="Enter client name"
                {...register('name')}
              />
              {errors.name && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.name.message}
                </p>
              )}
            </div>
            {/* Phone Number */}
            <div className="mb-4">
              <label
                className="mb-2 block text-sm font-medium text-black dark:text-white"
                htmlFor="phone number"
              >
                Phone Number
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="Enter client number"
                {...register('phone_number')}
              />
              {errors.phone_number && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.phone_number.message}
                </p>
              )}
            </div>
            {/* Email */}
            <div className="mb-4">
              <label
                className="mb-2 block text-sm font-medium text-black dark:text-white"
                htmlFor="email"
              >
                Email
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="Enter client email"
                {...register('email')}
              />
              {errors.email && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.email.message}
                </p>
              )}
            </div>
            {/* Location */}
            <div className="mb-4">
              <label
                className="mb-2 border-b pb-2 border-stroke dark:border-slate-600 block text-Base font-medium text-black dark:text-white"
                htmlFor="location"
              >
                Location
              </label>
              {/* Country & City */}
              <div className="mb-4 flex flex-col gap-5.5 sm:flex-row">
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
                      name="location.country"
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
                  {errors.location?.country && (
                    <p className="text-red-500 font-medium text-sm italic mt-2">
                      {errors.location.country.message}
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
                      name="location.city"
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
                  {errors.location?.city && (
                    <p className="text-red-500 font-medium text-sm italic mt-2">
                      {errors.location.city.message}
                    </p>
                  )}
                </div>
              </div>
              <label
                className="mb-2 block text-sm font-medium text-black dark:text-white"
                htmlFor="address"
              >
                Address
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="eg. Oued Tansift Street N2"
                {...register('location.street_address')}
              />
              {errors.location?.street_address && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.location.street_address.message}
                </p>
              )}
            </div>
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
              (!supplierHasChanges()
                ? 'cursor-not-allowed bg-blue-400 '
                : 'bg-primary hover:bg-opacity-90 ') +
              'rounded py-2 px-6 font-medium text-gray'
            }
            type="submit"
            disabled={isSubmitting || !supplierHasChanges()}
          >
            {isSubmitting ? (
              <ClipLoader color="#ffffff" size={23} />
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditSupplier;
import React, { useEffect, useState } from 'react';
import Select, { SingleValue } from 'react-select';
import { IRowNode } from '@ag-grid-community/core';
import CreatableSelect from 'react-select/creatable';
import ClipLoader from 'react-spinners/ClipLoader';
import { useAlert } from '../../../contexts/AlertContext';
import { useClientOrders } from '../../../contexts/ClientOrdersContext';
import {
  customSelectStyles,
} from '../../../utils/form';
import { useForm, Controller, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { schema, ClientSchema } from './AddClient';
import { ClientProps } from './Client';
import { findCountryAndSetCitiesForClient } from './utils';
import { api } from '../../../api/axios';
import { useDispatch } from 'react-redux';
import { setClientOrders } from '../../../store/slices/clientOrdersSlice';
import { AppDispatch } from '../../../store/store';
import toast from 'react-hot-toast';

interface EditClientProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  client: ClientProps;
  setClient?: React.Dispatch<React.SetStateAction<ClientProps | null>>;
  rowNode?: IRowNode<ClientProps>;
  setRowData: React.Dispatch<React.SetStateAction<ClientProps[]>>;
}

const EditClient = ({
  open,
  setOpen,
  client,
  setClient,
  rowNode,
  setRowData,
}: EditClientProps) => {
  const { isDarkMode, setAlert } = useAlert();
  const dispatch = useDispatch<AppDispatch>();
  const { clients, countries, acqSources } = useClientOrders();
  const [cityOptions, setCityOptions] = useState<
    { value: string; label: string }[]
  >([]);
  const [initialValues, setInitialValues] = useState<ClientSchema | null>(null);
  const {
    register,
    handleSubmit,
    control,
    setValue,
    setError,
    watch,
    reset,
    formState: { errors, isSubmitting, dirtyFields },
  } = useForm<ClientSchema>({
    resolver: zodResolver(schema),
  });

  const currentValues = watch();

  const sexOptions = [
    { value: 'Male', label: 'Male' },
    { value: 'Female', label: 'Female' },
  ];

  const countryOptions = countries.map((country) => ({
    value: country.name,
    label: country.name,
  }));

  const acqSourceOptions = acqSources.map((source) => ({
    value: source,
    label: source,
  }));

  const handleCountryChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    if (option) {
      onChange(option.value);
      findCountryAndSetCitiesForClient(
        option.value,
        countries,
        setCityOptions,
        currentValues,
        setValue,
      );
    } else {
      onChange(null);
      setCityOptions([]);
      setValue('location.city', null, { shouldDirty: true });
    }
  };

  const onSubmit: SubmitHandler<ClientSchema> = async (data) => {
    try {
      const res = await api.put(`/client_orders/clients/${client.id}/`, data);
      const clientUpdate = res.data;
      if (setClient) {
        setClient(clientUpdate);
        toast.success('Client has been successfully updated!', {
          duration: 5000,
        });
      }
      rowNode?.setData(res.data);
      setRowData((prev) =>
        prev.map((client) =>
          client.id === clientUpdate.id ? clientUpdate : client,
        ),
      );
      setAlert({
        type: 'success',
        title: 'Client Updated',
        description: `Client ${clientUpdate.name} has been successfully updated.`,
      });
      dispatch((dispatch, getState) => {
        const { clientOrders } = getState();
        dispatch(
          setClientOrders({
            ...clientOrders,
            clients: {
              count: clients.count,
              names: clients.names.map((name) =>
                name === client.name ? clientUpdate.name : name,
              ),
            },
          }),
        );
      });
      setOpen(false);
    } catch (error: any) {
      console.log('Error during form submission:', error);
      if (error.response && error.response.status === 400) {
        const errorData = error.response.data;
        (Object.keys(errorData) as Array<keyof ClientSchema>).forEach(
          (field) => {
            if (field === 'location') {
              const locationErrors = errorData[field];
              Object.keys(locationErrors).forEach((prop) => {
                const locationProp = prop as keyof ClientSchema['location'];
                setError(`${field}.${locationProp}`, {
                  message: locationErrors[locationProp],
                });
              });
            } else {
              setError(field, { message: errorData[field] });
            }
          },
        );
      } else {
        setError('root', {
          message: 'Something went wrong. Please try again later.',
        });
      }
    }
  };

  const clientHasChanges = () => {
    if (!initialValues || !currentValues) return false;
    return (Object.keys(dirtyFields) as Array<keyof ClientSchema>).some(
      (key) => {
        if (key === 'location') {
          return (
            JSON.stringify(initialValues[key]) !==
            JSON.stringify(currentValues[key])
          );
        } else if (key === 'age') {
          return initialValues[key] !== Number(currentValues[key]);
        }
        return initialValues[key] !== currentValues[key];
      },
    );
  };

  useEffect(() => {
    const loadData = () => {
      console.log(client);
      const { name, phone_number, email, age, sex, source, location } = client;

      if (location && location.country) {
        findCountryAndSetCitiesForClient(
          location.country,
          countries,
          setCityOptions,
          currentValues,
          setValue,
        );
      }

      const formData = {
        name,
        phone_number,
        email,
        age,
        sex,
        source,
        location,
      };

      setInitialValues(formData);
      reset(formData);
    };

    if (open) loadData();
  }, [open, reset, client]);

  useEffect(() => {
    clientHasChanges();
  }, [initialValues, currentValues]);

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Edit Client:{' '}
          {client.name.length > 28
            ? client.name.substring(0, 28) + '...'
            : client.name}
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
            {/* Age & Sex */}
            <div className="mb-4 flex flex-col gap-5.5 sm:flex-row">
              {/* Age */}
              <div className="w-full sm:w-1/2">
                <label
                  className="mb-2 block text-sm font-medium text-black dark:text-white"
                  htmlFor="age"
                >
                  Age
                </label>
                <input
                  className="w-full rounded border border-stroke bg-gray py-2 pl-3 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                  type="number"
                  placeholder="e.g. 20"
                  {...register('age', {
                    valueAsNumber: true,
                  })}
                />
                {errors.age && (
                  <p className="text-red-500 font-medium text-sm italic mt-2">
                    {errors.age.message}
                  </p>
                )}
              </div>

              {/* Sex */}
              <div className="w-full sm:w-1/2">
                <label
                  className="mb-2 block text-sm font-medium text-black dark:text-white"
                  htmlFor="sex"
                >
                  Sex
                </label>
                {open && (
                  <Controller
                    name="sex"
                    control={control}
                    rules={{ required: false }}
                    render={({ field: { value, onChange, ...field } }) => (
                      <Select
                        {...field}
                        isClearable
                        value={
                          value
                            ? sexOptions.find(
                                (option) => option.value === value,
                              )
                            : null
                        }
                        onChange={(option) => onChange(option?.value || null)}
                        options={sexOptions}
                        styles={customSelectStyles(isDarkMode)}
                      />
                    )}
                  />
                )}
                {errors.sex && (
                  <p className="text-red-500 font-medium text-sm italic mt-2">
                    {errors.sex.message}
                  </p>
                )}
              </div>
            </div>
            {/* Source of Acquisition */}
            <div className="mb-4">
              <label
                className="mb-2 block text-sm font-medium text-black dark:text-white"
                htmlFor="source"
              >
                Source of Acquisition
              </label>
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
                          ? acqSourceOptions.find(
                              (option) => option.value === value,
                            )
                          : null
                      }
                      onChange={(option) => onChange(option?.value || null)}
                      options={acqSourceOptions}
                      styles={customSelectStyles(isDarkMode)}
                      placeholder={<span>Create or Select...</span>}
                    />
                  )}
                />
              )}
              {errors.source && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.source.message}
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
              (!clientHasChanges()
                ? 'cursor-not-allowed bg-blue-400 '
                : 'bg-primary hover:bg-opacity-90 ') +
              'rounded py-2 px-6 font-medium text-gray'
            }
            type="submit"
            disabled={isSubmitting || !clientHasChanges()}
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

export default EditClient;

import { SubmitHandler, useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import Select from 'react-select';
import { zodResolver } from '@hookform/resolvers/zod';
import React from 'react';
import ClipLoader from 'react-spinners/ClipLoader';
import { requiredStringField, customSelectStyles } from '../../../utils/form';
import { useAlert } from '../../../contexts/AlertContext';
import { ClientProps } from './Clients';

export const schema = z.object({
  name: requiredStringField('Name'),
  phone_number: z.string(),
  email: z.string().email().optional(),
  age: z.number(),
  sex: z.string(),
  location: z.object({
    country: z.string(),
    region: z.string(),
    city: z.string(),
    street_address: z.string(),
  }),
  source: z.string(),
});

export type ClientSchema = z.infer<typeof schema>;

interface AddClientProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setRowData: React.Dispatch<React.SetStateAction<ClientProps[]>>;
}

const AddClient = ({ open, setOpen, setRowData }: AddClientProps) => {
  const { isDarkMode } = useAlert();
  const sexOptions = [
    { value: 'Male', label: 'Male' },
    { value: 'Female', label: 'Female' },
  ];
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<ClientSchema>({
    resolver: zodResolver(schema),
  });

  const onSubmit: SubmitHandler<ClientSchema> = (data) => {
    console.log(data);
  };

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {/* Form Header */}
      <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
        <h3 className="font-semibold text-lg text-black dark:text-white">
          Create New Client
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
                placeholder="Enter item name"
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
                placeholder="Enter item name"
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
                placeholder="Enter item name"
                {...register('phone_number')}
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
                  {...register('age')}
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
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="Enter item name"
                {...register('source')}
              />
              {errors.source && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.source.message}
                </p>
              )}
            </div>
            {/* Location */}
            <div className="mb-4">
              <label
                className="mb-2 block text-sm font-medium text-black dark:text-white"
                htmlFor="location"
              >
                Location
              </label>
              <input
                className="w-full rounded border border-stroke bg-gray py-2 pl-3 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                type="text"
                placeholder="Enter item name"
                {...register('location')}
              />
              {errors.location && (
                <p className="text-red-500 font-medium text-sm italic mt-2">
                  {errors.location.message}
                </p>
              )}
            </div>
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
              'Add new client'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AddClient;

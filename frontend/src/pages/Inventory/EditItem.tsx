import ClipLoader from 'react-spinners/ClipLoader';
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  SubmitHandler,
  useForm,
  useFieldArray,
  Controller,
} from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import CreatableSelect from 'react-select/creatable';
import ProductionQuantityLimitsOutlinedIcon from '@mui/icons-material/ProductionQuantityLimitsOutlined';
import LocalOfferOutlinedIcon from '@mui/icons-material/LocalOfferOutlined';
import EditNoteOutlinedIcon from '@mui/icons-material/EditNoteOutlined';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import Breadcrumb from '../../components/Breadcrumbs/Breadcrumb';
import Loader from '../../common/Loader';
import { customSelectStyles } from '../../utils/form';
import Default from '../../images/item/default.jpg';
import { api } from '../../api/axios';
import { useInventory } from '../../contexts/InventoryContext';
import { useAlert } from '../../contexts/AlertContext';
import { schema } from './AddItem';
import { ItemSchema } from './AddItem';

const EditItem = () => {
  const { id } = useParams();
  const { isDarkMode } = useAlert();
  const {
    register,
    handleSubmit,
    setError,
    setValue,
    clearErrors,
    control,
    reset,
    watch,
    formState: { errors, dirtyFields, isSubmitting },
  } = useForm<ItemSchema>({
    resolver: zodResolver(schema),
  });

  const { fields, append, remove } = useFieldArray({
    name: 'variants',
    control,
  });

  const { loading, categories, suppliers, variants } = useInventory();
  const categoryOptions = categories.names.map((name) => ({
    value: name,
    label: name,
  }));
  const supplierOptions = suppliers.names.map((name) => ({
    value: name,
    label: name,
  }));

  const variantsOptions = variants.map((name) => ({
    value: name,
    label: name,
  }));

  const [itemPicture, setItemPicture] = useState<string | null>(null);
  const [itemLoading, setItemLoading] = useState<boolean>(false);
  const [pictureModified, setPictureModified] = useState<boolean>(false);
  const [hasVariants, setHasVariants] = useState<boolean>(false);
  const [previewPictureUrl, setPreviewPictureUrl] = useState<string | null>(
    null,
  );
  const [initialValues, setInitialValues] = useState(null);
  const currentValues = watch();
  const currentTextValues = { ...currentValues };
  delete currentTextValues.picture;

  const handleFileClear = () => {
    setValue('picture', undefined);
    clearErrors('picture');
    setPreviewPictureUrl(null);
    setItemPicture(null);
    setPictureModified(true);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setItemPicture(null);
    setPictureModified(true);
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      // Checking file type (JPEG or PNG)
      if (!['image/jpeg', 'image/png'].includes(file.type)) {
        setError('picture', {
          type: 'manual',
          message: 'Only JPEG or PNG files are allowed',
        });
        setValue('picture', undefined);
      } else if (file.size > 2000000) {
        // Checking file size (2MB)
        setError('picture', {
          type: 'manual',
          message: 'File size must be less than or equal to 2MB',
        });
        setValue('picture', undefined);
      } else {
        // Clearing previous errors
        clearErrors('picture');
        setPreviewPictureUrl(URL.createObjectURL(file));
      }
    } else {
      // clearing the file and errors if no file is selected,
      setValue('picture', undefined);
      clearErrors('picture');
    }
  };

  const variantToggleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setHasVariants(true);
      append({ name: '', options: '' });
    } else {
      setHasVariants(false);
      remove();
    }
  };

  const removeVariantFields = (index: number) => {
    if (index === 0 && fields.length <= 1) {
      setHasVariants(false);
      remove();
    } else {
      remove(index);
    }
  };

  const onSubmit: SubmitHandler<ItemSchema> = async (data) => {
    const formData = new FormData();
    formData.append('name', data.name);
    formData.append('price', data.price.toString());
    formData.append('quantity', data.quantity.toString());
    if (data.category) {
      formData.append('category', data.category);
    }
    if (data.supplier) {
      formData.append('supplier', data.supplier);
    }
    formData.append('variants', JSON.stringify(data.variants));
    if (data.picture && data.picture?.length > 0) {
      formData.append('picture', data.picture[0]);
    }
    if (!data.picture && !itemPicture) {
      formData.append('empty_picture', '');
    }
    try {
      const res = await api.put(`/inventory/items/${id}/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log(res.data);
    } catch (error: any) {
      console.log('Error during form submission:', error);
      if (error.response && error.response.status === 400) {
        (Object.keys(error.response.data) as Array<keyof ItemSchema>).forEach(
          (field) => {
            setError(field, { message: error.response.data[field] });
          },
        );
      } else {
        setError('root', {
          message: 'Something went wrong. Please try again later.',
        });
      }
    }
  };

  useEffect(() => {
    //  Loading Item's data
    async function loadData() {
      setItemLoading(true);
      try {
        const res = await api.get(`/inventory/items/${id}/`);
        if (res.data.variants) setHasVariants(true);
        if (res.data.picture) setItemPicture(res.data.picture);
        const manipulatedData = {
          ...res.data,
          variants: res.data.variants
            ? res.data.variants.map(
                (variant: { name: string; options: string[] }) => ({
                  name: variant.name,
                  options: variant.options.join(', '),
                }),
              )
            : [],
        };
        delete manipulatedData.picture;
        setInitialValues(manipulatedData);
        reset(manipulatedData);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('root', {
          message: 'Something went wrong. Please try again later.',
        });
      } finally {
        setItemLoading(false);
      }
    }

    loadData();
  }, [id, reset]);

  const itemHasChanges = () => {
    if (pictureModified) return true;
    if (!initialValues || !currentTextValues) return false;
    return (Object.keys(dirtyFields) as Array<keyof ItemSchema>).some((key) => {
      // Deep comparison for variants
      if (key === 'variants') {
        return (
          JSON.stringify(initialValues[key]) !==
          JSON.stringify(currentTextValues[key])
        );
      }
      // Regular comparison for other fields
      return initialValues[key] !== currentTextValues[key];
    });
  };

  useEffect(() => {
    return () => {
      if (previewPictureUrl) {
        URL.revokeObjectURL(previewPictureUrl);
      }
    };
  }, [previewPictureUrl]);

  useEffect(() => {
    itemHasChanges();
  }, [initialValues, currentValues, pictureModified]);

  return (
    <>
      <div className="mx-auto max-w-3xl">
        <Breadcrumb main="Inventory" pageName="Edit Item" />
        <div className="col-span-5 xl:col-span-3">
          {' '}
          {loading || itemLoading ? (
            <Loader />
          ) : (
            <div className="w-full border border-stroke bg-white shadow-default dark:border-strokedark dark:bg-boxdark">
              <div className="border-b border-stroke py-4 px-7 dark:border-strokedark">
                <h3 className="font-medium text-black dark:text-white">
                  Item Information
                </h3>
              </div>
              <div className="p-7">
                <form onSubmit={handleSubmit(onSubmit)}>
                  {/* Name */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="name"
                    >
                      Name*
                    </label>
                    <div className="relative">
                      <span className="absolute left-3.5 top-3">
                        <EditNoteOutlinedIcon />
                      </span>
                      <input
                        className="w-full rounded border border-stroke bg-gray py-3 pl-11.5 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                        type="text"
                        {...register('name')}
                      />
                    </div>
                    {errors.name && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.name.message}
                      </p>
                    )}
                  </div>

                  {/* Price & Quantity */}
                  <div className="mb-5.5 flex flex-col gap-5.5 sm:flex-row">
                    {/* Price */}
                    <div className="w-full sm:w-1/2">
                      <label
                        className="mb-3 block text-sm font-medium text-black dark:text-white"
                        htmlFor="price"
                      >
                        Price*
                      </label>
                      <div className="relative">
                        <span className="absolute left-3.5 top-3">
                          <LocalOfferOutlinedIcon />
                        </span>
                        <input
                          className="w-full rounded border border-stroke bg-gray py-3 pl-11.5 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                          type="number"
                          step="0.01"
                          {...register('price')}
                        />
                      </div>
                      {errors.price && (
                        <p className="text-red-500 font-medium text-sm italic mt-2">
                          {errors.price.message}
                        </p>
                      )}
                    </div>

                    {/* Quantity */}
                    <div className="w-full sm:w-1/2">
                      <label
                        className="mb-3 block text-sm font-medium text-black dark:text-white"
                        htmlFor="quantity"
                      >
                        Quantity*
                      </label>
                      <div className="relative">
                        <span className="absolute left-3.5 top-3">
                          <ProductionQuantityLimitsOutlinedIcon />
                        </span>
                        <input
                          className="w-full rounded border border-stroke bg-gray pl-11.5 py-3 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                          type="number"
                          {...register('quantity')}
                        />
                      </div>
                      {errors.quantity && (
                        <p className="text-red-500 font-medium text-sm italic mt-2">
                          {errors.quantity.message}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Category */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="category"
                    >
                      Category
                    </label>
                    <div className="relative">
                      <Controller
                        name="category"
                        control={control}
                        rules={{ required: false }}
                        render={({ field: { value, onChange, ...field } }) => (
                          <CreatableSelect
                            {...field}
                            isClearable
                            value={
                              value
                                ? categoryOptions.find(
                                    (option) => option.value === value,
                                  )
                                : null
                            }
                            onChange={(option) =>
                              onChange(option?.value || null)
                            }
                            options={categoryOptions}
                            styles={customSelectStyles(isDarkMode)}
                            placeholder={<div>Create or Select...</div>}
                          />
                        )}
                      />
                    </div>
                    {errors.category && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.category.message}
                      </p>
                    )}
                  </div>

                  {/* Supplier */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-sm font-medium text-black dark:text-white"
                      htmlFor="supplier"
                    >
                      Supplier
                    </label>
                    <div className="relative">
                      <Controller
                        name="supplier"
                        control={control}
                        rules={{ required: false }}
                        render={({ field: { value, onChange, ...field } }) => (
                          <CreatableSelect
                            {...field}
                            isClearable
                            value={
                              value
                                ? supplierOptions.find(
                                    (option) => option.value === value,
                                  )
                                : null
                            }
                            onChange={(option) =>
                              onChange(option?.value || null)
                            }
                            options={supplierOptions}
                            styles={customSelectStyles(isDarkMode)}
                            placeholder={<div>Create or Select...</div>}
                          />
                        )}
                      />
                    </div>
                    {errors.supplier && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.supplier.message}
                      </p>
                    )}
                  </div>

                  {/* Variants */}
                  <div
                    className={
                      'mb-2.5 border-t ' +
                      (!hasVariants && 'border-b ') +
                      ' border-stroke dark:border-slate-600'
                    }
                  >
                    <div className="mt-3">
                      <label className="inline-flex items-center cursor-pointer mb-2">
                        <span className="mr-2 mb-1 text-base font-medium text-black dark:text-white">
                          This item has variants
                        </span>
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={hasVariants}
                          onChange={variantToggleChange}
                        />
                        <div className="relative w-11 h-6 bg-slate-200 peer-checked:bg-blue-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600"></div>
                      </label>
                    </div>
                    {/* Attributes and Options */}
                    {hasVariants && (
                      <div>
                        {fields.map((field, index) => (
                          <div
                            className={
                              'mb-1.5' +
                              (index >= fields.length - 1
                                ? ''
                                : ' border-b border-stroke dark:border-slate-600')
                            }
                            key={field.id}
                          >
                            {/* Attribute */}
                            <div className="mt-2 mb-3.5">
                              <label
                                className="mb-2 block text-sm font-medium text-black dark:text-white"
                                htmlFor="variant-attribute"
                              >
                                Attribute
                              </label>

                              <div className="flex items-center">
                                <Controller
                                  name={`variants.${index}.name`}
                                  control={control}
                                  rules={{ required: false }}
                                  render={({
                                    field: { value, onChange, ...field },
                                  }) => (
                                    <CreatableSelect
                                      {...field}
                                      isClearable
                                      value={
                                        value
                                          ? variantsOptions.find(
                                              (option) =>
                                                option.value === value,
                                            )
                                          : null
                                      }
                                      onChange={(option) =>
                                        onChange(option?.value || '')
                                      }
                                      options={variantsOptions}
                                      styles={customSelectStyles(isDarkMode)}
                                      placeholder={
                                        <div>Create or Select...</div>
                                      }
                                      className="w-full"
                                    />
                                  )}
                                />

                                <button
                                  type="button"
                                  className="ml-2 border border-slate-300 dark:border-slate-600 text-slate-400 py-2 px-2.5 rounded"
                                  onClick={() => removeVariantFields(index)}
                                >
                                  <DeleteOutlinedIcon />
                                </button>
                              </div>
                              {errors.variants?.[index]?.name && (
                                <p className="text-red-500 font-medium text-sm italic mt-1">
                                  {errors.variants[index].name.message}
                                </p>
                              )}
                            </div>
                            {/* Options */}
                            <div className="mb-4.5">
                              <label
                                className="mb-2 block text-sm font-medium text-black dark:text-white"
                                htmlFor="variant-options"
                              >
                                Options
                              </label>

                              <input
                                className="w-full rounded border border-stroke bg-gray py-2 pl-4.5 pr-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                                type="text"
                                placeholder="Type options separated by comma."
                                {...register(
                                  `variants.${index}.options` as const,
                                )}
                              />
                              {errors.variants?.[index]?.options && (
                                <p className="text-red-500 font-medium text-sm italic mt-1">
                                  {errors.variants[index].options.message}
                                </p>
                              )}
                            </div>
                          </div>
                        ))}
                        {/* Add Attributes Button */}
                        <button
                          type="button"
                          className="mb-3 text-sm inline-flex items-center justify-center rounded-md bg-meta-3 py-2 px-2 text-center font-medium text-white hover:bg-opacity-90 lg:px-3 xl:px-2"
                          onClick={() => append({ name: '', options: '' })}
                        >
                          <AddCircleOutlinedIcon
                            sx={{ marginRight: '0.2em' }}
                          />
                          Add Attribute
                        </button>
                      </div>
                    )}
                  </div>
                  {/* Photo */}
                  <div className="mb-5.5">
                    <label
                      className="mb-3 block text-base font-medium text-black dark:text-white border-b border-stroke py-3 dark:border-strokedark"
                      htmlFor="bio"
                    >
                      Picture
                    </label>
                    <div className="mb-3 flex items-center gap-3">
                      <div className="h-14 w-14 rounded-full">
                        {previewPictureUrl ? (
                          <img
                            src={previewPictureUrl}
                            className="w-full h-full object-cover rounded-full"
                            alt="User"
                          />
                        ) : (
                          <img
                            src={itemPicture || Default}
                            className="w-full h-full object-cover rounded-full"
                            alt="User"
                          />
                        )}
                      </div>
                      <div>
                        <span className="mb-1.5 text-black dark:text-white">
                          {previewPictureUrl || itemPicture
                            ? 'Edit Picture'
                            : 'Select Picture'}
                        </span>
                        <span className="mt-2 flex gap-2.5">
                          {(previewPictureUrl || itemPicture) && (
                            <button
                              onClick={handleFileClear}
                              type="button"
                              className="bg-red-500 hover:bg-red-700 text-white text-sm font-bold py-1 px-3 rounded"
                            >
                              Delete
                            </button>
                          )}
                          <input
                            type="file"
                            {...register('picture')}
                            onChange={handleFileChange}
                            className="text-sm font-bold rounded
                                    cursor-pointer
                                    file:me-2 file:py-1 file:px-4
                                    file:cursor-pointer
                                    file:border-0
                                    file:bg-slate-500 file:text-white
                                    hover:file:bg-slate-600
                                    dark:file:bg-slate-500
                                    dark:hover:file:bg-slate-600"
                          />
                        </span>
                      </div>
                    </div>
                    {errors.picture && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.picture.message}
                      </p>
                    )}
                  </div>
                  <div className="text-center mb-3">
                    {errors.root && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.root.message}
                      </p>
                    )}
                  </div>
                  <div className="flex justify-end gap-4.5">
                    <button
                      className={
                        'flex justify-center ' +
                        (!itemHasChanges()
                          ? 'cursor-not-allowed bg-blue-400 '
                          : 'bg-primary hover:bg-opacity-90 ') +
                        'rounded py-2 px-6 font-medium text-gray'
                      }
                      type="submit"
                      disabled={!itemHasChanges()}
                    >
                      {isSubmitting ? (
                        <ClipLoader color="#ffffff" size={23} />
                      ) : (
                        'Save'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default EditItem;

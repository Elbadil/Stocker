import ClipLoader from 'react-spinners/ClipLoader';
import React, { useState, useEffect } from 'react';
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
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';
import DeleteOutlinedIcon from '@mui/icons-material/DeleteOutlined';
import toast from 'react-hot-toast';
import Loader from '../../common/Loader';
import {
  requiredStringField,
  requiredPositiveNumberField,
  nonBlankField,
  customSelectStyles,
  selectOptionsFromObjects,
  selectOptionsFromStrings,
} from '../../utils/form';
import Default from '../../images/item/default.jpg';
import { api } from '../../api/axios';
import { useInventory } from '../../contexts/InventoryContext';
import { setInventory } from '../../store/slices/inventorySlice';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store/store';
import { useAlert } from '../../contexts/AlertContext';
import { ItemProps } from './Item';
import { getUpdatedInventory } from './utils';
import AddSupplier from '../SupplierOrders/Suppliers/AddSupplier';
import ModalOverlay from '../../components/ModalOverlay';
import { useSupplierOrders } from '../../contexts/SupplierOrdersContext';
import { setSupplierOrders } from '../../store/slices/supplierOrdersSlice';

export const schema = z.object({
  name: requiredStringField('Name'),
  price: requiredPositiveNumberField('Price'),
  quantity: requiredPositiveNumberField('Quantity'),
  category: z.string().optional().nullable(),
  supplier: z.string().optional().nullable(),
  picture: z.instanceof(FileList).optional(),
  variants: z
    .array(
      z.object({
        name: nonBlankField('Attribute'),
        options: nonBlankField('Options').transform((val) =>
          val.length > 0 ? val.split(',').map((option) => option.trim()) : val,
        ),
      }),
    )
    .superRefine((variants, ctx) => {
      // Collect all variant names
      const varAttrNames = variants.map((attribute) => attribute.name);
      const nameCount: { [key: string]: number } = {};
      varAttrNames.forEach((name: string, index: number) => {
        const nameLower = name.toLowerCase().trim();
        nameCount[nameLower] = (nameCount[nameLower] || 0) + 1;
        if (nameCount[nameLower] > 1) {
          ctx.addIssue({
            code: 'custom',
            path: [index, 'name'], // Point to the specific field in the array
            message: `Attribute "${name.trim()}" has already been selected.`,
          });
        }
      });
    }),
});

export type ItemSchema = z.infer<typeof schema>;

interface AddItemProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setRowData?: React.Dispatch<React.SetStateAction<ItemProps[]>>;
  supplier?: string;
}

const AddItem = ({ open, setOpen, setRowData, supplier }: AddItemProps) => {
  const dispatch = useDispatch<AppDispatch>();
  const { setAlert, isDarkMode } = useAlert();
  const [openAddSupplier, setOpenAddSupplier] = useState<boolean>(false);

  const {
    register,
    handleSubmit,
    setError,
    setValue,
    clearErrors,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ItemSchema>({
    resolver: zodResolver(schema),
  });

  const { fields, append, remove } = useFieldArray({
    name: 'variants',
    control,
  });

  const {
    loading,
    items,
    categories,
    variants,
    totalItems,
    totalQuantity,
    totalValue,
  } = useInventory();

  const { suppliers, newSupplier } = useSupplierOrders();

  const categoryOptions = selectOptionsFromStrings(categories.names);
  const supplierOptions = selectOptionsFromObjects(suppliers);
  const variantsOptions = selectOptionsFromStrings(variants);

  const [hasVariants, setHasVariants] = useState<boolean>(false);
  const [previewPictureUrl, setPreviewPictureUrl] = useState<string | null>(
    null,
  );

  const handleSupplierChange = (
    onChange: (value: string | null) => void,
    option: SingleValue<{ value: string; label: string }>,
  ) => {
    if (newSupplier) {
      dispatch((dispatch, getState) => {
        const { supplierOrders } = getState();
        dispatch(
          setSupplierOrders({
            ...supplierOrders,
            newSupplier: null,
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

  const handleFileClear = () => {
    setValue('picture', undefined);
    clearErrors('picture');
    setPreviewPictureUrl(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
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
    if (index === 0) {
      setHasVariants(false);
      remove();
    } else {
      remove(index);
    }
  };

  const updateSupplierItemState = (newItem: ItemProps) => {
    const { name, quantity, price } = newItem;

    dispatch((dispatch, getState) => {
      const { supplierOrders, inventory } = getState();
      const updatedSuppliers = suppliers.map((supplier) =>
        supplier.name === newItem.supplier
          ? {
              ...supplier,
              item_names: [...supplier.item_names, newItem.name],
            }
          : supplier,
      );

      dispatch(
        setSupplierOrders({
          ...supplierOrders,
          suppliers: updatedSuppliers,
          newOrderedItem: {
            item: name,
            ordered_quantity: quantity,
            ordered_price: price,
          },
        }),
      );
    });
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
    if (data.variants.length > 0) {
      formData.append('variants', JSON.stringify(data.variants));
    }
    if (data.picture && data.picture?.length > 0) {
      formData.append('picture', data.picture[0]);
    }
    if (supplier) {
      formData.append('supplier', supplier);
      formData.append('in_inventory', 'false');
    } else {
      formData.append('in_inventory', 'true');
    }
    try {
      const res = await api.post('/inventory/items/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      const newItem = res.data;
      const inventoryPlusNewItem = getUpdatedInventory(
        'add',
        items,
        newItem,
        categories.names,
        suppliers.map((supplier) => supplier.name),
        variants,
        totalItems,
        totalValue,
        totalQuantity,
      );

      dispatch((dispatch, getState) => {
        const { inventory } = getState();
        dispatch(
          setInventory({
            ...inventory,
            ...inventoryPlusNewItem,
          }),
        );
      });

      if (supplier) {
        updateSupplierItemState(newItem);
      }

      if (setRowData) {
        setAlert({
          type: 'success',
          title: 'New item added',
          description: `Item ${newItem.name} has been successfully added to your inventory.`,
        });
        setRowData((prev) => [newItem, ...prev]);
      } else {
        toast.success(`Item ${newItem.name} has been successfully added.`, {
          duration: 5000,
        });
      }
      setOpen(false);
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
    return () => {
      if (previewPictureUrl) {
        URL.revokeObjectURL(previewPictureUrl);
      }
    };
  }, [previewPictureUrl]);

  useEffect(() => {
    if (open) {
      reset();
      setHasVariants(false);
      setValue('variants', []);
      setValue('category', null);
      setValue('supplier', null);
      setPreviewPictureUrl(null);
    }
  }, [open]);

  useEffect(() => {
    if (newSupplier) setValue('supplier', newSupplier);
  }, [newSupplier]);

  return (
    <div className="mx-auto max-w-md border rounded-md border-stroke bg-white shadow-default dark:border-slate-700 dark:bg-boxdark">
      {loading ? (
        <Loader />
      ) : (
        <>
          {/* Form Header */}
          <div className="flex justify-between items-center border-b rounded-t-md border-stroke bg-slate-100 py-4 px-6 dark:border-strokedark dark:bg-slate-700">
            <h3 className="font-semibold text-lg text-black dark:text-white">
              Create New Item
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
                {supplier && (
                  <div className="mb-4 text-sm text-black dark:text-slate-300">
                    <div className="mb-2">
                      * The item will be created with '{supplier}' as its
                      associated supplier.
                    </div>
                    <div>
                      * The item will not be added to the inventory until the
                      supplier order is marked as delivered.
                    </div>
                  </div>
                )}
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

                {/* Price & Quantity */}
                <div className="mb-4 flex flex-col gap-5.5 sm:flex-row">
                  {/* Quantity */}
                  <div className="w-full sm:w-1/2">
                    <label
                      className="mb-2 block text-sm font-medium text-black dark:text-white"
                      htmlFor="quantity"
                    >
                      Quantity*
                    </label>
                    <input
                      className="w-full rounded border border-stroke bg-gray pl-3 py-2 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                      type="number"
                      placeholder="e.g. 1"
                      {...register('quantity')}
                    />
                    {errors.quantity && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.quantity.message}
                      </p>
                    )}
                  </div>

                  {/* Price */}
                  <div className="w-full sm:w-1/2">
                    <label
                      className="mb-2 block text-sm font-medium text-black dark:text-white"
                      htmlFor="price"
                    >
                      Price*
                    </label>
                    <input
                      className="w-full rounded border border-stroke bg-gray py-2 pl-3 px-4.5 text-black focus:border-primary focus-visible:outline-none dark:border-strokedark dark:bg-meta-4 dark:text-white dark:focus:border-primary"
                      type="number"
                      step="0.01"
                      placeholder="e.g. 19.99"
                      {...register('price')}
                    />
                    {errors.price && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.price.message}
                      </p>
                    )}
                  </div>
                </div>

                {/* Category */}
                <div className="mb-4">
                  <label
                    className="mb-2 block text-sm font-medium text-black dark:text-white"
                    htmlFor="category"
                  >
                    Category
                  </label>
                  {open && (
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
                          onChange={(option) => onChange(option?.value || null)}
                          options={categoryOptions}
                          styles={customSelectStyles(isDarkMode)}
                          placeholder={<div>Create or Select...</div>}
                        />
                      )}
                    />
                  )}

                  {errors.category && (
                    <p className="text-red-500 font-medium text-sm italic mt-2">
                      {errors.category.message}
                    </p>
                  )}
                </div>

                {/* Supplier */}
                {!supplier && (
                  <div className="mb-4">
                    <div className="flex items-center gap-2.5 mb-2">
                      <label
                        className="block text-sm font-medium text-black dark:text-white"
                        htmlFor="supplier_name"
                      >
                        Supplier
                      </label>
                      <button
                        type="button"
                        onClick={() => setOpenAddSupplier(true)}
                        className="text-sm font-sm text-slate-400 hover:text-black dark:text-slate-400 dark:hover:text-white hover:underline"
                      >
                        new supplier?
                      </button>
                    </div>

                    {open && (
                      <Controller
                        name="supplier"
                        control={control}
                        rules={{ required: false }}
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

                    {errors.supplier && (
                      <p className="text-red-500 font-medium text-sm italic mt-2">
                        {errors.supplier.message}
                      </p>
                    )}
                  </div>
                )}

                {/* Variants */}
                <div
                  className={
                    'mb-1.5 border-t ' +
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
                                            (option) => option.value === value,
                                          )
                                        : null
                                    }
                                    onChange={(option) =>
                                      onChange(option?.value || '')
                                    }
                                    options={variantsOptions}
                                    styles={customSelectStyles(isDarkMode)}
                                    placeholder={<div>Create or Select...</div>}
                                    className="w-full"
                                  />
                                )}
                              />
                              {/* Delete Attribute Button */}
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
                        className="mb-1 text-sm inline-flex items-center justify-center rounded-md bg-meta-3 py-2 px-2 text-center font-medium text-white hover:bg-opacity-90 lg:px-3 xl:px-2"
                        onClick={() => append({ name: '', options: '' })}
                      >
                        <AddCircleOutlinedIcon sx={{ marginRight: '0.2em' }} />
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
                  <div className="mb-3 flex items-start gap-2">
                    <div className="h-14 w-14 rounded-full overflow-hidden mr-1">
                      {previewPictureUrl ? (
                        <img
                          src={previewPictureUrl}
                          className="w-full h-full object-cover"
                          alt="User"
                        />
                      ) : (
                        <img
                          src={Default}
                          className="w-full h-full object-cover"
                          alt="User"
                        />
                      )}
                    </div>
                    <div className="flex-1 overflow-hidden">
                      {/* Allow overflow for this div */}
                      <span className="mb-1.5 text-black dark:text-white whitespace-nowrap overflow-ellipsis overflow-hidden">
                        {previewPictureUrl ? 'Edit Picture' : 'Select Picture'}
                      </span>
                      <span className="mt-2 flex gap-2.5 overflow-hidden">
                        {previewPictureUrl && (
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
                          accept="image/*"
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
                  'Add new item'
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
        </>
      )}
    </div>
  );
};

export default AddItem;

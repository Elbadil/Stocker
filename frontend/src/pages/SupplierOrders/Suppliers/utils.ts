import { UseFormSetValue } from 'react-hook-form';
import { utils, writeFile } from 'xlsx';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import { SupplierSchema } from './AddSupplier';
import { SupplierProps } from './Supplier';
import { api } from '../../../api/axios';

export const findCountryAndSetCitiesForSupplier = (
  countryName: string,
  countries: { name: string; cities: string[] }[],
  setCityOptions: React.Dispatch<
    React.SetStateAction<{ value: string; label: string }[]>
  >,
  currentValues?: SupplierSchema,
  setValue?: UseFormSetValue<SupplierSchema>,
) => {
  const country = countries.find(
    (country: { name: string; cities: string[] }) =>
      country.name === countryName,
  );
  if (country) {
    const countryCities = country.cities.map((city) => ({
      value: city,
      label: city,
    }));
    setCityOptions(countryCities);
    if (currentValues && setValue) {
      const currentCity = currentValues?.location?.city ?? null;
      if (currentCity && !country.cities.includes(currentCity)) {
        setValue('location.city', null, { shouldDirty: true });
      }
    }
  }
};

export const supplierDataFlattener = (suppliers: SupplierProps[]) =>
  suppliers.map((supplier: SupplierProps) => ({
    ...supplier,
    location: supplier.location
      ? Object.values(supplier.location).reverse().join(', ')
      : null,
    updated_at: supplier.updated ? supplier.updated_at : null,
  }));

export const createSheetFile = (supplier: SupplierProps[]) => {
  const flattenedData = supplierDataFlattener(supplier);
  const ws = utils.json_to_sheet(flattenedData);
  /* create workbook and append worksheet */
  const wb = utils.book_new();
  const dateNow = format(new Date(), 'dd-MM-yyyy');
  utils.book_append_sheet(wb, ws, `Supplier ${dateNow}`);
  if (supplier.length > 1) {
    writeFile(wb, `${supplier[0].created_by}_suppliers_${dateNow}.xlsx`);
  } else {
    writeFile(wb, `supplier_${supplier[0].name}_${dateNow}.xlsx`);
  }
};

export const handleSupplierExport = (selectedRows?: SupplierProps[]) => {
  if (selectedRows) {
    createSheetFile(selectedRows);
  } else {
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

export const handleSupplierBulkExport = async () => {
  try {
    const res = await api.get('/supplier_orders/suppliers/');
    const suppliersData: SupplierProps[] = res.data;
    createSheetFile(suppliersData);
  } catch (err) {
    console.log('Error during bulk export', err);
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

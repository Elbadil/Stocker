import { UseFormSetError, UseFormSetValue } from 'react-hook-form';
import { SaleSchema, SoldItemSchema } from './AddSale';

export const findCountryAndSetCitiesForSale = (
  countryName: string,
  countries: { name: string; cities: string[] }[],
  setCityOptions: React.Dispatch<
    React.SetStateAction<{ value: string; label: string }[]>
  >,
  currentValues?: SaleSchema,
  setValue?: UseFormSetValue<SaleSchema>,
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
      const currentCity = currentValues?.shipping_address?.city ?? null;
      if (currentCity && !country.cities.includes(currentCity)) {
        setValue('shipping_address.city', null);
      }
    }
  }
};

export const handleSaleExport = () => {};
export const handleSalesBulkExport = () => {};

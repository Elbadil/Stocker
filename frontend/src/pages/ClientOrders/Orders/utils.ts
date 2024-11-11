import { UseFormSetValue } from 'react-hook-form';
import { OrderSchema } from './AddOrder';

export const findCountryAndSetCitiesForOrder = (
  countryName: string,
  countries: { name: string; cities: string[] }[],
  setCityOptions: React.Dispatch<
    React.SetStateAction<{ value: string; label: string }[]>
  >,
  currentValues?: OrderSchema,
  setValue?: UseFormSetValue<OrderSchema>,
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
        setValue('shipping_address.city', null, { shouldDirty: true });
      }
    }
  }
};

export const handleBulkExport = () => {};
export const handleOrderExport = () => {};
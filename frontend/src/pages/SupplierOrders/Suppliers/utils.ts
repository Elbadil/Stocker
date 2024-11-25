import { UseFormSetValue } from "react-hook-form";
import { SupplierSchema } from "./AddSupplier";

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

export const handleSupplierBulkExport = () => {};
export const handleSupplierExport = () => {};
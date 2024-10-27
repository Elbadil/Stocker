import React from 'react';
import { UseFormSetValue } from 'react-hook-form';
import { ClientSchema } from './AddClient';

export const findCountryAndSetCities = (
  countryName: string,
  countries: { name: string; cities: string[] }[],
  setCityOptions: React.Dispatch<
    React.SetStateAction<{ value: string; label: string }[]>
  >,
  currentValues: ClientSchema,
  setValue: UseFormSetValue<ClientSchema>,
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
    const currentCity = currentValues?.location?.city ?? null;
    if (currentCity && !country.cities.includes(currentCity)) {
      setValue('location.city', null, { shouldDirty: true });
    }
  }
};

export const handleClientExport = () => {};

export const handleBulkExport = () => {};

import React from 'react';
import { utils, writeFile } from 'xlsx';
import { format } from 'date-fns';
import { UseFormSetValue } from 'react-hook-form';
import { ClientSchema } from './AddClient';
import { api } from '../../../api/axios';
import { ClientProps } from './Client';
import toast from 'react-hot-toast';

export const findCountryAndSetCitiesForClient = (
  countryName: string,
  countries: { name: string; cities: string[] }[],
  setCityOptions: React.Dispatch<
    React.SetStateAction<{ value: string; label: string }[]>
  >,
  currentValues?: ClientSchema,
  setValue?: UseFormSetValue<ClientSchema>,
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

export const clientDataFlattener = (clients: ClientProps[]) =>
  clients.map((client: ClientProps) => ({
    ...client,
    location: client.location
      ? Object.values(client.location).reverse().join(', ')
      : null,
  }));

export const createSheetFile = (clients: ClientProps[]) => {
  const flattenedData = clientDataFlattener(clients);
  const ws = utils.json_to_sheet(flattenedData);
  /* create workbook and append worksheet */
  const wb = utils.book_new();
  const dateNow = format(new Date(), 'dd-MM-yyyy');
  utils.book_append_sheet(wb, ws, `Clients ${dateNow}`);
  if (clients.length > 1) {
    writeFile(wb, `${clients[0].created_by}_clients_${dateNow}.xlsx`);
  } else {
    writeFile(wb, `client_${clients[0].name}_${dateNow}.xlsx`);
  }
};

export const handleClientExport = (selectedRows?: ClientProps[]) => {
  if (selectedRows) {
    createSheetFile(selectedRows);
  } else {
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

export const handleBulkExport = async () => {
  try {
    const res = await api.get('/client_orders/clients/');
    const clientsData: ClientProps[] = res.data;
    createSheetFile(clientsData);
  } catch (err) {
    console.log('Error during bulk export', err);
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

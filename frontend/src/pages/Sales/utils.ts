import { UseFormSetValue } from 'react-hook-form';
import { SaleSchema } from './AddSale';
import { SaleProps } from './Sale';
import toast from 'react-hot-toast';
import { utils, writeFile } from 'xlsx';
import { format } from 'date-fns';
import { api } from '../../api/axios';

type FlattenedSoldItems = {
  [key: string]: string;
};


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

export const soldItemsDataFlattener = (sale: SaleProps) => {
  return sale.sold_items.reduce<FlattenedSoldItems>(
    (acc, soldItem, index) => {
      acc[`ordered_item-${index + 1}`] = `${soldItem.item} | Quantity: ${
        soldItem.sold_quantity
      } | Unit Price: ${soldItem.sold_price.toFixed(
        2,
      )} | Total Price: ${soldItem.total_price.toFixed(2)}`;
      return acc;
    },
    {},
  );
};

export const saleDataFlattener = (sales: SaleProps[]) =>
  sales.map((sale) => ({
    ...sale,
    ordered_items: `${sale.sold_items.length} unique ${
      sale.sold_items.length > 1 ? 'items' : 'item'
    }`,
    ...soldItemsDataFlattener(sale),
    net_profit: sale.net_profit.toFixed(2),
    shipping_address: sale.shipping_address
      ? Object.values(sale.shipping_address).reverse().join(', ')
      : null,
    updated_at: sale.updated ? sale.updated_at : null,
  }));

export const createSheetFile = (sales: SaleProps[]) => {
  const flattenedData = saleDataFlattener(sales);
  const ws = utils.json_to_sheet(flattenedData);
  /* create workbook and append worksheet */
  const wb = utils.book_new();
  const dateNow = format(new Date(), 'dd-MM-yyyy');
  utils.book_append_sheet(wb, ws, `Sales ${dateNow}`);
  if (sales.length > 1) {
    writeFile(wb, `${sales[0].created_by}_sales_${dateNow}.xlsx`);
  } else {
    writeFile(wb, `sale_${sales[0].reference_id}_${dateNow}.xlsx`);
  }
};

export const handleSaleExport = (selectedRows?: SaleProps[]) => {
  if (selectedRows) {
    createSheetFile(selectedRows);
  } else {
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

export const handleSaleBulkExport = async () => {
  try {
    const res = await api.get('/sales/');
    const orders = res.data;
    createSheetFile(orders);
  } catch (error: any) {
    console.log('Error during sales export', error);
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

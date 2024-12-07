import { UseFormSetValue } from 'react-hook-form';
import { utils, writeFile } from 'xlsx';
import { format } from 'date-fns';
import { ClientOrderSchema } from './AddClientOrder';
import { ClientOrderProps } from './ClientOrder';
import toast from 'react-hot-toast';
import { api } from '../../../api/axios';
import { dispatch } from '../../../store/store';
import { setClientOrders } from '../../../store/slices/clientOrdersSlice';

type FlattenedOrderedItems = {
  [key: string]: string;
};

export const findCountryAndSetCitiesForOrder = (
  countryName: string,
  countries: { name: string; cities: string[] }[],
  setCityOptions: React.Dispatch<
    React.SetStateAction<{ value: string; label: string }[]>
  >,
  currentValues?: ClientOrderSchema,
  setValue?: UseFormSetValue<ClientOrderSchema>,
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

export const resetNewClient = () => {
  dispatch((dispatch, getState) => {
    const { clientOrders } = getState();
    dispatch(
      setClientOrders({
        ...clientOrders,
        newClient: null,
      }),
    );
  });
};

export const orderedItemsDataFlattener = (order: ClientOrderProps) => {
  return order.ordered_items.reduce<FlattenedOrderedItems>(
    (acc, orderedItem, index) => {
      acc[`ordered_item-${index + 1}`] = `${orderedItem.item} | Quantity: ${
        orderedItem.ordered_quantity
      } | Unit Price: $${orderedItem.ordered_price.toFixed(
        2,
      )} | Total Price: $${orderedItem.total_price.toFixed(2)}`;
      return acc;
    },
    {},
  );
};

export const orderDataFlattener = (orders: ClientOrderProps[]) =>
  orders.map((order) => ({
    ...order,
    ordered_items: `${order.ordered_items.length} unique ${
      order.ordered_items.length > 1 ? 'items' : 'item'
    }`,
    ...orderedItemsDataFlattener(order),
    net_profit: order.net_profit.toFixed(2),
    shipping_address: order.shipping_address
      ? Object.values(order.shipping_address).reverse().join(', ')
      : null,
    updated_at: order.updated ? order.updated_at : null,
  }));

export const createSheetFile = (orders: ClientOrderProps[]) => {
  const flattenedData = orderDataFlattener(orders);
  const ws = utils.json_to_sheet(flattenedData);
  /* create workbook and append worksheet */
  const wb = utils.book_new();
  const dateNow = format(new Date(), 'dd-MM-yyyy');
  utils.book_append_sheet(wb, ws, `Clients ${dateNow}`);
  if (orders.length > 1) {
    writeFile(wb, `${orders[0].created_by}_orders_${dateNow}.xlsx`);
  } else {
    writeFile(wb, `order_${orders[0].reference_id}_${dateNow}.xlsx`);
  }
};

export const handleOrderExport = (selectedRows?: ClientOrderProps[]) => {
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
    const res = await api.get('/client_orders/orders/');
    const orders = res.data;
    createSheetFile(orders);
  } catch (error: any) {
    console.log('Error during orders export', error);
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

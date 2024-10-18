import { utils, writeFile } from 'xlsx';
import toast from 'react-hot-toast';
import { format } from 'date-fns';
import { ItemProps } from './Item';
import { api } from '../../api/axios';

export const getUpdatedInventory = (
  type: 'add' | 'update',
  newItemData: ItemProps,
  categories: string[],
  suppliers: string[],
  variants: string[],
  totalItems: number,
  totalValue: number,
  totalQuantity: number,
  OldItemData?: ItemProps,
) => {
  const newVariants = newItemData.variants
    ? newItemData.variants.map(
        (variant: { name: string; options: string[] }) => variant.name,
      )
    : null;
  const updateNames = (list: string[], entry: string | null) => {
    return entry && !list.includes(entry) ? [...list, entry] : list;
  };

  const updateQuantityOrValue = (
    prop: number,
    newItemProp: number,
    oldItemProp: number,
  ) => {
    if (oldItemProp === newItemProp) return prop;
    return oldItemProp > newItemProp
      ? prop - (oldItemProp - newItemProp)
      : prop + (newItemProp - oldItemProp);
  };

  const updatedCategories = updateNames(categories, newItemData.category);
  const updatedSuppliers = updateNames(suppliers, newItemData.supplier);
  const updatedVariants = newVariants
    ? Array.from(new Set(variants.concat(newVariants)))
    : variants;

  if (type === 'update' && OldItemData) {
    return {
      categories: { names: updatedCategories },
      suppliers: { names: updatedSuppliers },
      variants: updatedVariants,
      totalItems,
      totalQuantity: updateQuantityOrValue(
        totalQuantity,
        newItemData.quantity,
        OldItemData.quantity,
      ),
      totalValue: updateQuantityOrValue(
        totalValue,
        newItemData.total_price,
        OldItemData.total_price,
      ),
    };
  }
  return {
    categories: { names: updatedCategories },
    suppliers: { names: updatedSuppliers },
    variants: updatedVariants,
    totalItems: totalItems + 1,
    totalQuantity: totalQuantity + newItemData.quantity,
    totalValue: totalValue + newItemData.total_price,
  };
};

export const variantsExcelFormat = (
  variants: { name: string; options: string[] }[],
) => {
  const variantsNewFormat: { [key: string]: string } = {};
  variants.forEach((variant) => {
    variantsNewFormat[`variant-${variant.name}`] = variant.options.join(', ');
  });
  return variantsNewFormat;
};

export const itemDataFlattener = (items: ItemProps[]) =>
  items.map((item: ItemProps) => ({
    ...item,
    price: item.price.toFixed(2),
    total_price: item.total_price.toFixed(2),
    variants: item.variants ? `variants types: ${item.variants.length}` : null,
    ...(item.variants ? variantsExcelFormat(item.variants) : {}),
  }));

export const createSheetFile = (items: ItemProps[]) => {
  const flattenedData = itemDataFlattener(items);
  /* create worksheet from items data */
  const ws = utils.json_to_sheet(flattenedData);
  /* create workbook and append worksheet */
  const wb = utils.book_new();
  const dateNow = format(new Date(), 'dd-MM-yyyy');
  utils.book_append_sheet(wb, ws, `Inventory Items ${dateNow}`);
  if (items.length > 1) {
    writeFile(wb, `${items[0].user}_inventory_${dateNow}.xlsx`);
  } else {
    writeFile(wb, `${items[0].name}_${dateNow}.xlsx`);
  }
};

export const handleItemExport = (selectedRows?: ItemProps[]) => {
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
    const res = await api.get('/inventory/user/items/');
    const itemsData: ItemProps[] = res.data;
    createSheetFile(itemsData);
  } catch (err) {
    console.log('Error during bulk export', err);
    toast.error('Something went wrong. Please try again later.', {
      duration: 5000,
    });
  }
};

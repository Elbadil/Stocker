import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../api/axios';

export interface SupplierOrdersState {
  suppliers: { name: string; item_names: string[] }[];
  noSupplierItems: string[];
  suppliersCount: number;
  newSupplier: string | null;
  newOrderedItem: {
    item: string;
    ordered_quantity: number;
    ordered_price: number;
  } | null;
  ordersCount: number;
  orderStatus: {
    delivery_status: string[];
    payment_status: string[];
    active: number;
    completed: number;
    failed: number;
  };
  loading: boolean;
  error: string | null;
}

const initialState: SupplierOrdersState = {
  suppliers: [],
  noSupplierItems: [],
  suppliersCount: 0,
  newSupplier: null,
  newOrderedItem: null,
  ordersCount: 0,
  orderStatus: {
    delivery_status: [],
    payment_status: [],
    active: 0,
    completed: 0,
    failed: 0,
  },
  loading: true,
  error: null,
};

export interface SupplierOrdersApiResponse
  extends Omit<
    SupplierOrdersState,
    'ordersCount' | 'orderStatus' | 'suppliersCount' | 'noSupplierItems'
  > {
  orders_count: number;
  order_status: {
    delivery_status: string[];
    payment_status: string[];
    active: number;
    completed: number;
    failed: number;
  };
  suppliers_count: number;
  no_supplier_items: string[];
}

export const getSupplierOrdersData = createAsyncThunk<
  SupplierOrdersApiResponse,
  void
>('supplierOrders/getSupplierOrdersData', async () => {
  try {
    const res = await api.get('/supplier_orders/data/');
    return res.data;
  } catch (error: any) {
    console.log('Error getting supplier orders data', error);
    throw new Error(
      error.response?.data || 'Failed to get supplier orders data',
    );
  }
});

const supplierOrdersSlice = createSlice({
  name: 'supplierOrders',
  initialState,
  reducers: {
    setSupplierOrders(state, { payload }) {
      state.suppliers = payload.suppliers;
      state.noSupplierItems = payload.noSupplierItems;
      state.suppliersCount = payload.suppliersCount;
      state.newSupplier = payload.newSupplier;
      state.newOrderedItem = payload.newOrderedItem;
      state.ordersCount = payload.ordersCount;
      state.orderStatus = payload.orderStatus;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getSupplierOrdersData.pending, (state) => {
        state.loading = true;
      })
      .addCase(getSupplierOrdersData.fulfilled, (state, { payload }) => {
        state.suppliers = payload.suppliers;
        state.noSupplierItems = payload.no_supplier_items;
        state.ordersCount = payload.orders_count;
        state.orderStatus = payload.order_status;
        state.suppliersCount = payload.suppliers_count;
        state.loading = false;
      })
      .addCase(getSupplierOrdersData.rejected, (state, action) => {
        state.loading = false;
        state.error =
          action.error.message || 'Failed to get supplier orders data';
      });
  },
});

export const { setSupplierOrders } = supplierOrdersSlice.actions;
export default supplierOrdersSlice.reducer;

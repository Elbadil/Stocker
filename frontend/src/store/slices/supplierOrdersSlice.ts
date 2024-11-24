import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../api/axios';

export interface SupplierOrdersState {
  suppliers: { count: number; names: string[] };
  ordersCount: number;
  loading: boolean;
  error: string | null;
}

const initialState: SupplierOrdersState = {
  suppliers: { count: 0, names: [] },
  ordersCount: 0,
  loading: true,
  error: null,
};

export interface SupplierOrdersApiResponse
  extends Omit<SupplierOrdersState, 'ordersCount'> {
  orders_count: number;
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
      state.ordersCount = payload.orders_count;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getSupplierOrdersData.pending, (state) => {
        state.loading = true;
      })
      .addCase(getSupplierOrdersData.fulfilled, (state, { payload }) => {
        state.suppliers = payload.suppliers;
        state.ordersCount = payload.orders_count;
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

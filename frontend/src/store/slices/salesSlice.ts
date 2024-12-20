import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { api } from '../../api/axios';

export interface SalesState {
  salesCount: number;
  saleStatus: {
    delivery_status: string[];
    payment_status: string[];
    active: number;
    completed: number;
    failed: number;
  };
  loading: boolean;
  error: string | null;
}

export interface SalesApiResponse
  extends Omit<SalesState, 'salesCount' | 'saleStatus'> {
  sales_count: number;
  sale_status: {
    delivery_status: string[];
    payment_status: string[];
    active: number;
    completed: number;
    failed: number;
  };
}

const initialState: SalesState = {
  salesCount: 0,
  saleStatus: {
    delivery_status: [],
    payment_status: [],
    active: 0,
    completed: 0,
    failed: 0,
  },
  loading: true,
  error: null,
};

export const getSalesData = createAsyncThunk<SalesApiResponse, void>(
  'sales/getSalesData',
  async () => {
    try {
      const res = await api.get('/sales/data/');
      return res.data;
    } catch (error: any) {
      console.log('Error getting sales data', error);
      throw new Error(error.response?.data || 'Failed to get sales data.');
    }
  },
);

const salesSlice = createSlice({
  name: 'sales',
  initialState,
  reducers: {
    setSales(state, { payload }) {
      state.salesCount = payload.salesCount;
      state.saleStatus = payload.saleStatus;
    },
  },
  extraReducers: (builder) =>
    builder
      .addCase(getSalesData.pending, (state) => {
        state.loading = true;
      })
      .addCase(getSalesData.fulfilled, (state, { payload }) => {
        state.salesCount = payload.sales_count;
        state.saleStatus = payload.sale_status;
        state.loading = false;
      })
      .addCase(getSalesData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to get sales data.';
      }),
});

export const { setSales } = salesSlice.actions;
export default salesSlice.reducer;

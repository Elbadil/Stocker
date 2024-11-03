import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../api/axios';

export interface inventoryState {
  items: { name: string; quantity: number }[];
  totalValue: number;
  totalQuantity: number;
  totalItems: number;
  categories: { count: number; names: string[] };
  suppliers: { count: number; names: string[] };
  variants: string[];
  loading: boolean;
  error: string | Array<string> | null;
}

export interface inventoryApiResponse
  extends Omit<inventoryState, 'totalValue' | 'totalQuantity' | 'totalItems'> {
  total_value: number;
  total_quantity: number;
  total_items: number;
}

const initialState: inventoryState = {
  items: [],
  totalValue: 0,
  totalQuantity: 0,
  totalItems: 0,
  categories: { count: 0, names: [] },
  suppliers: { count: 0, names: [] },
  variants: ['Color', 'Size', 'Weight'],
  loading: true,
  error: null,
};

export const getInventoryData = createAsyncThunk<inventoryApiResponse, void>(
  'inventory/getInventoryData',
  async () => {
    try {
      const res = await api.get('/inventory/data/');
      return res.data;
    } catch (err: any) {
      console.log('Error getting inventory data:', err);
      throw new Error(err.response?.data || 'Failed to get inventory data.');
    }
  },
);

const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {
    setInventory(state, { payload }) {
      state.items = payload.items.map(
        (item: { name: string; quantity: number }) => ({
          name: item.name,
          quantity: item.quantity,
        }),
      );
      state.categories = {
        count: payload.categories.count,
        names: payload.categories.names,
      };
      state.suppliers = {
        count: payload.suppliers.count,
        names: payload.suppliers.names,
      };
      state.variants = Array.from(
        new Set(state.variants.concat(payload.variants)),
      );
      state.totalItems = payload.totalItems;
      state.totalValue = payload.totalValue;
      state.totalQuantity = payload.totalQuantity;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getInventoryData.pending, (state) => {
        state.loading = true;
      })
      .addCase(getInventoryData.fulfilled, (state, { payload }) => {
        state.items = payload.items.map(
          (item: { name: string; quantity: number }) => ({
            name: item.name,
            quantity: item.quantity,
          }),
        );
        state.categories = {
          count: payload.categories.count,
          names: payload.categories.names,
        };
        state.suppliers = {
          count: payload.suppliers.count,
          names: payload.suppliers.names,
        };
        state.variants = Array.from(
          new Set(state.variants.concat(payload.variants)),
        );
        state.totalItems = payload.total_items;
        state.totalValue = payload.total_value;
        state.totalQuantity = payload.total_quantity;
        state.loading = false;
      })
      .addCase(getInventoryData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to get inventory data.';
      });
  },
});

export const { setInventory } = inventorySlice.actions;
export default inventorySlice.reducer;

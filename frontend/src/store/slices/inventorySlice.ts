import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../api/axios';

export interface inventoryState {
  categories: { count: number; names: string[] };
  suppliers: { count: number; names: string[] };
  variants: string[];
  loading: boolean;
  error: string | Array<string> | null;
}

const initialState: inventoryState = {
  categories: { count: 0, names: [] },
  suppliers: { count: 0, names: [] },
  variants: [],
  loading: true,
  error: null,
};

export const getInventoryData = createAsyncThunk<inventoryState, void>(
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
      state.categories = {
        count: payload.categories.count,
        names: payload.categories.names,
      };
      state.suppliers = {
        count: payload.suppliers.count,
        names: payload.suppliers.names,
      };
      state.variants = payload.variants;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getInventoryData.pending, (state) => {
        state.loading = true;
      })
      .addCase(getInventoryData.fulfilled, (state, { payload }) => {
        state.categories = {
          count: payload.categories.count,
          names: payload.categories.names,
        };
        state.suppliers = {
          count: payload.suppliers.count,
          names: payload.suppliers.names,
        };
        state.variants = payload.variants;
        state.loading = false;
      })
      .addCase(getInventoryData.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to get the access token.';
      });
  },
});

export const { setInventory } = inventorySlice.actions;
export default inventorySlice.reducer;

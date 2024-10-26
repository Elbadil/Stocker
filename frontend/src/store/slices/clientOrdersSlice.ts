import { createSlice } from '@reduxjs/toolkit';
import { createAsyncThunk } from '@reduxjs/toolkit';
import { api } from '../../api/axios';

export interface ClientOrdersState {
  clients: {
    count: number;
    names: string[];
  };
  ordersCount: number;
  countries: {
    name: string;
    cities: string[];
  }[];
  acqSources: string[];
  orderStatus: string[];
  loading: boolean;
  error: string | null;
}

export interface ClientOrdersApiResponse
  extends Omit<
    ClientOrdersState,
    'ordersCount' | 'acqSources' | 'orderStatus'
  > {
  orders_count: number;
  acq_sources: string[];
  order_status: string[];
}

const initialState: ClientOrdersState = {
  clients: {
    count: 0,
    names: [],
  },
  ordersCount: 0,
  countries: [],
  acqSources: [],
  orderStatus: [],
  loading: true,
  error: null,
};

export const getClientOrdersData = createAsyncThunk<
  ClientOrdersApiResponse,
  void
>('clientOrders/getClientOrdersData', async () => {
  try {
    const res = await api.get('/client_orders/data/');
    return res.data;
  } catch (err: any) {
    console.log('Error getting client orders data:', err);
    throw new Error(err.response?.data || 'Failed to get client orders data.');
  }
});

const clientOrdersSlice = createSlice({
  name: 'clientOrders',
  initialState,
  reducers: {
    setClientOrders(state, { payload }) {
      state.clients = {
        count: payload.clients.count,
        names: payload.clients.names,
      };
      state.ordersCount = payload.ordersCount;
      state.countries = payload.countries.map(
        (country: { name: string; cities: string[] }) => ({
          name: country.name,
          cities: country.cities,
        }),
      );
      state.acqSources = payload.acqSources;
      state.orderStatus = payload.orderStatus;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(getClientOrdersData.pending, (state) => {
        state.loading = true;
      })
      .addCase(getClientOrdersData.fulfilled, (state, { payload }) => {
        state.clients = {
          count: payload.clients.count,
          names: payload.clients.names,
        };
        state.ordersCount = payload.orders_count;
        state.countries = payload.countries.map(
          (country: { name: string; cities: string[] }) => ({
            name: country.name,
            cities: country.cities,
          }),
        );
        state.acqSources = payload.acq_sources;
        state.orderStatus = payload.order_status;
        state.loading = false;
      })
      .addCase(getClientOrdersData.rejected, (state, action) => {
        state.loading = false;
        state.error =
          action.error.message || 'Failed to get client orders data.';
      });
  },
});

export const { setClientOrders } = clientOrdersSlice.actions;
export default clientOrdersSlice.reducer;

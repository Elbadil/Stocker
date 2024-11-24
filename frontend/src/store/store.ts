import { configureStore } from '@reduxjs/toolkit';
import authSlice from './slices/authSlice';
import inventorySlice from './slices/inventorySlice';
import clientOrdersSlice from './slices/clientOrdersSlice';
import supplierOrdersSlice from './slices/supplierOrdersSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    inventory: inventorySlice,
    clientOrders: clientOrdersSlice,
    supplierOrders: supplierOrdersSlice,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

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

export const dispatch = store.dispatch;
export const getState = store.getState;

export type RootState = ReturnType<typeof getState>;
export type AppDispatch = typeof dispatch;

export default store;

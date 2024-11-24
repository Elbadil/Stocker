import React, { createContext, useContext, ReactNode, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import {
  SupplierOrdersState,
  getSupplierOrdersData,
} from '../store/slices/supplierOrdersSlice';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store/store';

const SupplierOrdersContext = createContext<SupplierOrdersState | undefined>(
  undefined,
);

export const SupplierOrdersProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { pathname } = useLocation();
  const dispatch = useDispatch<AppDispatch>();
  const { suppliers, ordersCount, loading, error } = useSelector(
    (state: RootState) => state.supplierOrders,
  );

  useEffect(() => {
    if (pathname.startsWith('/supplier_orders/')) {
      dispatch(getSupplierOrdersData());
    }
  }, [pathname]);

  return (
    <SupplierOrdersContext.Provider
      value={{ suppliers, ordersCount, loading, error }}
    >
      {children}
    </SupplierOrdersContext.Provider>
  );
};

export const useSupplierOrders = () => {
  const context = useContext(SupplierOrdersContext);
  if (!context) {
    throw new Error(
      'useSupplierOrders must be used inside a SupplierOrdersProvider',
    );
  }
  return context;
};

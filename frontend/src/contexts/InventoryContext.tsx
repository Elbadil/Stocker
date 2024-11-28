import React, { ReactNode } from 'react';
import { createContext, useContext, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { getInventoryData } from '../store/slices/inventorySlice';
import { inventoryState } from '../store/slices/inventorySlice';
import { AppDispatch, RootState } from '../store/store';

const InventoryContext = createContext<inventoryState | undefined>(undefined);

export const InventoryProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { pathname } = useLocation();
  const dispatch = useDispatch<AppDispatch>();
  const inventory = useSelector((state: RootState) => state.inventory);

  useEffect(() => {
    if (
      pathname.startsWith('/inventory/') ||
      pathname.startsWith('/client_orders/') ||
      pathname.startsWith('/supplier_orders/')
    ) {
      dispatch(getInventoryData());
    }
  }, [dispatch, pathname]);

  return (
    <InventoryContext.Provider value={inventory}>
      {children}
    </InventoryContext.Provider>
  );
};

export const useInventory = () => {
  const context = useContext(InventoryContext);
  if (!context) {
    throw new Error('UseInventory must be used within an InventoryProvider');
  }
  return context;
};

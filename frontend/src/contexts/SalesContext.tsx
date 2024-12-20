import React, { createContext, ReactNode, useContext, useEffect } from 'react';
import { SalesState } from '../store/slices/salesSlice';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store/store';
import { getSalesData } from '../store/slices/salesSlice';
import { useLocation } from 'react-router-dom';

export const SalesContext = createContext<SalesState | undefined>(undefined);

export const SalesProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { pathname } = useLocation();
  const dispatch = useDispatch<AppDispatch>();
  const sales = useSelector((state: RootState) => state.sales);

  useEffect(() => {
    if (pathname.startsWith('/sales')) {
      dispatch(getSalesData());
    }
  }, [pathname]);

  return (
    <SalesContext.Provider value={sales}>{children}</SalesContext.Provider>
  );
};

export const useSales = () => {
  const context = useContext(SalesContext);
  if (!context) {
    throw new Error('useSales must be used inside a SalesProvider');
  }
  return context;
};

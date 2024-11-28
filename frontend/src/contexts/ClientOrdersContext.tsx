import { createContext, ReactNode, useContext, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ClientOrdersState } from '../store/slices/clientOrdersSlice';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store/store';
import { getClientOrdersData } from '../store/slices/clientOrdersSlice';

export const ClientOrdersContext = createContext<ClientOrdersState | undefined>(
  undefined,
);

export const ClientOrdersProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { pathname } = useLocation();
  const dispatch = useDispatch<AppDispatch>();
  const clientOrders = useSelector((state: RootState) => state.clientOrders);

  useEffect(() => {
    if (
      pathname.startsWith('/client') ||
      pathname.startsWith('/supplier') ||
      pathname.startsWith('/inventory')
    ) {
      dispatch(getClientOrdersData());
    }
  }, [dispatch, pathname]);

  return (
    <ClientOrdersContext.Provider value={clientOrders}>
      {children}
    </ClientOrdersContext.Provider>
  );
};

export const useClientOrders = () => {
  const clientOrders = useContext(ClientOrdersContext);
  if (!clientOrders) {
    throw new Error(
      'useClientOrders must be used inside a ClientOrdersProvider',
    );
  }
  return clientOrders;
};

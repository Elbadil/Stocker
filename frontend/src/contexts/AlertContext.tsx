import React, { ReactNode, useState } from 'react';
import { createContext, useContext } from 'react';
import { AlertProps } from '../pages/UiElements/Alert';

interface AlertContextType {
  alert: AlertProps | null;
  setAlert: (alert: AlertProps | null) => void;
}

export const AlertContext = createContext<AlertContextType | undefined>(
  undefined,
);

export const AlertProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [alert, setAlert] = useState<AlertProps | null>(null);

  return (
    <AlertContext.Provider value={{ alert, setAlert }}>
      {children}
    </AlertContext.Provider>
  );
};

export const useAlert = () => {
  const alert = useContext(AlertContext);
  if (alert === undefined) {
    throw new Error('useAlert must be used within an AlertProvider');
  }
  return alert;
};

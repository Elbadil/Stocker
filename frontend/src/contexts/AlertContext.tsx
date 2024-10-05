import React, { ReactNode, useState } from 'react';
import { createContext, useContext } from 'react';
import { AlertProps } from '../pages/UiElements/Alert';
import useColorMode from '../hooks/useColorMode';

interface AlertContextType {
  alert: AlertProps | null;
  setAlert: (alert: AlertProps | null) => void;
  isDarkMode: boolean;
  setIsDarkMode: (isDarkMode: boolean) => void;
}

export const AlertContext = createContext<AlertContextType | undefined>(
  undefined,
);

export const AlertProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [colorMode] = useColorMode();
  const [alert, setAlert] = useState<AlertProps | null>(null);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(colorMode === 'dark');

  return (
    <AlertContext.Provider
      value={{ alert, setAlert, isDarkMode, setIsDarkMode }}
    >
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

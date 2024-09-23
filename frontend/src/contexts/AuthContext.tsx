import { createContext, ReactNode, useContext, useLayoutEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { validateTokenAndSetUserAsync } from '../store/slices/authSlice';
import { AppDispatch, RootState } from '../store/store';
import { useAlert } from './AlertContext';

interface AuthContextType {
  isLoading: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { setAlert } = useAlert();
  const isLoading = useSelector((state: RootState) => state.auth.loading);
  const dispatch = useDispatch<AppDispatch>();

  const checkAuth = async () => {
    console.log('Hi from authContext, pathname:', pathname);
    if (pathname.startsWith('/auth')) {
    } else {
      const resultAction = await dispatch(validateTokenAndSetUserAsync());
      if (validateTokenAndSetUserAsync.fulfilled.match(resultAction)) {
        console.log('User is authenticated.');
      } else {
        console.log('User is not authenticated.');
        setAlert({
          type: 'warning',
          title: 'Session Expired',
          description:
            'Oops! It looks like your session has expired or you are not logged in. Please log in again to continue.',
        });
        navigate('/auth/signin');
      }
    }
  };

  useLayoutEffect(() => {
    checkAuth();
  }, [pathname]);

  return (
    <AuthContext.Provider value={{ isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const auth = useContext(AuthContext);
  if (auth === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return auth;
};

import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { validateTokenAndSetUserAsync } from '../store/slices/authSlice';
import { AppDispatch, RootState } from '../store/store';
import { useAlert } from './AlertContext';
import { UserProps } from '../store/slices/authSlice';

interface AuthContextType {
  user: UserProps | null;
  loading: boolean;
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
  const { user, isAuthenticated } = useSelector(
    (state: RootState) => state.auth,
  );
  const [loading, setLoading] = useState<boolean>(true);
  const dispatch = useDispatch<AppDispatch>();

  const isAuthRoute = pathname.startsWith('/auth/');

  const checkAuth = async () => {
    console.log('Hi from authContext, pathname:', pathname);
    if (isAuthenticated && isAuthRoute) {
      navigate('/');
    }
    if (!isAuthRoute) {
      const resultAction = await dispatch(validateTokenAndSetUserAsync());
      if (validateTokenAndSetUserAsync.fulfilled.match(resultAction)) {
        console.log('User is authenticated.');
        setLoading(false);
      } else {
        console.log('User is not authenticated.');
        setLoading(false);
        setAlert({
          type: 'warning',
          title: 'Session Expired',
          description:
            'Oops! It looks like your session has expired or you are not logged in. Please log in again to continue.',
        });
        navigate('/auth/login');
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    checkAuth();
  }, [pathname]);

  return (
    <AuthContext.Provider value={{ loading, user }}>
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

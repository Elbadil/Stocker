import {
  createContext,
  ReactNode,
  useContext,
  useLayoutEffect,
  useState,
} from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { validateTokenAndSetUserAsync } from '../store/slices/authSlice';
import { AppDispatch } from '../store/store';

interface AuthContextType {
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
  const [loading, setLoading] = useState<boolean>(false);
  const dispatch = useDispatch<AppDispatch>();

  const checkAuth = async () => {
    setLoading(true);
    console.log('Hi from authContext, pathname:', pathname);
    if (pathname.startsWith('/auth')) {
      setLoading(false);
      return;
    }
    const resultAction = await dispatch(validateTokenAndSetUserAsync());
    if (validateTokenAndSetUserAsync.fulfilled.match(resultAction)) {
      console.log('User is authenticated.');
      setLoading(false);
    } else {
      console.log('User is not authenticated.');
      setLoading(false);
      return navigate('/auth/signin');
    }
  };

  useLayoutEffect(() => {
    checkAuth();
  }, [pathname]);

  return (
    <AuthContext.Provider value={{ loading }}>{children}</AuthContext.Provider>
  );
};

export const useAuth = () => {
  const auth = useContext(AuthContext);
  if (auth === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return auth;
};

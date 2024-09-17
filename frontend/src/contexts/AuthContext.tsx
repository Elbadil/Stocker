import { createContext, ReactNode, useContext, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { validateTokenAndSetUserAsync } from '../store/slices/authSlice';
import { AppDispatch, RootState } from '../store/store';

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
  const dispatch = useDispatch<AppDispatch>();
  const isLoading = useSelector((state: RootState) => state.auth.loading);
  // const nonAuthPaths = ['/auth/signin', '/auth/signup'];
  // const [loading, setLoading] = useState(false)

  const checkAuth = async () => {
    console.log('Hi from authContext');
    const resultAction = await dispatch(validateTokenAndSetUserAsync());
    if (validateTokenAndSetUserAsync.fulfilled.match(resultAction)) {
      console.log('User is authenticated.');
    } else {
      console.log('User is not authenticated.');
      return navigate('/auth/signin');
    }
  };

  useEffect(() => {
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

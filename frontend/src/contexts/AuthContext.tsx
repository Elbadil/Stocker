import {
  createContext,
  useState,
  ReactNode,
  useEffect,
  useContext,
} from 'react';
import { useLocation } from 'react-router-dom';
import { getAccessToken, refreshAccessToken, logoutUser } from '../utils/auth';

export interface UserProps {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  avatar: string;
  bio: string;
  is_confirmed: boolean;
}

interface AuthContextType {
  user: UserProps | null;
  setUser: (user: UserProps | null) => void;
  loading: boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { pathname } = useLocation();
  const nonAuthPaths = ['/auth/signin', '/auth/signup'];
  const [user, setUser] = useState<UserProps | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const checkAuth = async () => {
    setLoading(true);
    console.log('Hi from Auth');

    if (nonAuthPaths.includes(pathname)) {
      setLoading(false);
      return;
    }

    const accessToken = getAccessToken();
    if (!accessToken) {
      console.log('No access token found.');
      setLoading(false);
      setUser(null);
      return await logoutUser();
    }
    const userData = JSON.parse(atob(accessToken.split('.')[1]));
    const tokenExpiryDate = new Date(userData.exp * 1000);
    const dateNow = new Date();
    if (dateNow >= tokenExpiryDate) {
      console.log('Token expired, attempting refresh...');
      try {
        const newAccessToken = await refreshAccessToken();
        const newUserData = JSON.parse(atob(newAccessToken.split('.')[1]));
        setUser(newUserData);
        console.log('refreshed from checkAuth');
      } catch (err) {
        console.log('checkAuth: Error refreshing the access token', err);
        setUser(null);
        return await logoutUser();
      }
    } else {
      setUser(userData);
    }
    setLoading(false);
  };

  useEffect(() => {
    checkAuth();
  }, [pathname]);

  return (
    <AuthContext.Provider value={{ user, setUser, loading }}>
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

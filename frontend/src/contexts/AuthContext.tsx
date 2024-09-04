import { createContext, useState, ReactNode, useContext } from 'react';

export interface UserProps {
  username: string;
  firstName: string;
  lastName: string;
  email: string;
  avatar: string;
  bio: string;
  isConfirmed: boolean;
}

interface AuthContextType {
  user: UserProps | null;
  setUser: (user: UserProps | null) => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<UserProps | null>(null);
  return (
    <AuthContext.Provider value={{ user, setUser }}>
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

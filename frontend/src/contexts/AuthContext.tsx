import React, { createContext, useContext, useState } from 'react';
import { Credentials } from '@/types';

interface AuthContextType {
  credentials: Credentials | null;
  setCredentials: (credentials: Credentials | null) => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [credentials, setCredentials] = useState<Credentials | null>(null);

  const isAuthenticated = credentials !== null;

  return (
    <AuthContext.Provider value={{ credentials, setCredentials, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

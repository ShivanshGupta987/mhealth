import React, { createContext, useContext, useState, useEffect } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  adminId: string | null;
  login: (token: string, adminId: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'mhealth_auth_token';
const ADMIN_ID_KEY = 'mhealth_admin_id';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY);
  });
  const [adminId, setAdminId] = useState<string | null>(() => {
    return localStorage.getItem(ADMIN_ID_KEY);
  });

  const login = (newToken: string, newAdminId: string) => {
    setToken(newToken);
    setAdminId(newAdminId);
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(ADMIN_ID_KEY, newAdminId);
  };

  const logout = () => {
    setToken(null);
    setAdminId(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ADMIN_ID_KEY);
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ isAuthenticated, token, adminId, login, logout }}>
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

import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { getToken, setToken, clearToken, login, register } from "../api/client";

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  loginUser: (username: string, password: string) => Promise<void>;
  registerUser: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // On mount, check if token already exists in localStorage
    const token = getToken();
    setIsAuthenticated(!!token);
    setIsLoading(false);
  }, []);

  async function loginUser(username: string, password: string) {
    const token = await login(username, password);
    setToken(token.access_token);
    setIsAuthenticated(true);
  }

  async function registerUser(username: string, password: string) {
    await register(username, password);
    // Auto-login after registration
    await loginUser(username, password);
  }

  function logout() {
    clearToken();
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider
      value={{ isAuthenticated, isLoading, loginUser, registerUser, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

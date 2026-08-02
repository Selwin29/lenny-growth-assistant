import React, { createContext, useContext, useState, useEffect } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check auth state on mount
  useEffect(() => {
    async function initializeAuth() {
      const savedToken = localStorage.getItem("lenny_auth_token");
      const savedUser = localStorage.getItem("lenny_auth_user");

      if (savedToken && savedUser) {
        try {
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
          
          // Verify token against backend
          const response = await api.get("/auth/me");
          setUser(response.data);
          localStorage.setItem("lenny_auth_user", JSON.stringify(response.data));
        } catch (err) {
          console.error("Session verification failed:", err);
          logout();
        }
      }
      setLoading(false);
    }
    initializeAuth();
  }, []);

  const login = async (email, fullName) => {
    setLoading(true);
    try {
      const response = await api.post("/auth/login", {
        email,
        full_name: fullName || null,
      });

      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      
      localStorage.setItem("lenny_auth_token", access_token);
      localStorage.setItem("lenny_auth_user", JSON.stringify(userData));
      return { success: true };
    } catch (err) {
      console.error("Login failed:", err);
      const errorMsg = err.response?.data?.detail || "Login failed. Please try again.";
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("lenny_auth_token");
    localStorage.removeItem("lenny_auth_user");
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token,
        user,
        token,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

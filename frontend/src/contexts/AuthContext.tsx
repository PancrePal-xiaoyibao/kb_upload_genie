import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { UserInfo, getCurrentUser, isAuthenticated, getStoredUser } from '@/services/auth';
import { validateStoredToken, clearAuthData } from '@/utils/auth';

interface AuthState {
  isAuthenticated: boolean;
  user: UserInfo | null;
  loading: boolean;
}

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: UserInfo }
  | { type: 'LOGIN_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; payload: boolean };

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  loading: true,
};

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_START':
      return {
        ...state,
        loading: true,
      };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload,
        loading: false,
      };
    case 'LOGIN_FAILURE':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
      };
    case 'LOGOUT':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload,
      };
    default:
      return state;
  }
};

interface AuthContextType extends AuthState {
  login: (user: UserInfo) => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  const login = (user: UserInfo) => {
    dispatch({ type: 'LOGIN_SUCCESS', payload: user });
  };

  const logout = () => {
    clearAuthData();
    dispatch({ type: 'LOGOUT' });
  };

  const checkAuth = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      console.log('开始认证检查...');
      
      // 首先验证存储的令牌是否有效
      const tokenValid = validateStoredToken();
      console.log('令牌验证结果:', tokenValid);
      
      if (!tokenValid) {
        console.log('令牌无效，设置为未认证状态');
        dispatch({ type: 'LOGIN_FAILURE' });
        return;
      }

      if (isAuthenticated()) {
        console.log('用户已认证，检查本地用户信息...');
        
        // 先尝试从本地存储获取用户信息
        const storedUser = getStoredUser();
        console.log('本地存储的用户信息:', storedUser);
        
        if (storedUser) {
          console.log('使用本地用户信息设置认证状态');
          dispatch({ type: 'LOGIN_SUCCESS', payload: storedUser });
          return;
        }
        
        console.log('本地无用户信息，从服务器获取...');
        // 如果本地没有用户信息，从服务器获取
        const user = await getCurrentUser();
        console.log('从服务器获取的用户信息:', user);
        dispatch({ type: 'LOGIN_SUCCESS', payload: user });
      } else {
        console.log('用户未认证');
        dispatch({ type: 'LOGIN_FAILURE' });
      }
    } catch (error) {
      console.error('认证检查失败:', error);
      clearAuthData();
      dispatch({ type: 'LOGIN_FAILURE' });
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth必须在AuthProvider内部使用');
  }
  return context;
};
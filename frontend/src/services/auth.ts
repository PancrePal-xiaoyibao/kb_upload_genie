import request from '@/utils/request';

export interface LoginParams {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse {
  user: UserInfo;
  token: TokenResponse;
  message: string;
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  role: string;
  status: string;
  created_at: string;
  last_login_at?: string;
}

// 管理员登录
export const adminLogin = async (params: LoginParams): Promise<LoginResponse> => {
  const response = await request.post('/v1/auth/login', params);
  return response.data;
};

// 获取当前用户信息
export const getCurrentUser = async (): Promise<UserInfo> => {
  const response = await request.get('/v1/auth/me');
  return response.data;
};

// 退出登录
export const logout = async (): Promise<void> => {
  await request.post('/v1/auth/logout');
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_user');
};

// 检查是否已登录
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('admin_token');
  return !!token;
};

// 获取存储的用户信息
export const getStoredUser = (): UserInfo | null => {
  const userStr = localStorage.getItem('admin_user');
  return userStr ? JSON.parse(userStr) : null;
};

// 存储用户信息
export const storeUserInfo = (token: string, user: UserInfo): void => {
  localStorage.setItem('admin_token', token);
  localStorage.setItem('admin_user', JSON.stringify(user));
};
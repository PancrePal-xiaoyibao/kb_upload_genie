import request from '@/utils/request';
import { UserInfo } from './auth';

export interface DashboardStats {
  message: string;
  current_admin: {
    id: string;
    email: string;
    name: string;
  };
  system_stats: {
    total_users: number;
    active_users: number;
    admin_users: number;
    moderator_users: number;
    regular_users: number;
  };
}

export interface SystemInfo {
  system: {
    project_name: string;
    version: string;
    debug_mode: boolean;
    database_url: string;
    jwt_algorithm: string;
    admin_email: string;
  };
  current_admin: {
    email: string;
    name: string;
    login_time: string;
  };
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended'
}

// 获取管理员仪表板数据
export const getDashboardData = async (): Promise<DashboardStats> => {
  const response = await request.get('/v1/admin/dashboard');
  return response.data;
};

// 获取所有用户列表
export const getAllUsers = async (): Promise<UserInfo[]> => {
  const response = await request.get('/v1/admin/users');
  return response.data;
};

// 获取用户详情
export const getUserDetail = async (userId: string): Promise<UserInfo> => {
  const response = await request.get(`/v1/admin/users/${userId}`);
  return response.data;
};

// 修改用户状态
export const updateUserStatus = async (userId: string, status: UserStatus): Promise<void> => {
  await request.put(`/v1/admin/users/${userId}/status`, { new_status: status });
};

// 获取系统信息
export const getSystemInfo = async (): Promise<SystemInfo> => {
  const response = await request.get('/v1/admin/system/info');
  return response.data;
};
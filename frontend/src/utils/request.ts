import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { message } from 'antd';
import { validateStoredToken, getStoredToken, clearAuthData } from './auth';

// 防止重复跳转的标志
let isRedirecting = false;

// 创建axios实例
const request: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 验证并获取有效的token
    if (validateStoredToken()) {
      const token = getStoredToken();
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } else {
      // 如果令牌无效，清理认证数据
      clearAuthData();
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          if (!isRedirecting) {
            isRedirecting = true;
            message.error('登录已过期，请重新登录');
            clearAuthData();
            
            // 延迟跳转，确保消息显示
            setTimeout(() => {
              window.location.href = '/admin/login';
              isRedirecting = false;
            }, 1000);
          }
          break;
        case 403:
          message.error('权限不足');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器内部错误');
          break;
        default:
          message.error(data?.detail || '请求失败');
      }
    } else {
      message.error('网络连接失败');
    }
    
    return Promise.reject(error);
  }
);

export default request;
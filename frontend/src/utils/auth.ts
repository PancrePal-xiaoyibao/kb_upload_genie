/**
 * 认证相关工具函数
 */

// 检查令牌是否有效（基本格式验证）
export const isValidToken = (token: string | null): boolean => {
  if (!token) return false;
  
  // JWT令牌应该有三个部分，用点分隔
  const parts = token.split('.');
  if (parts.length !== 3) return false;
  
  // 检查每个部分是否为有效的base64字符串
  try {
    parts.forEach(part => {
      if (!part) throw new Error('Empty part');
      // 简单的base64格式检查
      atob(part.replace(/-/g, '+').replace(/_/g, '/'));
    });
    return true;
  } catch {
    return false;
  }
};

// 检查令牌是否过期
export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp < currentTime;
  } catch {
    return true;
  }
};

// 获取令牌剩余时间（秒）
export const getTokenRemainingTime = (token: string): number => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    return Math.max(0, payload.exp - currentTime);
  } catch {
    return 0;
  }
};

// 清理认证信息
export const clearAuthData = (): void => {
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_user');
};

// 获取存储的令牌
export const getStoredToken = (): string | null => {
  return localStorage.getItem('admin_token');
};

// 验证存储的令牌是否有效
export const validateStoredToken = (): boolean => {
  const token = getStoredToken();
  if (!token) return false;
  
  if (!isValidToken(token)) {
    clearAuthData();
    return false;
  }
  
  if (isTokenExpired(token)) {
    clearAuthData();
    return false;
  }
  
  return true;
};
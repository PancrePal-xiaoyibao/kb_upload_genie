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
    parts.forEach((part, index) => {
      if (!part) throw new Error('Empty part');
      
      // 对于JWT，只需要验证payload部分（第二部分）能够正确解码
      if (index === 1) {
        // JWT使用base64url编码，需要进行适当的填充
        let base64 = part.replace(/-/g, '+').replace(/_/g, '/');
        // 添加必要的填充
        while (base64.length % 4) {
          base64 += '=';
        }
        atob(base64);
      }
    });
    return true;
  } catch (error) {
    console.warn('Token validation failed:', error);
    return false;
  }
};

// 检查令牌是否过期
export const isTokenExpired = (token: string): boolean => {
  try {
    const payloadPart = token.split('.')[1];
    // JWT使用base64url编码，需要进行适当的填充
    let base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4) {
      base64 += '=';
    }
    const payload = JSON.parse(atob(base64));
    const currentTime = Math.floor(Date.now() / 1000);
    return payload.exp < currentTime;
  } catch (error) {
    console.warn('Token expiry check failed:', error);
    return true;
  }
};

// 获取令牌剩余时间（秒）
export const getTokenRemainingTime = (token: string): number => {
  try {
    const payloadPart = token.split('.')[1];
    // JWT使用base64url编码，需要进行适当的填充
    let base64 = payloadPart.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4) {
      base64 += '=';
    }
    const payload = JSON.parse(atob(base64));
    const currentTime = Math.floor(Date.now() / 1000);
    return Math.max(0, payload.exp - currentTime);
  } catch (error) {
    console.warn('Token remaining time check failed:', error);
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
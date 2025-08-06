import request from '@/utils/request';

export interface TrackerStatus {
  tracker_id: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'rejected';
  upload_method?: string;
  title?: string;
  file_type?: string;
  file_size?: number;
  created_at: string;
  updated_at: string;
  processed_at?: string;
  metadata?: any;
  error_message?: string;
}

export interface TrackerResponse {
  success: boolean;
  message: string;
  data?: TrackerStatus;
  error_code?: string;
}

export interface TrackerQueryRequest {
  tracker_id: string;
}

/**
 * 跟踪服务类
 */
export class TrackerService {
  private static baseUrl = '/v1/tracker';

  /**
   * 通过POST方法查询跟踪状态
   */
  static async queryStatus(trackerId: string): Promise<TrackerResponse> {
    try {
      const response = await request.post<TrackerResponse>(`${this.baseUrl}/query`, {
        tracker_id: trackerId
      });
      return response.data;
    } catch (error: any) {
      // 处理HTTP错误响应
      if (error.response?.data) {
        return error.response.data;
      }
      
      // 处理网络错误
      return {
        success: false,
        message: '网络错误，请稍后重试',
        error_code: 'NETWORK_ERROR'
      };
    }
  }

  /**
   * 通过GET方法查询跟踪状态
   */
  static async getStatus(trackerId: string): Promise<TrackerResponse> {
    try {
      const response = await request.get<TrackerResponse>(`${this.baseUrl}/status/${trackerId}`);
      return response.data;
    } catch (error: any) {
      // 处理HTTP错误响应
      if (error.response?.data) {
        return error.response.data;
      }
      
      // 处理网络错误
      return {
        success: false,
        message: '网络错误，请稍后重试',
        error_code: 'NETWORK_ERROR'
      };
    }
  }

  /**
   * 检查跟踪服务健康状态
   */
  static async checkHealth(): Promise<{ status: string; service: string; message: string }> {
    try {
      const response = await request.get(`${this.baseUrl}/health`);
      return response.data;
    } catch (error) {
      throw new Error('跟踪服务不可用');
    }
  }

  /**
   * 格式化文件大小
   */
  static formatFileSize(bytes?: number): string {
    if (!bytes) return '未知';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  }

  /**
   * 格式化日期时间
   */
  static formatDateTime(dateString: string): string {
    try {
      return new Date(dateString).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (error) {
      return dateString;
    }
  }

  /**
   * 获取上传方法的中文名称
   */
  static getUploadMethodText(method?: string): string {
    const methodMap: Record<string, string> = {
      'email_upload': '邮件上传',
      'simple_email': '简单邮件',
      'web_upload': '网页上传',
      'github_direct': 'GitHub直接',
      'api_upload': 'API上传',
      'batch_import': '批量导入'
    };
    
    return methodMap[method || ''] || method || '未知';
  }

  /**
   * 获取处理状态的中文名称
   */
  static getStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      'pending': '待处理',
      'processing': '处理中',
      'completed': '已完成',
      'rejected': '已拒绝'
    };
    
    return statusMap[status] || '未知状态';
  }

  /**
   * 获取状态对应的图标
   */
  static getStatusIcon(status: string): string {
    const iconMap: Record<string, string> = {
      'pending': '⏳',
      'processing': '🔄',
      'completed': '✅',
      'rejected': '❌'
    };
    
    return iconMap[status] || '❓';
  }

  /**
   * 获取状态对应的颜色类
   */
  static getStatusColor(status: string): string {
    const colorMap: Record<string, string> = {
      'pending': 'bg-orange-500',
      'processing': 'bg-blue-500',
      'completed': 'bg-green-500',
      'rejected': 'bg-red-500'
    };
    
    return colorMap[status] || 'bg-gray-500';
  }

  /**
   * 获取状态对应的进度值
   */
  static getProgressValue(status: string): number {
    const progressMap: Record<string, number> = {
      'pending': 25,
      'processing': 75,
      'completed': 100,
      'rejected': 100
    };
    
    return progressMap[status] || 0;
  }

  /**
   * 验证跟踪ID格式
   */
  static validateTrackerId(trackerId: string): { valid: boolean; message?: string } {
    if (!trackerId) {
      return { valid: false, message: '跟踪ID不能为空' };
    }

    if (trackerId.length < 8 || trackerId.length > 36) {
      return { valid: false, message: '跟踪ID长度应在8-36字符之间' };
    }

    // 检查是否包含有效字符（字母、数字、短横线）
    const validPattern = /^[A-Za-z0-9\-]+$/;
    if (!validPattern.test(trackerId)) {
      return { valid: false, message: '跟踪ID只能包含字母、数字和短横线' };
    }

    return { valid: true };
  }

  /**
   * 格式化跟踪ID用于显示
   */
  static formatTrackerDisplay(trackerId: string): string {
    if (!trackerId) return '无';
    
    // 如果ID很长，显示前6位...后4位
    if (trackerId.length > 12) {
      return `${trackerId.slice(0, 6)}...${trackerId.slice(-4)}`;
    }
    
    return trackerId;
  }
}

export default TrackerService;
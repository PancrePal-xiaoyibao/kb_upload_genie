import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Alert } from './ui/alert';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  success: (title: string, message?: string, duration?: number) => void;
  error: (title: string, message?: string, duration?: number) => void;
  warning: (title: string, message?: string, duration?: number) => void;
  info: (title: string, message?: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

interface ToastProviderProps {
  children: ReactNode;
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = {
      ...toast,
      id,
      duration: toast.duration ?? 5000
    };

    setToasts(prev => [...prev, newToast]);

    // 自动移除toast
    if (newToast.duration && newToast.duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, newToast.duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const success = useCallback((title: string, message?: string, duration?: number) => {
    addToast({ type: 'success', title, message, duration });
  }, [addToast]);

  const error = useCallback((title: string, message?: string, duration?: number) => {
    addToast({ type: 'error', title, message, duration: duration ?? 8000 });
  }, [addToast]);

  const warning = useCallback((title: string, message?: string, duration?: number) => {
    addToast({ type: 'warning', title, message, duration });
  }, [addToast]);

  const info = useCallback((title: string, message?: string, duration?: number) => {
    addToast({ type: 'info', title, message, duration });
  }, [addToast]);

  return (
    <ToastContext.Provider value={{
      toasts,
      addToast,
      removeToast,
      success,
      error,
      warning,
      info
    }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
};

interface ToastItemProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
  const getToastStyles = (type: ToastType) => {
    switch (type) {
      case 'success':
        return {
          className: 'border-green-200 bg-green-50',
          icon: '✅',
          iconColor: 'text-green-600',
          titleColor: 'text-green-800',
          messageColor: 'text-green-700'
        };
      case 'error':
        return {
          className: 'border-red-200 bg-red-50',
          icon: '❌',
          iconColor: 'text-red-600',
          titleColor: 'text-red-800',
          messageColor: 'text-red-700'
        };
      case 'warning':
        return {
          className: 'border-orange-200 bg-orange-50',
          icon: '⚠️',
          iconColor: 'text-orange-600',
          titleColor: 'text-orange-800',
          messageColor: 'text-orange-700'
        };
      case 'info':
        return {
          className: 'border-blue-200 bg-blue-50',
          icon: 'ℹ️',
          iconColor: 'text-blue-600',
          titleColor: 'text-blue-800',
          messageColor: 'text-blue-700'
        };
      default:
        return {
          className: 'border-gray-200 bg-gray-50',
          icon: '📝',
          iconColor: 'text-gray-600',
          titleColor: 'text-gray-800',
          messageColor: 'text-gray-700'
        };
    }
  };

  const styles = getToastStyles(toast.type);

  return (
    <Alert className={`${styles.className} shadow-lg animate-in slide-in-from-right duration-300`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <span className={`${styles.iconColor} text-lg`}>{styles.icon}</span>
          <div className="flex-1 min-w-0">
            <h4 className={`font-medium ${styles.titleColor} text-sm`}>
              {toast.title}
            </h4>
            {toast.message && (
              <p className={`${styles.messageColor} text-sm mt-1`}>
                {toast.message}
              </p>
            )}
            {toast.action && (
              <button
                onClick={toast.action.onClick}
                className={`${styles.titleColor} text-sm font-medium underline hover:no-underline mt-2`}
              >
                {toast.action.label}
              </button>
            )}
          </div>
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className={`${styles.iconColor} hover:opacity-70 ml-2 text-lg leading-none`}
          aria-label="关闭通知"
        >
          ×
        </button>
      </div>
    </Alert>
  );
};

// Hook for easy toast usage
export const useToastHelpers = () => {
  const { success, error, warning, info } = useToast();

  return {
    showSuccess: success,
    showError: error,
    showWarning: warning,
    showInfo: info,
    
    // 常用的预设消息
    showNetworkError: () => error('网络错误', '请检查网络连接后重试'),
    showServerError: () => error('服务器错误', '服务器暂时不可用，请稍后重试'),
    showValidationError: (message: string) => error('输入错误', message),
    showSuccessMessage: (action: string) => success('操作成功', `${action}已完成`),
    showLoadingError: () => error('加载失败', '数据加载失败，请刷新页面重试'),
    showSaveSuccess: () => success('保存成功', '您的更改已保存'),
    showDeleteSuccess: () => success('删除成功', '项目已成功删除'),
    showCopySuccess: () => success('复制成功', '内容已复制到剪贴板'),
    
    // 跟踪相关的预设消息
    showTrackerNotFound: () => error('跟踪ID未找到', '请检查跟踪ID是否正确或联系管理员'),
    showTrackerQuerySuccess: () => success('查询成功', '已获取最新状态信息'),
    showInvalidTrackerId: () => error('无效的跟踪ID', '请输入正确格式的跟踪ID'),
    showTrackerExpired: () => warning('跟踪ID已过期', '该跟踪记录可能已过期，请联系管理员')
  };
};

export default ToastProvider;
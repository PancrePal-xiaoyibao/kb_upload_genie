import React from 'react';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'rejected';

interface StatusIndicatorProps {
  status: ProcessingStatus;
  showProgress?: boolean;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  showProgress = false,
  showIcon = true,
  size = 'md',
  className = ''
}) => {
  const getStatusConfig = (status: ProcessingStatus) => {
    switch (status) {
      case 'pending':
        return {
          color: 'bg-orange-500 hover:bg-orange-600',
          textColor: 'text-orange-700',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          text: '待处理',
          icon: '⏳',
          progress: 25,
          description: '文件已接收，等待处理'
        };
      case 'processing':
        return {
          color: 'bg-blue-500 hover:bg-blue-600',
          textColor: 'text-blue-700',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          text: '处理中',
          icon: '🔄',
          progress: 75,
          description: '正在分析和处理文件'
        };
      case 'completed':
        return {
          color: 'bg-green-500 hover:bg-green-600',
          textColor: 'text-green-700',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          text: '已完成',
          icon: '✅',
          progress: 100,
          description: '文件处理完成，可以正常使用'
        };
      case 'rejected':
        return {
          color: 'bg-red-500 hover:bg-red-600',
          textColor: 'text-red-700',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          text: '已拒绝',
          icon: '❌',
          progress: 100,
          description: '文件处理失败或被拒绝'
        };
      default:
        return {
          color: 'bg-gray-500 hover:bg-gray-600',
          textColor: 'text-gray-700',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          text: '未知状态',
          icon: '❓',
          progress: 0,
          description: '状态未知'
        };
    }
  };

  const getSizeClasses = (size: string) => {
    switch (size) {
      case 'sm':
        return {
          badge: 'text-xs px-2 py-1',
          icon: 'text-sm',
          progress: 'h-1'
        };
      case 'lg':
        return {
          badge: 'text-base px-4 py-2',
          icon: 'text-lg',
          progress: 'h-3'
        };
      default: // md
        return {
          badge: 'text-sm px-3 py-1',
          icon: 'text-base',
          progress: 'h-2'
        };
    }
  };

  const config = getStatusConfig(status);
  const sizeClasses = getSizeClasses(size);

  if (showProgress) {
    return (
      <div className={`space-y-2 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {showIcon && (
              <span className={sizeClasses.icon}>{config.icon}</span>
            )}
            <span className={`font-medium ${config.textColor}`}>
              {config.text}
            </span>
          </div>
          <span className={`text-sm ${config.textColor}`}>
            {config.progress}%
          </span>
        </div>
        <Progress 
          value={config.progress} 
          className={`${sizeClasses.progress} ${config.bgColor}`}
        />
        <p className={`text-xs ${config.textColor} opacity-75`}>
          {config.description}
        </p>
      </div>
    );
  }

  return (
    <Badge 
      className={`${config.color} text-white ${sizeClasses.badge} ${className}`}
    >
      {showIcon && (
        <span className={`mr-1 ${sizeClasses.icon}`}>{config.icon}</span>
      )}
      {config.text}
    </Badge>
  );
};

export default StatusIndicator;

// 状态卡片组件
interface StatusCardProps {
  status: ProcessingStatus;
  title: string;
  description?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
  className?: string;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  status,
  title,
  description,
  timestamp,
  metadata,
  className = ''
}) => {
  const getCardStatusConfig = (status: ProcessingStatus) => {
    switch (status) {
      case 'pending':
        return {
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          textColor: 'text-orange-700',
          icon: '⏳'
        };
      case 'processing':
        return {
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          textColor: 'text-blue-700',
          icon: '🔄'
        };
      case 'completed':
        return {
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-700',
          icon: '✅'
        };
      case 'rejected':
        return {
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-700',
          icon: '❌'
        };
      default:
        return {
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-700',
          icon: '❓'
        };
    }
  };

  const config = getCardStatusConfig(status);

  return (
    <div className={`
      rounded-lg border-2 p-4 transition-all duration-200 hover:shadow-md
      ${config.bgColor} ${config.borderColor} ${className}
    `}>
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <h3 className={`font-semibold ${config.textColor}`}>
              {title}
            </h3>
            {description && (
              <p className={`text-sm mt-1 ${config.textColor} opacity-75`}>
                {description}
              </p>
            )}
          </div>
        </div>
        <StatusIndicator status={status} size="sm" />
      </div>
      
      {timestamp && (
        <div className={`mt-3 text-xs ${config.textColor} opacity-60`}>
          {timestamp}
        </div>
      )}
      
      {metadata && Object.keys(metadata).length > 0 && (
        <div className="mt-3 pt-3 border-t border-current border-opacity-20">
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(metadata).slice(0, 4).map(([key, value]) => (
              <div key={key} className={config.textColor}>
                <span className="opacity-60">{key}:</span>
                <span className="ml-1 font-medium">
                  {typeof value === 'string' ? value : JSON.stringify(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// 状态时间线组件
interface StatusTimelineProps {
  statuses: Array<{
    status: ProcessingStatus;
    timestamp: string;
    description?: string;
  }>;
  currentStatus: ProcessingStatus;
  className?: string;
}

export const StatusTimeline: React.FC<StatusTimelineProps> = ({
  statuses,
  currentStatus,
  className = ''
}) => {
  const allStatuses: ProcessingStatus[] = ['pending', 'processing', 'completed'];
  
  const isStatusReached = (status: ProcessingStatus) => {
    const statusOrder = { pending: 0, processing: 1, completed: 2, rejected: 2 };
    const currentOrder = statusOrder[currentStatus];
    const targetOrder = statusOrder[status];
    
    if (currentStatus === 'rejected') {
      return status === 'pending' || status === 'rejected';
    }
    
    return targetOrder <= currentOrder;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {allStatuses.map((status, index) => {
        const isReached = isStatusReached(status);
        const isCurrent = status === currentStatus;
        const statusData = statuses.find(s => s.status === status);
        
        return (
          <div key={status} className="flex items-start space-x-4">
            <div className="flex flex-col items-center">
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-sm
                ${isReached 
                  ? isCurrent 
                    ? 'bg-blue-500 text-white ring-4 ring-blue-200' 
                    : 'bg-green-500 text-white'
                  : 'bg-gray-200 text-gray-400'
                }
              `}>
                {isReached ? '✓' : index + 1}
              </div>
              {index < allStatuses.length - 1 && (
                <div className={`
                  w-0.5 h-8 mt-2
                  ${isReached ? 'bg-green-300' : 'bg-gray-200'}
                `} />
              )}
            </div>
            <div className="flex-1 pb-8">
              <div className="flex items-center space-x-2">
                <StatusIndicator 
                  status={status} 
                  size="sm" 
                  showIcon={false}
                />
                {isCurrent && (
                  <span className="text-xs text-blue-600 font-medium">当前状态</span>
                )}
              </div>
              {statusData && (
                <div className="mt-1 space-y-1">
                  <p className="text-sm text-gray-600">
                    {statusData.description}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(statusData.timestamp).toLocaleString('zh-CN')}
                  </p>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
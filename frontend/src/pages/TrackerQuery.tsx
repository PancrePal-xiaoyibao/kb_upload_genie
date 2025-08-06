import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Alert } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Separator } from '../components/ui/separator';
import TrackerService, { TrackerResponse, TrackerStatus } from '../services/tracker';
import StatusIndicator, { StatusCard } from '../components/StatusIndicator';
import { SimpleErrorBoundary } from '../components/ErrorBoundary';
import { useToastHelpers } from '../components/Toast';

const TrackerQuery: React.FC = () => {
  const [trackerId, setTrackerId] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TrackerResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const toast = useToastHelpers();

  const handleQuery = async () => {
    const trimmedId = trackerId.trim();
    
    if (!trimmedId) {
      toast.showValidationError('请输入跟踪ID');
      setError('请输入跟踪ID');
      return;
    }

    // 验证跟踪ID格式
    const validation = TrackerService.validateTrackerId(trimmedId);
    if (!validation.valid) {
      toast.showInvalidTrackerId();
      setError(validation.message || '跟踪ID格式无效');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await TrackerService.getStatus(trimmedId);
      setResult(data);
      
      if (data.success) {
        toast.showTrackerQuerySuccess();
      } else {
        if (data.error_code === 'TRACKER_NOT_FOUND') {
          toast.showTrackerNotFound();
        } else {
          toast.showError('查询失败', data.message || '未知错误');
        }
        setError(data.message || '查询失败');
      }
    } catch (err) {
      toast.showNetworkError();
      setError('网络错误，请稍后重试');
      console.error('查询错误:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyTrackerId = async (trackerId: string) => {
    try {
      await navigator.clipboard.writeText(trackerId);
      toast.showSuccess('复制成功', '跟踪ID已复制到剪贴板');
    } catch (err) {
      // 降级方案：使用传统方法复制
      const textArea = document.createElement('textarea');
      textArea.value = trackerId;
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        toast.showSuccess('复制成功', '跟踪ID已复制到剪贴板');
      } catch (fallbackErr) {
        toast.showError('复制失败', '请手动复制跟踪ID');
      }
      document.body.removeChild(textArea);
    }
  };


  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">KB</span>
                </div>
                <h1 className="text-xl font-semibold text-gray-900">上传跟踪</h1>
              </div>
            </div>
            <div>
              <Button 
                variant="outline" 
                onClick={() => window.location.href = '/'}
                className="text-gray-600 hover:text-gray-900"
              >
                返回首页
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* 主要内容 */}
      <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* 查询表单卡片 */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <span>🔍</span>
              <span>查询上传状态</span>
            </CardTitle>
            <CardDescription>
              输入您的跟踪ID来查询文件上传和处理状态
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="tracker-id">跟踪ID</Label>
                <div className="flex space-x-2 mt-1">
                  <Input
                    id="tracker-id"
                    type="text"
                    placeholder="请输入跟踪ID，例如：TRK-12345678-9ABC"
                    value={trackerId}
                    onChange={(e) => setTrackerId(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
                    className="flex-1"
                  />
                  <Button 
                    onClick={handleQuery} 
                    disabled={loading}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {loading ? '查询中...' : '查询状态'}
                  </Button>
                </div>
              </div>
              
              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <div className="flex items-center space-x-2">
                    <span className="text-red-500">❌</span>
                    <span className="text-red-700">{error}</span>
                  </div>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 状态显示区域 */}
        {result && result.success && result.data && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span>{TrackerService.getStatusIcon(result.data.processing_status)}</span>
                  <span>跟踪状态</span>
                </div>
                <StatusIndicator 
                  status={result.data.processing_status} 
                  size="md"
                />
              </CardTitle>
              <CardDescription className="flex items-center justify-between">
                <span>跟踪ID: {result.data.tracker_id}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleCopyTrackerId(result.data.tracker_id)}
                  className="ml-2 text-xs"
                >
                  📋 复制
                </Button>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* 进度条 */}
                <div>
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>处理进度</span>
                    <span>{TrackerService.getProgressValue(result.data.processing_status)}%</span>
                  </div>
                  <Progress 
                    value={TrackerService.getProgressValue(result.data.processing_status)} 
                    className="h-2"
                  />
                </div>

                <Separator />

                {/* 基本信息 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-500">文件标题</Label>
                    <p className="mt-1 text-sm text-gray-900">
                      {result.data.title || '未知'}
                    </p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">上传方式</Label>
                    <p className="mt-1 text-sm text-gray-900">
                      {TrackerService.getUploadMethodText(result.data.upload_method)}
                    </p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">文件类型</Label>
                    <p className="mt-1 text-sm text-gray-900">
                      {result.data.file_type || '未知'}
                    </p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">文件大小</Label>
                    <p className="mt-1 text-sm text-gray-900">
                      {TrackerService.formatFileSize(result.data.file_size)}
                    </p>
                  </div>
                </div>

                <Separator />

                {/* 时间信息 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-gray-500">创建时间</Label>
                    <p className="mt-1 text-sm text-gray-900">
                      {TrackerService.formatDateTime(result.data.created_at)}
                    </p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium text-gray-500">更新时间</Label>
                    <p className="mt-1 text-sm text-gray-900">
                      {TrackerService.formatDateTime(result.data.updated_at)}
                    </p>
                  </div>
                  {result.data.processed_at && (
                    <div className="md:col-span-2">
                      <Label className="text-sm font-medium text-gray-500">处理完成时间</Label>
                      <p className="mt-1 text-sm text-gray-900">
                        {TrackerService.formatDateTime(result.data.processed_at)}
                      </p>
                    </div>
                  )}
                </div>

                {/* 错误信息 */}
                {result.data.error_message && (
                  <>
                    <Separator />
                    <Alert className="border-red-200 bg-red-50">
                      <div className="space-y-2">
                        <div className="flex items-center space-x-2">
                          <span className="text-red-500">⚠️</span>
                          <span className="font-medium text-red-700">处理错误</span>
                        </div>
                        <p className="text-red-700 text-sm">
                          {result.data.error_message}
                        </p>
                      </div>
                    </Alert>
                  </>
                )}

                {/* 元数据信息 */}
                {result.data.metadata && (
                  <>
                    <Separator />
                    <div>
                      <Label className="text-sm font-medium text-gray-500 mb-2 block">
                        详细信息
                      </Label>
                      <div className="bg-gray-50 rounded-lg p-4">
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(result.data.metadata, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 使用说明 */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <span>💡</span>
              <span>使用说明</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm text-gray-600">
              <p>• <strong>跟踪ID</strong>：在文件上传成功后会自动生成，请妥善保存</p>
              <p>• <strong>状态说明</strong>：</p>
              <div className="ml-4 space-y-1">
                <p>- <span className="inline-flex items-center space-x-1"><span>⏳</span><span>待处理</span></span>：文件已接收，等待处理</p>
                <p>- <span className="inline-flex items-center space-x-1"><span>🔄</span><span>处理中</span></span>：正在分析和处理文件</p>
                <p>- <span className="inline-flex items-center space-x-1"><span>✅</span><span>已完成</span></span>：文件处理完成，可以正常使用</p>
                <p>- <span className="inline-flex items-center space-x-1"><span>❌</span><span>已拒绝</span></span>：文件处理失败或被拒绝</p>
              </div>
              <p>• 如有疑问，请联系系统管理员</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default TrackerQuery;
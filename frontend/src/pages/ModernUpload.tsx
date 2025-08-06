import React, { useState, useCallback } from 'react'
import { Upload as UploadIcon, FileText, AlertCircle, CheckCircle, X, Shield, Copy, ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import TurnstileComponent from '../components/TurnstileComponent'
import { useTurnstileConfig } from '../hooks/useTurnstile'
import { cn } from '@/lib/utils'
import request from '@/utils/request'

interface FileItem {
  id: string
  file: File
  name: string
  size: number
  type: string
  status: 'ready' | 'uploading' | 'done' | 'error'
  progress: number
  error?: string
  trackerId?: string
}

const ModernUpload: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([])
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null)
  const [turnstileVerified, setTurnstileVerified] = useState(false)
  const [showTurnstileModal, setShowTurnstileModal] = useState(false)
  const [turnstileLoading, setTurnstileLoading] = useState(false)
  const [turnstileRetryCount, setTurnstileRetryCount] = useState(0)

  // 获取Turnstile配置
  const { config: turnstileConfig, error: configError } = useTurnstileConfig()

  const MAX_RETRY_COUNT = 3
  const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50MB
  const ALLOWED_TYPES = ['.md', '.txt', '.docx', '.pdf', '.pptx', '.js', '.ts', '.py', '.java', '.cpp', '.html', '.css', '.jpg', '.png', '.gif', '.svg', '.webp']

  // 复制Tracker ID到剪贴板
  const copyTrackerId = async (trackerId: string) => {
    try {
      await navigator.clipboard.writeText(trackerId)
      // 这里可以添加一个toast提示
      console.log('Tracker ID已复制到剪贴板')
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  // 跳转到跟踪查询页面
  // 跳转到跟踪查询页面
  const goToTracker = (trackerId: string) => {
    // 直接跳转到跟踪页面，并在URL中预填充tracker_id
    const url = new URL('/tracker', window.location.origin)
    url.searchParams.set('id', trackerId)
    window.open(url.toString(), '_blank')
  }

  // 文件验证
  const validateFile = (file: File): string | null => {
    if (file.size > MAX_FILE_SIZE) {
      return '文件大小不能超过50MB'
    }

    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_TYPES.includes(fileExtension)) {
      return `不支持的文件类型: ${fileExtension}`
    }

    return null
  }

  // 添加文件
  const addFiles = useCallback((newFiles: File[]) => {
    const validFiles: FileItem[] = []
    
    newFiles.forEach(file => {
      const error = validateFile(file)
      if (!error) {
        const fileItem: FileItem = {
          id: `${Date.now()}-${Math.random()}`,
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          status: 'ready',
          progress: 0
        }
        validFiles.push(fileItem)
      } else {
        // 显示错误消息
        console.error(`文件 ${file.name} 验证失败: ${error}`)
      }
    })

    setFiles(prev => [...prev, ...validFiles])
  }, [])

  // 拖拽处理
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const droppedFiles = Array.from(e.dataTransfer.files)
    addFiles(droppedFiles)
  }, [addFiles])

  // 文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    addFiles(selectedFiles)
    // 清空input值，允许重复选择同一文件
    e.target.value = ''
  }, [addFiles])

  // 移除文件
  const removeFile = useCallback((id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id))
  }, [])

  // Turnstile验证处理
  const handleTurnstileVerify = (token: string) => {
    setTurnstileToken(token)
    setTurnstileVerified(true)
    setTurnstileLoading(false)
    setShowTurnstileModal(false)
    
    // 验证成功后立即开始上传
    performUpload(token)
  }

  const handleTurnstileError = (_error: string) => {
    setTurnstileLoading(false)
    setTurnstileRetryCount(prev => prev + 1)
    
    if (turnstileRetryCount >= MAX_RETRY_COUNT) {
      setShowTurnstileModal(false)
      setTurnstileToken(null)
      setTurnstileVerified(false)
      setTurnstileRetryCount(0)
      return
    }
  }

  const handleTurnstileExpire = () => {
    setTurnstileToken(null)
    setTurnstileVerified(false)
    setTurnstileLoading(false)
  }

  // 开始上传
  const handleUpload = async () => {
    if (files.length === 0) return

    // 如果启用了Turnstile验证且未验证，先进行验证
    if (turnstileConfig?.enabled && !turnstileVerified) {
      setShowTurnstileModal(true)
      setTurnstileLoading(true)
      return
    }

    await performUpload()
  }

  // 执行上传
  const performUpload = async (providedToken?: string) => {
    setUploading(true)

    try {
      for (const fileItem of files) {
        if (fileItem.status !== 'ready') continue

        // 更新状态为上传中
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id 
            ? { ...f, status: 'uploading', progress: 0 }
            : f
        ))

        try {
          const formData = new FormData()
          formData.append('file', fileItem.file)

          // 添加Turnstile令牌
          if (turnstileConfig?.enabled) {
            const tokenToSend = providedToken || turnstileToken || ''
            formData.append('turnstile_token', tokenToSend)
          }

          const response = await request.post('/v1/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })

          const result = response.data

          if (response.status === 200 && result.success) {
            // 上传成功，保存tracker_id
            const trackerId = result.data?.tracker_id
            setFiles(prev => prev.map(f => 
              f.id === fileItem.id 
                ? { ...f, status: 'done', progress: 100, trackerId }
                : f
            ))
          } else {
            // 上传失败
            const errorMsg = result.detail || result.message || '未知错误'
            setFiles(prev => prev.map(f => 
              f.id === fileItem.id 
                ? { ...f, status: 'error', progress: 0, error: errorMsg }
                : f
            ))

            // 如果是Turnstile相关错误，重置验证状态
            if (errorMsg.includes('Turnstile') || errorMsg.includes('验证令牌')) {
              setTurnstileVerified(false)
              setTurnstileToken(null)
            }
          }
        } catch (error: any) {
          // 处理Axios错误
          let errorMsg = '网络错误'
          if (error.response?.data?.detail) {
            errorMsg = error.response.data.detail
          } else if (error.message) {
            errorMsg = error.message
          }
          
          setFiles(prev => prev.map(f => 
            f.id === fileItem.id 
              ? { ...f, status: 'error', progress: 0, error: errorMsg }
              : f
          ))

          // 如果是认证相关错误，重置验证状态
          if (error.response?.status === 401 || errorMsg.includes('Turnstile') || errorMsg.includes('验证令牌')) {
            setTurnstileVerified(false)
            setTurnstileToken(null)
          }
        }
      }

      // 上传完成后重置验证状态
      if (turnstileConfig?.enabled) {
        setTurnstileVerified(false)
        setTurnstileToken(null)
      }
    } finally {
      setUploading(false)
    }
  }

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 获取文件类型标签颜色
  const getFileTypeColor = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'pdf': return 'bg-red-100 text-red-800'
      case 'doc': case 'docx': return 'bg-blue-100 text-blue-800'
      case 'txt': case 'md': return 'bg-gray-100 text-gray-800'
      case 'js': case 'ts': return 'bg-yellow-100 text-yellow-800'
      case 'py': return 'bg-green-100 text-green-800'
      case 'jpg': case 'png': case 'gif': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const supportedFileTypes = [
    { category: '文档类型', types: ['.pdf', '.doc', '.docx', '.txt', '.md'] },
    { category: '代码类型', types: ['.js', '.ts', '.py', '.java', '.cpp', '.html', '.css'] },
    { category: '图片类型', types: ['.jpg', '.png', '.gif', '.svg', '.webp'] }
  ]

  return (
    <div className="max-w-4xl mx-auto px-6 space-y-8">
      {/* 页面标题 */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">文件上传</h1>
        <p className="text-muted-foreground text-lg">
          支持拖拽上传，自动识别文件类型并进行智能分类
        </p>
      </div>

      {/* 配置错误提示 */}
      {configError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>配置加载失败: {configError}</AlertDescription>
        </Alert>
      )}

      {/* 文件上传区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UploadIcon className="h-5 w-5" />
            上传文件
          </CardTitle>
          <CardDescription>
            点击选择文件或拖拽文件到下方区域
            {turnstileConfig?.enabled && (
              <span className="block mt-1 text-blue-600">
                点击"开始上传"按钮时将进行安全验证
              </span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 拖拽上传区域 */}
          <div
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
              isDragOver 
                ? "border-primary bg-primary/5" 
                : "border-muted-foreground/25 hover:border-primary/50"
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <UploadIcon className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">点击或拖拽文件到此区域上传</h3>
            <p className="text-sm text-muted-foreground">
              支持单个或批量上传。严禁上传公司数据或其他敏感文件。
            </p>
            <input
              id="file-input"
              type="file"
              multiple
              className="hidden"
              onChange={handleFileSelect}
              accept={ALLOWED_TYPES.join(',')}
            />
          </div>

          {/* 上传按钮 */}
          <div className="flex justify-center">
            <Button
              onClick={handleUpload}
              disabled={files.length === 0 || uploading}
              size="lg"
              className="px-8"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  上传中...
                </>
              ) : (
                <>
                  <UploadIcon className="h-4 w-4 mr-2" />
                  开始上传
                </>
              )}
            </Button>
          </div>

          {turnstileConfig?.enabled && !uploading && files.length > 0 && (
            <p className="text-xs text-center text-muted-foreground">
              点击后将先进行安全验证，验证通过后自动开始上传
            </p>
          )}
        </CardContent>
      </Card>

      {/* 文件列表 */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>上传进度</CardTitle>
            <CardDescription>
              {files.filter(f => f.status === 'done').length} / {files.length} 个文件已完成
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {files.map((file) => (
                <div key={file.id} className="flex items-center space-x-4 p-4 border rounded-lg">
                  <FileText className="h-8 w-8 text-muted-foreground flex-shrink-0" />
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <div className="flex items-center space-x-2">
                        <Badge className={getFileTypeColor(file.name)}>
                          {file.name.split('.').pop()?.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatFileSize(file.size)}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(file.id)}
                          disabled={file.status === 'uploading'}
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <div className="flex-1">
                        <Progress value={file.progress} className="h-2" />
                      </div>
                      <div className="flex items-center space-x-1">
                        {file.status === 'done' && (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        )}
                        {file.status === 'error' && (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )}
                        <Badge variant={
                          file.status === 'done' ? 'default' :
                          file.status === 'error' ? 'destructive' :
                          file.status === 'uploading' ? 'secondary' : 'outline'
                        }>
                          {file.status === 'done' ? '完成' :
                           file.status === 'error' ? '失败' :
                           file.status === 'uploading' ? '上传中' : '就绪'}
                        </Badge>
                      </div>
                    </div>
                    
                    {file.error && (
                      <p className="text-xs text-red-500 mt-1">{file.error}</p>
                    )}

                    {/* 显示Tracker ID */}
                    {file.status === 'done' && file.trackerId && (
                      <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-green-800 mb-1">
                              🎉 上传成功！您的跟踪ID：
                            </p>
                            <div className="flex items-center space-x-2">
                              <code className="text-sm bg-white px-2 py-1 rounded border text-green-700 font-mono">
                                {file.trackerId}
                              </code>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => copyTrackerId(file.trackerId!)}
                                className="h-7 px-2"
                              >
                                <Copy className="h-3 w-3 mr-1" />
                                复制
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => goToTracker(file.trackerId!)}
                                className="h-7 px-2"
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                查看状态
                              </Button>
                            </div>
                          </div>
                        </div>
                        <p className="text-xs text-green-600 mt-2">
                          💡 请保存此跟踪ID，您可以随时使用它查询文件处理状态
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 支持的文件类型 */}
      <Card>
        <CardHeader>
          <CardTitle>支持的文件类型</CardTitle>
          <CardDescription>
            以下是系统支持的文件格式，单个文件大小限制为50MB
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {supportedFileTypes.map((category, index) => (
              <div key={index}>
                <h4 className="font-medium mb-2">{category.category}</h4>
                <div className="flex flex-wrap gap-2">
                  {category.types.map((type) => (
                    <Badge key={type} variant="outline">
                      {type}
                    </Badge>
                  ))}
                </div>
                {index < supportedFileTypes.length - 1 && <Separator className="mt-4" />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Turnstile验证模态框 */}
      {showTurnstileModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                安全验证
              </CardTitle>
              <CardDescription>
                为了防止机器人恶意上传，请完成以下安全验证
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {turnstileRetryCount > 0 && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    验证失败 {turnstileRetryCount}/{MAX_RETRY_COUNT} 次，请仔细完成验证步骤
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="flex justify-center">
                {turnstileConfig?.site_key && (
                  <TurnstileComponent
                    siteKey={turnstileConfig.site_key}
                    onVerify={handleTurnstileVerify}
                    onError={handleTurnstileError}
                    onExpire={handleTurnstileExpire}
                    onWidgetLoad={() => setTurnstileLoading(false)}
                  />
                )}
              </div>
              
              {turnstileLoading && (
                <div className="text-center">
                  <p className="text-sm text-muted-foreground">正在加载验证组件...</p>
                </div>
              )}
              
              <div className="flex justify-end">
                <Button
                  variant="outline"
                  onClick={() => setShowTurnstileModal(false)}
                >
                  取消
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default ModernUpload
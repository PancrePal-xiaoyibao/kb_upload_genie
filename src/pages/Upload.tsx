import React, { useState } from 'react'
import { 
  Card, 
  Typography, 
  Upload as AntUpload, 
  Button, 
  message, 
  Progress,
  List,
  Tag,
  Space,
  Alert,
  Modal
} from 'antd'
import { InboxOutlined, UploadOutlined, SecurityScanOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import TurnstileComponent from '../components/TurnstileComponent'
import { useTurnstileConfig } from '../hooks/useTurnstile'
import '../styles/turnstile.css'

const { Title, Paragraph } = Typography
const { Dragger } = AntUpload

interface FileItem {
  uid: string
  name: string
  status: 'ready' | 'uploading' | 'done' | 'error'
  percent: number
  type?: string
  size?: number
}

const Upload: React.FC = () => {
  const [fileList, setFileList] = useState<FileItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null)
  const [turnstileVerified, setTurnstileVerified] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [showTurnstileModal, setShowTurnstileModal] = useState(false)
  const [turnstileLoading, setTurnstileLoading] = useState(false)
  const [turnstileRetryCount, setTurnstileRetryCount] = useState(0)
  const [turnstileTimeout, setTurnstileTimeout] = useState<NodeJS.Timeout | null>(null)
  
  // 获取Turnstile配置
  const { config: turnstileConfig, error: configError } = useTurnstileConfig()

  // 最大重试次数
  const MAX_RETRY_COUNT = 3
  // 验证超时时间 (30秒)
  const VERIFICATION_TIMEOUT = 30000

  // Turnstile验证处理
  const handleTurnstileVerify = (token: string) => {
    if (turnstileTimeout) {
      clearTimeout(turnstileTimeout)
      setTurnstileTimeout(null)
    }
    
    // console.log('🔐 Turnstile验证成功，获得令牌:', token ? `${token.substring(0, 20)}...` : '空令牌')
    
    setTurnstileToken(token)
    setTurnstileVerified(true)
    setTurnstileLoading(false)
    setShowTurnstileModal(false)
    message.success('安全验证成功')
    
    // 验证成功后立即开始上传，直接传递token
    // console.log('🚀 立即开始上传，使用新获得的令牌')
    performUpload(token)
  }

  const handleTurnstileError = (error: string) => {
    if (turnstileTimeout) {
      clearTimeout(turnstileTimeout)
      setTurnstileTimeout(null)
    }
    
    setTurnstileLoading(false)
    setTurnstileRetryCount(prev => prev + 1)
    
    if (turnstileRetryCount >= MAX_RETRY_COUNT) {
      setShowTurnstileModal(false)
      setTurnstileToken(null)
      setTurnstileVerified(false)
      setTurnstileRetryCount(0)
      message.error(`安全验证失败次数过多，请稍后重试`)
      return
    }
    
    message.error(`安全验证失败: ${error}，请重试 (${turnstileRetryCount + 1}/${MAX_RETRY_COUNT})`)
  }

  const handleTurnstileExpire = () => {
    if (turnstileTimeout) {
      clearTimeout(turnstileTimeout)
      setTurnstileTimeout(null)
    }
    
    setTurnstileToken(null)
    setTurnstileVerified(false)
    setTurnstileLoading(false)
    message.warning('安全验证已过期，请重新验证')
  }

  // 开始验证流程
  const startTurnstileVerification = () => {
    setShowTurnstileModal(true)
    setTurnstileLoading(true)
    setTurnstileToken(null)
    setTurnstileVerified(false)
    
    // 设置超时
    const timeout = setTimeout(() => {
      setTurnstileLoading(false)
      setShowTurnstileModal(false)
      message.error('验证超时，请重试')
    }, VERIFICATION_TIMEOUT)
    
    setTurnstileTimeout(timeout)
  }

  // 关闭验证模态框
  const closeTurnstileModal = () => {
    if (turnstileTimeout) {
      clearTimeout(turnstileTimeout)
      setTurnstileTimeout(null)
    }
    setShowTurnstileModal(false)
    setTurnstileLoading(false)
    setTurnstileRetryCount(0)
  }

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    customRequest: () => {
      // 禁用自动上传，只处理文件选择
    },
    onChange(info) {
      // 更新文件列表状态，但不进行上传
      const newFileList = info.fileList.map(file => {
        const fileItem: FileItem = {
          uid: file.uid,
          name: file.name,
          status: 'ready' as any, // 设置为准备状态
          percent: 0,
          type: file.type,
          size: file.size
        }
        return fileItem
      })
      setFileList(newFileList)
      
      // 保存原始文件对象
      const files = info.fileList.map(file => file.originFileObj).filter(Boolean) as File[]
      setSelectedFiles(files)
    },
    onDrop(e) {
      console.log('Dropped files', e.dataTransfer.files)
    },
    beforeUpload: (file) => {
      // 检查文件大小 (50MB限制)
      const isLt50M = file.size / 1024 / 1024 < 50
      if (!isLt50M) {
        message.error('文件大小不能超过50MB!')
        return false
      }
      
      // 检查文件类型
      const allowedTypes = ['.md', '.txt', '.docx', '.pdf', '.pptx', '.js', '.ts', '.py', '.java', '.cpp', '.html', '.css', '.jpg', '.png', '.gif', '.svg', '.webp']
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
      
      if (!allowedTypes.includes(fileExtension)) {
        message.error(`不支持的文件类型: ${fileExtension}`)
        return false
      }
      
      // 允许选择文件，但不自动上传
      return false
    },
    showUploadList: false, // 我们使用自定义的文件列表显示
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      message.warning('请先选择要上传的文件')
      return
    }

    console.log('上传检查状态:', {
      turnstileEnabled: turnstileConfig?.enabled,
      turnstileVerified,
      turnstileToken: turnstileToken ? `${turnstileToken.substring(0, 20)}...` : null
    })

    // 如果启用了Turnstile验证，需要先进行验证
    if (turnstileConfig?.enabled && !turnstileVerified) {
      console.log('需要进行Turnstile验证')
      startTurnstileVerification()
      return
    }
    
    // 如果已验证或未启用验证，直接上传
    console.log('开始上传，跳过验证或已验证')
    await performUpload()
  }

  // 实际执行上传的函数
  const performUpload = async (providedToken?: string) => {
    // console.log('📤 开始执行上传，参数:', {
    //   providedToken: providedToken ? `${providedToken.substring(0, 20)}...` : null,
    //   stateToken: turnstileToken ? `${turnstileToken.substring(0, 20)}...` : null,
    //   turnstileEnabled: turnstileConfig?.enabled
    // })
    
    setUploading(true)
    
    try {
      // 逐个上传文件
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i]
        const fileItem = fileList.find(item => item.name === file.name)
        
        if (!fileItem) continue
        
        // 更新状态为上传中
        setFileList(prev => prev.map(item => 
          item.uid === fileItem.uid 
            ? { ...item, status: 'uploading', percent: 0 }
            : item
        ))
        
        try {
          const formData = new FormData()
          formData.append('file', file)
          
          // 添加Turnstile令牌
          if (turnstileConfig?.enabled) {
            // 优先使用提供的token，然后是状态中的token
            const tokenToSend = providedToken || turnstileToken || ''
            formData.append('turnstile_token', tokenToSend)
            // console.log('发送Turnstile令牌:', tokenToSend ? `${tokenToSend.substring(0, 20)}...` : '(空令牌)')
            
            // 如果没有令牌，这里就应该失败，让用户看到错误
            if (!tokenToSend) {
              console.warn('⚠️ 警告：启用了Turnstile但没有令牌，上传可能失败')
            }
          }
          
          const response = await fetch('http://localhost:8000/api/v1/upload', {
            method: 'POST',
            body: formData,
          })
          
          const result = await response.json()
          
          if (response.ok && result.success) {
            // 上传成功
            setFileList(prev => prev.map(item => 
              item.uid === fileItem.uid 
                ? { ...item, status: 'done', percent: 100 }
                : item
            ))
            message.success(`${file.name} 上传成功`)
          } else {
            // 上传失败
            setFileList(prev => prev.map(item => 
              item.uid === fileItem.uid 
                ? { ...item, status: 'error', percent: 0 }
                : item
            ))
            const errorMsg = result.detail || result.message || '未知错误'
            console.error('上传失败详情:', result)
            
            // 如果是Turnstile相关错误，提供特殊处理
            if (errorMsg.includes('Turnstile') || errorMsg.includes('验证令牌')) {
              message.error(`${file.name} 上传失败: ${errorMsg}`)
              // 重置验证状态，让用户重新验证
              setTurnstileVerified(false)
              setTurnstileToken(null)
            } else {
              message.error(`${file.name} 上传失败: ${errorMsg}`)
            }
          }
        } catch (error) {
          // 网络错误
          setFileList(prev => prev.map(item => 
            item.uid === fileItem.uid 
              ? { ...item, status: 'error', percent: 0 }
              : item
          ))
          message.error(`${file.name} 上传失败: 网络错误`)
        }
      }
      
      message.info('所有文件上传完成')
      
      // 上传完成后重置验证状态
      if (turnstileConfig?.enabled) {
        setTurnstileVerified(false)
        setTurnstileToken(null)
      }
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2}>文件上传</Title>
        <Paragraph>
          支持拖拽上传，自动识别文件类型并进行智能分类
        </Paragraph>
      </div>

      {/* 配置加载错误提示 */}
      {configError && (
        <Alert 
          message="配置加载失败" 
          description={configError}
          type="error" 
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Turnstile安全验证模态框 */}
      <Modal
        title={
          <Space>
            <SecurityScanOutlined />
            安全验证
          </Space>
        }
        open={showTurnstileModal}
        onCancel={closeTurnstileModal}
        footer={[
          <Button key="cancel" onClick={closeTurnstileModal}>
            取消
          </Button>
        ]}
        destroyOnClose={true}
        maskClosable={false}
        width={400}
      >
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Paragraph style={{ marginBottom: 20 }}>
            为了防止机器人恶意上传，请完成以下安全验证：
          </Paragraph>
          
          {turnstileRetryCount > 0 && (
            <Alert
              message={`验证失败 ${turnstileRetryCount}/${MAX_RETRY_COUNT} 次`}
              description="请仔细完成验证步骤"
              type="warning"
              style={{ marginBottom: 16 }}
            />
          )}
          
          {turnstileConfig?.site_key && (
            <TurnstileComponent
              siteKey={turnstileConfig.site_key}
              onVerify={handleTurnstileVerify}
              onError={handleTurnstileError}
              onExpire={handleTurnstileExpire}
              className="turnstile-container"
            />
          )}
          
          {turnstileLoading && (
            <div style={{ marginTop: 16 }}>
              <Paragraph type="secondary">正在加载验证组件...</Paragraph>
            </div>
          )}
        </div>
      </Modal>

      <Card title="上传文件" style={{ marginBottom: 24 }}>
        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或批量上传。严禁上传公司数据或其他敏感文件。
            {turnstileConfig?.enabled && (
              <>
                <br />
                <span style={{ color: '#1890ff' }}>点击"开始上传"按钮时将进行安全验证</span>
              </>
            )}
          </p>
        </Dragger>

        <div style={{ textAlign: 'center' }}>
          <Button
            type="primary"
            onClick={handleUpload}
            disabled={selectedFiles.length === 0 || uploading}
            loading={uploading}
            icon={<UploadOutlined />}
          >
            {uploading ? '上传中' : '开始上传'}
          </Button>
          {turnstileConfig?.enabled && !uploading && selectedFiles.length > 0 && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
              点击后将先进行安全验证，验证通过后自动开始上传
            </div>
          )}
        </div>
      </Card>

      <Card title="上传进度">
        {fileList.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            暂无上传文件
          </div>
        ) : (
          <List
            dataSource={fileList}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={item.name}
                  description={
                    <Space>
                      <Tag color={
                        item.status === 'done' ? 'green' : 
                        item.status === 'error' ? 'red' : 
                        item.status === 'uploading' ? 'blue' : 'default'
                      }>
                        {item.status === 'done' ? '完成' : 
                         item.status === 'error' ? '失败' : 
                         item.status === 'uploading' ? '上传中' : '就绪'}
                      </Tag>
                      {item.size && <span>{(item.size / 1024 / 1024).toFixed(2)} MB</span>}
                    </Space>
                  }
                />
                <div style={{ width: 200 }}>
                  <Progress 
                    percent={item.percent} 
                    status={item.status === 'error' ? 'exception' : undefined}
                    size="small"
                  />
                </div>
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card title="支持的文件类型" style={{ marginTop: 24 }}>
        <div>
          <Title level={4}>文档类型</Title>
          <Space wrap>
            <Tag>.pdf</Tag>
            <Tag>.doc</Tag>
            <Tag>.docx</Tag>
            <Tag>.txt</Tag>
            <Tag>.md</Tag>
          </Space>
        </div>
        <div style={{ marginTop: 16 }}>
          <Title level={4}>代码类型</Title>
          <Space wrap>
            <Tag>.js</Tag>
            <Tag>.ts</Tag>
            <Tag>.py</Tag>
            <Tag>.java</Tag>
            <Tag>.cpp</Tag>
            <Tag>.html</Tag>
            <Tag>.css</Tag>
          </Space>
        </div>
        <div style={{ marginTop: 16 }}>
          <Title level={4}>图片类型</Title>
          <Space wrap>
            <Tag>.jpg</Tag>
            <Tag>.png</Tag>
            <Tag>.gif</Tag>
            <Tag>.svg</Tag>
            <Tag>.webp</Tag>
          </Space>
        </div>
      </Card>
    </div>
  )
}

export default Upload
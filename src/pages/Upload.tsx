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
  Space
} from 'antd'
import { InboxOutlined, UploadOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'

const { Title, Paragraph } = Typography
const { Dragger } = AntUpload

interface FileItem {
  uid: string
  name: string
  status: 'uploading' | 'done' | 'error'
  percent: number
  type?: string
  size?: number
}

const Upload: React.FC = () => {
  const [fileList, setFileList] = useState<FileItem[]>([])
  const [uploading, setUploading] = useState(false)

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    action: 'http://localhost:8002/api/v1/upload',
    headers: {
      'Accept': 'application/json',
    },
    onChange(info) {
      const { status, response } = info.file
      
      // 更新文件列表状态
      const newFileList = info.fileList.map(file => ({
        uid: file.uid,
        name: file.name,
        status: file.status as 'uploading' | 'done' | 'error',
        percent: file.percent || 0,
        type: file.type,
        size: file.size
      }))
      setFileList(newFileList)
      
      if (status !== 'uploading') {
        console.log(info.file, info.fileList)
      }
      if (status === 'done') {
        if (response && response.success) {
          message.success(`${info.file.name} 文件上传成功`)
        } else {
          message.error(`${info.file.name} 上传失败: ${response?.message || '未知错误'}`)
        }
      } else if (status === 'error') {
        message.error(`${info.file.name} 文件上传失败`)
      }
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
      
      return true
    },
    showUploadList: false, // 我们使用自定义的文件列表显示
  }

  const handleUpload = () => {
    if (fileList.length === 0) {
      message.warning('请先选择要上传的文件')
      return
    }
    
    const pendingFiles = fileList.filter(file => file.status !== 'done')
    if (pendingFiles.length === 0) {
      message.info('所有文件已上传完成')
      return
    }
    
    message.info(`开始上传 ${pendingFiles.length} 个文件...`)
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 32 }}>
        <Title level={2}>文件上传</Title>
        <Paragraph>
          支持拖拽上传，自动识别文件类型并进行智能分类
        </Paragraph>
      </div>

      <Card title="上传文件" style={{ marginBottom: 24 }}>
        <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持单个或批量上传。严禁上传公司数据或其他敏感文件。
          </p>
        </Dragger>

        <div style={{ textAlign: 'center' }}>
          <Button
            type="primary"
            onClick={handleUpload}
            disabled={fileList.length === 0}
            loading={uploading}
            icon={<UploadOutlined />}
          >
            {uploading ? '上传中' : '开始上传'}
          </Button>
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
                      <Tag color={item.status === 'done' ? 'green' : item.status === 'error' ? 'red' : 'blue'}>
                        {item.status === 'done' ? '完成' : item.status === 'error' ? '失败' : '上传中'}
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
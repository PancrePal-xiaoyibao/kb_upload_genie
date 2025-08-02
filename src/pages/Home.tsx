import React from 'react'
import { Card, Typography, Row, Col, Button } from 'antd'
import { Link } from 'react-router-dom'
import { UploadOutlined, FileTextOutlined, RobotOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography

const Home: React.FC = () => {
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title level={1}>GitHub上传分类智能前端系统</Title>
        <Paragraph style={{ fontSize: 18, color: '#666' }}>
          智能化的文件上传和分类管理系统，让您的GitHub项目管理更加高效
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={8}>
          <Card
            hoverable
            style={{ height: '100%' }}
            cover={
              <div style={{ padding: 40, textAlign: 'center', backgroundColor: '#f0f2f5' }}>
                <UploadOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </div>
            }
          >
            <Card.Meta
              title="智能上传"
              description="支持多种文件格式的智能上传，自动识别文件类型并进行分类处理"
            />
            <div style={{ marginTop: 16 }}>
              <Link to="/upload">
                <Button type="primary" block>
                  开始上传
                </Button>
              </Link>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card
            hoverable
            style={{ height: '100%' }}
            cover={
              <div style={{ padding: 40, textAlign: 'center', backgroundColor: '#f0f2f5' }}>
                <FileTextOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              </div>
            }
          >
            <Card.Meta
              title="文件管理"
              description="高效的文件分类和管理功能，支持文件预览、编辑和版本控制"
            />
            <div style={{ marginTop: 16 }}>
              <Button block disabled>
                即将推出
              </Button>
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card
            hoverable
            style={{ height: '100%' }}
            cover={
              <div style={{ padding: 40, textAlign: 'center', backgroundColor: '#f0f2f5' }}>
                <RobotOutlined style={{ fontSize: 48, color: '#722ed1' }} />
              </div>
            }
          >
            <Card.Meta
              title="AI助手"
              description="集成AI助手功能，提供智能代码分析、文档生成和项目优化建议"
            />
            <div style={{ marginTop: 16 }}>
              <Button block disabled>
                即将推出
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      <div style={{ marginTop: 48, textAlign: 'center' }}>
        <Card>
          <Title level={3}>系统特性</Title>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4}>🚀 高性能</Title>
                <Paragraph>基于React + FastAPI构建，提供流畅的用户体验</Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4}>🔒 安全可靠</Title>
                <Paragraph>完善的权限控制和数据加密，保障文件安全</Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4}>🎯 智能分类</Title>
                <Paragraph>AI驱动的文件分类，自动识别和整理文件</Paragraph>
              </div>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <div>
                <Title level={4}>📱 响应式</Title>
                <Paragraph>完美适配各种设备，随时随地管理文件</Paragraph>
              </div>
            </Col>
          </Row>
        </Card>
      </div>
    </div>
  )
}

export default Home
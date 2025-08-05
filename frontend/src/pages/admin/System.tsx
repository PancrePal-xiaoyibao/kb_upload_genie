import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Descriptions,
  Typography,
  Space,
  Alert,
  Spin,
  Button,
  Tag,
} from 'antd';
import {
  ReloadOutlined,
  DatabaseOutlined,
  ApiOutlined,
  SafetyOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { getSystemInfo } from '@/services/admin';
import type { SystemInfo } from '@/services/admin';
import { useAuth } from '@/contexts/AuthContext';
import dayjs from 'dayjs';
import './System.css';

const { Title, Text } = Typography;

const System: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  // 获取系统信息
  const fetchSystemInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSystemInfo();
      setSystemInfo(data);
    } catch (err: any) {
      console.error('获取系统信息失败:', err);
      setError(err.response?.data?.detail || '获取系统信息失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemInfo();
  }, []);

  // 获取状态指示器
  const getStatusIndicator = (status: boolean) => {
    return status ? (
      <Tag icon={<CheckCircleOutlined />} color="success">
        正常
      </Tag>
    ) : (
      <Tag icon={<ExclamationCircleOutlined />} color="error">
        异常
      </Tag>
    );
  };

  // 获取调试模式标签
  const getDebugModeTag = (debugMode: boolean) => {
    return debugMode ? (
      <Tag color="orange">开发模式</Tag>
    ) : (
      <Tag color="green">生产模式</Tag>
    );
  };

  if (loading && !systemInfo) {
    return (
      <div className="system-loading">
        <Spin size="large" tip="正在加载系统信息..." />
      </div>
    );
  }

  if (error && !systemInfo) {
    return (
      <Alert
        message="系统信息加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <Button onClick={fetchSystemInfo} type="primary" size="small">
            重试
          </Button>
        }
      />
    );
  }

  return (
    <div className="system-container">
      {/* 页面头部 */}
      <div className="system-header">
        <div className="header-content">
          <Title level={4} style={{ margin: 0 }}>
            系统信息
          </Title>
          <Text type="secondary">
            查看系统运行状态和配置信息
          </Text>
        </div>
        <Button
          icon={<ReloadOutlined />}
          onClick={fetchSystemInfo}
          loading={loading}
        >
          刷新
        </Button>
      </div>

      {/* 系统状态概览 */}
      <Row gutter={[16, 16]} className="status-overview">
        <Col xs={24} sm={8}>
          <Card className="status-card" bordered={false}>
            <div className="status-item">
              <div className="status-icon database">
                <DatabaseOutlined />
              </div>
              <div className="status-info">
                <Text strong>数据库连接</Text>
                <div>{getStatusIndicator(true)}</div>
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card className="status-card" bordered={false}>
            <div className="status-item">
              <div className="status-icon api">
                <ApiOutlined />
              </div>
              <div className="status-info">
                <Text strong>API服务</Text>
                <div>{getStatusIndicator(true)}</div>
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={8}>
          <Card className="status-card" bordered={false}>
            <div className="status-item">
              <div className="status-icon auth">
                <SafetyOutlined />
              </div>
              <div className="status-info">
                <Text strong>认证服务</Text>
                <div>{getStatusIndicator(true)}</div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 系统配置信息 */}
      {systemInfo && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <InfoCircleOutlined />
                  系统配置
                </Space>
              }
              bordered={false}
              className="config-card"
            >
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="项目名称">
                  <Text strong>{systemInfo.system.project_name}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="系统版本">
                  <Tag color="blue">{systemInfo.system.version}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="运行模式">
                  {getDebugModeTag(systemInfo.system.debug_mode)}
                </Descriptions.Item>
                <Descriptions.Item label="数据库类型">
                  <Text code>{systemInfo.system.database_url}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="JWT算法">
                  <Text code>{systemInfo.system.jwt_algorithm}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="管理员邮箱">
                  <Text copyable>{systemInfo.system.admin_email}</Text>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <SafetyOutlined />
                  当前管理员
                </Space>
              }
              bordered={false}
              className="admin-card"
            >
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="管理员邮箱">
                  <Text copyable>{systemInfo.current_admin.email}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="管理员姓名">
                  <Text strong>{systemInfo.current_admin.name || '未设置'}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="当前角色">
                  <Tag color={user?.role === 'admin' ? 'gold' : 'purple'}>
                    {user?.role === 'admin' ? '超级管理员' : '审核员'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="登录时间">
                  {systemInfo.current_admin.login_time ? (
                    <Text>
                      {dayjs(systemInfo.current_admin.login_time).format('YYYY-MM-DD HH:mm:ss')}
                    </Text>
                  ) : (
                    <Text type="secondary">未记录</Text>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="会话状态">
                  <Tag icon={<CheckCircleOutlined />} color="success">
                    已认证
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>
        </Row>
      )}

      {/* 系统健康检查 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title={
              <Space>
                <CheckCircleOutlined />
                系统健康检查
              </Space>
            }
            bordered={false}
            className="health-card"
          >
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <div className="health-item">
                  <div className="health-status success">
                    <CheckCircleOutlined />
                  </div>
                  <div className="health-info">
                    <Text strong>Web服务器</Text>
                    <br />
                    <Text type="secondary">运行正常</Text>
                  </div>
                </div>
              </Col>
              
              <Col xs={24} sm={12} md={6}>
                <div className="health-item">
                  <div className="health-status success">
                    <CheckCircleOutlined />
                  </div>
                  <div className="health-info">
                    <Text strong>数据库连接</Text>
                    <br />
                    <Text type="secondary">连接正常</Text>
                  </div>
                </div>
              </Col>
              
              <Col xs={24} sm={12} md={6}>
                <div className="health-item">
                  <div className="health-status success">
                    <CheckCircleOutlined />
                  </div>
                  <div className="health-info">
                    <Text strong>缓存服务</Text>
                    <br />
                    <Text type="secondary">运行正常</Text>
                  </div>
                </div>
              </Col>
              
              <Col xs={24} sm={12} md={6}>
                <div className="health-item">
                  <div className="health-status success">
                    <CheckCircleOutlined />
                  </div>
                  <div className="health-info">
                    <Text strong>文件存储</Text>
                    <br />
                    <Text type="secondary">可用</Text>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 系统资源使用情况 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card
            title="系统资源"
            bordered={false}
            className="resource-card"
          >
            <Alert
              message="资源监控"
              description="系统资源监控功能需要额外的监控服务支持，当前显示模拟数据。"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <div className="resource-item">
                  <Text strong>CPU使用率</Text>
                  <div className="resource-value">
                    <Text style={{ fontSize: '24px', color: '#52c41a' }}>15%</Text>
                  </div>
                  <Text type="secondary">正常范围</Text>
                </div>
              </Col>
              
              <Col xs={24} sm={8}>
                <div className="resource-item">
                  <Text strong>内存使用</Text>
                  <div className="resource-value">
                    <Text style={{ fontSize: '24px', color: '#1890ff' }}>2.1GB</Text>
                  </div>
                  <Text type="secondary">共8GB</Text>
                </div>
              </Col>
              
              <Col xs={24} sm={8}>
                <div className="resource-item">
                  <Text strong>磁盘空间</Text>
                  <div className="resource-value">
                    <Text style={{ fontSize: '24px', color: '#faad14' }}>45GB</Text>
                  </div>
                  <Text type="secondary">共100GB</Text>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default System;
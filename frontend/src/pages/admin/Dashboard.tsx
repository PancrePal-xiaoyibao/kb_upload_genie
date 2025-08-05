import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Space,
  Alert,
  Spin,
  Progress,
} from 'antd';
import {
  UserOutlined,
  TeamOutlined,
  CrownOutlined,
  SafetyOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { getDashboardData } from '@/services/admin';
import type { DashboardStats } from '@/services/admin';
import { useAuth } from '@/contexts/AuthContext';
import './Dashboard.css';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  // 获取仪表板数据
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDashboardData();
      setDashboardData(data);
    } catch (err: any) {
      console.error('获取仪表板数据失败:', err);
      setError(err.response?.data?.detail || '获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // 计算用户活跃度百分比
  const getActiveUserPercentage = () => {
    if (!dashboardData?.system_stats) return 0;
    const { total_users, active_users } = dashboardData.system_stats;
    return total_users > 0 ? Math.round((active_users / total_users) * 100) : 0;
  };

  // 统计卡片配置
  const getStatisticCards = () => {
    if (!dashboardData?.system_stats) return [];

    const { system_stats } = dashboardData;
    
    return [
      {
        title: '总用户数',
        value: system_stats.total_users,
        icon: <TeamOutlined />,
        color: '#1890ff',
        suffix: '人',
      },
      {
        title: '活跃用户',
        value: system_stats.active_users,
        icon: <UserOutlined />,
        color: '#52c41a',
        suffix: '人',
      },
      {
        title: '管理员',
        value: system_stats.admin_users,
        icon: <CrownOutlined />,
        color: '#faad14',
        suffix: '人',
      },
      {
        title: '审核员',
        value: system_stats.moderator_users,
        icon: <SafetyOutlined />,
        color: '#722ed1',
        suffix: '人',
      },
    ];
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <Spin size="large" tip="正在加载仪表板数据..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="数据加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <button onClick={fetchDashboardData} className="retry-btn">
            重试
          </button>
        }
      />
    );
  }

  return (
    <div className="dashboard-container">
      {/* 欢迎信息 */}
      <Card className="welcome-card" bordered={false}>
        <Row align="middle">
          <Col flex="auto">
            <Space direction="vertical" size="small">
              <Title level={3} style={{ margin: 0, color: '#262626' }}>
                {dashboardData?.message || '欢迎访问管理员仪表板'}
              </Title>
              <Text type="secondary">
                当前登录用户：{user?.name || user?.email} ({user?.role === 'admin' ? '管理员' : '审核员'})
              </Text>
            </Space>
          </Col>
          <Col>
            <div className="welcome-icon">
              <TrophyOutlined />
            </div>
          </Col>
        </Row>
      </Card>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="statistics-row">
        {getStatisticCards().map((card, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card className="statistic-card" bordered={false}>
              <div className="statistic-content">
                <div className="statistic-icon" style={{ backgroundColor: card.color }}>
                  {card.icon}
                </div>
                <div className="statistic-info">
                  <Statistic
                    title={card.title}
                    value={card.value}
                    suffix={card.suffix}
                    valueStyle={{ color: card.color, fontSize: '24px', fontWeight: 'bold' }}
                  />
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 详细统计 */}
      <Row gutter={[16, 16]} className="details-row">
        {/* 用户活跃度 */}
        <Col xs={24} lg={12}>
          <Card title="用户活跃度" bordered={false} className="detail-card">
            <div className="activity-content">
              <Progress
                type="circle"
                percent={getActiveUserPercentage()}
                format={(percent) => `${percent}%`}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                size={120}
              />
              <div className="activity-info">
                <Space direction="vertical" size="small">
                  <Text strong>活跃用户比例</Text>
                  <Text type="secondary">
                    {dashboardData?.system_stats.active_users} / {dashboardData?.system_stats.total_users} 用户处于活跃状态
                  </Text>
                </Space>
              </div>
            </div>
          </Card>
        </Col>

        {/* 用户角色分布 */}
        <Col xs={24} lg={12}>
          <Card title="用户角色分布" bordered={false} className="detail-card">
            <div className="role-distribution">
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div className="role-item">
                  <div className="role-info">
                    <UserOutlined style={{ color: '#1890ff' }} />
                    <span>普通用户</span>
                  </div>
                  <div className="role-count">
                    {dashboardData?.system_stats.regular_users || 0}
                  </div>
                </div>
                <div className="role-item">
                  <div className="role-info">
                    <SafetyOutlined style={{ color: '#722ed1' }} />
                    <span>审核员</span>
                  </div>
                  <div className="role-count">
                    {dashboardData?.system_stats.moderator_users || 0}
                  </div>
                </div>
                <div className="role-item">
                  <div className="role-info">
                    <CrownOutlined style={{ color: '#faad14' }} />
                    <span>管理员</span>
                  </div>
                  <div className="role-count">
                    {dashboardData?.system_stats.admin_users || 0}
                  </div>
                </div>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 系统状态 */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="系统状态" bordered={false} className="system-status-card">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <div className="status-item">
                  <div className="status-indicator status-online"></div>
                  <div className="status-info">
                    <Text strong>数据库连接</Text>
                    <br />
                    <Text type="secondary">正常</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div className="status-item">
                  <div className="status-indicator status-online"></div>
                  <div className="status-info">
                    <Text strong>API服务</Text>
                    <br />
                    <Text type="secondary">运行中</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={8}>
                <div className="status-item">
                  <div className="status-indicator status-online"></div>
                  <div className="status-info">
                    <Text strong>认证服务</Text>
                    <br />
                    <Text type="secondary">正常</Text>
                  </div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
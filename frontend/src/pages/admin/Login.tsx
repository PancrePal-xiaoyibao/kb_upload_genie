import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { adminLogin, storeUserInfo } from '@/services/auth';
import type { LoginParams } from '@/services/auth';
import './Login.css';

const { Title, Text } = Typography;

const AdminLogin: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (values: LoginParams) => {
    setLoading(true);
    try {
      const response = await adminLogin(values);
      
      // 检查用户角色是否为管理员或审核员
      if (!['admin', 'moderator'].includes(response.user.role)) {
        message.error('权限不足，仅管理员和审核员可以访问');
        return;
      }

      // 使用后端返回的用户信息
      const userInfo = response.user;
      
      // 存储认证信息 - 使用token.access_token
      storeUserInfo(response.token.access_token, userInfo);
      
      // 更新认证状态
      login(userInfo);
      
      message.success('登录成功');
      navigate('/admin/dashboard');
    } catch (error: any) {
      console.error('登录失败:', error);
      message.error(error.response?.data?.detail || '登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-background">
        <div className="login-overlay" />
      </div>
      
      <Card className="login-card" bordered={false}>
        <div className="login-header">
          <Space direction="vertical" align="center" size="large">
            <div className="login-logo">
              <LoginOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
            </div>
            <Title level={2} style={{ margin: 0, color: '#262626' }}>
              管理员登录
            </Title>
            <Text type="secondary">
              知识库上传系统 - 后台管理
            </Text>
          </Space>
        </div>

        <Form
          form={form}
          name="admin-login"
          onFinish={handleSubmit}
          autoComplete="off"
          size="large"
          className="login-form"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="管理员邮箱"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位字符' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              className="login-button"
            >
              {loading ? '登录中...' : '登录'}
            </Button>
          </Form.Item>
        </Form>

        <div className="login-footer">
          <Text type="secondary" style={{ fontSize: '12px' }}>
            © 2024 知识库上传系统. 保留所有权利.
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default AdminLogin;
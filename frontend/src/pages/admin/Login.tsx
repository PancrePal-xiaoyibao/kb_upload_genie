import React, { useState } from 'react';
import { Form, Input, Button, Card, message, Typography, Space, Alert, Modal } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined, SafetyOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { adminLogin, storeUserInfo } from '@/services/auth';
import type { LoginParams } from '@/services/auth';
import TurnstileComponent from '@/components/TurnstileComponent';
import { useTurnstileConfig } from '@/hooks/useTurnstile';
import './Login.css';

const { Title, Text } = Typography;

const AdminLogin: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const { login } = useAuth();
  
  // Turnstile相关状态
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileVerified, setTurnstileVerified] = useState(false);
  const [turnstileError, setTurnstileError] = useState<string | null>(null);
  const [showTurnstileModal, setShowTurnstileModal] = useState(false);
  const [pendingFormValues, setPendingFormValues] = useState<LoginParams | null>(null);
  
  // 获取Turnstile配置
  const { config: turnstileConfig, loading: configLoading, error: configError } = useTurnstileConfig();

  // Turnstile验证处理函数
  const handleTurnstileVerify = (token: string) => {
    setTurnstileToken(token);
    setTurnstileVerified(true);
    setTurnstileError(null);
    setShowTurnstileModal(false);
    
    // 验证成功后自动提交表单
    if (pendingFormValues) {
      performLogin(pendingFormValues, token);
    }
  };

  const handleTurnstileError = (error: string) => {
    setTurnstileError(error);
    setTurnstileVerified(false);
    setTurnstileToken(null);
  };

  const handleTurnstileExpire = () => {
    setTurnstileToken(null);
    setTurnstileVerified(false);
    setTurnstileError(null);
  };

  const handleSubmit = async (values: LoginParams) => {
    // 如果启用了Turnstile验证且未验证，先显示验证组件
    if (turnstileConfig?.enabled && !turnstileVerified) {
      setPendingFormValues(values);
      setShowTurnstileModal(true);
      return;
    }

    await performLogin(values);
  };

  const performLogin = async (values: LoginParams, providedToken?: string) => {
    setLoading(true);
    try {
      // 构建登录参数，包含Turnstile token
      const loginParams: LoginParams = { ...values };
      
      if (turnstileConfig?.enabled) {
        const tokenToSend = providedToken || turnstileToken;
        if (tokenToSend) {
          loginParams.turnstile_token = tokenToSend;
        }
      }

      console.log('开始登录:', loginParams);
      const response = await adminLogin(loginParams);
      
      // 检查用户角色是否为管理员或审核员
      if (!['admin', 'moderator'].includes(response.user.role)) {
        message.error('权限不足，仅管理员和审核员可以访问');
        return;
      }

      // 使用后端返回的用户信息
      const userInfo = response.user;
      
      // 存储认证信息
      storeUserInfo(response.token.access_token, userInfo);
      
      // 更新认证状态
      login(userInfo);
      
      message.success('登录成功');
      navigate('/admin/dashboard');
      
      // 登录成功后重置Turnstile状态
      if (turnstileConfig?.enabled) {
        setTurnstileVerified(false);
        setTurnstileToken(null);
      }
      
    } catch (error: any) {
      console.error('登录失败:', error);
      
      let errorMessage = '登录失败，请检查用户名和密码';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      message.error(errorMessage);
      
      // 如果是Turnstile相关错误，重置验证状态
      if (errorMessage.includes('Turnstile') || errorMessage.includes('验证令牌')) {
        setTurnstileVerified(false);
        setTurnstileToken(null);
      }
    } finally {
      setLoading(false);
      setPendingFormValues(null);
    }
  };


  return (
    <div className="login-container">
      <div className="login-background">
        <div className="login-overlay" />
      </div>
      
      <Card className="login-card" variant="outlined">
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

        {/* 配置加载状态和错误提示 */}
        {configLoading && (
          <Alert
            message="正在加载安全验证配置..."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        
        {configError && (
          <Alert
            message="配置加载失败"
            description={configError}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Turnstile错误提示 */}
        {turnstileError && (
          <Alert
            message="安全验证失败"
            description={turnstileError}
            type="error"
            showIcon
            closable
            onClose={() => setTurnstileError(null)}
            style={{ marginBottom: 16 }}
          />
        )}

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
              disabled={configLoading}
              block
              size="large"
              className="login-button"
            >
              {loading ? '登录中...' : configLoading ? '加载配置中...' : '登录'}
            </Button>
          </Form.Item>
        </Form>

        {/* Turnstile提示信息 */}
        {turnstileConfig?.enabled && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              <SafetyOutlined style={{ marginRight: 4 }} />
              登录时将进行安全验证以防止机器人攻击
            </Text>
          </div>
        )}

        <div className="login-footer">
          <Text type="secondary" style={{ fontSize: '12px' }}>
            © 2024 知识库上传系统. 保留所有权利.
          </Text>
        </div>
      </Card>

      {/* Turnstile验证模态框 - 使用模拟验证 */}
      <Modal
        title={
          <Space>
            <SafetyOutlined />
            安全验证
          </Space>
        }
        open={showTurnstileModal}
        onCancel={() => {
          setShowTurnstileModal(false);
          setPendingFormValues(null);
        }}
        footer={null}
        centered
        destroyOnClose
      >
        <div style={{ textAlign: 'center', padding: '20px 0' }}>
          <Text type="secondary" style={{ display: 'block', marginBottom: 20 }}>
            为了防止机器人恶意登录，请完成以下安全验证
          </Text>
          
          {turnstileError && (
            <Alert
              message={turnstileError}
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          
          {/* 真实的Turnstile验证组件 */}
          {turnstileConfig?.site_key && (
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <TurnstileComponent
                siteKey={turnstileConfig.site_key}
                onVerify={handleTurnstileVerify}
                onError={handleTurnstileError}
                onExpire={handleTurnstileExpire}
              />
            </div>
          )}
          
          {!turnstileConfig?.site_key && (
            <Alert
              message="验证组件加载失败"
              description="无法获取验证配置，请稍后重试"
              type="error"
              showIcon
            />
          )}
        </div>
      </Modal>
    </div>
  );
};

export default AdminLogin;
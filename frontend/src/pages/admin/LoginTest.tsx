import React from 'react';
import { Form, Input, Button, Card, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';

const { Title } = Typography;

const LoginTest: React.FC = () => {
  const handleSubmit = (values: any) => {
    console.log('登录信息:', values);
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      backgroundColor: '#f0f2f5'
    }}>
      <Card style={{ width: 400, padding: 20 }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2}>管理员登录</Title>
        </div>
        
        <Form onFinish={handleSubmit} size="large">
          <Form.Item
            name="email"
            rules={[{ required: true, message: '请输入邮箱' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="邮箱"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default LoginTest;
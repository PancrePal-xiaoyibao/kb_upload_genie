import React, { useState } from 'react';
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Space,
  Typography,
  Breadcrumb,
  Button,
  message,
} from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  TeamOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { logout } from '@/services/auth';
import './AdminLayout.css';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

const AdminLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout: authLogout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // 菜单项配置
  const menuItems = [
    {
      key: '/admin/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/admin/users',
      icon: <TeamOutlined />,
      label: '用户管理',
    },
    {
      key: '/admin/system',
      icon: <InfoCircleOutlined />,
      label: '系统信息',
    },
  ];

  // 面包屑映射
  const breadcrumbMap: Record<string, string> = {
    '/admin': '管理后台',
    '/admin/dashboard': '仪表板',
    '/admin/users': '用户管理',
    '/admin/system': '系统信息',
  };

  // 生成面包屑
  const generateBreadcrumb = () => {
    const pathSnippets = location.pathname.split('/').filter(i => i);
    const breadcrumbItems = pathSnippets.map((_, index) => {
      const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
      const name = breadcrumbMap[url] || pathSnippets[index];
      return {
        title: name,
      };
    });
    
    return breadcrumbItems;
  };

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  // 处理退出登录
  const handleLogout = async () => {
    try {
      await logout();
      authLogout();
      message.success('退出登录成功');
      navigate('/admin/login');
    } catch (error) {
      console.error('退出登录失败:', error);
      // 即使API调用失败，也要清除本地状态
      authLogout();
      navigate('/admin/login');
    }
  };

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
      onClick: () => message.info('个人资料功能开发中'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
      onClick: () => message.info('设置功能开发中'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <div className="admin-layout-container">
      <Layout className="admin-layout">
      {/* 侧边栏 */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="admin-sider"
        width={240}
      >
        {/* Logo区域 */}
        <div className="admin-logo">
          <div className="logo-icon">
            <SettingOutlined />
          </div>
          {!collapsed && (
            <div className="logo-text">
              <Title level={4} style={{ color: 'white', margin: 0 }}>
                管理后台
              </Title>
            </div>
          )}
        </div>

        {/* 导航菜单 */}
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          className="admin-menu"
        />

        {/* 版本信息 */}
        {!collapsed && (
          <div className="admin-version">
            <Text type="secondary" style={{ fontSize: '12px' }}>
              v1.0.0
            </Text>
          </div>
        )}
      </Sider>

      {/* 主内容区域 */}
      <Layout className="admin-main">
        {/* 顶部导航栏 */}
        <Header className="admin-header">
          <div className="header-left">
            <Button
              type="text"
              icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              className="collapse-btn"
            />
          </div>

          <div className="header-right">
            <Space size="middle">
              <Text type="secondary">
                欢迎回来，{user?.name || user?.email}
              </Text>
              
              <Dropdown
                menu={{ items: userMenuItems }}
                placement="bottomRight"
                arrow
              >
                <Space className="user-info" style={{ cursor: 'pointer' }}>
                  <Avatar
                    size="small"
                    icon={<UserOutlined />}
                    style={{ backgroundColor: '#1890ff' }}
                  />
                  <Text strong>{user?.name || '管理员'}</Text>
                </Space>
              </Dropdown>
            </Space>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content className="admin-content">
          {/* 面包屑导航 */}
          <div className="content-breadcrumb">
            <Breadcrumb items={generateBreadcrumb()} />
          </div>

          {/* 页面内容 */}
          <div className="content-main">
            <Outlet />
          </div>
        </Content>
      </Layout>
    </div>
  );
};

export default AdminLayout;
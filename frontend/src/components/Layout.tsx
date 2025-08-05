import React from 'react'
import { Layout as AntLayout, Menu, Typography, Button, Space } from 'antd'
import { Link, useLocation, Outlet } from 'react-router-dom'
import { HomeOutlined, UploadOutlined, SettingOutlined } from '@ant-design/icons'

const { Header, Content, Footer } = AntLayout
const { Title } = Typography

const Layout: React.FC = () => {
  const location = useLocation()

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: '/upload',
      icon: <UploadOutlined />,
      label: <Link to="/upload">文件上传</Link>,
    },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Title level={3} style={{ color: 'white', margin: 0, marginRight: 24 }}>
            知识库上传系统
          </Title>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{ minWidth: 0 }}
          />
        </div>
        
        <Space>
          <Link to="/admin/login">
            <Button 
              type="primary" 
              icon={<SettingOutlined />}
              style={{ background: 'rgba(255, 255, 255, 0.2)', border: 'none' }}
            >
              管理后台
            </Button>
          </Link>
        </Space>
      </Header>
      
      <Content style={{ padding: '24px', background: '#f5f5f5' }}>
        <div style={{ background: '#fff', padding: '24px', borderRadius: '8px', minHeight: '500px' }}>
          <Outlet />
        </div>
      </Content>
      
      <Footer style={{ textAlign: 'center', background: '#001529', color: 'rgba(255, 255, 255, 0.65)' }}>
        知识库上传系统 ©2024 Created with ❤️
      </Footer>
    </AntLayout>
  )
}

export default Layout

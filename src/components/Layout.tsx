import React from 'react'
import { Layout as AntLayout, Menu, Typography } from 'antd'
import { Link, useLocation } from 'react-router-dom'
import { HomeOutlined, UploadOutlined } from '@ant-design/icons'

const { Header, Content, Footer } = AntLayout
const { Title } = Typography

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
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
      <Header style={{ display: 'flex', alignItems: 'center' }}>
        <Title level={3} style={{ color: 'white', margin: 0, marginRight: 24 }}>
          KB Upload Genie
        </Title>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ padding: '24px' }}>
        {children}
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        KB Upload Genie ©2024 Created by AI Assistant
      </Footer>
    </AntLayout>
  )
}

export default Layout
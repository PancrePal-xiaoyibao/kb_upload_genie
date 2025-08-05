import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AuthProvider } from '@/contexts/AuthContext';
import ProtectedRoute from '@/components/ProtectedRoute';
import AdminLayout from '@/components/AdminLayout';
import Layout from '@/components/Layout';
import AdminLogin from '@/pages/admin/Login';
import Dashboard from '@/pages/admin/Dashboard';
import Users from '@/pages/admin/Users';
import System from '@/pages/admin/System';
import Home from '@/pages/Home';
import Upload from '@/pages/Upload';
import 'dayjs/locale/zh-cn';
import './App.css';

// 配置 dayjs 中文
import dayjs from 'dayjs';
dayjs.locale('zh-cn');

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* 主站路由 */}
              <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="upload" element={<Upload />} />
              </Route>
              
              {/* 管理员登录页面 */}
              <Route path="/admin/login" element={<AdminLogin />} />
              
              {/* 管理员后台路由 */}
              <Route
                path="/admin"
                element={
                  <ProtectedRoute>
                    <AdminLayout />
                  </ProtectedRoute>
                }
              >
                {/* 默认重定向到仪表板 */}
                <Route index element={<Navigate to="/admin/dashboard" replace />} />
                
                {/* 仪表板 */}
                <Route path="dashboard" element={<Dashboard />} />
                
                {/* 用户管理 */}
                <Route path="users" element={<Users />} />
                
                {/* 系统信息 */}
                <Route path="system" element={<System />} />
              </Route>
              
              {/* 404 页面重定向到首页 */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  );
};

export default App;

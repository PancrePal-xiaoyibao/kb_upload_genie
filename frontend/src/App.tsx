import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import ModernProtectedRoute from '@/components/ModernProtectedRoute';
import ModernAdminLayout from '@/components/ModernAdminLayout';
import ModernLayout from '@/components/ModernLayout';
import ErrorBoundary from '@/components/ErrorBoundary';
import { ToastProvider } from '@/components/Toast';
import AdminLogin from '@/pages/admin/Login';
import Dashboard from '@/pages/admin/Dashboard';
import Users from '@/pages/admin/Users';
import System from '@/pages/admin/System';
import Home from '@/pages/Home';
import Upload from '@/pages/Upload';
import TrackerQuery from '@/pages/TrackerQuery';
import TrackerTest from '@/pages/TrackerTest';
import './App.css';

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AuthProvider>
          <Router>
            <div className="App">
              <Routes>
                {/* 主站路由 */}
                <Route path="/" element={<ModernLayout />}>
                  <Route index element={<Home />} />
                  <Route path="upload" element={<Upload />} />
                </Route>
                
                {/* 跟踪查询页面（独立路由，不需要布局） */}
                <Route path="/tracker" element={<TrackerQuery />} />
                <Route path="/tracker-test" element={<TrackerTest />} />
                
                {/* 管理员登录页面 */}
                <Route path="/admin/login" element={<AdminLogin />} />
                
                {/* 管理员后台路由 */}
                <Route
                  path="/admin"
                  element={
                    <ModernProtectedRoute>
                      <ModernAdminLayout />
                    </ModernProtectedRoute>
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
      </ToastProvider>
    </ErrorBoundary>
  );
};

export default App;
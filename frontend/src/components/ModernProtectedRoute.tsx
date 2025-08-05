import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

interface ModernProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: string[]
}

const ModernProtectedRoute: React.FC<ModernProtectedRouteProps> = ({ 
  children, 
  requiredRole = ['admin', 'moderator'] 
}) => {
  const { isAuthenticated, user, loading } = useAuth()
  const location = useLocation()

  // 显示加载状态
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">正在验证身份...</p>
        </div>
      </div>
    )
  }

  // 未认证，重定向到登录页
  if (!isAuthenticated || !user) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />
  }

  // 检查角色权限
  if (requiredRole.length > 0 && !requiredRole.includes(user.role)) {
    return <Navigate to="/admin/login" replace />
  }

  return <>{children}</>
}

export default ModernProtectedRoute
import React, { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { 
  Menu, 
  X, 
  LayoutDashboard, 
  Users, 
  Info, 
  LogOut, 
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'
import { useAuth } from '@/contexts/AuthContext'
import { logout } from '@/services/auth'
import { cn } from '@/lib/utils'

const ModernAdminLayout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { user, logout: authLogout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const navigationItems = [
    {
      name: '仪表板',
      href: '/admin/dashboard',
      icon: LayoutDashboard,
    },
    {
      name: '用户管理',
      href: '/admin/users',
      icon: Users,
    },
    {
      name: '系统信息',
      href: '/admin/system',
      icon: Info,
    },
  ]

  const isActive = (href: string) => location.pathname === href

  const handleLogout = async () => {
    try {
      await logout()
      authLogout()
      navigate('/admin/login')
    } catch (error) {
      console.error('退出登录失败:', error)
      authLogout()
      navigate('/admin/login')
    }
  }

  const SidebarContent = ({ isMobile = false }) => (
    <div className="flex flex-col h-full">
      {/* Logo区域 */}
      <div className="flex items-center px-6 py-4 border-b">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <Settings className="h-4 w-4 text-primary-foreground" />
          </div>
          {(!sidebarCollapsed || isMobile) && (
            <div>
              <h2 className="text-lg font-semibold">管理后台</h2>
            </div>
          )}
        </div>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 px-4 py-4 space-y-2">
        {navigationItems.map((item) => {
          const Icon = item.icon
          return (
            <button
              key={item.href}
              onClick={() => {
                navigate(item.href)
                if (isMobile) setMobileMenuOpen(false)
              }}
              className={cn(
                "w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors text-left",
                isActive(item.href)
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              <Icon className="h-4 w-4 flex-shrink-0" />
              {(!sidebarCollapsed || isMobile) && <span>{item.name}</span>}
            </button>
          )
        })}
      </nav>

      {/* 版本信息 */}
      {(!sidebarCollapsed || isMobile) && (
        <div className="px-6 py-4 border-t">
          <p className="text-xs text-muted-foreground">v1.0.0</p>
        </div>
      )}
    </div>
  )

  return (
    <div className="min-h-screen bg-background flex">
      {/* 桌面端侧边栏 */}
      <aside className={cn(
        "hidden lg:flex flex-col border-r bg-card transition-all duration-300",
        sidebarCollapsed ? "w-16" : "w-64"
      )}>
        <SidebarContent />
        
        {/* 折叠按钮 */}
        <div className="absolute -right-3 top-20 z-10">
          <Button
            variant="outline"
            size="icon"
            className="h-6 w-6 rounded-full bg-background border shadow-md"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-3 w-3" />
            ) : (
              <ChevronLeft className="h-3 w-3" />
            )}
          </Button>
        </div>
      </aside>

      {/* 主内容区域 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 顶部导航栏 */}
        <header className="h-16 border-b bg-card flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center space-x-4">
            {/* 移动端菜单按钮 */}
            <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="lg:hidden"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64 p-0">
                <SidebarContent isMobile />
              </SheetContent>
            </Sheet>

            <div className="lg:hidden">
              <h1 className="text-lg font-semibold">管理后台</h1>
            </div>
          </div>

          {/* 用户信息和操作 */}
          <div className="flex items-center space-x-4">
            <span className="hidden sm:inline-block text-sm text-muted-foreground">
              欢迎回来，{user?.name || user?.email}
            </span>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      {user?.name?.[0] || user?.email?.[0] || 'A'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <div className="flex items-center justify-start gap-2 p-2">
                  <div className="flex flex-col space-y-1 leading-none">
                    <p className="font-medium">{user?.name || '管理员'}</p>
                    <p className="text-xs text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>退出登录</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* 面包屑导航 */}
        <div className="px-4 lg:px-6 py-4 border-b bg-muted/30">
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <span>管理后台</span>
            <span>/</span>
            <span className="text-foreground">
              {navigationItems.find(item => isActive(item.href))?.name || '页面'}
            </span>
          </div>
        </div>

        {/* 页面内容 */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

export default ModernAdminLayout
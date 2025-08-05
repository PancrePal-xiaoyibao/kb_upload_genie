import React, { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Menu, X, Home, Upload, Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { cn } from '@/lib/utils'

const ModernLayout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()

  const navigationItems = [
    {
      name: '首页',
      href: '/',
      icon: Home,
    },
    {
      name: '文件上传',
      href: '/upload',
      icon: Upload,
    },
  ]

  const isActive = (href: string) => location.pathname === href

  const NavigationContent = ({ isMobile = false }) => (
    <nav className={cn(
      "flex",
      isMobile ? "flex-col space-y-2" : "flex-row space-x-1"
    )}>
      {navigationItems.map((item) => {
        const Icon = item.icon
        return (
          <Link
            key={item.href}
            to={item.href}
            className={cn(
              "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              isActive(item.href)
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-muted"
            )}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <Icon className="h-4 w-4" />
            <span>{item.name}</span>
          </Link>
        )
      })}
    </nav>
  )

  return (
    <div className="min-h-screen bg-background">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          {/* Logo和标题 */}
          <div className="flex items-center space-x-4">
            {/* 移动端菜单按钮 */}
            <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="md:hidden"
                >
                  <Menu className="h-5 w-5" />
                  <span className="sr-only">打开菜单</span>
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-64">
                <div className="flex flex-col space-y-4 py-4">
                  <div className="px-3">
                    <h2 className="text-lg font-semibold">知识库上传系统</h2>
                  </div>
                  <NavigationContent isMobile={true} />
                </div>
              </SheetContent>
            </Sheet>

            <Link to="/" className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">KB</span>
              </div>
              <span className="font-bold text-xl hidden sm:inline-block">
                知识库上传系统
              </span>
            </Link>
          </div>

          {/* 桌面端导航 */}
          <div className="hidden md:flex items-center space-x-6">
            <NavigationContent isMobile={false} />
          </div>

          {/* 右侧操作区 */}
          <div className="flex items-center space-x-4">
            <Link to="/admin/login">
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                管理后台
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>

      {/* 底部 */}
      <footer className="border-t bg-muted/50">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-sm text-muted-foreground">
            <p>知识库上传系统 ©2024 Created with ❤️</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default ModernLayout
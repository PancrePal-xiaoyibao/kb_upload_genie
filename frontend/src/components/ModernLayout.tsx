import React, { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { cn } from '@/lib/utils'

const ModernLayout: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const location = useLocation()

  const navigationItems = [
    {
      name: '功能特性',
      href: '/',
    },
    {
      name: '文件上传',
      href: '/upload',
    },
  ]

  const isActive = (href: string) => location.pathname === href

  return (
    <div className="min-h-screen bg-white">
      {/* 顶部导航栏 - 简洁设计 */}
      <header className="sticky top-0 z-50 w-full bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/95">
        <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-6">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">KB</span>
              </div>
              <span className="font-bold text-xl text-gray-900">知识库上传系统</span>
            </div>
          </Link>

          {/* 桌面端导航 */}
          <nav className="hidden md:flex items-center space-x-8">
            {navigationItems.map((item) => (
              <Link
                key={item.href}
                to={item.href}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-emerald-600",
                  isActive(item.href)
                    ? "text-emerald-600"
                    : "text-gray-600"
                )}
              >
                {item.name}
              </Link>
            ))}
          </nav>

          {/* 右侧按钮组 */}
          <div className="hidden md:flex items-center space-x-4">
            <Link to="/admin/login">
              <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-900">
                管理后台
              </Button>
            </Link>
            <Link to="/upload">
              <Button size="sm" className="bg-emerald-500 hover:bg-emerald-600 text-white">
                开始上传
              </Button>
            </Link>
          </div>

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
            <SheetContent side="right" className="w-64">
              <div className="flex flex-col space-y-4 py-4">
                <div className="px-3">
                  <h2 className="text-lg font-semibold">知识库上传系统</h2>
                </div>
                <nav className="flex flex-col space-y-2">
                  {navigationItems.map((item) => (
                    <Link
                      key={item.href}
                      to={item.href}
                      className={cn(
                        "px-3 py-2 text-sm font-medium transition-colors hover:bg-gray-100 rounded-lg",
                        isActive(item.href)
                          ? "text-emerald-600 bg-emerald-50"
                          : "text-gray-600"
                      )}
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      {item.name}
                    </Link>
                  ))}
                  <div className="border-t pt-4 mt-4">
                    <Link to="/admin/login" onClick={() => setIsMobileMenuOpen(false)}>
                      <Button variant="ghost" size="sm" className="w-full justify-start">
                        管理后台
                      </Button>
                    </Link>
                    <Link to="/upload" onClick={() => setIsMobileMenuOpen(false)}>
                      <Button size="sm" className="w-full mt-2 bg-emerald-500 hover:bg-emerald-600 text-white">
                        开始上传
                      </Button>
                    </Link>
                  </div>
                </nav>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* 底部 - 简洁设计 */}
      <footer className="border-t bg-gray-50">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="text-center text-sm text-gray-500">
            <p>知识库上传系统 ©2024 Created with ❤️</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default ModernLayout

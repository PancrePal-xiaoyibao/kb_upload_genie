import React from 'react'
import { Link } from 'react-router-dom'
import { Upload, FileText, Bot, Rocket, Shield, Target, Smartphone } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const ModernHome: React.FC = () => {
  const features = [
    {
      icon: Upload,
      title: '智能上传',
      description: '支持多种文件格式的智能上传，自动识别文件类型并进行分类处理',
      action: '开始上传',
      href: '/upload',
      available: true,
      color: 'text-blue-500'
    },
    {
      icon: FileText,
      title: '文件管理',
      description: '高效的文件分类和管理功能，支持文件预览、编辑和版本控制',
      action: '即将推出',
      href: '#',
      available: false,
      color: 'text-green-500'
    },
    {
      icon: Bot,
      title: 'AI助手',
      description: '集成AI助手功能，提供智能代码分析、文档生成和项目优化建议',
      action: '即将推出',
      href: '#',
      available: false,
      color: 'text-purple-500'
    }
  ]

  const systemFeatures = [
    {
      icon: Rocket,
      title: '高性能',
      description: '基于React + FastAPI构建，提供流畅的用户体验'
    },
    {
      icon: Shield,
      title: '安全可靠',
      description: '完善的权限控制和数据加密，保障文件安全'
    },
    {
      icon: Target,
      title: '智能分类',
      description: 'AI驱动的文件分类，自动识别和整理文件'
    },
    {
      icon: Smartphone,
      title: '响应式设计',
      description: '完美适配各种设备，随时随地管理文件'
    }
  ]

  return (
    <div className="space-y-12">
      {/* 英雄区域 */}
      <div className="text-center space-y-6">
        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
            GitHub上传分类
            <span className="text-primary">智能前端系统</span>
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            智能化的文件上传和分类管理系统，让您的GitHub项目管理更加高效
          </p>
        </div>
      </div>

      {/* 主要功能卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <Card key={index} className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
              <CardHeader className="text-center pb-4">
                <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4 group-hover:bg-primary/10 transition-colors">
                  <Icon className={`h-8 w-8 ${feature.color} group-hover:scale-110 transition-transform`} />
                </div>
                <CardTitle className="text-xl">{feature.title}</CardTitle>
                <CardDescription className="text-sm">
                  {feature.description}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                {feature.available ? (
                  <Link to={feature.href}>
                    <Button className="w-full" size="lg">
                      {feature.action}
                    </Button>
                  </Link>
                ) : (
                  <Button className="w-full" size="lg" disabled>
                    {feature.action}
                  </Button>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 系统特性 */}
      <div className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">系统特性</h2>
          <p className="text-muted-foreground text-lg">
            为您提供全方位的文件管理解决方案
          </p>
        </div>
        
        <Card>
          <CardContent className="p-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              {systemFeatures.map((feature, index) => {
                const Icon = feature.icon
                return (
                  <div key={index} className="text-center space-y-4">
                    <div className="mx-auto w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-semibold text-lg">{feature.title}</h3>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 行动号召 */}
      <div className="text-center space-y-6 py-12">
        <div className="space-y-4">
          <h2 className="text-3xl font-bold">开始使用</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            立即体验我们的智能文件上传系统，让文件管理变得更加简单高效
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/upload">
            <Button size="lg" className="px-8">
              <Upload className="mr-2 h-5 w-5" />
              开始上传文件
            </Button>
          </Link>
          <Link to="/admin/login">
            <Button variant="outline" size="lg" className="px-8">
              管理后台
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default ModernHome
import React from 'react'
import { Link } from 'react-router-dom'
import { Upload, ArrowRight, Zap, Shield, Target, Smartphone } from 'lucide-react'
import { Button } from '@/components/ui/button'

const ModernHome: React.FC = () => {
  const features = [
    {
      icon: Zap,
      title: '高性能上传',
      description: '基于现代化技术栈构建，提供流畅的文件上传体验',
    },
    {
      icon: Shield,
      title: '安全可靠',
      description: '完善的权限控制和数据加密，保障您的文件安全',
    },
    {
      icon: Target,
      title: '智能分类',
      description: 'AI驱动的文件分类，自动识别和整理您的文件',
    },
    {
      icon: Smartphone,
      title: '响应式设计',
      description: '完美适配各种设备，随时随地管理您的文件',
    },
  ]

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-16">
        <div className="text-center space-y-8">
          {/* 装饰性边框 */}
          <div className="relative">
            <div className="absolute -top-4 -left-4 w-8 h-8 border-l-2 border-t-2 border-emerald-400"></div>
            <div className="absolute -top-4 -right-4 w-8 h-8 border-r-2 border-t-2 border-emerald-400"></div>
            <div className="absolute -bottom-4 -left-4 w-8 h-8 border-l-2 border-b-2 border-emerald-400"></div>
            <div className="absolute -bottom-4 -right-4 w-8 h-8 border-r-2 border-b-2 border-emerald-400"></div>
            
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 leading-tight">
              智能化文件上传系统
              <br />
              <span className="text-emerald-500">节省 90%</span> 的管理时间
            </h1>
          </div>
          
          <div className="space-y-4 max-w-4xl mx-auto">
            <p className="text-xl text-gray-600 leading-relaxed">
              将手动文件管理转换为自动化工作流程，使用先进的AI模型进行智能分类。
            </p>
            <p className="text-xl text-gray-600 leading-relaxed">
              无需技术知识，支持中文交互，让文件管理变得简单高效。
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-8">
            <Link to="/upload">
              <Button 
                size="lg" 
                className="px-8 py-4 text-lg bg-emerald-500 hover:bg-emerald-600 text-white font-medium"
              >
                开始上传
              </Button>
            </Link>
            <Link to="/admin/login">
              <Button 
                variant="outline" 
                size="lg" 
                className="px-8 py-4 text-lg border-gray-900 text-gray-900 hover:bg-gray-900 hover:text-white font-medium"
              >
                管理后台
              </Button>
            </Link>
          </div>

          <p className="text-sm text-gray-500 pt-4">
            支持多种上传方式
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-4xl mx-auto px-6 py-20">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div key={index} className="text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto">
                  <Icon className="h-8 w-8 text-emerald-600" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-semibold text-gray-900">{feature.title}</h3>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* Secondary CTA Section */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-6 text-center space-y-8">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900">
            准备好提升您的文件管理效率了吗？
          </h2>
          <p className="text-xl text-gray-600 leading-relaxed">
            立即体验我们的智能文件上传系统，让繁琐的文件管理工作变得简单高效。
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <Link to="/upload">
              <Button 
                size="lg" 
                className="px-8 py-4 text-lg bg-emerald-500 hover:bg-emerald-600 text-white font-medium group"
              >
                立即开始
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

export default ModernHome
import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'

interface TurnstileDebuggerProps {
  siteKey: string
  enabled: boolean
}

interface DebugInfo {
  domain: string
  protocol: string
  userAgent: string
  timestamp: number
  siteKey: string
  turnstileLoaded: boolean
  networkStatus: 'online' | 'offline'
  dnsResolution: boolean
  cloudflareReachable: boolean
}

/**
 * Turnstile 调试工具组件
 */
const TurnstileDebugger: React.FC<TurnstileDebuggerProps> = ({ siteKey, enabled }) => {
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null)
  const [testing, setTesting] = useState(false)
  const [testResults, setTestResults] = useState<string[]>([])

  useEffect(() => {
    collectDebugInfo()
  }, [siteKey])

  const collectDebugInfo = () => {
    const info: DebugInfo = {
      domain: window.location.hostname,
      protocol: window.location.protocol,
      userAgent: navigator.userAgent,
      timestamp: Date.now(),
      siteKey,
      turnstileLoaded: !!(window as any).turnstile,
      networkStatus: navigator.onLine ? 'online' : 'offline',
      dnsResolution: true, // 将通过测试确定
      cloudflareReachable: true // 将通过测试确定
    }
    setDebugInfo(info)
  }

  const runDiagnostics = async () => {
    setTesting(true)
    setTestResults([])
    const results: string[] = []

    try {
      // 测试 1: 检查站点密钥格式
      results.push('🔍 检查站点密钥格式...')
      if (!siteKey || siteKey.length < 10) {
        results.push('❌ 站点密钥格式无效')
      } else if (siteKey.startsWith('1x0000000000000000000')) {
        results.push('⚠️ 使用测试密钥，可能在生产环境中失效')
      } else {
        results.push('✅ 站点密钥格式正常')
      }

      // 测试 2: 检查域名配置
      results.push('🔍 检查域名配置...')
      const currentDomain = window.location.hostname
      if (currentDomain === 'localhost' || currentDomain === '127.0.0.1') {
        results.push('⚠️ 本地开发环境，确保 Turnstile 配置允许本地域名')
      } else {
        results.push(`✅ 当前域名: ${currentDomain}`)
      }

      // 测试 3: 检查网络连接
      results.push('🔍 检查网络连接...')
      try {
        const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/api.js', {
          method: 'HEAD',
          mode: 'no-cors'
        })
        results.push('✅ Cloudflare Turnstile API 可访问')
      } catch (error) {
        results.push('❌ 无法访问 Cloudflare Turnstile API')
        results.push(`错误详情: ${error}`)
      }

      // 测试 4: 检查浏览器兼容性
      results.push('🔍 检查浏览器兼容性...')
      const userAgent = navigator.userAgent
      if (userAgent.includes('Chrome') || userAgent.includes('Firefox') || userAgent.includes('Safari')) {
        results.push('✅ 浏览器兼容性正常')
      } else {
        results.push('⚠️ 浏览器可能不完全兼容')
      }

      // 测试 5: 检查 CSP 和安全策略
      results.push('🔍 检查内容安全策略...')
      const metaTags = document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]')
      if (metaTags.length > 0) {
        results.push('⚠️ 检测到 CSP 策略，确保允许 challenges.cloudflare.com')
      } else {
        results.push('✅ 未检测到限制性 CSP 策略')
      }

      // 测试 6: 检查 Turnstile 脚本加载
      results.push('🔍 检查 Turnstile 脚本加载...')
      if ((window as any).turnstile) {
        results.push('✅ Turnstile 脚本已加载')
      } else {
        results.push('❌ Turnstile 脚本未加载')
      }

    } catch (error) {
      results.push(`❌ 诊断过程中出现错误: ${error}`)
    }

    setTestResults(results)
    setTesting(false)
  }

  const getSiteKeyStatus = () => {
    if (!siteKey) return { status: 'error', text: '未配置' }
    if (siteKey.startsWith('1x0000000000000000000')) return { status: 'warning', text: '测试密钥' }
    return { status: 'success', text: '已配置' }
  }

  if (!enabled) {
    return (
      <Alert>
        <AlertDescription>
          Turnstile 验证已禁用
        </AlertDescription>
      </Alert>
    )
  }

  const siteKeyStatus = getSiteKeyStatus()

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Turnstile 调试工具</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {debugInfo && (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <strong>当前域名:</strong> {debugInfo.domain}
            </div>
            <div>
              <strong>协议:</strong> {debugInfo.protocol}
            </div>
            <div>
              <strong>站点密钥:</strong> 
              <Badge 
                variant={siteKeyStatus.status === 'error' ? 'destructive' : 
                        siteKeyStatus.status === 'warning' ? 'secondary' : 'default'}
                className="ml-2"
              >
                {siteKeyStatus.text}
              </Badge>
            </div>
            <div>
              <strong>网络状态:</strong> 
              <Badge variant={debugInfo.networkStatus === 'online' ? 'default' : 'destructive'} className="ml-2">
                {debugInfo.networkStatus}
              </Badge>
            </div>
            <div className="col-span-2">
              <strong>用户代理:</strong> {debugInfo.userAgent.substring(0, 80)}...
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <Button onClick={runDiagnostics} disabled={testing}>
            {testing ? '诊断中...' : '运行诊断'}
          </Button>
          <Button variant="outline" onClick={collectDebugInfo}>
            刷新信息
          </Button>
        </div>

        {testResults.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-semibold">诊断结果:</h4>
            <div className="bg-gray-50 p-3 rounded-md max-h-60 overflow-y-auto">
              {testResults.map((result, index) => (
                <div key={index} className="text-sm font-mono">
                  {result}
                </div>
              ))}
            </div>
          </div>
        )}

        <Alert>
          <AlertDescription>
            <strong>常见 400020 错误解决方案:</strong>
            <ul className="mt-2 space-y-1 text-sm">
              <li>• 确保站点密钥与当前域名匹配</li>
              <li>• 检查 Cloudflare Turnstile 控制台中的域名白名单</li>
              <li>• 验证网络连接和防火墙设置</li>
              <li>• 确保浏览器允许第三方 cookies</li>
              <li>• 检查内容安全策略 (CSP) 配置</li>
            </ul>
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  )
}

export default TurnstileDebugger
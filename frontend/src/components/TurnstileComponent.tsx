import React, { useRef, useEffect } from 'react'
import { Turnstile } from '@marsidev/react-turnstile'

interface TurnstileComponentProps {
  siteKey: string
  onVerify: (token: string) => void
  onError?: (error: string) => void
  onExpire?: () => void
  onWidgetLoad?: (widgetId: string) => void
  className?: string
}

/**
 * Cloudflare Turnstile验证组件
 */
const TurnstileComponent: React.FC<TurnstileComponentProps> = ({
  siteKey,
  onVerify,
  onError,
  onExpire,
  onWidgetLoad,
  className
}) => {
  const turnstileRef = useRef<any>(null)

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (turnstileRef.current) {
        try {
          turnstileRef.current.reset?.()
        } catch (error) {
          console.warn('Error resetting Turnstile:', error)
        }
      }
    }
  }, [])

  const handleError = (errorCode: string | Error) => {
    console.error('Turnstile error:', errorCode)
    console.error('Current site key:', siteKey)
    console.error('Current domain:', window.location.hostname)
    console.error('Current protocol:', window.location.protocol)
    
    let errorMessage = '验证失败'
    
    if (typeof errorCode === 'string') {
      switch (errorCode) {
        case '400020':
          errorMessage = '验证配置错误：站点密钥与当前域名不匹配或网络连接问题'
          console.error('Turnstile 400020 错误详情:', {
            siteKey,
            domain: window.location.hostname,
            protocol: window.location.protocol,
            userAgent: navigator.userAgent
          })
          break
        case 'expired':
          errorMessage = '验证已过期，请重新验证'
          break
        case 'timeout':
          errorMessage = '验证超时，请检查网络连接'
          break
        case 'invalid-input-response':
          errorMessage = '无效的验证响应'
          break
        case 'missing-input-response':
          errorMessage = '缺少验证响应'
          break
        case 'invalid-input-secret':
          errorMessage = '验证配置错误：无效的密钥配置'
          break
        case 'network-error':
          errorMessage = '网络连接错误，请检查网络设置'
          break
        case 'invalid-sitekey':
          errorMessage = '无效的站点密钥配置'
          break
        case 'missing-sitekey':
          errorMessage = '缺少站点密钥配置'
          break
        default:
          errorMessage = `验证失败: ${errorCode}`
          console.error('未知的 Turnstile 错误代码:', errorCode)
      }
    } else if (errorCode instanceof Error) {
      errorMessage = `验证失败: ${errorCode.message}`
      console.error('Turnstile Error 对象:', errorCode)
    }
    
    onError?.(errorMessage)
  }

  return (
    <div className={className}>
      <Turnstile
        ref={turnstileRef}
        siteKey={siteKey}
        onSuccess={onVerify}
        onError={handleError}
        onExpire={() => {
          console.warn('Turnstile expired')
          onExpire?.()
        }}
        onWidgetLoad={(widgetId) => {
          console.log('Turnstile widget loaded:', widgetId)
          onWidgetLoad?.(widgetId)
        }}
        options={{
          theme: 'light',
          size: 'normal',
          language: 'zh-cn',
          retry: 'auto',
          'retry-interval': 8000,
          'refresh-expired': 'auto',
          'response-field': true,
          'response-field-name': 'cf-turnstile-response',
          'error-callback': handleError,
          'execution': 'render',
          'appearance': 'always',
          'cData': {
            'chlPageData': JSON.stringify({
              domain: window.location.hostname,
              timestamp: Date.now(),
              userAgent: navigator.userAgent.substring(0, 100)
            })
          }
        } as any}
      />
    </div>
  )
}

export default TurnstileComponent

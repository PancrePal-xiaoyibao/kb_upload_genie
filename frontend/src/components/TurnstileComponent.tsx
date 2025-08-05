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
    
    let errorMessage = '验证失败'
    
    if (typeof errorCode === 'string') {
      switch (errorCode) {
        case 'expired':
          errorMessage = '验证已过期'
          break
        case 'timeout':
          errorMessage = '验证超时'
          break
        case 'invalid-input-response':
          errorMessage = '无效的验证响应'
          break
        case 'missing-input-response':
          errorMessage = '缺少验证响应'
          break
        case 'invalid-input-secret':
          errorMessage = '验证配置错误'
          break
        case 'network-error':
          errorMessage = '网络连接错误'
          break
        default:
          errorMessage = `验证失败: ${errorCode}`
      }
    } else if (errorCode instanceof Error) {
      errorMessage = `验证失败: ${errorCode.message}`
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
          'refresh-expired': 'auto',
          'response-field': true,
          'response-field-name': 'cf-turnstile-response'
        } as any}
      />
    </div>
  )
}

export default TurnstileComponent

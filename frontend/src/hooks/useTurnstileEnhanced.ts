import { useState, useEffect, useCallback, useRef } from 'react'
import { useTurnstileConfig } from './useTurnstile'

interface TurnstileState {
  token: string | null
  verified: boolean
  loading: boolean
  error: string | null
  retryCount: number
  widgetId: string | null
}

interface TurnstileActions {
  verify: (token: string) => void
  handleError: (error: string) => void
  handleExpire: () => void
  reset: () => void
  retry: () => void
  setLoading: (loading: boolean) => void
}

interface UseTurnstileEnhancedOptions {
  maxRetries?: number
  retryDelay?: number
  autoRetry?: boolean
  onSuccess?: (token: string) => void
  onError?: (error: string, retryCount: number) => void
  onMaxRetriesReached?: () => void
}

/**
 * 增强的 Turnstile Hook，提供更好的错误处理和重试机制
 */
export const useTurnstileEnhanced = (options: UseTurnstileEnhancedOptions = {}) => {
  const {
    maxRetries = 3,
    retryDelay = 2000,
    autoRetry = true,
    onSuccess,
    onError,
    onMaxRetriesReached
  } = options

  const { config, loading: configLoading, error: configError } = useTurnstileConfig()
  const retryTimeoutRef = useRef<NodeJS.Timeout>()

  const [state, setState] = useState<TurnstileState>({
    token: null,
    verified: false,
    loading: false,
    error: null,
    retryCount: 0,
    widgetId: null
  })

  // 清理定时器
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
    }
  }, [])

  // 重置状态
  const reset = useCallback(() => {
    setState({
      token: null,
      verified: false,
      loading: false,
      error: null,
      retryCount: 0,
      widgetId: null
    })
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
    }
  }, [])

  // 设置加载状态
  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({ ...prev, loading }))
  }, [])

  // 验证成功处理
  const verify = useCallback((token: string) => {
    setState(prev => ({
      ...prev,
      token,
      verified: true,
      loading: false,
      error: null,
      retryCount: 0
    }))
    onSuccess?.(token)
  }, [onSuccess])

  // 错误处理
  const handleError = useCallback((error: string) => {
    setState(prev => {
      const newRetryCount = prev.retryCount + 1
      const shouldRetry = autoRetry && newRetryCount <= maxRetries

      // 特殊处理 400020 错误
      let processedError = error
      if (error.includes('400020')) {
        processedError = `验证配置错误 (400020): 站点密钥与域名不匹配或网络问题。重试 ${newRetryCount}/${maxRetries}`
      }

      const newState = {
        ...prev,
        error: processedError,
        loading: false,
        retryCount: newRetryCount,
        verified: false,
        token: null
      }

      // 触发错误回调
      onError?.(processedError, newRetryCount)

      // 如果达到最大重试次数
      if (newRetryCount > maxRetries) {
        onMaxRetriesReached?.()
        return newState
      }

      // 自动重试
      if (shouldRetry) {
        retryTimeoutRef.current = setTimeout(() => {
          setState(current => ({
            ...current,
            loading: true,
            error: null
          }))
        }, retryDelay)
      }

      return newState
    })
  }, [autoRetry, maxRetries, retryDelay, onError, onMaxRetriesReached])

  // 过期处理
  const handleExpire = useCallback(() => {
    setState(prev => ({
      ...prev,
      token: null,
      verified: false,
      loading: false,
      error: '验证已过期，请重新验证'
    }))
  }, [])

  // 手动重试
  const retry = useCallback(() => {
    if (state.retryCount < maxRetries) {
      setState(prev => ({
        ...prev,
        loading: true,
        error: null,
        retryCount: prev.retryCount + 1
      }))
    }
  }, [state.retryCount, maxRetries])

  // Widget 加载处理
  const handleWidgetLoad = useCallback((widgetId: string) => {
    setState(prev => ({
      ...prev,
      widgetId,
      loading: false
    }))
  }, [])

  const actions: TurnstileActions = {
    verify,
    handleError,
    handleExpire,
    reset,
    retry,
    setLoading
  }

  return {
    // 状态
    ...state,
    config,
    configLoading,
    configError,
    
    // 计算属性
    canRetry: state.retryCount < maxRetries,
    isMaxRetriesReached: state.retryCount >= maxRetries,
    
    // 操作方法
    ...actions,
    handleWidgetLoad,
    
    // 调试信息
    debugInfo: {
      retryCount: state.retryCount,
      maxRetries,
      autoRetry,
      retryDelay,
      widgetId: state.widgetId,
      configEnabled: config?.enabled,
      siteKey: config?.site_key
    }
  }
}

export default useTurnstileEnhanced
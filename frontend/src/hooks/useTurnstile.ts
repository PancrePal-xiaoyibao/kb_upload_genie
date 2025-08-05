import { useState, useEffect } from 'react'
import axios from 'axios'

interface TurnstileConfig {
  enabled: boolean
  site_key: string | null
}

/**
 * Turnstile配置钩子
 */
export const useTurnstileConfig = () => {
  const [config, setConfig] = useState<TurnstileConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await axios.get('/api/v1/turnstile/config')
        setConfig(response.data)
      } catch (err) {
        setError('获取Turnstile配置失败')
        console.error('Error fetching Turnstile config:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [])

  return { config, loading, error }
}

import axios from 'axios'

const client = axios.create({
  baseURL: '/shj',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

client.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      const message = data?.error?.message || data?.message || '请求失败'

      if (status === 503) {
        window.dispatchEvent(new CustomEvent('api-notification', {
          detail: { type: 'warning', title: 'AI 服务暂不可用', content: 'Hermes Agent 当前无法响应，请稍后重试' }
        }))
      }

      return Promise.reject({ status, message, code: data?.error?.code })
    }
    if (error.code === 'ECONNABORTED') {
      return Promise.reject({ status: 0, message: '请求超时，请检查网络连接' })
    }
    return Promise.reject({ status: 0, message: '网络错误，请检查连接' })
  }
)

export default client

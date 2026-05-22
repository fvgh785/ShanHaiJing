import client from './client'

export function generatePrompt(data) {
  return client.post('/api/v1/hermes/generate-prompt', data)
}

export function reviewStyle(data) {
  return client.post('/api/v1/hermes/review-style', data)
}

export function fetchHermesLogs(params = {}) {
  return client.get('/api/v1/hermes/logs', { params })
}

export function fetchHermesLog(id) {
  return client.get(`/api/v1/hermes/logs/${id}`)
}

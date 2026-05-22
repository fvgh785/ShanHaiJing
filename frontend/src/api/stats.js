import client from './client'

export function fetchStats() {
  return client.get('/api/v1/stats')
}

export function fetchDashboard() {
  return client.get('/api/v1/stats/dashboard')
}

export function updateQuota(tool, data) {
  return client.put(`/api/v1/stats/quota/${tool}`, data)
}

import client from './client'

export function fetchBaselines(params = {}) {
  return client.get('/api/v1/baselines', { params })
}

export function fetchBaseline(id) {
  return client.get(`/api/v1/baselines/${id}`)
}

export function createBaseline(data) {
  return client.post('/api/v1/baselines', data)
}

export function updateBaseline(id, data) {
  return client.put(`/api/v1/baselines/${id}`, data)
}

export function activateBaseline(id) {
  return client.post(`/api/v1/baselines/${id}/activate`)
}

export function deleteBaseline(id) {
  return client.delete(`/api/v1/baselines/${id}`)
}

export function fetchBaselineVersions(id) {
  return client.get(`/api/v1/baselines/${id}/versions`)
}

import client from './client'

export function fetchRecords(params = {}) {
  return client.get('/api/v1/records', { params })
}

export function fetchRecord(id) {
  return client.get(`/api/v1/records/${id}`)
}

export function createRecord(data) {
  return client.post('/api/v1/records', data)
}

export function updateRecord(id, data) {
  return client.put(`/api/v1/records/${id}`, data)
}

export function deleteRecord(id) {
  return client.delete(`/api/v1/records/${id}`)
}

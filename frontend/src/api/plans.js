import client from './client'

export function fetchPlans(params = {}) {
  return client.get('/api/v1/plans', { params })
}

export function fetchPlan(id) {
  return client.get(`/api/v1/plans/${id}`)
}

export function createPlan(data) {
  return client.post('/api/v1/plans', data)
}

export function updatePlan(id, data) {
  return client.put(`/api/v1/plans/${id}`, data)
}

export function patchPlanStatus(id, status) {
  return client.patch(`/api/v1/plans/${id}/status`, { status })
}

export function deletePlan(id) {
  return client.delete(`/api/v1/plans/${id}`)
}

export function importPlansCSV(formData) {
  return client.post('/api/v1/plans/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

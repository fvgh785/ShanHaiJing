import client from './client'

export function exportAllData() {
  return client.get('/api/v1/data/export', { responseType: 'blob' })
}

export function exportFilteredData(params) {
  return client.post('/api/v1/data/export', params, { responseType: 'blob' })
}

export function importData(formData) {
  return client.post('/api/v1/data/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export function fetchBackups() {
  return client.get('/api/v1/data/backups')
}

export function downloadBackup(backupId) {
  return client.get(`/api/v1/data/backups/${backupId}/download`, { responseType: 'blob' })
}

export function deleteBackup(backupId) {
  return client.delete(`/api/v1/data/backups/${backupId}`)
}

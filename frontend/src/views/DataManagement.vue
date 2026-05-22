<template>
  <div class="data-page">
    <div class="page-header">
      <h2 class="page-title">数据管理</h2>
    </div>

    <n-space vertical :size="20">
      <n-card title="导出数据" size="small">
        <n-space vertical>
          <n-text depth="3">导出全部数据为 JSON 文件，可用于备份或迁移</n-text>
          <n-button type="primary" :loading="exportingAll" @click="handleExportAll">
            导出全部数据
          </n-button>
        </n-space>

        <n-divider />

        <n-text depth="3" style="display: block; margin-bottom: 8px">按条件筛选导出</n-text>
        <n-space align="end" wrap>
          <n-form-item label="日期范围" label-placement="left">
            <n-date-picker
              v-model:formatted-value="exportFilters.dateRange"
              type="daterange"
              clearable
              style="width: 240px"
            />
          </n-form-item>
          <n-form-item label="异兽名称">
            <n-input v-model:value="exportFilters.creature_name" placeholder="可选过滤" clearable style="width: 160px" />
          </n-form-item>
          <n-button :loading="exportingFiltered" @click="handleExportFiltered">筛选导出</n-button>
        </n-space>
      </n-card>

      <n-card title="导入数据" size="small">
        <n-space vertical>
          <n-text depth="3">从 JSON 文件导入数据（会合并到现有数据中）</n-text>
          <n-upload
            accept=".json"
            :show-file-list="true"
            :max="1"
            @change="handleImportFile"
          >
            <n-button>选择 JSON 文件</n-button>
          </n-upload>
          <n-alert v-if="importResult" :type="importResult.type" :title="importResult.title" closable style="margin-top: 8px" />
        </n-space>
      </n-card>

      <n-card title="备份管理" size="small">
        <n-spin :show="backupsLoading">
          <n-empty v-if="!backups.length && !backupsLoading" description="暂无备份文件" size="small" style="padding: 24px 0" />
          <n-table v-else :single-line="false" size="small">
            <thead>
              <tr>
                <th>文件名</th>
                <th>创建时间</th>
                <th>大小</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="bk in backups" :key="bk.id">
                <td>{{ bk.filename || bk.name || '-' }}</td>
                <td>{{ bk.created_at || '-' }}</td>
                <td>{{ formatSize(bk.size) }}</td>
                <td>
                  <n-space>
                    <n-button size="small" quaternary type="primary" :loading="downloadingId === bk.id" @click="handleDownload(bk)">
                      下载
                    </n-button>
                    <n-popconfirm @positive="handleDeleteBackup(bk.id)">
                      <n-button size="small" quaternary type="error">删除</n-button>
                    </n-popconfirm>
                  </n-space>
                </td>
              </tr>
            </tbody>
          </n-table>
        </n-spin>
      </n-card>
    </n-space>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { exportAllData, exportFilteredData, importData, fetchBackups, downloadBackup, deleteBackup } from '../api/data'

const message = useMessage()

const exportingAll = ref(false)
const exportingFiltered = ref(false)
const importResult = ref(null)
const backups = ref([])
const backupsLoading = ref(false)
const downloadingId = ref(null)

const exportFilters = ref({
  dateRange: null,
  creature_name: ''
})

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

async function handleExportAll() {
  exportingAll.value = true
  try {
    const res = await exportAllData()
    const blob = res instanceof Blob ? res : new Blob([JSON.stringify(res)], { type: 'application/json' })
    downloadBlob(blob, `shanhaijing-export-${new Date().toISOString().slice(0, 10)}.json`)
    message.success('导出成功')
  } catch (err) {
    message.error('导出失败: ' + (err.message || '未知错误'))
  } finally {
    exportingAll.value = false
  }
}

async function handleExportFiltered() {
  exportingFiltered.value = true
  try {
    const params = {}
    if (exportFilters.value.creature_name) params.creature_name = exportFilters.value.creature_name
    if (exportFilters.value.dateRange) {
      const [start, end] = exportFilters.value.dateRange
      params.date_from = start
      params.date_to = end
    }
    const res = await exportFilteredData(params)
    const blob = res instanceof Blob ? res : new Blob([JSON.stringify(res)], { type: 'application/json' })
    downloadBlob(blob, `shanhaijing-filtered-export-${new Date().toISOString().slice(0, 10)}.json`)
    message.success('筛选导出成功')
  } catch (err) {
    message.error('筛选导出失败: ' + (err.message || '未知错误'))
  } finally {
    exportingFiltered.value = false
  }
}

async function handleImportFile(options) {
  const file = options.file?.file || options.file
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await importData(formData)
    importResult.value = { type: 'success', title: res.message || '导入成功' }
    await loadBackups()
  } catch (err) {
    importResult.value = { type: 'error', title: '导入失败: ' + (err.message || '未知错误') }
  }
}

async function loadBackups() {
  backupsLoading.value = true
  try {
    const res = await fetchBackups()
    backups.value = res.data || res || []
  } catch (err) {
    // silently ignore
  } finally {
    backupsLoading.value = false
  }
}

async function handleDownload(bk) {
  downloadingId.value = bk.id
  try {
    const res = await downloadBackup(bk.id)
    const blob = res instanceof Blob ? res : new Blob([JSON.stringify(res)], { type: 'application/json' })
    downloadBlob(blob, bk.filename || bk.name || 'backup.json')
  } catch (err) {
    message.error('下载失败')
  } finally {
    downloadingId.value = null
  }
}

async function handleDeleteBackup(id) {
  try {
    await deleteBackup(id)
    message.success('已删除')
    await loadBackups()
  } catch (err) {
    message.error('删除失败')
  }
}

function formatSize(bytes) {
  if (bytes == null) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

onMounted(loadBackups)
</script>

<style scoped>
.data-page {
  max-width: 800px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 22px;
}
</style>

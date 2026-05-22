<template>
  <div class="records-page">
    <div class="page-header">
      <h2 class="page-title">制作记录</h2>
      <n-button type="primary" @click="$router.push('/records/new')">新建记录</n-button>
    </div>

    <n-card size="small" class="filter-card">
      <n-space align="center" wrap>
        <n-date-picker
          v-model:formatted-value="filters.dateRange"
          type="daterange"
          clearable
          style="width: 100%; max-width: 240px;"
        />
        <n-input
          v-model:value="filters.creature_name"
          placeholder="搜索异兽名称"
          clearable
          style="width: 100%; max-width: 160px;"
        />
        <n-select
          v-model:value="filters.tool"
          :options="toolFilterOptions"
          placeholder="工具"
          clearable
          style="width: 100%; max-width: 120px;"
        />
        <n-select
          v-model:value="filters.status"
          :options="statusFilterOptions"
          placeholder="状态"
          clearable
          style="width: 100%; max-width: 120px;"
        />
        <n-input
          v-model:value="filters.juan"
          placeholder="卷名"
          clearable
          style="width: 100%; max-width: 120px;"
        />
        <n-button type="primary" @click="doSearch">搜索</n-button>
        <n-button @click="resetFilters">重置</n-button>
      </n-space>
    </n-card>

    <n-spin :show="loading">
      <n-alert v-if="error" type="error" :title="error" closable style="margin-bottom: 16px" />

      <n-data-table
        :columns="columns"
        :data="records"
        :pagination="pagination"
        :bordered="false"
        :single-line="false"
        class="records-table"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-spin>
  </div>
</template>

<script setup>
import { ref, reactive, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NTag, NButton, NText } from 'naive-ui'
import { useRecordsStore } from '../stores/records'

const router = useRouter()
const store = useRecordsStore()

const loading = computed(() => store.loading)
const error = computed(() => store.error)
const records = computed(() => store.records)
const total = computed(() => store.total)

const filters = reactive({
  dateRange: null,
  creature_name: '',
  tool: null,
  status: null,
  juan: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  pageSizes: [10, 20, 50],
  showSizePicker: true,
  itemCount: computed(() => total.value),
  prefix: (info) => `共 ${info.itemCount} 条`
})

const toolFilterOptions = [
  { label: '即梦 AI', value: '即梦 AI' },
  { label: '小云雀', value: '小云雀' },
  { label: '可灵', value: '可灵' },
  { label: 'Runway', value: 'Runway' },
  { label: 'Pika', value: 'Pika' }
]

const statusFilterOptions = [
  { label: '制作中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

const columns = [
  {
    title: '异兽名称',
    key: 'creature_name',
    ellipsis: { tooltip: true },
    width: 140
  },
  {
    title: '制作日期',
    key: 'work_date',
    width: 120,
    render(row) {
      return row.work_date ? row.work_date.slice(0, 10) : '-'
    }
  },
  {
    title: '使用工具',
    key: 'tools_used',
    width: 160,
    render(row) {
      const tools = row.tools_used || []
      return tools.join(', ') || '-'
    }
  },
  {
    title: '状态',
    key: 'status',
    width: 90,
    render(row) {
      const map = { in_progress: 'warning', completed: 'success', failed: 'error' }
      const labelMap = { in_progress: '制作中', completed: '已完成', failed: '失败' }
      return h(NTag, { type: map[row.status] || 'default', size: 'small', bordered: false }, () => labelMap[row.status] || row.status)
    }
  },
  {
    title: '风格评分',
    key: 'style_review_score',
    width: 100,
    render(row) {
      if (row.style_review_score == null) return '-'
      const score = row.style_review_score
      const color = score >= 80 ? '#18a058' : score >= 60 ? '#f0a020' : '#d03050'
      return h(NTag, { color: { color, textColor: '#fff' }, size: 'small', bordered: false }, () => `${score}分`)
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    fixed: 'right',
    render(row) {
      return h(
        NButton,
        { size: 'small', quaternary: true, type: 'primary', onClick: () => router.push(`/records/${row.id}`) },
        () => '详情'
      )
    }
  }
]

function buildParams() {
  const params = {
    page: pagination.page,
    per_page: pagination.pageSize
  }
  if (filters.creature_name) params.creature_name = filters.creature_name
  if (filters.tool) params.tool = filters.tool
  if (filters.status) params.status = filters.status
  if (filters.juan) params.juan = filters.juan
  if (filters.dateRange) {
    const [start, end] = filters.dateRange
    params.date_from = start
    params.date_to = end
  }
  return params
}

async function doSearch() {
  pagination.page = 1
  await loadData()
}

function resetFilters() {
  filters.dateRange = null
  filters.creature_name = ''
  filters.tool = null
  filters.status = null
  filters.juan = ''
  pagination.page = 1
  loadData()
}

async function loadData() {
  await store.fetchRecordList(buildParams())
}

function handlePageChange(page) {
  pagination.page = page
  loadData()
}

function handlePageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.records-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 20px;
}

.filter-card {
  margin-bottom: 16px;
  padding: 0;
}

.records-table {
  margin-top: 8px;
  padding: 0;
}

@media (max-width: 768px) {
  .records-page {
    padding: 0 12px;
  }
  
  .filter-card {
    margin-bottom: 12px;
  }
  
  .records-table {
    margin-top: 8px;
  }
}
</style>

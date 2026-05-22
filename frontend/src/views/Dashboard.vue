<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h2 class="page-title">工作台</h2>
        <n-text depth="3">{{ dateHeader }}</n-text>
      </div>
      <n-space>
        <n-button type="primary" @click="$router.push('/records/new')">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          开始制作
        </n-button>
        <n-button @click="$router.push('/records')">查询历史</n-button>
        <n-button @click="$router.push('/data')">导出数据</n-button>
      </n-space>
    </div>

    <n-spin :show="loading">
      <div class="dashboard-grid">
        <div class="main-col">
          <QuotaPanel />

          <n-card title="今日统计" size="small" class="stats-card">
            <div class="stats-row">
              <div class="stat-item">
                <n-statistic label="已完成 / 总数" :value="`${stats.todayCompleted} / ${stats.todayTotal}`" />
              </div>
              <div class="stat-item">
                <n-statistic label="今日消耗积分" :value="stats.pointsConsumed" />
              </div>
            </div>
          </n-card>

          <Heatmap :data="heatmapData" />

          <n-card title="今日任务" size="small" class="tasks-card">
            <n-empty v-if="!todayTasks.length" description="今日暂无排期任务" style="padding: 24px 0" />
            <div v-else class="task-list">
              <div v-for="task in todayTasks" :key="task.id" class="task-item">
                <div class="task-info">
                  <n-text strong>{{ task.creature_name }}</n-text>
                  <div class="task-meta">
                    <n-tag size="tiny" :bordered="false" type="info">{{ task.juan }}</n-tag>
                    <n-tag size="tiny" :bordered="false" type="success">{{ task.recommended_tool || '未指定' }}</n-tag>
                    <n-tag
                      size="tiny"
                      :bordered="false"
                      :type="statusTagType(task.status)"
                    >
                      {{ statusLabel(task.status) }}
                    </n-tag>
                  </div>
                </div>
                <n-button size="small" type="primary" @click="startProduction(task)">
                  开始制作
                </n-button>
              </div>
            </div>
          </n-card>
        </div>

        <div class="side-col">
          <StatsCharts :stats-data="statsData" />
        </div>
      </div>
    </n-spin>

    <n-alert v-if="error" type="error" :title="error" closable style="margin-top: 16px" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { AddOutline } from '@vicons/ionicons5'
import { useDashboardStore } from '../stores/dashboard'
import { fetchStats } from '../api/stats'
import QuotaPanel from '../components/QuotaPanel.vue'
import Heatmap from '../components/Heatmap.vue'
import StatsCharts from '../components/StatsCharts.vue'

const router = useRouter()
const message = useMessage()
const store = useDashboardStore()

const loading = computed(() => store.loading)
const error = computed(() => store.error)
const todayTasks = computed(() => store.todayTasks)
const stats = computed(() => store.stats)
const heatmapData = computed(() => store.heatmapData)
const statsData = ref({})

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const dateHeader = computed(() => {
  const now = new Date()
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 星期${weekdays[now.getDay()]}`
})

function statusLabel(status) {
  const map = { pending: '待制作', in_progress: '制作中', completed: '已完成' }
  return map[status] || status
}

function statusTagType(status) {
  const map = { pending: 'default', in_progress: 'warning', completed: 'success' }
  return map[status] || 'default'
}

function startProduction(task) {
  router.push({ path: '/records/new', query: { plan_id: task.id } })
}

onMounted(async () => {
  await store.fetchDashboardData()
  try {
    const res = await fetchStats()
    statsData.value = res.data || res
  } catch (err) {
    message.warning('获取统计数据失败')
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 100%;
  padding: 0 16px;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
  padding: 0 16px;
  box-sizing: border-box;
}

.page-title {
  margin: 0 0 4px 0;
  font-size: 20px;
}

.dashboard-grid {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.main-col {
  flex: 1;
  min-width: 100%;
}

.side-col {
  flex: 1;
  min-width: 100%;
  margin-top: 16px;
}

.stats-card {
  margin-bottom: 16px;
}

.stats-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-item {
  flex: 1;
}

.tasks-card {
  margin-top: 16px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #eee;
  margin-bottom: 8px;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-meta {
  display: flex;
  gap: 4px;
}
</style>

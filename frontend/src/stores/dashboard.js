import { defineStore } from 'pinia'
import { fetchDashboard } from '../api/stats'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    todayTasks: [],
    quotas: { jimeng: { used: 0, total: 100 }, xiaoyunque: { used: 0, total: 100 } },
    stats: { todayCompleted: 0, todayTotal: 0, pointsConsumed: 0 },
    heatmapData: [],
    loading: false,
    error: null
  }),

  actions: {
    async fetchDashboardData() {
      this.loading = true
      this.error = null
      try {
        const res = await fetchDashboard()
        const data = res.data || res
        this.todayTasks = data.today_tasks || []
        this.quotas = data.quotas || this.quotas
        this.stats = data.stats || this.stats
        this.heatmapData = data.heatmap || []
      } catch (err) {
        this.error = err.message || '获取数据失败'
      } finally {
        this.loading = false
      }
    }
  }
})

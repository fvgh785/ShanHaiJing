<template>
  <div class="stats-charts">
    <n-card size="small" title="工具使用频次" class="chart-card">
      <div v-for="item in toolUsageList" :key="item.name" class="tool-bar-item">
        <div class="tool-bar-header">
          <n-text>{{ item.name }}</n-text>
          <n-text depth="3">{{ item.count }}</n-text>
        </div>
        <n-progress
          type="line"
          :percentage="item.percent"
          :color="item.color"
          :height="10"
          :border-radius="5"
          :show-indicator="false"
        />
      </div>
      <n-empty v-if="!toolUsageList.length" description="暂无数据" size="small" />
    </n-card>

    <n-card size="small" title="积分使用趋势" class="chart-card">
      <div class="points-trend">
        <div v-for="(pt, i) in pointsTrendList" :key="i" class="trend-item">
          <n-text depth="3" class="trend-date">{{ pt.date.slice(5) }}</n-text>
          <n-text class="trend-value">{{ pt.points }}</n-text>
        </div>
      </div>
      <n-empty v-if="!pointsTrendList.length" description="暂无数据" size="small" />
    </n-card>

    <n-card size="small" title="风格评分趋势" class="chart-card">
      <div class="score-trend">
        <div
          v-for="(st, i) in scoreTrendList"
          :key="i"
          class="score-dot"
          :style="{ backgroundColor: getScoreColor(st.score) }"
          :title="`${st.date}: ${st.score}分`"
        >
          {{ st.score }}
        </div>
      </div>
      <n-empty v-if="!scoreTrendList.length" description="暂无数据" size="small" />
    </n-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  statsData: { type: Object, default: () => ({}) }
})

const toolColors = ['#7c3aed', '#18a058', '#f0a020', '#2080f0', '#d03050']

const toolUsageList = computed(() => {
  const usage = props.statsData.tool_usage || []
  const max = Math.max(...usage.map((u) => u.count), 1)
  return usage.map((u, i) => ({
    ...u,
    percent: Math.round((u.count / max) * 100),
    color: toolColors[i % toolColors.length]
  }))
})

const pointsTrendList = computed(() => {
  return props.statsData.points_trend || []
})

const scoreTrendList = computed(() => {
  return props.statsData.score_trend || []
})

function getScoreColor(score) {
  if (score >= 80) return '#18a058'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}
</script>

<style scoped>
.stats-charts {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.chart-card {
  flex: 1;
  min-width: 240px;
}

.tool-bar-item {
  margin-bottom: 10px;
}

.tool-bar-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}

.points-trend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.trend-item {
  text-align: center;
  min-width: 50px;
}

.trend-date {
  font-size: 11px;
  display: block;
}

.trend-value {
  font-weight: 600;
  font-size: 14px;
}

.score-trend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.score-dot {
  width: 32px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #fff;
  cursor: default;
}
</style>

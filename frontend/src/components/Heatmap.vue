<template>
  <div class="heatmap-wrapper">
    <div class="heatmap-label">近7天活跃度</div>
    <div class="heatmap-row">
      <div
        v-for="day in displayDays"
        :key="day.date"
        class="heatmap-cell"
        :style="{ backgroundColor: getColor(day.count) }"
        :title="`${day.date}: ${day.count} 条记录`"
      >
        <span class="heatmap-count">{{ day.count }}</span>
      </div>
    </div>
    <div class="heatmap-legend">
      <span>少</span>
      <span class="legend-swatch" style="background: #ebedf0"></span>
      <span class="legend-swatch" style="background: #c6e48b"></span>
      <span class="legend-swatch" style="background: #7bc96f"></span>
      <span class="legend-swatch" style="background: #239a3b"></span>
      <span class="legend-swatch" style="background: #196127"></span>
      <span>多</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  }
})

const displayDays = computed(() => {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const dateStr = d.toISOString().slice(0, 10)
    const found = props.data.find((item) => item.date === dateStr)
    days.push({ date: dateStr, count: found ? found.count : 0 })
  }
  return days
})

function getColor(count) {
  if (count === 0) return '#ebedf0'
  if (count <= 1) return '#c6e48b'
  if (count <= 3) return '#7bc96f'
  if (count <= 6) return '#239a3b'
  return '#196127'
}
</script>

<style scoped>
.heatmap-wrapper {
  margin-top: 16px;
}

.heatmap-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.heatmap-row {
  display: flex;
  gap: 4px;
}

.heatmap-cell {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
}

.heatmap-count {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 11px;
  color: #999;
}

.legend-swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
</style>

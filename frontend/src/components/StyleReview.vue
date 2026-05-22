<template>
  <div class="style-review">
    <div class="review-header">
      <n-text strong>风格审核结果</n-text>
      <n-tag :type="scoreType" size="medium" round>{{ reviewData.overall_score }} 分</n-tag>
    </div>

    <div class="score-bar-wrapper">
      <n-progress
        type="line"
        :percentage="reviewData.overall_score"
        :color="scoreColor"
        :height="14"
        :border-radius="7"
        :show-indicator="false"
      />
    </div>

    <div class="dimensions">
      <div v-for="dim in dimensions" :key="dim.key" class="dimension-item">
        <div class="dim-header">
          <n-text depth="3">{{ dim.label }}</n-text>
          <n-text depth="2">{{ dim.value }} / 100</n-text>
        </div>
        <n-progress
          type="line"
          :percentage="dim.value"
          :color="dim.color"
          :height="8"
          :border-radius="4"
          :show-indicator="false"
        />
      </div>
    </div>

    <div v-if="reviewData.suggestions?.length" class="suggestions">
      <n-text depth="2" class="suggestions-title">优化建议</n-text>
      <n-ul>
        <n-li v-for="(s, i) in reviewData.suggestions" :key="i">{{ s }}</n-li>
      </n-ul>
    </div>

    <div v-if="showActions" class="review-actions">
      <n-space>
        <n-button size="small" type="primary" @click="$emit('adopt-suggestion')">采纳建议</n-button>
        <n-button size="small" quaternary @click="$emit('ignore')">忽略</n-button>
      </n-space>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  reviewData: {
    type: Object,
    default: () => ({
      overall_score: 0,
      dimension_scores: {},
      suggestions: []
    })
  },
  showActions: { type: Boolean, default: true }
})

defineEmits(['adopt-suggestion', 'ignore'])

const dimensions = computed(() => {
  const scores = props.reviewData.dimension_scores || {}
  return [
    { key: 'lighting_match', label: '光照匹配', value: scores.lighting_match || 0, color: '#f0a020' },
    { key: 'composition_match', label: '构图匹配', value: scores.composition_match || 0, color: '#7c3aed' },
    { key: 'color_match', label: '色彩匹配', value: scores.color_match || 0, color: '#18a058' },
    { key: 'detail_match', label: '细节匹配', value: scores.detail_match || 0, color: '#2080f0' }
  ]
})

const scoreType = computed(() => {
  const s = props.reviewData.overall_score
  if (s >= 80) return 'success'
  if (s >= 60) return 'warning'
  return 'error'
})

const scoreColor = computed(() => {
  const s = props.reviewData.overall_score
  if (s >= 80) return '#18a058'
  if (s >= 60) return '#f0a020'
  return '#d03050'
})
</script>

<style scoped>
.style-review {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #eee;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.score-bar-wrapper {
  margin-bottom: 12px;
}

.dimensions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.dimension-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dim-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.suggestions {
  margin-bottom: 12px;
}

.suggestions-title {
  font-weight: 600;
  display: block;
  margin-bottom: 4px;
}

.review-actions {
  padding-top: 8px;
  border-top: 1px solid #eee;
}
</style>

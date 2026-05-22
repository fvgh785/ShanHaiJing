<template>
  <div class="record-detail-page">
    <div class="page-header">
      <n-space align="center">
        <n-button quaternary @click="$router.back()">
          <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        </n-button>
        <h2 class="page-title">记录详情</h2>
      </n-space>
      <n-button type="primary" @click="$router.push(`/records/${recordId}/edit`)">编辑</n-button>
    </div>

    <n-spin :show="loading">
      <n-alert v-if="error" type="error" :title="error" closable style="margin-bottom: 16px" />

      <template v-if="record">
        <n-card title="基本信息" size="small" class="section-card">
          <n-descriptions label-placement="left" :column="2" bordered>
            <n-descriptions-item label="异兽名称">{{ record.creature_name || '-' }}</n-descriptions-item>
            <n-descriptions-item label="制作日期">{{ displayDate }}</n-descriptions-item>
            <n-descriptions-item label="使用工具">{{ toolList }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="statusTagType" :bordered="false">{{ statusLabel }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item v-if="record.style_tag" label="风格标签">{{ record.style_tag }}</n-descriptions-item>
            <n-descriptions-item v-if="record.juan" label="卷">{{ record.juan }}</n-descriptions-item>
          </n-descriptions>
        </n-card>

        <n-card title="提示词" size="small" class="section-card">
          <n-space vertical size="medium">
            <div>
              <n-text depth="3" class="prompt-label">图片提示词</n-text>
              <div class="prompt-box">{{ record.image_prompt || '暂无' }}</div>
            </div>
            <div>
              <n-text depth="3" class="prompt-label">视频提示词</n-text>
              <div class="prompt-box">{{ record.video_prompt || '暂无' }}</div>
            </div>
            <div>
              <n-text depth="3" class="prompt-label">负向提示词</n-text>
              <div class="prompt-box">{{ record.negative_prompt || '暂无' }}</div>
            </div>
          </n-space>
        </n-card>

        <n-card v-if="record.style_review" title="风格审核" size="small" class="section-card">
          <StyleReview :review-data="record.style_review" :show-actions="false" />
        </n-card>

        <n-card title="产出信息" size="small" class="section-card">
          <n-descriptions label-placement="left" :column="2" bordered>
            <n-descriptions-item label="消耗积分">{{ record.points_consumed ?? 0 }}</n-descriptions-item>
            <n-descriptions-item label="成品链接">
              <n-a v-if="record.output_url" :href="record.output_url" target="_blank">打开链接</n-a>
              <span v-else>-</span>
            </n-descriptions-item>
            <n-descriptions-item label="中间产物" :span="2">
              <div v-if="record.intermediate_urls?.length">
                <n-a
                  v-for="(url, i) in record.intermediate_urls"
                  :key="i"
                  :href="url"
                  target="_blank"
                  style="display: block; margin-bottom: 4px"
                >
                  链接 {{ i + 1 }}
                </n-a>
              </div>
              <span v-else>-</span>
            </n-descriptions-item>
            <n-descriptions-item label="备注" :span="2">{{ record.notes || '-' }}</n-descriptions-item>
          </n-descriptions>
        </n-card>

        <n-card title="Hermes 调用日志" size="small" class="section-card">
          <n-empty v-if="!hermesLogs.length" description="暂无调用记录" size="small" style="padding: 16px 0" />
          <n-table v-else :single-line="false" size="small">
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>模型</th>
                <th>Token 用量</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in hermesLogs" :key="log.id">
                <td>{{ log.created_at || '-' }}</td>
                <td>{{ log.call_type || '-' }}</td>
                <td>{{ log.model || '-' }}</td>
                <td>{{ log.total_tokens ?? '-' }}</td>
                <td>
                  <n-tag
                    :type="log.status === 'success' ? 'success' : 'error'"
                    size="small"
                    :bordered="false"
                  >
                    {{ log.status === 'success' ? '成功' : '失败' }}
                  </n-tag>
                </td>
              </tr>
            </tbody>
          </n-table>
        </n-card>
      </template>
    </n-spin>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowBackOutline } from '@vicons/ionicons5'
import { fetchRecord } from '../api/records'
import { fetchHermesLogs } from '../api/hermes'
import StyleReview from '../components/StyleReview.vue'

const route = useRoute()
const recordId = computed(() => route.params.id)

const record = ref(null)
const hermesLogs = ref([])
const loading = ref(false)
const error = ref('')

const displayDate = computed(() => {
  if (!record.value?.work_date) return '-'
  return record.value.work_date.slice(0, 10)
})

const toolList = computed(() => {
  const tools = record.value?.tools_used || []
  return tools.length ? tools.join(', ') : '-'
})

const statusLabel = computed(() => {
  const map = { in_progress: '制作中', completed: '已完成', failed: '失败' }
  return map[record.value?.status] || record.value?.status || '-'
})

const statusTagType = computed(() => {
  const map = { in_progress: 'warning', completed: 'success', failed: 'error' }
  return map[record.value?.status] || 'default'
})

async function loadRecord() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchRecord(recordId.value)
    record.value = res.data || res
  } catch (err) {
    error.value = err.message || '加载记录失败'
  } finally {
    loading.value = false
  }
}

async function loadHermesLogs() {
  try {
    const res = await fetchHermesLogs({ record_id: recordId.value })
    hermesLogs.value = res.data || res || []
  } catch (err) {
    // silently ignore hermes log load failure
  }
}

onMounted(async () => {
  await loadRecord()
  await loadHermesLogs()
})
</script>

<style scoped>
.record-detail-page {
  max-width: 900px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 22px;
}

.section-card {
  margin-bottom: 16px;
}

.prompt-label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 600;
}

.prompt-box {
  background: #f8f8f8;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  min-height: 40px;
  color: #333;
}
</style>

<template>
  <n-card title="平台配额" size="small" class="quota-panel">
    <div class="quota-item">
      <div class="quota-header">
        <span class="quota-label">即梦 AI</span>
        <span class="quota-value">{{ quotas.jimeng.used }} / {{ quotas.jimeng.total }}</span>
      </div>
      <n-progress
        type="line"
        :percentage="jimengPercent"
        :color="jimengPercent > 90 ? '#d03050' : '#7c3aed'"
        :height="20"
        :border-radius="4"
        :show-indicator="false"
      />
    </div>
    <div class="quota-item">
      <div class="quota-header">
        <span class="quota-label">小云雀</span>
        <span class="quota-value">{{ quotas.xiaoyunque.used }} / {{ quotas.xiaoyunque.total }}</span>
      </div>
      <n-progress
        type="line"
        :percentage="xiaoyunquePercent"
        :color="xiaoyunquePercent > 90 ? '#d03050' : '#18a058'"
        :height="20"
        :border-radius="4"
        :show-indicator="false"
      />
    </div>
    <n-button size="small" quaternary @click="showUpdateModal = true" class="update-btn">
      更新配额
    </n-button>

    <n-modal v-model:show="showUpdateModal" preset="card" title="更新配额" style="width: 400px">
      <n-form :model="updateForm" label-placement="left" label-width="80">
        <n-form-item label="工具">
          <n-select v-model:value="updateForm.tool" :options="toolOptions" />
        </n-form-item>
        <n-form-item label="已用量">
          <n-input-number v-model:value="updateForm.used" :min="0" style="width: 100%" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showUpdateModal = false">取消</n-button>
          <n-button type="primary" @click="handleUpdate">确认更新</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { fetchStats, updateQuota } from '../api/stats'

const message = useMessage()
const quotas = ref({ jimeng: { used: 0, total: 100 }, xiaoyunque: { used: 0, total: 100 } })
const showUpdateModal = ref(false)
const updateForm = ref({ tool: 'jimeng', used: 0 })

const toolOptions = [
  { label: '即梦 AI', value: 'jimeng' },
  { label: '小云雀', value: 'xiaoyunque' }
]

const jimengPercent = computed(() => {
  if (quotas.value.jimeng.total === 0) return 0
  return Math.round((quotas.value.jimeng.used / quotas.value.jimeng.total) * 100)
})

const xiaoyunquePercent = computed(() => {
  if (quotas.value.xiaoyunque.total === 0) return 0
  return Math.round((quotas.value.xiaoyunque.used / quotas.value.xiaoyunque.total) * 100)
})

async function loadQuotas() {
  try {
    const res = await fetchStats()
    if (res.data?.quotas) {
      quotas.value = res.data.quotas
    }
  } catch (err) {
    message.warning('获取配额信息失败')
  }
}

async function handleUpdate() {
  try {
    await updateQuota(updateForm.value.tool, { used: updateForm.value.used })
    await loadQuotas()
    showUpdateModal.value = false
    message.success('配额更新成功')
  } catch (err) {
    message.error('配额更新失败')
  }
}

onMounted(loadQuotas)
</script>

<style scoped>
.quota-panel {
  margin-bottom: 16px;
  padding: 0 16px;
  box-sizing: border-box;
}

.quota-item {
  margin-bottom: 16px;
}

.quota-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  align-items: center;
}

.quota-label {
  font-size: 14px;
  color: #666;
}

.quota-value {
  font-size: 14px;
  font-weight: 600;
}

.update-btn {
  margin-top: 12px;
  width: 100%;
}
</style>

<template>
  <div class="plans-page">
    <div class="page-header">
      <h2 class="page-title">排期管理</h2>
      <n-space>
        <n-upload accept=".csv" :show-file-list="false" @change="handleImportFile">
          <n-button>导入 CSV</n-button>
        </n-upload>
        <n-button type="primary" @click="showCreateModal = true">新建计划</n-button>
      </n-space>
    </div>

    <n-spin :show="loading">
      <n-alert v-if="error" type="error" :title="error" closable style="margin-bottom: 16px" />

      <KanbanBoard
        :plans="plans"
        :columns="columns"
        @status-change="handleStatusChange"
        @card-click="handleCardClick"
      />
    </n-spin>

    <n-modal v-model:show="showCreateModal" preset="card" title="新建制作计划" style="width: 520px">
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="left" label-width="100">
        <n-form-item label="异兽名称" path="creature_name">
          <n-input v-model:value="createForm.creature_name" placeholder="输入异兽名称" />
        </n-form-item>
        <n-form-item label="卷" path="juan">
          <n-input v-model:value="createForm.juan" placeholder="如 南山经" />
        </n-form-item>
        <n-form-item label="优先级" path="priority">
          <n-rate v-model:value="createForm.priority" :count="5" />
        </n-form-item>
        <n-form-item label="计划日期" path="planned_date">
          <n-date-picker v-model:formatted-value="createForm.planned_date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="推荐工具" path="recommended_tool">
          <n-select
            v-model:value="createForm.recommended_tool"
            :options="toolOptions"
            placeholder="选择推荐工具"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="handleCreate">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showEditModal" preset="card" title="编辑计划" style="width: 520px">
      <n-form :model="editForm" label-placement="left" label-width="100">
        <n-form-item label="异兽名称">
          <n-input v-model:value="editForm.creature_name" />
        </n-form-item>
        <n-form-item label="卷">
          <n-input v-model:value="editForm.juan" />
        </n-form-item>
        <n-form-item label="优先级">
          <n-rate v-model:value="editForm.priority" :count="5" />
        </n-form-item>
        <n-form-item label="计划日期">
          <n-date-picker v-model:formatted-value="editForm.planned_date" type="date" style="width: 100%" />
        </n-form-item>
        <n-form-item label="推荐工具">
          <n-select
            v-model:value="editForm.recommended_tool"
            :options="toolOptions"
            clearable
          />
        </n-form-item>
        <n-form-item label="状态">
          <n-select
            v-model:value="editForm.status"
            :options="statusOptions"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-popconfirm @positive="handleDelete(editForm.id)">
            <n-button type="error" quaternary>删除</n-button>
          </n-popconfirm>
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import KanbanBoard from '../components/KanbanBoard.vue'
import { fetchPlans, createPlan, updatePlan, patchPlanStatus, deletePlan, importPlansCSV } from '../api/plans'

const message = useMessage()
const plans = ref([])
const loading = ref(false)
const error = ref('')
const creating = ref(false)
const saving = ref(false)

const columns = ref([
  { status: 'pending', label: '待制作', type: 'default' },
  { status: 'in_progress', label: '制作中', type: 'warning' },
  { status: 'completed', label: '已完成', type: 'success' }
])

const toolOptions = [
  { label: '即梦 AI', value: '即梦 AI' },
  { label: '小云雀', value: '小云雀' },
  { label: '可灵', value: '可灵' },
  { label: 'Runway', value: 'Runway' },
  { label: 'Pika', value: 'Pika' }
]

const statusOptions = [
  { label: '待制作', value: 'pending' },
  { label: '制作中', value: 'in_progress' },
  { label: '已完成', value: 'completed' }
]

const showCreateModal = ref(false)
const createFormRef = ref(null)
const createForm = ref({
  creature_name: '',
  juan: '',
  priority: 3,
  planned_date: null,
  recommended_tool: null
})

const createRules = {
  creature_name: { required: true, message: '请输入异兽名称', trigger: 'blur' },
  juan: { required: true, message: '请输入卷名', trigger: 'blur' }
}

const showEditModal = ref(false)
const editForm = ref({
  id: null,
  creature_name: '',
  juan: '',
  priority: 3,
  planned_date: null,
  recommended_tool: null,
  status: 'pending'
})

async function loadPlans() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchPlans()
    plans.value = res.data || res || []
  } catch (err) {
    error.value = err.message || '加载排期失败'
  } finally {
    loading.value = false
  }
}

async function handleStatusChange(planId, newStatus) {
  try {
    await patchPlanStatus(planId, newStatus)
    const plan = plans.value.find((p) => p.id === planId)
    if (plan) plan.status = newStatus
    message.success('状态更新成功')
  } catch (err) {
    message.error('状态更新失败')
    await loadPlans()
  }
}

function handleCardClick(plan) {
  editForm.value = { ...plan }
  showEditModal.value = true
}

async function handleCreate() {
  creating.value = true
  try {
    await createPlan(createForm.value)
    showCreateModal.value = false
    createForm.value = { creature_name: '', juan: '', priority: 3, planned_date: null, recommended_tool: null }
    message.success('创建成功')
    await loadPlans()
  } catch (err) {
    message.error(err.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    await updatePlan(editForm.value.id, editForm.value)
    showEditModal.value = false
    message.success('保存成功')
    await loadPlans()
  } catch (err) {
    message.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  try {
    await deletePlan(id)
    showEditModal.value = false
    message.success('删除成功')
    await loadPlans()
  } catch (err) {
    message.error('删除失败')
  }
}

async function handleImportFile(options) {
  const file = options.file?.file || options.file
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await importPlansCSV(formData)
    message.success(res.message || '导入成功')
    await loadPlans()
  } catch (err) {
    message.error(err.message || '导入失败')
  }
}

onMounted(loadPlans)
</script>

<style scoped>
.plans-page {
  max-width: 100%;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
  padding: 0 8px;
}

.page-title {
  margin: 0;
  font-size: 22px;
}

@media (max-width: 768px) {
  .plans-page {
    padding: 0 12px;
  }
  
  .page-header {
    margin-bottom: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }
}
</style>

<template>
  <div class="baselines-page">
    <div class="page-header">
      <h2 class="page-title">风格基线</h2>
      <n-button type="primary" @click="openCreateModal">新建基线</n-button>
    </div>

    <n-spin :show="loading">
      <n-alert v-if="error" type="error" :title="error" closable style="margin-bottom: 16px" />

      <n-empty v-if="!baselines.length && !loading" description="暂无风格基线" style="padding: 48px 0">
        <template #extra>
          <n-button type="primary" @click="openCreateModal">创建第一条基线</n-button>
        </template>
      </n-empty>

      <div v-else class="baseline-grid">
        <n-card v-for="bl in baselines" :key="bl.id" size="small" class="baseline-card">
          <template #header>
            <div class="card-header-row">
              <n-text strong>{{ bl.name }}</n-text>
              <div class="card-header-tags">
                <n-tag v-if="bl.is_active" type="success" size="small" :bordered="false">启用中</n-tag>
                <n-tag size="small" :bordered="false">v{{ bl.version || 1 }}</n-tag>
              </div>
            </div>
          </template>

          <div class="card-body">
            <div class="card-field">
              <n-text depth="3">工具类型</n-text>
              <n-text>{{ bl.tool_type || '-' }}</n-text>
            </div>
            <div class="card-field">
              <n-text depth="3">使用次数</n-text>
              <n-text>{{ bl.usage_count ?? 0 }}</n-text>
            </div>
            <div class="card-field" v-if="bl.style_tags?.length">
              <n-text depth="3">风格标签</n-text>
              <n-space wrap :size="4">
                <n-tag v-for="tag in bl.style_tags" :key="tag" size="tiny" :bordered="false" type="info">
                  {{ tag }}
                </n-tag>
              </n-space>
            </div>
          </div>

          <template #action>
            <n-space>
              <n-button v-if="!bl.is_active" size="small" type="primary" quaternary @click="handleActivate(bl.id)">
                启用
              </n-button>
              <n-button size="small" quaternary @click="openEditModal(bl)">编辑</n-button>
              <n-popconfirm @positive="handleDelete(bl.id)">
                <n-button size="small" type="error" quaternary>删除</n-button>
              </n-popconfirm>
            </n-space>
          </template>

          <n-collapse @update:expanded-names="(names) => onVersionExpand(bl, names)">
            <n-collapse-item title="版本历史" name="versions">
              <n-spin :show="versionsLoading[bl.id]">
                <n-empty v-if="!bl._versions?.length" description="暂无历史版本" size="small" />
                <div v-else class="version-list">
                  <div v-for="v in bl._versions" :key="v.id" class="version-item">
                    <n-text depth="2">v{{ v.version }}</n-text>
                    <n-text depth="3" class="version-date">{{ v.created_at?.slice(0, 10) || '-' }}</n-text>
                  </div>
                </div>
              </n-spin>
            </n-collapse-item>
          </n-collapse>
        </n-card>
      </div>
    </n-spin>

    <n-modal v-model:show="showFormModal" preset="card" :title="editingBaseline ? '编辑风格基线' : '新建风格基线'" style="width: 560px">
      <n-form :model="formModel" label-placement="left" label-width="100">
        <n-form-item label="名称" required>
          <n-input v-model:value="formModel.name" placeholder="基线名称" />
        </n-form-item>
        <n-form-item label="工具类型" required>
          <n-select
            v-model:value="formModel.tool_type"
            :options="toolTypeOptions"
            placeholder="选择工具类型"
          />
        </n-form-item>
        <n-form-item label="风格标签">
          <n-select
            v-model:value="formModel.style_tags"
            :options="styleTagOptions"
            multiple
            tag
            filterable
            placeholder="输入或选择风格标签"
          />
        </n-form-item>
        <n-form-item label="提示词模板">
          <n-input
            v-model:value="formModel.prompt_template"
            type="textarea"
            :rows="6"
            placeholder="提示词模板，使用 {{creature_name}} 等占位符"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showFormModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="handleSaveBaseline">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  fetchBaselines,
  createBaseline,
  updateBaseline,
  activateBaseline,
  deleteBaseline,
  fetchBaselineVersions
} from '../api/baselines'

const message = useMessage()
const baselines = ref([])
const loading = ref(false)
const error = ref('')
const saving = ref(false)
const showFormModal = ref(false)
const editingBaseline = ref(null)
const versionsLoading = ref({})

const formModel = ref({
  name: '',
  tool_type: null,
  style_tags: [],
  prompt_template: ''
})

const toolTypeOptions = [
  { label: '即梦 AI', value: '即梦 AI' },
  { label: '小云雀', value: '小云雀' },
  { label: '可灵', value: '可灵' },
  { label: 'Runway', value: 'Runway' },
  { label: 'Pika', value: 'Pika' }
]

const styleTagOptions = [
  { label: '写实风格', value: '写实风格' },
  { label: '水墨风格', value: '水墨风格' },
  { label: '赛博朋克', value: '赛博朋克' },
  { label: '国风插画', value: '国风插画' },
  { label: '3D 渲染', value: '3D 渲染' },
  { label: '像素风格', value: '像素风格' }
]

async function loadBaselines() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchBaselines()
    baselines.value = (res.data || res || []).map((bl) => ({ ...bl, _versions: [] }))
  } catch (err) {
    error.value = err.message || '加载基线失败'
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  editingBaseline.value = null
  formModel.value = { name: '', tool_type: null, style_tags: [], prompt_template: '' }
  showFormModal.value = true
}

function openEditModal(bl) {
  editingBaseline.value = bl
  formModel.value = {
    name: bl.name,
    tool_type: bl.tool_type,
    style_tags: bl.style_tags || [],
    prompt_template: bl.prompt_template || ''
  }
  showFormModal.value = true
}

async function handleSaveBaseline() {
  saving.value = true
  try {
    if (editingBaseline.value) {
      await updateBaseline(editingBaseline.value.id, formModel.value)
      message.success('基线更新成功(创建新版本)')
    } else {
      await createBaseline(formModel.value)
      message.success('基线创建成功')
    }
    showFormModal.value = false
    await loadBaselines()
  } catch (err) {
    message.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleActivate(id) {
  try {
    await activateBaseline(id)
    message.success('已启用')
    await loadBaselines()
  } catch (err) {
    message.error('启用失败')
  }
}

async function handleDelete(id) {
  try {
    await deleteBaseline(id)
    message.success('已删除')
    await loadBaselines()
  } catch (err) {
    message.error('删除失败')
  }
}

async function onVersionExpand(bl, names) {
  if (names?.includes('versions')) {
    await loadVersionsForBaseline(bl)
  }
}

async function loadVersionsForBaseline(bl) {
  if (bl._versions?.length) return
  versionsLoading.value[bl.id] = true
  try {
    const res = await fetchBaselineVersions(bl.id)
    bl._versions = res.data || res || []
  } catch (err) {
    message.warning('加载版本历史失败')
  } finally {
    versionsLoading.value[bl.id] = false
  }
}

onMounted(loadBaselines)
</script>

<style scoped>
.baselines-page {
  max-width: 1400px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 22px;
}

.baseline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.baseline-card {
  display: flex;
  flex-direction: column;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header-tags {
  display: flex;
  gap: 4px;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.version-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
  background: #fafafa;
  border-radius: 4px;
}

.version-date {
  font-size: 12px;
}
</style>

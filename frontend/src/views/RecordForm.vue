<template>
  <div class="record-form-page">
    <div class="page-header">
      <h2 class="page-title">{{ isEdit ? '编辑制作记录' : '新建制作记录' }}</h2>
    </div>

    <n-card>
      <n-steps :current="currentStep" :status="stepStatus" class="form-steps">
        <n-step title="任务绑定" description="选择任务或创建临时" />
        <n-step title="AI 提示词" description="生成并调整提示词" />
        <n-step title="产出与审核" description="填写产出链接和评分" />
        <n-step title="保存" description="确认并提交" />
      </n-steps>
    </n-card>

    <div class="step-content">
      <n-card v-if="currentStep === 0" title="步骤 1: 任务绑定">
        <n-form label-placement="left" label-width="100">
          <n-form-item label="关联计划">
            <n-space vertical style="width: 100%">
              <n-select
                v-model:value="form.plan_id"
                :options="planOptions"
                placeholder="选择已有排期计划"
                filterable
                clearable
                :disabled="form.is_temporary"
                @update:value="onPlanSelected"
              />
              <n-checkbox v-model:checked="form.is_temporary">
                临时任务（不关联排期计划）
              </n-checkbox>
            </n-space>
          </n-form-item>
          <n-form-item label="异兽名称" required>
            <n-input
              v-model:value="form.creature_name"
              placeholder="输入异兽名称"
              :disabled="form.is_temporary ? false : !!form.plan_id"
            />
          </n-form-item>
          <n-form-item label="制作日期" required>
            <n-date-picker v-model:formatted-value="form.work_date" type="date" style="width: 100%" />
          </n-form-item>
          <n-form-item label="使用工具" required>
            <n-checkbox-group v-model:value="form.tools_used">
              <n-space>
                <n-checkbox value="即梦 AI">即梦 AI</n-checkbox>
                <n-checkbox value="小云雀">小云雀</n-checkbox>
                <n-checkbox value="可灵">可灵</n-checkbox>
                <n-checkbox value="Runway">Runway</n-checkbox>
                <n-checkbox value="Pika">Pika</n-checkbox>
              </n-space>
            </n-checkbox-group>
          </n-form-item>
        </n-form>
        <div class="step-actions">
          <n-button type="primary" @click="goStep(1)" :disabled="!canProceedStep1">下一步</n-button>
        </div>
      </n-card>

      <n-card v-if="currentStep === 1" title="步骤 2: AI 提示词生成">
        <n-form label-placement="left" label-width="100">
          <n-form-item label="风格标签">
            <n-select
              v-model:value="form.style_tag"
              :options="styleTagOptions"
              placeholder="选择风格标签"
              clearable
            />
          </n-form-item>
          <n-form-item label="自动审核">
            <n-checkbox v-model:checked="autoReview">
              生成后自动进行风格审核
            </n-checkbox>
          </n-form-item>
        </n-form>

        <HermesPanel
          :creature-name="form.creature_name"
          :style-tag="form.style_tag"
          :baseline-id="form.baseline_id"
          @generated="onPromptGenerated"
          @error="onPromptError"
        />

        <div v-if="generatedPrompt" class="generated-prompts">
          <n-form label-placement="left" label-width="120">
            <n-form-item label="图片提示词">
              <n-input
                type="textarea"
                :value="generatedPrompt.image_prompt"
                :rows="5"
                @update:value="updateGenerated('image_prompt', $event)"
              />
            </n-form-item>
            <n-form-item label="视频提示词">
              <n-input
                type="textarea"
                :value="generatedPrompt.video_prompt"
                :rows="5"
                @update:value="updateGenerated('video_prompt', $event)"
              />
            </n-form-item>
            <n-form-item label="负向提示词">
              <n-input
                type="textarea"
                :value="generatedPrompt.negative_prompt"
                :rows="3"
                @update:value="updateGenerated('negative_prompt', $event)"
              />
            </n-form-item>
          </n-form>

          <StyleReview
            v-if="autoReview && styleReviewData"
            :review-data="styleReviewData"
            @adopt-suggestion="handleAdopt"
            @ignore="handleIgnoreReview"
          />
        </div>

        <div class="step-actions">
          <n-button @click="goStep(0)">上一步</n-button>
          <n-space>
            <n-button @click="regenerate">重新生成</n-button>
            <n-button type="primary" @click="adoptAndContinue">采纳并继续</n-button>
          </n-space>
        </div>
      </n-card>

      <n-card v-if="currentStep === 2" title="步骤 3: 产出与审核">
        <n-form label-placement="left" label-width="120">
          <n-form-item label="消耗积分">
            <n-input-number v-model:value="form.points_consumed" :min="0" style="width: 100%" />
          </n-form-item>
          <n-form-item label="成品链接">
            <n-input v-model:value="form.output_url" placeholder="视频/图片输出链接" />
          </n-form-item>
          <n-form-item label="中间产物链接">
            <n-dynamic-input v-model:value="form.intermediate_urls" placeholder="输入中间产物链接" />
          </n-form-item>
          <n-form-item label="备注">
            <n-input
              v-model:value="form.notes"
              type="textarea"
              :rows="3"
              placeholder="制作备注，遇到的问题等"
            />
          </n-form-item>
          <n-form-item label="状态">
            <n-select
              v-model:value="form.status"
              :options="recordStatusOptions"
            />
          </n-form-item>
        </n-form>
        <div class="step-actions">
          <n-button @click="goStep(1)">上一步</n-button>
          <n-button type="primary" @click="goStep(3)">下一步</n-button>
        </div>
      </n-card>

      <n-card v-if="currentStep === 3" title="步骤 4: 确认并保存">
        <n-descriptions label-placement="left" :column="2" bordered>
          <n-descriptions-item label="异兽名称">{{ form.creature_name || '-' }}</n-descriptions-item>
          <n-descriptions-item label="制作日期">{{ form.work_date || '-' }}</n-descriptions-item>
          <n-descriptions-item label="使用工具">{{ form.tools_used.join(', ') || '-' }}</n-descriptions-item>
          <n-descriptions-item label="风格标签">{{ form.style_tag || '-' }}</n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="recordStatusTagType(form.status)">
              {{ recordStatusLabel(form.status) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="消耗积分">{{ form.points_consumed }}</n-descriptions-item>
          <n-descriptions-item label="图片提示词" :span="2">
            <n-ellipsis expand-trigger="click" line-clamp="2" :tooltip="false">
              {{ form.image_prompt || '-' }}
            </n-ellipsis>
          </n-descriptions-item>
          <n-descriptions-item label="视频提示词" :span="2">
            <n-ellipsis expand-trigger="click" line-clamp="2" :tooltip="false">
              {{ form.video_prompt || '-' }}
            </n-ellipsis>
          </n-descriptions-item>
          <n-descriptions-item label="成品链接" :span="2">{{ form.output_url || '-' }}</n-descriptions-item>
          <n-descriptions-item label="备注" :span="2">{{ form.notes || '-' }}</n-descriptions-item>
        </n-descriptions>

        <div class="step-actions">
          <n-button @click="goStep(2)">上一步</n-button>
          <n-button type="primary" :loading="saving" @click="handleSubmit">保存记录</n-button>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useRecordsStore } from '../stores/records'
import { fetchPlans } from '../api/plans'
import { generatePrompt, reviewStyle } from '../api/hermes'
import HermesPanel from '../components/HermesPanel.vue'
import StyleReview from '../components/StyleReview.vue'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const store = useRecordsStore()

const isEdit = computed(() => route.name === 'RecordEdit')
const recordId = computed(() => route.params.id)

const currentStep = ref(0)
const saving = ref(false)
const autoReview = ref(false)

const form = reactive({
  plan_id: null,
  creature_name: '',
  work_date: new Date().toISOString().slice(0, 10),
  tools_used: [],
  style_tag: null,
  baseline_id: null,
  image_prompt: '',
  video_prompt: '',
  negative_prompt: '',
  points_consumed: 0,
  output_url: '',
  intermediate_urls: [],
  notes: '',
  status: 'in_progress',
  is_temporary: false
})

const planOptions = ref([])
const generatedPrompt = ref(null)
const styleReviewData = ref(null)
const stepStatus = ref('process')

const styleTagOptions = [
  { label: '写实风格', value: '写实风格' },
  { label: '水墨风格', value: '水墨风格' },
  { label: '赛博朋克', value: '赛博朋克' },
  { label: '国风插画', value: '国风插画' },
  { label: '3D 渲染', value: '3D 渲染' },
  { label: '像素风格', value: '像素风格' }
]

const recordStatusOptions = [
  { label: '制作中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '失败', value: 'failed' }
]

function recordStatusLabel(status) {
  const map = { in_progress: '制作中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

function recordStatusTagType(status) {
  const map = { in_progress: 'warning', completed: 'success', failed: 'error' }
  return map[status] || 'default'
}

const canProceedStep1 = computed(() => {
  return form.creature_name && form.tools_used.length > 0
})

async function loadPlansForSelect() {
  try {
    const res = await fetchPlans({ status: 'pending,in_progress' })
    const list = res.data || res || []
    planOptions.value = list.map((p) => ({
      label: `${p.creature_name} (${p.juan})`,
      value: p.id
    }))
  } catch (err) {
    message.warning('加载排期列表失败')
  }
}

function onPlanSelected(planId) {
  if (!planId) return
  try {
    fetchPlans().then((res) => {
      const list = res.data || res || []
      const plan = list.find((p) => p.id === planId)
      if (plan) {
        form.creature_name = plan.creature_name
        if (plan.recommended_tool) {
          form.tools_used = [plan.recommended_tool]
        }
      }
    })
  } catch (err) {
    // silently ignore
  }
}

function goStep(step) {
  currentStep.value = step
}

function onPromptGenerated(result) {
  generatedPrompt.value = result
  form.image_prompt = result.image_prompt || ''
  form.video_prompt = result.video_prompt || ''
  form.negative_prompt = result.negative_prompt || ''

  if (autoReview.value) {
    performAutoReview()
  }
}

function onPromptError(errMsg) {
  message.error('AI 生成失败: ' + errMsg)
}

function updateGenerated(field, value) {
  if (generatedPrompt.value) {
    generatedPrompt.value[field] = value
  }
  form[field] = value
}

async function regenerate() {
  generatedPrompt.value = null
  form.image_prompt = ''
  form.video_prompt = ''
  form.negative_prompt = ''
  styleReviewData.value = null
}

async function performAutoReview() {
  if (!generatedPrompt.value) return
  try {
    const res = await reviewStyle({
      image_prompt: form.image_prompt,
      style_tag: form.style_tag
    })
    styleReviewData.value = res.data || res
  } catch (err) {
    message.warning('风格审核生成失败: ' + (err.message || '未知错误'))
  }
}

function handleAdopt() {
  message.success('已采纳风格建议')
}

function handleIgnoreReview() {
  styleReviewData.value = null
  message.info('已忽略风格审核结果')
}

function adoptAndContinue() {
  if (!generatedPrompt.value) {
    message.warning('请先生成提示词')
    return
  }
  form.image_prompt = generatedPrompt.value.image_prompt || ''
  form.video_prompt = generatedPrompt.value.video_prompt || ''
  form.negative_prompt = generatedPrompt.value.negative_prompt || ''
  goStep(2)
}

async function handleSubmit() {
  saving.value = true
  try {
    const payload = {
      plan_id: form.plan_id,
      creature_name: form.creature_name,
      work_date: form.work_date,
      tools_used: form.tools_used,
      style_tag: form.style_tag,
      baseline_id: form.baseline_id,
      image_prompt: form.image_prompt,
      video_prompt: form.video_prompt,
      negative_prompt: form.negative_prompt,
      points_consumed: form.points_consumed,
      output_url: form.output_url,
      intermediate_urls: form.intermediate_urls.filter(Boolean),
      notes: form.notes,
      status: form.status,
      is_temporary: form.is_temporary
    }

    if (isEdit.value) {
      await store.updateExistingRecord(recordId.value, payload)
      message.success('记录更新成功')
      router.push(`/records/${recordId.value}`)
    } else {
      await store.saveRecord(payload)
      message.success('记录创建成功')
      router.push('/records')
    }
  } catch (err) {
    message.error(err.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadPlansForSelect()

  const planId = route.query.plan_id
  if (planId) {
    form.plan_id = Number(planId)
    onPlanSelected(Number(planId))
  }

  if (isEdit.value && recordId.value) {
    await store.loadRecord(recordId.value)
    Object.assign(form, store.currentRecord)
    if (form.image_prompt) {
      generatedPrompt.value = {
        image_prompt: form.image_prompt,
        video_prompt: form.video_prompt,
        negative_prompt: form.negative_prompt
      }
    }
  }

  store.resetCurrentRecord()
})
</script>

<style scoped>
.record-form-page {
  max-width: 100%;
  padding: 0 16px;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 20px;
  padding: 0 16px;
  box-sizing: border-box;
}

.page-title {
  margin: 0;
  font-size: 20px;
}

.form-steps {
  margin-bottom: 0;
}

.step-content {
  margin-top: 20px;
  padding: 0 16px;
  box-sizing: border-box;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
  flex-wrap: wrap;
  gap: 12px;
}

.generated-prompts {
  margin-top: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.n-descriptions {
  margin-bottom: 0;
}
</style>

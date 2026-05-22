<template>
  <div class="hermes-panel">
    <n-space vertical>
      <div class="generate-bar">
        <n-button
          type="primary"
          :loading="loading"
          :disabled="!creatureName && !styleTag"
          @click="handleGenerate"
        >
          {{ loading ? 'AI 生成中...' : '使用 Hermes Agent 生成提示词' }}
        </n-button>
        <n-text v-if="error" type="error" depth="2">{{ error }}</n-text>
      </div>

      <div v-if="result" class="prompt-results">
        <n-form-item label="图片提示词 (Image Prompt)">
          <n-input
            type="textarea"
            :value="result.image_prompt"
            :rows="4"
            placeholder="AI 生成的图片提示词"
            @update:value="updateField('image_prompt', $event)"
          />
        </n-form-item>

        <n-form-item label="视频提示词 (Video Prompt)">
          <n-input
            type="textarea"
            :value="result.video_prompt"
            :rows="4"
            placeholder="AI 生成的视频提示词"
            @update:value="updateField('video_prompt', $event)"
          />
        </n-form-item>

        <n-form-item label="负向提示词 (Negative Prompt)">
          <n-input
            type="textarea"
            :value="result.negative_prompt"
            :rows="3"
            placeholder="AI 生成的负向提示词"
            @update:value="updateField('negative_prompt', $event)"
          />
        </n-form-item>
      </div>
    </n-space>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { generatePrompt } from '../api/hermes'

const props = defineProps({
  creatureName: { type: String, default: '' },
  styleTag: { type: String, default: null },
  baselineId: { type: [Number, String], default: null }
})

const emit = defineEmits(['generated', 'error'])
const message = useMessage()

const loading = ref(false)
const error = ref('')
const result = ref(null)

async function handleGenerate() {
  if (!props.creatureName) {
    message.warning('请先选择或输入异兽名称')
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const res = await generatePrompt({
      creature_name: props.creatureName,
      style_tag: props.styleTag,
      baseline_id: props.baselineId
    })
    result.value = res.data || res
    emit('generated', result.value)
  } catch (err) {
    error.value = err.message || '生成失败'
    message.error(error.value)
    emit('error', error.value)
  } finally {
    loading.value = false
  }
}

function updateField(field, value) {
  if (result.value) {
    result.value[field] = value
  }
}
</script>

<style scoped>
.hermes-panel {
  padding: 8px 0;
}

.generate-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.prompt-results {
  margin-top: 16px;
}
</style>

<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-layout class="app-layout">
            <n-layout-sider bordered collapse-mode="width" :collapsed-width="64" :width="200" :collapsed="collapsed">
              <div class="logo-wrapper">
                <div class="logo-icon">🐉</div>
                <span v-show="!collapsed" class="logo-text">山海经</span>
              </div>
              <n-menu
                :value="activeKey"
                :collapsed="collapsed"
                :collapsed-width="64"
                :options="menuOptions"
                @update:value="handleMenuChange"
              />
            </n-layout-sider>
            <n-layout>
              <n-layout-header bordered class="app-header">
                <div class="header-left">
                  <n-button quaternary @click="collapsed = !collapsed">
                    <template #icon>
                      <n-icon><MenuOutline /></n-icon>
                    </template>
                  </n-button>
                </div>
                <div class="header-right">
                  <n-text depth="3">山海经视频制作全流程留痕系统</n-text>
                </div>
              </n-layout-header>
              <n-layout-content class="app-content">
                <router-view />
              </n-layout-content>
            </n-layout>
          </n-layout>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { zhCN, dateZhCN } from 'naive-ui'
import {
  HomeOutline as HomeIcon,
  CalendarOutline as CalendarIcon,
  DocumentTextOutline as DocumentIcon,
  ColorPaletteOutline as PaletteIcon,
  SaveOutline as SaveIcon,
  MenuOutline
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)

const menuOptions = [
  { label: '工作台', key: 'dashboard', icon: renderIcon(HomeIcon) },
  { label: '排期管理', key: 'plans', icon: renderIcon(CalendarIcon) },
  { label: '制作记录', key: 'records', icon: renderIcon(DocumentIcon) },
  { label: '风格基线', key: 'baselines', icon: renderIcon(PaletteIcon) },
  { label: '数据管理', key: 'data', icon: renderIcon(SaveIcon) }
]

function renderIcon(icon) {
  return () => h(icon)
}

const activeKey = computed(() => {
  const name = route.name
  if (name === 'Dashboard') return 'dashboard'
  if (name === 'Plans') return 'plans'
  if (name === 'Records' || name === 'RecordForm' || name === 'RecordDetail') return 'records'
  if (name === 'Baselines') return 'baselines'
  if (name === 'DataManagement') return 'data'
  return 'dashboard'
})

function handleMenuChange(key) {
  const routeMap = {
    dashboard: '/',
    plans: '/plans',
    records: '/records',
    baselines: '/baselines',
    data: '/data'
  }
  router.push(routeMap[key] || '/')
}

const themeOverrides = {
  common: {
    primaryColor: '#7c3aed',
    primaryColorHover: '#8b5cf6',
    primaryColorPressed: '#6d28d9'
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-layout {
  height: 100vh;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 56px;
  padding: 0 12px;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-content {
  padding: 24px;
  overflow-y: auto;
  background: #f5f5f5;
  min-height: calc(100vh - 56px);
}
</style>

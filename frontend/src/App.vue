<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <div class="app-container">
            <!-- 左侧导航栏 -->
            <div class="sidebar" :class="{ 'sidebar-collapsed': collapsed }">
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
            </div>
            
            <!-- 右侧内容区 -->
            <div class="main-content">
              <div class="header">
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
              </div>
              
              <div class="content">
                <router-view />
              </div>
            </div>
          </div>
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
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#app {
  height: 100%;
}

.app-container {
  height: 100vh;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 200px;
  background: #fff;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.sidebar-collapsed {
  width: 64px;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64px;
  padding: 0 16px;
  gap: 8px;
  border-bottom: 1px solid #eee;
  background: #fafafa;
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

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 64px;
  border-bottom: 1px solid #eee;
  background: #fff;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f5f5;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100% !important;
    height: auto !important;
    border-right: none;
    border-bottom: 1px solid #eee;
  }
  
  .sidebar-collapsed {
    width: 100% !important;
  }
  
  .main-content {
    flex: 1;
  }
  
  .content {
    height: calc(100vh - 64px - 64px);
    padding: 16px;
  }
  
  .logo-wrapper {
    height: 56px;
    padding: 0 12px;
  }
  
  .logo-icon {
    font-size: 22px;
  }
  
  .logo-text {
    font-size: 16px;
  }
  
  .header {
    height: 56px;
    padding: 0 12px;
  }
}
</style>

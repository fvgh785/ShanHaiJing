import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/plans',
    name: 'Plans',
    component: () => import('../views/Plans.vue')
  },
  {
    path: '/records',
    name: 'Records',
    component: () => import('../views/Records.vue')
  },
  {
    path: '/records/new',
    name: 'RecordForm',
    component: () => import('../views/RecordForm.vue')
  },
  {
    path: '/records/:id',
    name: 'RecordDetail',
    component: () => import('../views/RecordDetail.vue')
  },
  {
    path: '/records/:id/edit',
    name: 'RecordEdit',
    component: () => import('../views/RecordForm.vue')
  },
  {
    path: '/baselines',
    name: 'Baselines',
    component: () => import('../views/Baselines.vue')
  },
  {
    path: '/data',
    name: 'DataManagement',
    component: () => import('../views/DataManagement.vue')
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router

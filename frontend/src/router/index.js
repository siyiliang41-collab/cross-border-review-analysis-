import { createRouter, createWebHashHistory } from 'vue-router'

/**
 * Vue Router 配置 — 各 Tab 独立路由
 *   使用 hash 模式，兼容 SpringBoot 内嵌部署
 */
const routes = [
  {
    path: '/overview',
    name: 'overview',
    meta: { tab: 'overview' },
  },
  {
    path: '/product',
    name: 'product',
    meta: { tab: 'product' },
  },
  {
    path: '/market',
    name: 'market',
    meta: { tab: 'market' },
  },
  {
    path: '/quality',
    name: 'quality',
    meta: { tab: 'quality' },
  },
  {
    path: '/data-manage',
    name: 'data-manage',
    meta: { tab: 'data-manage' },
  },
  {
    path: '/',
    redirect: '/overview',
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router

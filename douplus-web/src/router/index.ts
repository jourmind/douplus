import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '首页概览', icon: 'HomeFilled' }
      },
      {
        path: 'account',
        name: 'Account',
        component: () => import('@/views/account/Index.vue'),
        meta: { title: '账号管理', icon: 'User' }
      },
      {
        path: 'account/:id/dashboard',
        name: 'AccountDashboard',
        component: () => import('@/views/account/Dashboard.vue'),
        meta: { title: '账户概览' }
      },
      {
        path: 'douplus',
        name: 'Douplus',
        redirect: '/douplus/create',
        meta: { title: 'DOU+监控', icon: 'VideoPlay' },
        children: [
          {
            path: 'create',
            name: 'DouplusCreate',
            component: () => import('@/views/douplus/Create.vue'),
            meta: { title: 'DOU+投放' }
          },
          {
            path: 'records',
            name: 'DouplusRecords',
            component: () => import('@/views/douplus/Records.vue'),
            meta: { title: '投放记录' }
          }
        ]
      },
      {
        path: 'comment',
        name: 'Comment',
        redirect: '/comment/list',
        meta: { title: '评论管理', icon: 'ChatDotRound' },
        children: [
          {
            path: 'list',
            name: 'CommentList',
            component: () => import('@/views/comment/List.vue'),
            meta: { title: '评论列表' }
          },
          {
            path: 'negative',
            name: 'CommentNegative',
            component: () => import('@/views/comment/Negative.vue'),
            meta: { title: '负面评论' }
          },
          {
            path: 'blacklist',
            name: 'Blacklist',
            component: () => import('@/views/comment/Blacklist.vue'),
            meta: { title: '黑名单管理' }
          }
        ]
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router

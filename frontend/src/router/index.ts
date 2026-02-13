import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/chat',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/RegisterView.vue'),
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/chat/:conversationId',
    name: 'ChatConversation',
    component: () => import('../views/ChatView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('../views/DocumentsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/carbon',
    name: 'Carbon',
    component: () => import('../views/CarbonView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/credit-score',
    name: 'CreditScore',
    component: () => import('../views/CreditScoreView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/action-plan',
    name: 'ActionPlan',
    component: () => import('../views/ActionPlanView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: 'skills',
        name: 'AdminSkills',
        component: () => import('../views/admin/SkillsListView.vue'),
      },
      {
        path: 'skills/new',
        name: 'AdminSkillNew',
        component: () => import('../views/admin/SkillEditView.vue'),
      },
      {
        path: 'skills/:id',
        name: 'AdminSkillEdit',
        component: () => import('../views/admin/SkillEditView.vue'),
      },
      {
        path: 'referentiels',
        name: 'AdminReferentiels',
        component: () => import('../views/admin/ReferentielsListView.vue'),
      },
      {
        path: 'referentiels/new',
        name: 'AdminReferentielNew',
        component: () => import('../views/admin/ReferentielEditView.vue'),
      },
      {
        path: 'referentiels/:id',
        name: 'AdminReferentielEdit',
        component: () => import('../views/admin/ReferentielEditView.vue'),
      },
      {
        path: 'fonds',
        name: 'AdminFonds',
        component: () => import('../views/admin/FondsListView.vue'),
      },
      {
        path: 'fonds/:id',
        name: 'AdminFondEdit',
        component: () => import('../views/admin/FondEditView.vue'),
      },
      {
        path: 'templates',
        name: 'AdminTemplates',
        component: () => import('../views/admin/TemplatesListView.vue'),
      },
      {
        path: 'stats',
        name: 'AdminStats',
        component: () => import('../views/admin/StatsView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('token')
  const isAuthenticated = !!token

  // If user is already logged in and tries to access login/register, redirect to chat
  if (isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    return next('/chat')
  }

  // If route requires auth and user is not authenticated, redirect to login
  if (to.matched.some((record) => record.meta.requiresAuth) && !isAuthenticated) {
    return next('/login')
  }

  // If route requires admin role, check the auth store
  if (to.matched.some((record) => record.meta.requiresAdmin)) {
    const authStore = useAuthStore()
    if (!authStore.isAdmin) {
      return next('/chat')
    }
  }

  next()
})

export default router

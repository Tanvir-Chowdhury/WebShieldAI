import { createRouter, createWebHistory } from 'vue-router'
import SignupPage from '../components/SignupPage.vue'
import LoginPage from '../components/LoginPage.vue'
import LandingPage from '../components/LandingPage.vue'
import DashboardPage from '../components/DashboardPage.vue' 

const routes = [
  { path: '/', component: LandingPage },
  { path: '/signup', component: SignupPage },
  { path: '/login', component: LoginPage },
  {
    path: '/dashboard',
    component: DashboardPage,
    meta: { requiresAuth: true } 
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

import axios from 'axios'

router.beforeEach(async (to, from, next) => {
  if (to.meta.requiresAuth) {
    try {
      await axios.get('http://localhost:8000/me', {
        withCredentials: true
      })
      next() 
    } catch (err) {
      next('/login') 
    }
  } else {
    next() 
  }
})


export default router

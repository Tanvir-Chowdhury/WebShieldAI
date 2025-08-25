import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

// const user = ref(null)
// const loading = ref(true)

// export function useAuth() {
//   const router = useRouter()

//   async function checkAuth() {
//     loading.value = true
//     try {
//       const res = await axios.get('http://localhost:8000/me', {
//         withCredentials: true
//       })
//       user.value = res.data
//     } catch (err) {
//       user.value = null
//       router.push('/login')
//     } finally {
//       loading.value = false
//     }
//   }

//   return {
//     user,
//     loading,
//     checkAuth
//   }
// }

import api from './axios'

export function useAuth() {
  const user = ref(null)
  const loading = ref(true)
  const router = useRouter()

  async function checkAuth() {
    loading.value = true
    try {
      const res = await api.get('http://localhost:8000/me')
      user.value = res.data
    } catch (err) {
      user.value = null
      router.push('/login')
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    loading,
    checkAuth
  }
}

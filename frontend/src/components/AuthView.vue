<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login-success'])

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const errorMsg = ref('')
const isLoading = ref(false)

const toggleMode = () => {
  isLogin.value = !isLogin.value
  errorMsg.value = ''
}

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    errorMsg.value = '请填写用户名和密码'
    return
  }

  isLoading.value = true
  errorMsg.value = ''

  const endpoint = isLogin.value ? '/api/v1/auth/login' : '/api/v1/auth/register'
  
  try {
    const response = await fetch(`http://localhost:8000${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    const data = await response.json()

    if (!response.ok) {
      console.error('API Error Details:', data)
      throw new Error(data.detail || '请求失败')
    }

    if (isLogin.value) {
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', username.value)
      emit('login-success', { username: username.value })
    } else {
      errorMsg.value = '注册成功，请登录'
      isLogin.value = true
      password.value = ''
    }
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <h2>{{ isLogin ? '用户登录' : '用户注册' }}</h2>
      <p class="subtitle">登录以保存您的对话历史</p>
      
      <div class="form-group">
        <label>用户名</label>
        <input v-model="username" type="text" placeholder="输入用户名" @keyup.enter="handleSubmit" />
      </div>
      
      <div class="form-group">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="输入密码" @keyup.enter="handleSubmit" />
      </div>

      <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

      <button class="submit-btn" @click="handleSubmit" :disabled="isLoading">
        {{ isLoading ? '处理中...' : (isLogin ? '登录' : '注册') }}
      </button>

      <div class="toggle-mode">
        {{ isLogin ? '没有账号?' : '已有账号?' }}
        <a href="#" @click.prevent="toggleMode">{{ isLogin ? '立即注册' : '立即登录' }}</a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f8f9fa;
}

.auth-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.05);
  width: 100%;
  max-width: 400px;
}

h2 {
  margin-top: 0;
  margin-bottom: 8px;
  text-align: center;
  color: #202124;
}

.subtitle {
  text-align: center;
  color: #5f6368;
  font-size: 0.875rem;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #3c4043;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #dadce0;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 1rem;
}

input:focus {
  outline: none;
  border-color: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26,115,232,0.1);
}

.error-msg {
  color: #d93025;
  font-size: 0.875rem;
  margin-bottom: 15px;
  text-align: center;
}

.submit-btn {
  width: 100%;
  padding: 12px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.submit-btn:hover {
  background: #1765cc;
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.toggle-mode {
  margin-top: 20px;
  text-align: center;
  font-size: 0.875rem;
  color: #5f6368;
}

.toggle-mode a {
  color: #1a73e8;
  text-decoration: none;
  font-weight: 500;
}
</style>

<script setup>
import { ref, onMounted } from 'vue'
import ChatInterface from './components/ChatInterface.vue'
import AuthView from './components/AuthView.vue'
import Sidebar from './components/Sidebar.vue'

const isLoggedIn = ref(false)
const username = ref('')
const sidebarRef = ref(null)
const chatInterfaceRef = ref(null)
const isSidebarCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')

const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  localStorage.setItem('sidebarCollapsed', isSidebarCollapsed.value)
}

const checkLoginStatus = () => {
  const token = localStorage.getItem('token')
  const storedUser = localStorage.getItem('username')
  if (token && storedUser) {
    isLoggedIn.value = true
    username.value = storedUser
  }
}

const handleLoginSuccess = (user) => {
  isLoggedIn.value = true
  username.value = user.username
}

const handleLogout = () => {
  isLoggedIn.value = false
  username.value = ''
}

const handleSelectSession = (session) => {
  if (chatInterfaceRef.value) {
    chatInterfaceRef.value.loadSession(session.id)
  }
}

const handleNewChat = () => {
  if (chatInterfaceRef.value) {
    chatInterfaceRef.value.startNewChat()
  }
}

const onMessageSent = () => {
  if (sidebarRef.value) {
    sidebarRef.value.fetchSessions()
  }
}

onMounted(checkLoginStatus)
</script>

<template>
  <div class="app-container" v-if="isLoggedIn">
    <Sidebar 
      ref="sidebarRef"
      :username="username" 
      :is-collapsed="isSidebarCollapsed"
      @logout="handleLogout" 
      @select-session="handleSelectSession"
      @new-chat="handleNewChat"
      @toggle="toggleSidebar"
    />
    <div class="main-content">
      <main>
        <ChatInterface ref="chatInterfaceRef" @message-sent="onMessageSent" />
      </main>
    </div>
  </div>
  <AuthView v-else @login-success="handleLoginSuccess" />
</template>

<style>
/* 全局变量定义 */
:root {
  --bg-color: #f8f9fa;
  --text-primary: #202124;
  --text-secondary: #5f6368;
  --accent-color: #1a73e8;
  --border-color: #dadce0;
}

body, html, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
</style>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  transition: all 0.3s ease;
}

main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>

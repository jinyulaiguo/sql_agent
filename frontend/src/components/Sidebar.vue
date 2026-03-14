<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  username: String,
  isCollapsed: Boolean
})
const emit = defineEmits(['select-session', 'new-chat', 'logout', 'toggle'])
const sessions = ref([])
const isLoading = ref(false)
const activeSessionId = ref(null)

const fetchSessions = async () => {
  isLoading.value = true
  const token = localStorage.getItem('token')
  try {
    const response = await fetch('http://localhost:8000/api/v1/sessions', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      sessions.value = await response.json()
    }
  } catch (err) {
    console.error('Failed to fetch sessions:', err)
  } finally {
    isLoading.value = false
  }
}

const handleSelect = (session) => {
  activeSessionId.value = session.id
  emit('select-session', session)
}

const handleNewChat = () => {
  activeSessionId.value = null
  emit('new-chat')
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  emit('logout')
}

const toggleSidebar = () => {
  emit('toggle')
}

defineExpose({ fetchSessions })

onMounted(fetchSessions)
</script>

<template>
  <div :class="['sidebar', { collapsed: isCollapsed }]">
    <div class="sidebar-header">
      <div class="header-top">
        <h1 v-if="!isCollapsed" class="app-title">✨ Text-to-SQL</h1>
        <button class="toggle-btn" @click="toggleSidebar" :title="isCollapsed ? '展开侧边栏' : '收起侧边栏'">
          <svg v-if="isCollapsed" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
      </div>
      <button class="new-chat-btn" @click="handleNewChat" :title="isCollapsed ? '开启新对话' : ''">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        <span v-if="!isCollapsed">开启新对话</span>
      </button>
    </div>

    <div class="session-list">
      <div v-if="isLoading" class="loading">
        <span v-if="!isCollapsed">加载中...</span>
        <div v-else class="mini-loader"></div>
      </div>
      <div 
        v-for="session in sessions" 
        :key="session.id" 
        :class="['session-item', { active: activeSessionId === session.id }]"
        @click="handleSelect(session)"
        :title="isCollapsed ? session.title : ''"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span v-if="!isCollapsed" class="session-title">{{ session.title }}</span>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="user-info">
        <div class="avatar">{{ username?.charAt(0).toUpperCase() }}</div>
        <span v-if="!isCollapsed">{{ username }}</span>
      </div>
      <button v-if="!isCollapsed" class="logout-btn" @click="handleLogout" title="退出登录">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
          <polyline points="16 17 21 12 16 7"></polyline>
          <line x1="21" y1="12" x2="9" y2="12"></line>
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 260px;
  background: #f0f4f9;
  height: 100vh;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 40px;
}

.app-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
  background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.toggle-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #5f6368;
  padding: 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.sidebar.collapsed .header-top {
  justify-content: center;
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #ffffff;
  border: 1px solid #dadce0;
  border-radius: 12px;
  color: #1a73e8;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.sidebar.collapsed .new-chat-btn {
  padding: 12px;
  justify-content: center;
  width: 40px;
  margin: 0 auto;
}

.new-chat-btn:hover {
  background: #f1f3f4;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.loading {
  text-align: center;
  padding: 20px;
  color: #5f6368;
  font-size: 0.875rem;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  color: #3c4043;
  margin-bottom: 4px;
  transition: all 0.2s;
  white-space: nowrap;
}

.sidebar.collapsed .session-item {
  justify-content: center;
  padding: 10px 0;
  width: 40px;
  margin-left: auto;
  margin-right: auto;
}

.session-item:hover {
  background: #e1e3e1;
}

.session-item.active {
  background: #c2e7ff;
  color: #001d35;
}

.session-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.875rem;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: #3c4043;
}

.sidebar.collapsed .sidebar-footer {
  justify-content: center;
}

.avatar {
  width: 32px;
  height: 32px;
  background: #1a73e8;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.logout-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #5f6368;
  padding: 4px;
  border-radius: 4px;
}

.logout-btn:hover {
  background: #dadce0;
  color: #202124;
}

.mini-loader {
  width: 14px;
  height: 14px;
  border: 2px solid #e0e0e0;
  border-top-color: #1a73e8;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>

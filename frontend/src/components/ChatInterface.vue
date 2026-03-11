<script setup>
import { ref, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'

const messages = ref([
  { role: 'agent', content: '你好！我是你的 SQL 智能助手。你可以问我关于音乐数据库的任何问题，比如"统计每种流派的歌曲数量"。' }
])
const inputMessage = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)
const sessionId = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const startNewChat = () => {
  sessionId.value = null
  messages.value = [
    { role: 'agent', content: '你好！新的对话已开始。请问有什么问题？' }
  ]
}

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || isLoading.value) return

  messages.value.push({ role: 'user', content })
  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()

  try {
    const requestBody = { message: content }
    if (sessionId.value) {
      requestBody.session_id = sessionId.value
    }

    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    sessionId.value = data.session_id
    messages.value.push({ role: 'agent', content: data.response })
  } catch (error) {
    messages.value.push({ role: 'error', content: `请求失败: ${error.message}` })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>

<template>
  <div class="chat-interface">
    <div class="chat-header">
      <button class="new-chat-btn" @click="startNewChat" title="新对话">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"></line>
          <line x1="5" y1="12" x2="19" y2="12"></line>
        </svg>
        新对话
      </button>
    </div>

    <div class="chat-history" ref="chatContainer">
      <ChatMessage 
        v-for="(msg, index) in messages" 
        :key="index" 
        :role="msg.role" 
        :content="msg.content" 
      />
      <div v-if="isLoading" class="loading-indicator">
        <span class="dot"></span>
        <span class="dot"></span>
        <span class="dot"></span>
      </div>
    </div>

    <div class="input-area">
      <div class="input-wrapper">
        <input 
          v-model="inputMessage" 
          @keyup.enter="sendMessage" 
          type="text" 
          placeholder="输入你的问题..." 
          :disabled="isLoading"
        />
        <button @click="sendMessage" :disabled="!inputMessage.trim() || isLoading">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
      <p class="disclaimer">Agent 可能会犯错，请核对重要信息。</p>
    </div>
  </div>
</template>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.chat-header {
  padding: 12px 20px;
  display: flex;
  justify-content: flex-end;
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #dadce0;
  border-radius: 20px;
  background: white;
  color: var(--accent-color);
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s;
}

.new-chat-btn:hover {
  background: #f0f4f9;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

.loading-indicator {
  display: flex;
  gap: 8px;
  padding: 12px 18px;
  background: white;
  border-radius: 18px;
  width: fit-content;
  margin-left: 54px;
  margin-bottom: 24px;
}

.dot {
  width: 8px;
  height: 8px;
  background: #ccc;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  padding: 20px;
  background: var(--bg-color);
}

.input-wrapper {
  background: white;
  border-radius: 30px;
  display: flex;
  align-items: center;
  padding: 8px 8px 8px 24px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s;
}

.input-wrapper:focus-within {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

input {
  border: none;
  outline: none;
  flex: 1;
  font-size: 1rem;
  font-family: inherit;
  background: transparent;
}

button {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--accent-color);
  padding: 8px;
  border-radius: 50%;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

button:hover:not(:disabled) {
  background: #f0f4f9;
}

button:disabled {
  color: #ccc;
  cursor: not-allowed;
}

.disclaimer {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 12px;
  margin-bottom: 0px;
}
</style>

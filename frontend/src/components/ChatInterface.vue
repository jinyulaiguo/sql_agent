<script setup>
import { ref, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'

const emit = defineEmits(['message-sent'])

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

const loadSession = async (sid) => {
  sessionId.value = sid
  isLoading.value = true
  const token = localStorage.getItem('token')
  try {
    const response = await fetch(`http://localhost:8000/api/v1/sessions/${sid}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      const data = await response.json()
      // 合并历史消息：将连续的非用户消息合并为一个 agent 气泡
      const mergedMessages = []
      let lastAgentMsg = null

      data.messages.forEach(m => {
        if (m.role === 'system') return
        
        if (m.role === 'user') {
          mergedMessages.push({ role: 'user', content: m.content })
          lastAgentMsg = null
        } else {
          // assistant, tool 等中间角色统一映射为 agent
          let content = m.content || ''
          // 如果是工具输出，包裹在 thought 标签中以便折叠
          if (m.role === 'tool') {
             content = `\n<thought>🔧 工具执行结果: ${content}</thought>\n`
          }
          
          if (lastAgentMsg) {
            lastAgentMsg.content += content
          } else {
            lastAgentMsg = { role: 'agent', content: content }
            mergedMessages.push(lastAgentMsg)
          }
        }
      })
      messages.value = mergedMessages
      scrollToBottom()
    }
  } catch (err) {
    console.error('Failed to load session:', err)
  } finally {
    isLoading.value = false
  }
}

defineExpose({ startNewChat, loadSession })

const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || isLoading.value) return

  // 1. 添加用户提问
  messages.value.push({ role: 'user', content })
  inputMessage.value = ''
  isLoading.value = true
  scrollToBottom()

  // 2. 预先添加一个空的 agent 气泡，用于容纳流式输出
  const agentMessage = { role: 'agent', content: '' }
  messages.value.push(agentMessage)

  try {
    const requestBody = { message: content }
    if (sessionId.value) {
      requestBody.session_id = sessionId.value
    }

    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 3. 开始解析 SSE 数据流
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      
      // 按两段换行符分割 SSE 事件
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || '' // 保留最后一个不完整的块
      
      for (const part of parts) {
        if (part.trim().startsWith('data:')) {
          const jsonStr = part.replace(/^data:\s*/, '').trim()
          if (!jsonStr) continue
          
          try {
            const dataObj = JSON.parse(jsonStr)
            
            // 使用索引直接修改 messages 数组以确保触发 Vue 响应式 DOM 更新
            const lastIdx = messages.value.length - 1
            
            if (dataObj.event === 'session') {
              sessionId.value = dataObj.data
            } else if (dataObj.event === 'content') {
              // 追加正常回复或思维链内容到当前气泡
              messages.value[lastIdx].content += dataObj.data
              scrollToBottom()
            } else if (dataObj.event === 'tool') {
              // 工具调用的中间状态，包裹在 <thought> 标签中
              // 这样 ChatMessage.vue 可以统一识别并放入折叠框
              messages.value[lastIdx].content += `\n<thought>🔧 ${dataObj.data}...</thought>\n`
              scrollToBottom()
            } else if (dataObj.event === 'error') {
              messages.value[lastIdx].content += `\n**[Error]** ${dataObj.data}`
              scrollToBottom()
            } else if (dataObj.event === 'done') {
              // 流结束
              break
            }
          } catch (e) {
            console.error('JSON Parse error for chunk: ', jsonStr, e)
          }
        }
      }
    }
  } catch (error) {
    if (agentMessage.content === '') {
       agentMessage.role = 'error'
       agentMessage.content = `请求失败: ${error.message}`
    } else {
       agentMessage.content += `\n\n*(网络连接中断: ${error.message})*`
    }
  } finally {
    isLoading.value = false
    scrollToBottom()
    emit('message-sent') // 通知父组件刷新侧边栏列表
  }
}
</script>

<template>
  <div class="chat-interface">

    <div class="chat-history" ref="chatContainer">
      <ChatMessage 
        v-for="(msg, index) in messages" 
        :key="index" 
        :role="msg.role" 
        :content="msg.content" 
      />
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


.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
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

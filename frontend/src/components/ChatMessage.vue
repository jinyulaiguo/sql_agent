<script setup>
import { computed, ref, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps({
  role: {
    type: String,
    required: true,
    validator: (value) => ['user', 'agent', 'error'].includes(value)
  },
  content: {
    type: String,
    required: true
  }
})

// 控制思考过程的展开状态
const isThinkingExpanded = ref(false)

// 移除自动展开逻辑，确保思维链默认折叠
watch(() => props.content, (newVal) => {
  // 保持默认折叠状态，用户需要手动展开
}, { immediate: true })

const toggleThinking = () => {
  isThinkingExpanded.value = !isThinkingExpanded.value
}

// 分离思维链和主文本
const parsedMessage = computed(() => {
  let rawContent = props.content || ''
  const thoughts = []
  
  // 1. 匹配所有支持的标签（plan, plan_update, thought）
  // 匹配闭合标签
  const closedRegex = /<(plan|plan_update|thought)>([\s\S]*?)<\/\1>/g
  let match
  while ((match = closedRegex.exec(rawContent)) !== null) {
    thoughts.push({
      type: match[1],
      content: match[2].trim(),
      isComplete: true
    })
  }
  
  // 从原文中剥离闭合标签 (注意：这里要全局替换)
  let mainContent = rawContent.replace(closedRegex, '')

  // 2. 处理可能还未闭合的情况 (流式推流中途)
  const unclosedRegex = /<(plan|plan_update|thought)>([\s\S]*)$/
  const unclosedMatch = mainContent.match(unclosedRegex)
  
  if (unclosedMatch) {
    const contentInside = unclosedMatch[2].trim()
    // 只有当标签内确实有内容时，才认为“有思考过程”
    if (contentInside || unclosedMatch[0].length > 10) { 
      thoughts.push({
        type: unclosedMatch[1],
        content: contentInside,
        isComplete: false
      })
    }
    // 从主文本中剥离未闭合内容
    mainContent = mainContent.replace(unclosedRegex, '')
  }

  return {
    thoughts,
    hasThoughts: thoughts.length > 0,
    isStillThinking: thoughts.some(t => !t.isComplete),
    // 将主内容转为 HTML
    mainHtml: DOMPurify.sanitize(marked.parse(mainContent.trim() || ''))
  }
})

const getThoughtLabel = (type) => {
  switch (type) {
    case 'plan': return '分析计划'
    case 'plan_update': return '调整计划'
    case 'thought': return '推理思考'
    default: return '思考中'
  }
}
</script>

<template>
  <div class="message-row" :class="role">
    <div class="avatar">
      <span v-if="role === 'user'">👤</span>
      <span v-else-if="role === 'agent'">✨</span>
      <span v-else>⚠️</span>
    </div>
    
    <div class="message-content-wrapper">
      <!-- 思考过程切换按钮 (仅 Agent 且有思考过程时显示) -->
      <!-- 物理位置在正式回复之上 -->
      <div v-if="role === 'agent' && parsedMessage.hasThoughts" class="thought-container">
        <button 
          @click="toggleThinking" 
          class="thought-toggle"
          :class="{ 'is-active': isThinkingExpanded }"
        >
          <span class="toggle-icon">
            <svg v-if="isThinkingExpanded" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 15l-6-6-6 6"/></svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
          </span>
          <span class="toggle-text">
            Show thinking
          </span>
          <span v-if="parsedMessage.isStillThinking" class="pulsing-dot"></span>
        </button>

        <!-- 思考内容容器 -->
        <transition name="fade-slide">
          <div v-if="isThinkingExpanded" class="thought-content-box">
            <div v-for="(thought, idx) in parsedMessage.thoughts" :key="idx" class="thought-step">
              <div class="step-header">
                <span class="step-dot" :class="{ 'thinking': !thought.isComplete }"></span>
                <span class="step-label">{{ getThoughtLabel(thought.type) }}</span>
              </div>
              <div class="step-body">
                <pre>{{ thought.content }}<span v-if="!thought.isComplete" class="cursor">_</span></pre>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <div class="message-bubble">
        <div v-if="role === 'user'">{{ content }}</div>
        <div v-else>
          <!-- 正式回复区 -->
          <div 
            class="markdown-body" 
            v-html="parsedMessage.mainHtml" 
            v-show="parsedMessage.mainHtml"
          ></div>
          <div v-if="role === 'agent' && !parsedMessage.mainHtml" class="loading-state">
            <span>正在生成回答...</span>
            <div class="loading-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 850px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  background: #f0f4f9;
  border-radius: 50%;
  flex-shrink: 0;
  border: 1px solid #eef2f7;
}

.message-content-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 85%;
}

.message-row.user .message-content-wrapper {
  align-items: flex-end;
}

.message-bubble {
  padding: 14px 20px;
  border-radius: 20px;
  font-size: 1rem;
  line-height: 1.6;
  word-wrap: break-word;
  color: var(--text-primary);
  width: fit-content;
  max-width: 100%;
}

.message-row.user .message-bubble {
  background-color: var(--user-bubble-bg);
  border-bottom-right-radius: 4px;
}

.message-row.agent .message-bubble {
  background-color: transparent;
  padding-left: 0;
  padding-right: 0;
}

.message-row.error .message-bubble {
  background-color: #fce8e6;
  color: #c5221f;
  border: 1px solid #fad2cf;
}

/* 思考过程外观 */
.thought-container {
  width: 100%;
}

.thought-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f4f9;
  border: 1px solid #dee2e6;
  padding: 6px 12px;
  border-radius: 18px;
  font-size: 0.85rem;
  color: #5f6368;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  font-weight: 500;
  margin-bottom: 4px;
}

.thought-toggle:hover {
  background: #e8eaed;
  color: #202124;
}

.thought-toggle.is-active {
  border-color: #c2e7ff;
  background: #eaf1fb;
  color: #1a73e8;
}

.toggle-icon svg {
  width: 14px;
  height: 14px;
}

.thought-content-box {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  padding: 12px;
  margin-top: 4px;
  margin-bottom: 12px;
  font-size: 0.875rem;
  max-height: 400px;
  overflow-y: auto;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);
}

.thought-step {
  margin-bottom: 12px;
}

.thought-step:last-child {
  margin-bottom: 0;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-weight: 600;
  font-size: 0.75rem;
  color: #70757a;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.step-dot {
  width: 6px;
  height: 6px;
  background: #dadce0;
  border-radius: 50%;
}

.step-dot.thinking {
  background: #1a73e8;
  box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
  animation: pulse 1.5s infinite;
}

.step-body pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: 'Roboto Mono', monospace;
  background: #ffffff;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid #f1f3f4;
  color: #3c4043;
}

/* 加载状态样式 */
.loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #5f6368;
  font-size: 0.95rem;
  padding: 10px 0;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  background: #c3c7cb;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 动效 */
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from, .fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.pulsing-dot {
  width: 4px;
  height: 4px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
  margin-left: 4px;
}

.cursor {
  animation: blink 1s step-end infinite;
  font-weight: bold;
}

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Markdown 样式 */
.markdown-body {
  width: 100%;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  background: white;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid #e0e0e0;
  padding: 10px 12px;
  font-size: 0.9rem;
}
.markdown-body :deep(th) {
  background-color: #f8f9fa;
  font-weight: 600;
  text-align: left;
}
.markdown-body :deep(pre) {
  background: #f1f3f4;
  padding: 12px;
  border-radius: 12px;
  overflow-x: auto;
  margin: 1em 0;
}
</style>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

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

const parsedContent = computed(() => {
  return marked.parse(props.content)
})
</script>

<template>
  <div class="message-row" :class="role">
    <div class="avatar">
      <span v-if="role === 'user'">👤</span>
      <span v-else-if="role === 'agent'">✨</span>
      <span v-else>⚠️</span>
    </div>
    <div class="message-bubble">
      <div v-if="role === 'user'">{{ content }}</div>
      <div v-else class="markdown-body" v-html="parsedContent"></div>
    </div>
  </div>
</template>

<style scoped>
.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  background: var(--bg-color);
  border-radius: 50%;
  flex-shrink: 0;
}

.message-bubble {
  padding: 12px 18px;
  border-radius: 18px;
  font-size: 1rem;
  line-height: 1.6;
  max-width: 85%;
  word-wrap: break-word;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.message-row.user .message-bubble {
  background-color: var(--user-bubble-bg);
  border-bottom-right-radius: 4px;
  color: var(--text-primary);
}

.message-row.agent .message-bubble {
  background-color: var(--agent-bubble-bg);
  border-bottom-left-radius: 4px;
  color: var(--text-primary);
}

.message-row.error .message-bubble {
  background-color: #fce8e6;
  color: #c5221f;
  border: 1px solid #fce8e6;
}

/* Markdown Styles Override */
.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid #ddd;
  padding: 8px;
  font-size: 0.9em;
}
.markdown-body :deep(th) {
  background-color: #f9f9f9;
  text-align: left;
}
.markdown-body :deep(pre) {
  background: #f4f4f4;
  padding: 10px;
  border-radius: 8px;
  overflow-x: auto;
}
</style>

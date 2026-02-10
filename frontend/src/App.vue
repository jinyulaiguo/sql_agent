<script setup>
import ChatInterface from './components/ChatInterface.vue'
</script>

<template>
  <div class="app-container">
    <header>
      <h1>✨ Text-to-SQL Agent</h1>
    </header>
    <main>
      <ChatInterface />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

header {
  padding: 20px;
  text-align: center;
}

h1 {
  font-size: 1.5rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: linear-gradient(90deg, #4285f4, #9b72cb, #d96570);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

main {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>

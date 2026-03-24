<template>
  <span class="term-hint">
    <button class="term-button" type="button" @click="isOpen = true">
      {{ label || term }}
    </button>

    <Teleport to="body">
      <div v-if="isOpen" class="term-overlay" @click.self="isOpen = false">
        <div class="term-dialog" role="dialog" :aria-label="title || term" aria-modal="true">
          <div class="term-head">
            <div>
              <p class="term-kicker">Giải thích thuật ngữ</p>
              <h3>{{ title || term }}</h3>
            </div>
            <button class="close-button" type="button" @click="isOpen = false">Đóng</button>
          </div>

          <p class="term-summary">{{ summary }}</p>
          <p v-if="detail" class="term-detail">{{ detail }}</p>

          <ul v-if="bullets.length > 0" class="term-list">
            <li v-for="item in bullets" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </Teleport>
  </span>
</template>

<script setup lang="ts">
import { ref } from "vue";

withDefaults(
  defineProps<{
    term: string;
    label?: string;
    title?: string;
    summary: string;
    detail?: string;
    bullets?: string[];
  }>(),
  {
    label: "",
    title: "",
    detail: "",
    bullets: () => [],
  },
);

const isOpen = ref(false);
</script>

<style scoped>
.term-button,
.close-button {
  font: inherit;
}

.term-button {
  border: 1px solid color-mix(in srgb, var(--tp-accent) 26%, var(--tp-line));
  background: color-mix(in srgb, var(--tp-accent-soft) 68%, white);
  color: var(--tp-text);
  border-radius: 999px;
  padding: 0.38rem 0.72rem;
  cursor: pointer;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.term-overlay {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgba(20, 33, 38, 0.42);
  backdrop-filter: blur(10px);
}

.term-dialog {
  width: min(560px, 100%);
  padding: 1.35rem;
  border-radius: 1.2rem;
  border: 1px solid var(--tp-line);
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--tp-accent-soft) 50%, transparent), transparent 38%),
    linear-gradient(180deg, color-mix(in srgb, var(--tp-surface) 92%, white), color-mix(in srgb, var(--tp-surface-alt) 88%, white));
  box-shadow: 0 28px 64px rgba(20, 33, 38, 0.22);
  display: grid;
  gap: 0.9rem;
}

.term-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.term-head h3,
.term-summary,
.term-detail,
.term-list {
  margin: 0;
}

.term-kicker {
  margin: 0 0 0.25rem;
  color: var(--tp-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.close-button {
  border: 1px solid var(--tp-line);
  background: transparent;
  color: var(--tp-text);
  border-radius: 0.8rem;
  padding: 0.65rem 0.8rem;
  cursor: pointer;
}

.term-summary {
  font-size: 1rem;
  font-weight: 600;
  color: var(--tp-text);
}

.term-detail,
.term-list {
  color: var(--tp-muted);
}

.term-list {
  padding-left: 1.1rem;
}

@media (max-width: 640px) {
  .term-head {
    flex-direction: column;
  }
}
</style>

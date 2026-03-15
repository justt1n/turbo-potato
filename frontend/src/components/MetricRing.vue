<template>
  <article class="metric-card" :style="cardStyle">
    <div class="metric-copy">
      <p class="metric-label">{{ label }}</p>
      <strong>{{ value }}</strong>
      <p class="metric-caption">{{ caption }}</p>
    </div>

    <div class="metric-ring-wrap">
      <svg class="metric-ring" viewBox="0 0 120 120" role="img" :aria-label="label">
        <circle class="metric-track" cx="60" cy="60" r="44" />
        <circle
          class="metric-progress"
          cx="60"
          cy="60"
          r="44"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
        />
      </svg>
      <div class="metric-center">
        <span>{{ progress }}%</span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  label: string;
  value: string;
  caption: string;
  progress: number;
  tone?: string;
  glow?: string;
}>();

const radius = 44;
const circumference = 2 * Math.PI * radius;
const normalizedProgress = computed(() => Math.min(100, Math.max(0, props.progress)));
const dashOffset = computed(
  () => circumference - (normalizedProgress.value / 100) * circumference,
);

const cardStyle = computed(() => ({
  "--metric-tone": props.tone ?? "var(--tp-accent)",
  "--metric-glow": props.glow ?? "color-mix(in srgb, var(--tp-accent) 35%, transparent)",
}));
</script>

<style scoped>
.metric-card {
  display: grid;
  grid-template-columns: 1.2fr 160px;
  gap: 1rem;
  padding: 1.35rem;
  border-radius: 1rem;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--tp-surface-alt) 72%, white), color-mix(in srgb, var(--tp-surface) 86%, white));
  border: 1px solid var(--tp-line);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.7),
    0 12px 28px rgba(31, 41, 55, 0.08);
}

.metric-copy {
  display: grid;
  align-content: start;
  gap: 0.45rem;
}

.metric-label {
  margin: 0;
  color: var(--tp-muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.74rem;
}

.metric-copy strong {
  font-size: clamp(1.9rem, 3vw, 2.4rem);
  line-height: 1;
  color: var(--tp-text);
}

.metric-caption {
  margin: 0;
  color: var(--tp-muted);
  max-width: 26ch;
}

.metric-ring-wrap {
  position: relative;
  display: grid;
  place-items: center;
}

.metric-ring {
  width: 140px;
  height: 140px;
  transform: rotate(-90deg);
  filter: drop-shadow(0 0 12px var(--metric-glow));
}

.metric-track,
.metric-progress {
  fill: none;
  stroke-width: 11;
}

.metric-track {
  stroke: color-mix(in srgb, var(--tp-text) 10%, transparent);
}

.metric-progress {
  stroke: var(--metric-tone);
  stroke-linecap: round;
  transition: stroke-dashoffset 300ms ease;
}

.metric-center {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--tp-text);
}

@media (max-width: 720px) {
  .metric-card {
    grid-template-columns: 1fr;
  }
}
</style>

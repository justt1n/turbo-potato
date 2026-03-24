<template>
  <article class="panel signal-panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Line chart</p>
        <h3>{{ title }}</h3>
      </div>
      <span class="panel-kpi">{{ subtitle }}</span>
    </div>

    <div class="chart-shell">
      <svg class="signal-chart" viewBox="0 0 720 260" role="img" :aria-label="title">
        <g class="grid">
          <line v-for="line in gridLines" :key="line" x1="44" :y1="line" x2="676" :y2="line" />
        </g>

        <path class="signal-area" :d="areaPath" />
        <path class="signal-line" :d="linePath" />

        <g v-for="point in points" :key="point.label">
          <circle class="signal-marker" :cx="point.x" :cy="point.y" r="7" :style="{ fill: point.color }" />
          <text class="signal-value" :x="point.x" :y="point.y - 16">{{ point.progress }}%</text>
          <text class="signal-label" :x="point.x" y="232">{{ point.label }}</text>
        </g>
      </svg>
    </div>

    <div class="signal-list">
      <article v-for="item in items" :key="item.label" class="signal-item">
        <div>
          <strong>{{ item.label }}</strong>
          <p>{{ item.caption }}</p>
        </div>
        <div class="signal-meta">
          <span>{{ item.value }}</span>
          <small :class="item.status">{{ statusLabel(item.status) }}</small>
        </div>
      </article>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface SignalItem {
  label: string;
  value: string;
  caption: string;
  progress: number;
  status: string;
}

const props = defineProps<{
  title: string;
  subtitle: string;
  items: SignalItem[];
}>();

const gridLines = computed(() => [28, 84, 140, 196]);

const points = computed(() => {
  if (props.items.length === 0) {
    return [];
  }

  const width = 632;
  const step = props.items.length === 1 ? 0 : width / (props.items.length - 1);

  return props.items.map((item, index) => {
    const progress = Math.max(0, Math.min(100, item.progress));
    return {
      ...item,
      x: 44 + step * index,
      y: 196 - progress * 1.68,
      color: toneFromStatus(item.status),
    };
  });
});

const linePath = computed(() =>
  points.value.map((point, index) => `${index === 0 ? "M" : "L"}${point.x},${point.y}`).join(" "),
);

const areaPath = computed(() => {
  if (points.value.length === 0) {
    return "";
  }

  const topPath = points.value.map((point, index) => `${index === 0 ? "M" : "L"}${point.x},${point.y}`).join(" ");
  const last = points.value.at(-1);
  const first = points.value[0];
  return `${topPath} L${last?.x},196 L${first.x},196 Z`;
});

function statusLabel(status: string): string {
  switch (status) {
    case "critical":
      return "Nguy cơ";
    case "warning":
      return "Theo dõi";
    default:
      return "Ổn";
  }
}

function toneFromStatus(status: string): string {
  switch (status) {
    case "critical":
      return "var(--tp-danger)";
    case "warning":
      return "var(--tp-warm-text)";
    default:
      return "var(--tp-accent-strong)";
  }
}
</script>

<style scoped>
.signal-panel {
  display: grid;
  gap: 1rem;
}

.chart-shell {
  padding: 1rem;
  border-radius: 0.8rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 92%, white);
}

.signal-chart {
  width: 100%;
  height: auto;
}

.grid line {
  stroke: color-mix(in srgb, var(--tp-text) 8%, transparent);
  stroke-dasharray: 6 8;
}

.signal-area {
  fill: color-mix(in srgb, var(--tp-accent-soft) 90%, white);
}

.signal-line {
  fill: none;
  stroke: var(--tp-accent-strong);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.signal-marker {
  stroke: rgba(255, 255, 255, 0.92);
  stroke-width: 3;
}

.signal-value,
.signal-label {
  fill: var(--tp-text);
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
  text-anchor: middle;
}

.signal-value {
  font-size: 13px;
  font-weight: 700;
}

.signal-label {
  font-size: 13px;
  fill: var(--tp-muted);
}

.signal-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.signal-item {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  border-radius: 0.72rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 92%, white);
}

.signal-item strong,
.signal-item p,
.signal-meta span,
.signal-meta small {
  display: block;
}

.signal-item p {
  margin: 0.25rem 0 0;
  color: var(--tp-muted);
  font-size: 0.85rem;
}

.signal-meta {
  text-align: right;
}

.signal-meta span {
  font-weight: 800;
}

.signal-meta small {
  margin-top: 0.2rem;
  font-size: 0.78rem;
}

.signal-meta .healthy {
  color: var(--tp-accent-strong);
}

.signal-meta .warning {
  color: var(--tp-warm-text);
}

.signal-meta .critical {
  color: var(--tp-danger);
}

@media (max-width: 720px) {
  .signal-list {
    grid-template-columns: 1fr;
  }
}
</style>

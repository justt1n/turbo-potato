<template>
  <article class="panel combo-panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Combo chart</p>
        <h3>{{ title }}</h3>
      </div>
      <span class="panel-kpi">{{ subtitle }}</span>
    </div>

    <div class="chart-shell">
      <svg class="combo-chart" viewBox="0 0 720 260" role="img" :aria-label="title">
        <g class="grid">
          <line v-for="line in gridLines" :key="line" x1="44" :y1="line" x2="676" :y2="line" />
        </g>

        <path class="combo-line" :d="linePath" />

        <g v-for="bar in bars" :key="bar.label">
          <rect class="combo-bar" :x="bar.x" :y="bar.y" :width="bar.width" :height="bar.height" :style="{ fill: bar.color }" />
          <circle class="combo-point" :cx="bar.x + bar.width / 2" :cy="bar.previousY" r="6" />
          <text class="combo-label" :x="bar.x + bar.width / 2" y="232">{{ bar.label }}</text>
        </g>
      </svg>
    </div>

    <div class="combo-legend">
      <span><i class="legend-bar"></i>Cột hiện tại</span>
      <span><i class="legend-line"></i>Đường kỳ trước</span>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

interface ComboSeries {
  label: string;
  values: number[];
  color: string;
}

const props = defineProps<{
  title: string;
  subtitle: string;
  seriesList: ComboSeries[];
}>();

const gridLines = computed(() => [28, 84, 140, 196]);

const normalized = computed(() => {
  const source = props.seriesList.map((series) => {
    const current = series.values.at(-1) ?? 0;
    const previous = series.values.length > 1 ? series.values[series.values.length - 2] : current;
    return { ...series, current, previous };
  });
  const max = Math.max(100, ...source.flatMap((item) => [item.current, item.previous]));
  return source.map((item) => ({ ...item, max }));
});

const bars = computed(() => {
  if (normalized.value.length === 0) {
    return [];
  }

  const step = 632 / normalized.value.length;
  const width = Math.min(96, step * 0.48);

  return normalized.value.map((item, index) => {
    const x = 44 + step * index + (step - width) / 2;
    const height = (item.current / item.max) * 168;
    const previousHeight = (item.previous / item.max) * 168;
    return {
      label: item.label,
      color: item.color,
      x,
      width,
      y: 196 - height,
      height,
      previousY: 196 - previousHeight,
    };
  });
});

const linePath = computed(() =>
  bars.value.map((bar, index) => `${index === 0 ? "M" : "L"}${bar.x + bar.width / 2},${bar.previousY}`).join(" "),
);
</script>

<style scoped>
.combo-panel {
  display: grid;
  gap: 1rem;
}

.chart-shell {
  padding: 1rem;
  border-radius: 0.8rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 92%, white);
}

.combo-chart {
  width: 100%;
  height: auto;
}

.grid line {
  stroke: color-mix(in srgb, var(--tp-text) 8%, transparent);
  stroke-dasharray: 6 8;
}

.combo-line {
  fill: none;
  stroke: color-mix(in srgb, var(--tp-text) 70%, white);
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.combo-bar {
  rx: 10;
}

.combo-point {
  fill: #ffffff;
  stroke: color-mix(in srgb, var(--tp-text) 70%, white);
  stroke-width: 3;
}

.combo-label {
  fill: var(--tp-muted);
  font-size: 13px;
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
  text-anchor: middle;
}

.combo-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  color: var(--tp-muted);
  font-size: 0.84rem;
}

.combo-legend span {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

.legend-bar,
.legend-line {
  display: inline-block;
  width: 1.1rem;
  height: 0.55rem;
}

.legend-bar {
  border-radius: 0.3rem;
  background: linear-gradient(135deg, var(--tp-accent-strong), var(--tp-accent));
}

.legend-line {
  position: relative;
}

.legend-line::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  border-top: 2px solid color-mix(in srgb, var(--tp-text) 70%, white);
}
</style>

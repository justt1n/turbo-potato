<template>
  <article class="panel baseline-panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Baselines</p>
        <h3>{{ title }}</h3>
      </div>
      <span class="panel-kpi">{{ subtitle }}</span>
    </div>

    <div class="chart-shell">
      <svg class="baseline-chart" viewBox="0 0 680 260" role="img" :aria-label="title">
        <g class="grid">
          <line
            v-for="line in gridLines"
            :key="line"
            x1="0"
            :y1="line"
            x2="680"
            :y2="line"
          />
        </g>

        <path
          v-for="series in seriesList"
          :key="series.label"
          class="baseline-path"
          :d="buildLinePath(series.values, 680, 220)"
          :stroke="series.color"
        />
      </svg>
    </div>

    <div class="baseline-list">
      <article v-for="series in seriesList" :key="series.label" class="baseline-row">
        <div class="baseline-meta">
          <span class="baseline-dot" :style="{ background: series.color }"></span>
          <div>
            <strong>{{ series.label }}</strong>
            <p>{{ series.description }}</p>
          </div>
        </div>

        <div class="baseline-stats">
          <span>{{ series.current }}</span>
          <small :class="series.delta.startsWith('-') ? 'delta-good' : 'delta-bad'">
            {{ series.delta }}
          </small>
        </div>
      </article>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { buildLinePath } from "@/lib/chart";

export interface BaselineSeries {
  label: string;
  description: string;
  values: number[];
  current: string;
  delta: string;
  color: string;
}

const props = defineProps<{
  title: string;
  subtitle: string;
  seriesList: BaselineSeries[];
}>();

const gridLines = computed(() => [20, 80, 140, 200]);
</script>

<style scoped>
.baseline-panel {
  display: grid;
  gap: 1.1rem;
}

.chart-shell {
  position: relative;
  overflow: hidden;
  border-radius: 0.8rem;
  padding: 1rem 1rem 0.75rem;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--tp-surface) 76%, white), color-mix(in srgb, var(--tp-surface-alt) 72%, white));
  border: 1px solid var(--tp-line);
}

.baseline-chart {
  width: 100%;
  height: auto;
}

.grid line {
  stroke: color-mix(in srgb, var(--tp-text) 8%, transparent);
  stroke-dasharray: 6 8;
}

.baseline-path {
  fill: none;
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
  filter: drop-shadow(0 6px 10px color-mix(in srgb, currentColor 12%, transparent));
}

.baseline-list {
  display: grid;
  gap: 0.75rem;
}

.baseline-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 0.95rem 1rem;
  border-radius: 0.8rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 86%, white);
}

.baseline-meta {
  display: flex;
  gap: 0.8rem;
  align-items: flex-start;
}

.baseline-dot {
  width: 0.7rem;
  height: 0.7rem;
  margin-top: 0.35rem;
  border-radius: 999px;
  flex: 0 0 auto;
}

.baseline-meta strong,
.baseline-meta p,
.baseline-stats span,
.baseline-stats small {
  display: block;
}

.baseline-meta p {
  margin: 0.15rem 0 0;
  color: var(--tp-muted);
}

.baseline-stats {
  text-align: right;
}

.baseline-stats span {
  font-size: 1rem;
  font-weight: 700;
  color: var(--tp-text);
}

.baseline-stats small {
  margin-top: 0.2rem;
  font-size: 0.8rem;
}

.delta-good {
  color: #2c7a4b;
}

.delta-bad {
  color: #b44d61;
}

@media (max-width: 720px) {
  .baseline-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .baseline-stats {
    text-align: left;
  }
}
</style>


<template>
  <article class="panel baseline-panel">
    <div class="panel-head">
      <div>
        <p class="eyebrow">Đường chuẩn</p>
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
          <small :class="deltaClass(series)">
            {{ series.delta }}
          </small>
        </div>

        <div class="baseline-status-shell">
          <div class="baseline-status-copy">
            <strong>{{ statusLabel(series) }}</strong>
            <span>{{ statusDescription(series) }}</span>
          </div>
          <div class="baseline-status-track" aria-hidden="true">
            <span class="baseline-zone low"></span>
            <span class="baseline-zone balanced"></span>
            <span class="baseline-zone high"></span>
            <span class="baseline-marker" :style="{ left: markerOffset(series) }"></span>
          </div>
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

function latestValue(series: BaselineSeries): number {
  return series.values.at(-1) ?? 0;
}

function previousValue(series: BaselineSeries): number {
  return series.values.length > 1 ? series.values[series.values.length - 2] : latestValue(series);
}

function markerOffset(series: BaselineSeries): string {
  return `${Math.min(100, Math.max(0, latestValue(series)))}%`;
}

function isLowerBetter(series: BaselineSeries): boolean {
  return series.label !== "Tốc độ tích lũy";
}

function deltaClass(series: BaselineSeries): string {
  const rising = latestValue(series) > previousValue(series);
  if (isLowerBetter(series)) {
    return rising ? "delta-bad" : "delta-good";
  }
  return rising ? "delta-good" : "delta-bad";
}

function statusLabel(series: BaselineSeries): string {
  const current = latestValue(series);
  if (series.label === "Tốc độ tích lũy") {
    if (current >= 67) {
      return "Rất tốt";
    }
    if (current >= 34) {
      return "Đang lên";
    }
    return "Chậm";
  }

  if (current <= 33) {
    return "Ổn định";
  }
  if (current <= 66) {
    return "Cần theo dõi";
  }
  return "Căng cao";
}

function statusDescription(series: BaselineSeries): string {
  const label = statusLabel(series);
  if (series.label === "Tốc độ tích lũy") {
    if (label === "Rất tốt") {
      return "Tốc độ bổ sung cho mục tiêu đang vượt đường chuẩn gần đây.";
    }
    if (label === "Đang lên") {
      return "Dòng chuyển vào mục tiêu đang tăng, nhưng vẫn còn dư địa để mạnh hơn.";
    }
    return "Tốc độ tích lũy đang chậm hơn nhịp gần đây và cần chú ý.";
  }

  if (label === "Ổn định") {
    return "Mức hiện tại nằm trong vùng vận hành dễ chịu so với đường chuẩn gần đây.";
  }
  if (label === "Cần theo dõi") {
    return "Xu hướng này cao hơn vùng bình ổn và nên theo dõi thêm.";
  }
  return "Xu hướng này đang nóng hơn rõ so với đường chuẩn gần đây.";
}
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
  flex-wrap: wrap;
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
  margin-left: auto;
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

.baseline-status-shell {
  display: grid;
  gap: 0.55rem;
  width: 100%;
}

.baseline-status-copy {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
}

.baseline-status-copy strong {
  font-size: 0.9rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.baseline-status-copy span {
  color: var(--tp-muted);
  font-size: 0.84rem;
  text-align: right;
}

.baseline-status-track {
  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  height: 0.85rem;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tp-surface) 80%, white);
  border: 1px solid var(--tp-line);
}

.baseline-zone.low {
  background: color-mix(in srgb, var(--tp-accent) 72%, white);
}

.baseline-zone.balanced {
  background: color-mix(in srgb, var(--tp-accent-soft) 74%, #fff2c2);
}

.baseline-zone.high {
  background: color-mix(in srgb, var(--tp-danger-soft) 78%, white);
}

.baseline-marker {
  position: absolute;
  top: -0.15rem;
  bottom: -0.15rem;
  width: 0.5rem;
  margin-left: -0.25rem;
  border-radius: 999px;
  background: var(--tp-text);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--tp-surface) 88%, white);
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

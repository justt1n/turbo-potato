<template>
  <section class="page">
    <header class="dashboard-header panel">
      <div>
        <p class="eyebrow">Dashboard</p>
        <h2>Personal finance cockpit</h2>
        <p class="lede">
          A calmer Grafana-style surface for spending pressure, structural risk, and progress.
        </p>
      </div>

      <div class="status-strip">
        <span class="status-pill" :class="pillClass(summary?.sts.status)">
          {{ summary?.sts.label ?? "STS" }} {{ summary?.sts.status ?? "loading" }}
        </span>
        <span class="status-pill soft">
          {{ summary?.baselines.length ?? 0 }} baselines tracked
        </span>
        <span class="status-pill warn">
          {{ summary?.operatingPosture.status ?? "Waiting for snapshot" }}
        </span>
      </div>
    </header>

    <p v-if="summaryQuery.isLoading.value || reportsQuery.isLoading.value" class="panel state-panel">Loading dashboard data...</p>
    <p v-else-if="summaryQuery.isError.value || reportsQuery.isError.value" class="panel state-panel state-error">
      {{ ((summaryQuery.error.value ?? reportsQuery.error.value) as Error).message }}
    </p>

    <template v-else-if="summary">
      <div class="metrics-grid">
        <MetricRing
          :label="summary.sts.label"
          :value="summary.sts.value"
          :caption="summary.sts.caption"
          :progress="summary.sts.progress"
          :tone="toneFromStatus(summary.sts.status)"
          :glow="glowFromStatus(summary.sts.status)"
        />
        <MetricRing
          :label="summary.anomaly.label"
          :value="summary.anomaly.value"
          :caption="summary.anomaly.caption"
          :progress="summary.anomaly.progress"
          :tone="toneFromStatus(summary.anomaly.status)"
          :glow="glowFromStatus(summary.anomaly.status)"
        />
        <MetricRing
          :label="summary.goalPace.label"
          :value="summary.goalPace.value"
          :caption="summary.goalPace.caption"
          :progress="summary.goalPace.progress"
          :tone="toneFromStatus(summary.goalPace.status)"
          :glow="glowFromStatus(summary.goalPace.status)"
        />
      </div>

      <div class="dashboard-columns">
        <BaselineMonitor
          title="Baseline monitor"
          subtitle="Track multiple baselines at once"
          :series-list="baselineSeries"
        />

        <article class="panel summary-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Snapshot</p>
              <h3>Operating posture</h3>
            </div>
            <span class="panel-kpi">{{ summary.operatingPosture.status }}</span>
          </div>

          <ul class="summary-list">
            <li v-for="item in summary.operatingPosture.items" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </li>
          </ul>
        </article>
      </div>

      <div class="report-grid">
        <article class="panel report-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Daily report</p>
              <h3>{{ reports?.daily.title ?? "Daily financial status" }}</h3>
            </div>
            <span class="status-pill" :class="pillClass(reports?.daily.status)">
              {{ reports?.daily.status ?? "waiting" }}
            </span>
          </div>
          <p class="report-summary">{{ reports?.daily.summary }}</p>
          <pre class="report-body">{{ reports?.daily.body }}</pre>
          <p class="report-meta">
            {{ reports?.daily.verdict }} · {{ formatTimestamp(reports?.daily.createdAt) }}
          </p>
        </article>

        <article class="panel report-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Monthly report</p>
              <h3>{{ reports?.monthly?.title ?? "Monthly report not generated yet" }}</h3>
            </div>
            <button class="action-button" :disabled="monthlyMutation.isPending.value" @click="generateMonthly">
              {{ monthlyMutation.isPending.value ? "Generating..." : "Generate now" }}
            </button>
          </div>
          <p class="report-summary">
            {{ reports?.monthly?.summary ?? "Generated on demand, and auto-created on the first day of each month." }}
          </p>
          <pre class="report-body">{{ reports?.monthly?.body ?? "No monthly report available yet." }}</pre>
          <p class="report-meta">
            {{ reports?.monthly?.verdict ?? "Ask for a monthly analysis when you want a full structural review." }}
          </p>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { generateMonthlyReport, getDashboardReports, getDashboardSummary } from "@/api/dashboard";
import BaselineMonitor from "@/components/BaselineMonitor.vue";
import MetricRing from "@/components/MetricRing.vue";

const queryClient = useQueryClient();

const summaryQuery = useQuery({
  queryKey: ["dashboard-summary"],
  queryFn: getDashboardSummary,
});

const reportsQuery = useQuery({
  queryKey: ["dashboard-reports"],
  queryFn: getDashboardReports,
});

const monthlyMutation = useMutation({
  mutationFn: generateMonthlyReport,
  onSuccess: async () => {
    await queryClient.invalidateQueries({ queryKey: ["dashboard-reports"] });
  },
});

const summary = computed(() => summaryQuery.data.value);
const reports = computed(() => reportsQuery.data.value);

const baselineSeries = computed(() =>
  (summary.value?.baselines ?? []).map((series) => ({
    label: series.label,
    description: series.description,
    values: series.values,
    current: series.current,
    delta: series.delta,
    color: series.colorToken,
  })),
);

function toneFromStatus(status: string): string {
  switch (status) {
    case "critical":
      return "var(--tp-danger)";
    case "warning":
      return "var(--tp-danger-soft)";
    default:
      return "var(--tp-accent)";
  }
}

function glowFromStatus(status: string): string {
  switch (status) {
    case "critical":
      return "color-mix(in srgb, var(--tp-danger) 30%, transparent)";
    case "warning":
      return "color-mix(in srgb, var(--tp-danger-soft) 36%, transparent)";
    default:
      return "color-mix(in srgb, var(--tp-accent) 32%, transparent)";
  }
}

function pillClass(status?: string): string {
  switch (status) {
    case "critical":
      return "warn";
    case "warning":
      return "soft";
    default:
      return "ok";
  }
}

function generateMonthly(): void {
  monthlyMutation.mutate();
}

function formatTimestamp(value?: string): string {
  if (!value) {
    return "Not generated yet";
  }

  return new Date(value).toLocaleString();
}
</script>

<style scoped>
.dashboard-header {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-start;
}

.dashboard-header h2 {
  margin: 0.35rem 0 0.4rem;
  font-size: clamp(2.2rem, 4vw, 3.6rem);
  line-height: 0.9;
  letter-spacing: -0.05em;
}

.lede {
  max-width: 48rem;
  margin: 0;
  color: var(--tp-muted);
}

.status-strip {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.65rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.7rem 0.95rem;
  border-radius: 0.55rem;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: 1px solid var(--tp-line);
}

.ok {
  background: var(--tp-accent);
  color: var(--tp-text);
}

.soft {
  background: var(--tp-accent-soft);
  color: var(--tp-text);
}

.warn {
  background: var(--tp-danger-soft);
  color: #6b3f46;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.dashboard-columns {
  display: grid;
  grid-template-columns: 1.35fr 0.9fr;
  gap: 1rem;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
}

.state-panel {
  margin: 0;
}

.state-error {
  color: #8f2438;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.panel-head h3 {
  margin: 0.25rem 0 0;
  font-size: 1.35rem;
  letter-spacing: -0.03em;
}

.panel-kpi {
  color: var(--tp-muted);
  font-weight: 700;
}

.summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.85rem;
}

.summary-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 1rem 1.1rem;
  border-radius: 0.8rem;
  background: color-mix(in srgb, var(--tp-accent-soft) 65%, white);
  border: 1px solid var(--tp-line);
}

.summary-list span {
  color: var(--tp-muted);
}

.summary-list strong {
  font-size: 1.1rem;
  color: var(--tp-text);
}

.report-panel {
  min-height: 22rem;
}

.report-summary {
  margin: 0 0 1rem;
  font-size: 1rem;
  color: var(--tp-text);
}

.report-body {
  margin: 0;
  padding: 1rem;
  border-radius: 0.8rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 88%, white);
  font: inherit;
  color: var(--tp-muted);
  white-space: pre-wrap;
}

.report-meta {
  margin: 1rem 0 0;
  color: var(--tp-muted);
}

.action-button {
  border: 1px solid var(--tp-line);
  background: var(--tp-text);
  color: white;
  border-radius: 0.6rem;
  padding: 0.75rem 1rem;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.action-button:disabled {
  cursor: progress;
  opacity: 0.7;
}

@media (max-width: 980px) {
  .dashboard-header,
  .dashboard-columns {
    grid-template-columns: 1fr;
    display: grid;
  }

  .status-strip {
    justify-content: flex-start;
  }
}
</style>

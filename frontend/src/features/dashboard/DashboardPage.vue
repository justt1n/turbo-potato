<template>
  <section class="page">
    <header class="dashboard-header panel">
      <div>
        <p class="eyebrow">Tổng quan</p>
        <h2>Buồng lái tài chính cá nhân</h2>
        <p class="lede">
          Màn hình tổng hợp để theo dõi áp lực chi tiêu, rủi ro cấu trúc và tiến độ tài chính.
        </p>
      </div>

      <div class="status-cluster">
        <RouterLink class="detail-link" to="/dashboard/detail">Mở trang chi tiết</RouterLink>
        <div class="status-strip">
          <span class="status-pill" :class="pillClass(summary?.sts.status)">
            {{ metricLabel(summary?.sts.label ?? "STS") }} {{ statusLabel(summary?.sts.status ?? "loading") }}
          </span>
          <span class="status-pill soft">
            {{ summary?.baselines.length ?? 0 }} đường chuẩn đang theo dõi
          </span>
          <span class="status-pill warn">
            {{ postureStatusLabel(summary?.operatingPosture.status) }}
          </span>
        </div>
      </div>
    </header>

    <p v-if="summaryQuery.isLoading.value || reportsQuery.isLoading.value" class="panel state-panel">Đang tải dữ liệu tổng quan...</p>
    <p v-else-if="summaryQuery.isError.value || reportsQuery.isError.value" class="panel state-panel state-error">
      {{ ((summaryQuery.error.value ?? reportsQuery.error.value) as Error).message }}
    </p>

    <template v-else-if="summary">
      <div class="metrics-grid">
        <MetricRing
          :label="metricLabel(summary.sts.label)"
          :value="summary.sts.value"
          :caption="metricCaption(summary.sts.label, summary.sts.caption)"
          :progress="summary.sts.progress"
          :tone="toneFromStatus(summary.sts.status)"
          :glow="glowFromStatus(summary.sts.status)"
        />
        <MetricRing
          :label="metricLabel(summary.anomaly.label)"
          :value="summary.anomaly.value"
          :caption="metricCaption(summary.anomaly.label, summary.anomaly.caption)"
          :progress="summary.anomaly.progress"
          :tone="toneFromStatus(summary.anomaly.status)"
          :glow="glowFromStatus(summary.anomaly.status)"
        />
        <MetricRing
          :label="metricLabel(summary.tar.label)"
          :value="summary.tar.value"
          :caption="metricCaption(summary.tar.label, summary.tar.caption)"
          :progress="summary.tar.progress"
          :tone="toneFromStatus(summary.tar.status)"
          :glow="glowFromStatus(summary.tar.status)"
        />
        <MetricRing
          :label="metricLabel(summary.goalPace.label)"
          :value="summary.goalPace.value"
          :caption="metricCaption(summary.goalPace.label, summary.goalPace.caption)"
          :progress="summary.goalPace.progress"
          :tone="toneFromStatus(summary.goalPace.status)"
          :glow="glowFromStatus(summary.goalPace.status)"
        />
      </div>

      <div class="dashboard-columns">
        <BaselineMonitor
          title="Bảng theo dõi đường chuẩn"
          subtitle="Góc nhìn kiểu Garmin HRV cho những nhịp tài chính quan trọng"
          :series-list="baselineSeries"
        />

        <article class="panel summary-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Ảnh chụp nhanh</p>
              <h3>Thế vận hành</h3>
            </div>
            <span class="panel-kpi">{{ postureStatusLabel(summary.operatingPosture.status) }}</span>
          </div>

          <ul class="summary-list">
            <li v-for="item in summary.operatingPosture.items" :key="item.label">
              <span>{{ postureItemLabel(item.label) }}</span>
              <strong>{{ item.value }}</strong>
            </li>
          </ul>
        </article>
      </div>

      <div class="report-grid">
        <article class="panel report-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Báo cáo ngày</p>
              <h3>{{ reports?.daily.title ?? "Tình trạng tài chính trong ngày" }}</h3>
            </div>
            <span class="status-pill" :class="pillClass(reports?.daily.status)">
              {{ reportStatusLabel(reports?.daily.status) }}
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
              <p class="eyebrow">Báo cáo tháng</p>
              <h3>{{ reports?.monthly?.title ?? "Chưa tạo báo cáo tháng" }}</h3>
            </div>
            <button class="action-button" :disabled="monthlyMutation.isPending.value" @click="generateMonthly">
              {{ monthlyMutation.isPending.value ? "Đang tạo..." : "Tạo ngay" }}
            </button>
          </div>
          <p class="report-summary">
            {{ reports?.monthly?.summary ?? "Báo cáo tháng được tạo khi bạn yêu cầu, và tự động tạo vào ngày đầu tiên của tháng." }}
          </p>
          <pre class="report-body">{{ reports?.monthly?.body ?? "Chưa có báo cáo tháng." }}</pre>
          <p class="report-meta">
            {{ reports?.monthly?.verdict ?? "Hãy tạo báo cáo tháng khi bạn muốn xem đánh giá cấu trúc tổng thể." }}
          </p>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
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
    label: baselineLabel(series.label),
    description: baselineDescription(series.label, series.description),
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
    return "Chưa tạo";
  }

  return new Date(value).toLocaleString("vi-VN");
}

function metricLabel(label: string): string {
  switch (label) {
    case "Goal Pace":
      return "Tốc độ mục tiêu";
    case "Anomaly":
      return "Bất thường";
    case "TAR":
      return "TAR";
    case "STS":
      return "STS";
    default:
      return label;
  }
}

function metricCaption(label: string, fallback: string): string {
  switch (label) {
    case "STS":
      return "Mức chi an toàn mỗi ngày còn lại trong tháng này.";
    case "Anomaly":
      return "Độ lệch của chi tiêu hiện tại so với hành vi gần đây.";
    case "TAR":
      return "Chất lượng tích lũy sau khi trừ chi tiêu và dòng tiền mục tiêu.";
    case "Goal Pace":
      return "Tiến độ hiện tại hướng tới mục tiêu đang theo dõi.";
    default:
      return fallback;
  }
}

function baselineLabel(label: string): string {
  switch (label) {
    case "Variable spend":
      return "Chi tiêu biến đổi";
    case "Fixed-cost load":
      return "Tải chi phí cố định";
    case "Goal velocity":
      return "Tốc độ tích lũy";
    default:
      return label;
  }
}

function baselineDescription(label: string, fallback: string): string {
  switch (label) {
    case "Variable spend":
      return "Nhịp chi tiêu linh hoạt của bạn so với đường chuẩn gần đây.";
    case "Fixed-cost load":
      return "Mức độ chi phí cố định đang ép lên dòng tiền hiện tại.";
    case "Goal velocity":
      return "Động lực nạp tiền vào các mục tiêu trong thời gian gần đây.";
    default:
      return fallback;
  }
}

function postureItemLabel(label: string): string {
  switch (label) {
    case "Runway":
      return "Dự phòng";
    case "Fixed-cost load":
      return "Tải chi phí cố định";
    case "Goal velocity":
      return "Tốc độ tích lũy";
    case "ETA":
      return "Dự kiến cán đích";
    default:
      return label;
  }
}

function postureStatusLabel(status?: string): string {
  switch (status) {
    case "Stable":
      return "Ổn định";
    case "Moderate risk":
      return "Rủi ro vừa";
    case "High alert":
      return "Cảnh báo cao";
    case "waiting":
    case undefined:
      return "Đang chờ dữ liệu";
    default:
      return status;
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case "loading":
      return "đang tải";
    case "healthy":
      return "tốt";
    case "warning":
      return "cần theo dõi";
    case "critical":
      return "nguy cơ";
    default:
      return status;
  }
}

function reportStatusLabel(status?: string): string {
  switch (status) {
    case "healthy":
      return "tốt";
    case "warning":
      return "cần theo dõi";
    case "critical":
      return "nguy cơ";
    case "waiting":
    case undefined:
      return "đang chờ";
    default:
      return status;
  }
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

.status-cluster {
  display: grid;
  justify-items: end;
  gap: 0.85rem;
}

.status-strip {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.65rem;
}

.detail-link {
  display: inline-flex;
  align-items: center;
  padding: 0.8rem 1rem;
  border-radius: 0.7rem;
  background: var(--tp-text);
  color: #f7faf7;
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
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
  min-height: 11rem;
  white-space: pre-wrap;
  color: var(--tp-muted);
  font: 0.93rem/1.55 "IBM Plex Mono", monospace;
}

.report-meta {
  margin-top: 1rem;
  color: var(--tp-muted);
}

.action-button {
  border: 0;
  border-radius: 0.75rem;
  padding: 0.8rem 1rem;
  background: var(--tp-text);
  color: #f7faf7;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.action-button:disabled {
  opacity: 0.6;
  cursor: wait;
}

@media (max-width: 1080px) {
  .dashboard-header {
    flex-direction: column;
  }

  .dashboard-columns {
    grid-template-columns: 1fr;
  }

  .status-cluster {
    justify-items: start;
  }

  .status-strip {
    justify-content: flex-start;
  }
}
</style>

<template>
  <section class="page">
    <header class="detail-header panel">
      <div>
        <p class="eyebrow">Chi tiết tổng quan</p>
        <h2>Giải nghĩa chỉ số</h2>
        <p class="lede">
          Góc nhìn sâu hơn về ý nghĩa chỉ số, diễn giải xu hướng và tín hiệu hiện tại.
        </p>
      </div>

      <div class="detail-actions">
        <RouterLink class="detail-link" to="/">Quay lại tổng quan</RouterLink>
      </div>
    </header>

    <p v-if="summaryQuery.isLoading.value || reportsQuery.isLoading.value" class="panel">Đang tải phân tích chi tiết...</p>
    <p v-else-if="summaryQuery.isError.value || reportsQuery.isError.value" class="panel detail-error">
      {{ ((summaryQuery.error.value ?? reportsQuery.error.value) as Error).message }}
    </p>

    <template v-else-if="summary">
      <div class="detail-grid">
        <article v-for="metric in metricCards" :key="metric.label" class="panel metric-detail-card">
          <div class="metric-detail-head">
            <div>
              <p class="eyebrow">Chỉ số</p>
              <h3>{{ metric.displayLabel }}</h3>
            </div>
            <span class="status-pill" :class="pillClass(metric.status)">{{ statusLabel(metric.status) }}</span>
          </div>

          <div class="metric-detail-kpi">
            <strong>{{ metric.value }}</strong>
            <span>{{ metric.progress }}%</span>
          </div>

          <p class="metric-detail-caption">{{ metric.caption }}</p>
          <p class="metric-detail-description">{{ metric.description }}</p>
        </article>
      </div>

      <div class="detail-columns">
        <article class="panel posture-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Thế vận hành</p>
              <h3>{{ postureStatusLabel(summary.operatingPosture.status) }}</h3>
            </div>
            <span class="panel-kpi">Cấu trúc hiện tại</span>
          </div>

          <ul class="posture-list">
            <li v-for="item in summary.operatingPosture.items" :key="item.label">
              <span>{{ postureItemLabel(item.label) }}</span>
              <strong>{{ item.value }}</strong>
            </li>
          </ul>
        </article>

        <article class="panel baseline-summary-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Đọc đường chuẩn</p>
              <h3>Diễn giải tín hiệu</h3>
            </div>
            <span class="panel-kpi">{{ summary.baselines.length }} chuỗi</span>
          </div>

          <div class="baseline-summary-list">
            <article v-for="series in baselineSummaries" :key="series.label" class="baseline-summary-item">
              <strong>{{ series.label }}</strong>
              <p>{{ series.description }}</p>
              <div class="baseline-inline-meta">
                <span>{{ series.current }}</span>
                <small :class="series.deltaClass">{{ series.delta }}</small>
              </div>
              <p class="baseline-summary-status">{{ series.statusText }}</p>
            </article>
          </div>
        </article>
      </div>

      <BaselineMonitor
        title="Chi tiết đường chuẩn"
        subtitle="Góc nhìn kiểu Garmin HRV trên hành vi tài chính"
        :series-list="baselineSeries"
      />

      <div class="detail-columns">
        <article class="panel report-detail-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Báo cáo ngày</p>
              <h3>{{ reports?.daily.title ?? "Tình trạng tài chính trong ngày" }}</h3>
            </div>
            <span class="status-pill" :class="pillClass(reports?.daily.status)">{{ reportStatusLabel(reports?.daily.status) }}</span>
          </div>
          <p class="report-summary">{{ reports?.daily.summary }}</p>
          <pre class="report-body">{{ reports?.daily.body }}</pre>
        </article>

        <article class="panel report-detail-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Báo cáo tháng</p>
              <h3>{{ reports?.monthly?.title ?? "Chưa tạo báo cáo tháng" }}</h3>
            </div>
            <span class="panel-kpi">{{ reportStatusLabel(reports?.monthly?.status ?? "on-demand") }}</span>
          </div>
          <p class="report-summary">
            {{ reports?.monthly?.summary ?? "Hãy tạo báo cáo tháng từ trang tổng quan khi bạn muốn xem phân tích cấu trúc đầy đủ." }}
          </p>
          <pre class="report-body">{{ reports?.monthly?.body ?? "Chưa có báo cáo tháng." }}</pre>
        </article>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import { useQuery } from "@tanstack/vue-query";
import { getDashboardReports, getDashboardSummary } from "@/api/dashboard";
import BaselineMonitor from "@/components/BaselineMonitor.vue";

const summaryQuery = useQuery({
  queryKey: ["dashboard-summary"],
  queryFn: getDashboardSummary,
});

const reportsQuery = useQuery({
  queryKey: ["dashboard-reports"],
  queryFn: getDashboardReports,
});

const summary = computed(() => summaryQuery.data.value);
const reports = computed(() => reportsQuery.data.value);

const metricCards = computed(() => {
  if (!summary.value) {
    return [];
  }

  return [
    {
      ...summary.value.sts,
      displayLabel: metricLabel(summary.value.sts.label),
      description:
        "STS là mức chi linh hoạt an toàn mỗi ngày còn lại sau khi lấy thu nhập nền gần đây trừ chi phí cố định và phần cần dành cho mục tiêu.",
    },
    {
      ...summary.value.anomaly,
      displayLabel: metricLabel(summary.value.anomaly.label),
      description:
        "Anomaly dùng robust z-score trên chi tiêu theo ngày của 60 ngày gần đây để đo xem hôm nay lệch khỏi nhịp thường đến đâu.",
    },
    {
      ...summary.value.tar,
      displayLabel: metricLabel(summary.value.tar.label),
      description:
        "TAR ở dashboard này nên hiểu là tỷ lệ tiết kiệm ròng: thu nhập tháng trừ chi tiêu thực tế rồi chia cho thu nhập, không cộng đúp các khoản chuyển nội bộ.",
    },
    {
      ...summary.value.goalPace,
      displayLabel: metricLabel(summary.value.goalPace.label),
      description:
        "Tốc độ mục tiêu so sánh vận tốc nạp tiền 90 ngày gần đây với vận tốc cần có để kịp đích của mục tiêu đang active.",
    },
  ];
});

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

const baselineSummaries = computed(() =>
  baselineSeries.value.map((series) => ({
    ...series,
    deltaClass: deltaClass(series),
    statusText: detailStatusText(series),
  })),
);

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

function isLowerBetter(label: string): boolean {
  return label !== "Tốc độ tích lũy";
}

function deltaClass(series: { label: string; values: number[] }): string {
  const current = series.values.at(-1) ?? 0;
  const previous = series.values.length > 1 ? series.values[series.values.length - 2] : current;
  const rising = current > previous;
  if (isLowerBetter(series.label)) {
    return rising ? "delta-bad" : "delta-good";
  }
  return rising ? "delta-good" : "delta-bad";
}

function detailStatusText(series: { label: string; values: number[] }): string {
  const current = series.values.at(-1) ?? 0;
  if (series.label === "Tốc độ tích lũy") {
    if (current >= 67) {
      return "Động lực tích lũy đang cao hơn đường chuẩn gần đây và đi đúng hướng.";
    }
    if (current >= 34) {
      return "Động lực tích lũy đang cải thiện, nhưng vẫn còn dư địa để mạnh hơn.";
    }
    return "Động lực tích lũy đang thấp hơn đường chuẩn gần đây và cần chú ý.";
  }

  if (current <= 33) {
    return "Hành vi hiện tại đang nằm trong vùng ổn định và có thể duy trì.";
  }
  if (current <= 66) {
    return "Hành vi hiện tại đang cao hơn bình thường và nên theo dõi kỹ hơn.";
  }
  return "Hành vi hiện tại đang nóng rõ rệt so với đường chuẩn gần đây.";
}

function metricLabel(label: string): string {
  switch (label) {
    case "Goal Pace":
      return "Mức bám tiến độ mục tiêu";
    case "Anomaly":
      return "Lệch nhịp chi tiêu";
    case "TAR":
      return "Tỷ lệ tiết kiệm ròng";
    case "STS":
      return "STS";
    default:
      return label;
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
      return "Mức độ chi phí cố định đang tạo áp lực lên thu nhập.";
    case "Goal velocity":
      return "Tốc độ chuyển tiền vào mục tiêu trong thời gian gần đây.";
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
    default:
      return status ?? "Đang chờ dữ liệu";
  }
}

function statusLabel(status?: string): string {
  switch (status) {
    case "healthy":
      return "tốt";
    case "warning":
      return "cần theo dõi";
    case "critical":
      return "nguy cơ";
    default:
      return status ?? "đang chờ";
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
    case "on-demand":
      return "theo yêu cầu";
    default:
      return status ?? "đang chờ";
  }
}
</script>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-start;
}

.detail-header h2 {
  margin: 0.35rem 0 0.4rem;
  font-size: clamp(2rem, 3vw, 3.1rem);
  line-height: 0.95;
  letter-spacing: -0.05em;
}

.lede {
  max-width: 48rem;
  margin: 0;
  color: var(--tp-muted);
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
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

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.metric-detail-card {
  display: grid;
  gap: 0.9rem;
}

.metric-detail-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.metric-detail-head h3 {
  margin: 0.25rem 0 0;
  font-size: 1.25rem;
}

.metric-detail-kpi {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
}

.metric-detail-kpi strong {
  font-size: 2rem;
  line-height: 1;
}

.metric-detail-kpi span {
  color: var(--tp-muted);
  font-weight: 700;
}

.metric-detail-caption,
.metric-detail-description,
.report-summary,
.baseline-summary-status {
  margin: 0;
  color: var(--tp-muted);
}

.detail-columns {
  display: grid;
  grid-template-columns: 0.95fr 1.05fr;
  gap: 1rem;
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

.posture-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.85rem;
}

.posture-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 1rem 1.1rem;
  border-radius: 0.8rem;
  background: color-mix(in srgb, var(--tp-accent-soft) 65%, white);
  border: 1px solid var(--tp-line);
}

.baseline-summary-list {
  display: grid;
  gap: 0.85rem;
}

.baseline-summary-item {
  padding: 1rem;
  border-radius: 0.85rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 88%, white);
}

.baseline-summary-item strong {
  display: block;
  margin-bottom: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.baseline-summary-item p {
  margin: 0;
}

.baseline-inline-meta {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: baseline;
  margin: 0.7rem 0 0.45rem;
}

.baseline-inline-meta span {
  font-weight: 700;
}

.delta-good {
  color: #2c7a4b;
}

.delta-bad {
  color: #b44d61;
}

.report-detail-panel {
  min-height: 22rem;
}

.report-body {
  margin: 1rem 0 0;
  min-height: 11rem;
  white-space: pre-wrap;
  color: var(--tp-muted);
  font: 0.93rem/1.55 "IBM Plex Mono", monospace;
}

.detail-error {
  color: #8f2438;
}

@media (max-width: 1040px) {
  .detail-header,
  .detail-columns {
    grid-template-columns: 1fr;
    display: grid;
  }
}
</style>

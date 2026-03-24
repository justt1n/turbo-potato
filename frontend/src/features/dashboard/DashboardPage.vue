<template>
  <section class="page dashboard-page">
    <p v-if="summaryQuery.isLoading.value || reportsQuery.isLoading.value" class="panel state-panel">Đang tải dữ liệu tổng quan...</p>
    <p v-else-if="summaryQuery.isError.value || reportsQuery.isError.value" class="panel state-panel state-error">
      {{ ((summaryQuery.error.value ?? reportsQuery.error.value) as Error).message }}
    </p>

    <template v-else-if="summary">
      <header class="dashboard-hero panel" :class="heroClass(summary.operatingPosture.status)">
        <div class="hero-topline">
          <div>
            <p class="eyebrow">Bảng điều khiển tài chính</p>
            <h2>Bức tranh tài chính hôm nay</h2>
            <div class="hero-glossary">
              <TermHintModal
                term="STS"
                summary="STS là mức chi linh hoạt an toàn mỗi ngày sau khi trừ chi phí cố định và phần cần dành cho mục tiêu."
                detail="Nó được suy ra từ thu nhập nền gần đây, cam kết cố định trong tháng và nhu cầu nạp mục tiêu còn lại, thay vì dùng một ngân sách cứng."
                :bullets="[
                  'Màu xanh: còn đủ room để chi tiêu linh hoạt.',
                  'Màu vàng hoặc đỏ: nên siết khoản linh hoạt hoặc dời cam kết không cấp thiết.',
                ]"
              />
              <TermHintModal
                term="TAR"
                summary="TAR ở đây được dùng như tỷ lệ tiết kiệm ròng của tháng."
                detail="Công thức lấy thu nhập trừ toàn bộ chi tiêu thực tế rồi chia cho thu nhập, không cộng đúp các khoản chuyển nội bộ."
              />
              <TermHintModal
                term="Đường chuẩn"
                summary="Đường chuẩn là nhịp tham chiếu lấy từ lịch sử tháng gần đây."
                detail="Dashboard dùng chúng để so sánh hiện tại với nền trước đó, giúp đọc xu hướng thay vì nhìn một con số đứng yên."
              />
            </div>
          </div>

          <div class="hero-actions">
            <button class="detail-link secondary-link" type="button" @click="showMethodology = true">
              Xem phương pháp tính
            </button>
            <RouterLink class="detail-link" to="/dashboard/detail">Mở trang chi tiết</RouterLink>
            <RouterLink class="detail-link secondary-link" to="/assets">Xem tài sản</RouterLink>
            <p class="hero-updated">Cập nhật {{ formatTimestamp(reports?.daily.createdAt) }}</p>
          </div>
        </div>

        <div class="status-strip">
          <span class="status-pill" :class="pillClass(summary.sts.status)">
            {{ metricLabel(summary.sts.label) }} {{ statusLabel(summary.sts.status) }}
          </span>
          <span class="status-pill" :class="pillClass(reports?.daily.status)">
            Báo cáo ngày {{ reportStatusLabel(reports?.daily.status) }}
          </span>
          <span class="status-pill soft">
            {{ summary.baselines.length }} đường chuẩn đang theo dõi
          </span>
          <span class="status-pill" :class="posturePillClass(summary.operatingPosture.status)">
            {{ postureStatusLabel(summary.operatingPosture.status) }}
          </span>
        </div>

        <div class="hero-layout">
          <div class="hero-highlights">
            <article v-for="card in spotlightCards" :key="card.label" class="spotlight-card">
              <p class="spotlight-label">{{ card.label }}</p>
              <strong>{{ card.value }}</strong>
              <p>{{ card.description }}</p>
            </article>
          </div>

          <aside class="hero-focus">
            <div class="hero-focus-head">
              <div>
                <p class="eyebrow">Ưu tiên hôm nay</p>
                <h3>Những gì nên nhìn trước</h3>
              </div>
              <span class="focus-count">{{ focusItems.length }} điểm</span>
            </div>

            <ul class="focus-list">
              <li v-for="item in focusItems" :key="item.title">
                <strong>{{ item.title }}</strong>
                <p>{{ item.body }}</p>
              </li>
            </ul>
          </aside>
        </div>
      </header>

      <section class="section-block">
        <div class="section-head">
          <div>
            <p class="eyebrow">Tín hiệu cốt lõi</p>
            <h3>Đọc nhanh sức khỏe tài chính bằng xu hướng</h3>
          </div>
          <p class="section-copy">
            Ưu tiên line chart và combo chart để đọc hướng đi, nhịp thay đổi và tương quan giữa các trụ tài chính
            thay vì nhìn tỷ trọng tĩnh.
          </p>
        </div>

        <div class="trend-grid">
          <SignalLinePanel
            title="Đường tín hiệu 4 trụ"
            subtitle="STS, bất thường, TAR và tốc độ mục tiêu trên cùng một mặt phẳng"
            :items="signalChartItems"
          />
          <BaselineComboPanel
            title="Đường chuẩn hiện tại so với kỳ trước"
            subtitle="Cột là hiện tại, đường là điểm liền trước để đọc độ tăng giảm"
            :series-list="baselineSeries"
          />
        </div>

      </section>

      <div class="dashboard-columns">
        <BaselineMonitor
          title="Bảng theo dõi đường chuẩn"
          subtitle="So sánh nhịp tài chính hiện tại với quãng gần đây"
          :series-list="baselineSeries"
        />

        <div class="insight-stack">
          <article class="panel summary-panel">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Thế vận hành</p>
                <h3>Trạng thái cấu trúc</h3>
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

          <article class="panel snapshot-panel">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Nhịp báo cáo</p>
                <h3>Điểm đọc nhanh</h3>
              </div>
              <span class="panel-kpi">{{ reportStatusLabel(reports?.daily.status) }}</span>
            </div>

            <p class="snapshot-summary">{{ reports?.daily.summary }}</p>

            <ul class="summary-list compact">
              <li v-for="item in reportSnapshotItems" :key="item.label">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </li>
            </ul>
          </article>
        </div>
      </div>

      <section class="section-block">
        <div class="section-head">
          <div>
            <p class="eyebrow">Phân tích sâu</p>
            <h3>Báo cáo điều hướng quyết định</h3>
          </div>
          <p class="section-copy">
            Báo cáo ngày phục vụ phản xạ ngắn hạn, còn báo cáo tháng dành cho việc điều chỉnh cấu trúc và kế hoạch.
          </p>
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
            <p class="report-meta">{{ reports?.daily.verdict }} · {{ formatTimestamp(reports?.daily.createdAt) }}</p>
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
      </section>
    </template>

    <Teleport to="body">
      <div v-if="showMethodology" class="methodology-overlay" @click.self="showMethodology = false">
        <div class="methodology-dialog" role="dialog" aria-label="Phương pháp tính dashboard" aria-modal="true">
          <div class="methodology-head">
            <div>
              <p class="methodology-kicker">Phương pháp tính</p>
              <h3>Giải thích ngắn gọn cách đọc metric</h3>
            </div>
            <button class="methodology-close" type="button" @click="showMethodology = false">Đóng</button>
          </div>

          <div class="methodology-grid">
            <article class="methodology-item">
              <strong>STS</strong>
              <p>Thu nhập nền 3 tháng gần đây trừ chi phí cố định tháng này và phần cần dành cho mục tiêu, rồi chia cho số ngày còn lại.</p>
            </article>
            <article class="methodology-item">
              <strong>Lệch nhịp chi tiêu</strong>
              <p>Dùng robust z-score trên tổng chi theo ngày của 60 ngày gần đây để giảm nhiễu từ các khoản chi bất thường lẻ tẻ.</p>
            </article>
            <article class="methodology-item">
              <strong>Tỷ lệ tiết kiệm ròng</strong>
              <p>Lấy thu nhập tháng trừ toàn bộ chi tiêu thực tế rồi chia cho thu nhập; không cộng đúp các khoản chuyển nội bộ.</p>
            </article>
            <article class="methodology-item">
              <strong>Mức bám tiến độ mục tiêu</strong>
              <p>So vận tốc nạp mục tiêu 90 ngày gần đây với vận tốc cần có để kịp deadline của mục tiêu đang active.</p>
            </article>
            <article class="methodology-item">
              <strong>Runway</strong>
              <p>Dựa trên tài sản thanh khoản thực tế trong nguồn tiền, có haircut cho vàng, chia cho burn rate tháng hiện tại.</p>
            </article>
            <article class="methodology-item">
              <strong>Đường chuẩn</strong>
              <p>Dùng nhịp tháng gần đây làm baseline để đọc xu hướng hiện tại so với nền trước đó, thay vì nhìn tỷ trọng tĩnh.</p>
            </article>
          </div>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { RouterLink } from "vue-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { generateMonthlyReport, getDashboardReports, getDashboardSummary } from "@/api/dashboard";
import BaselineComboPanel from "@/components/BaselineComboPanel.vue";
import BaselineMonitor from "@/components/BaselineMonitor.vue";
import SignalLinePanel from "@/components/SignalLinePanel.vue";
import TermHintModal from "@/components/TermHintModal.vue";

const queryClient = useQueryClient();
const showMethodology = ref(false);

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

const metricCards = computed(() => {
  if (!summary.value) {
    return [];
  }

  return [
    {
      id: "sts",
      ...summary.value.sts,
      displayLabel: metricLabel(summary.value.sts.label),
      caption: metricCaption(summary.value.sts.label, summary.value.sts.caption),
    },
    {
      id: "anomaly",
      ...summary.value.anomaly,
      displayLabel: metricLabel(summary.value.anomaly.label),
      caption: metricCaption(summary.value.anomaly.label, summary.value.anomaly.caption),
    },
    {
      id: "tar",
      ...summary.value.tar,
      displayLabel: metricLabel(summary.value.tar.label),
      caption: metricCaption(summary.value.tar.label, summary.value.tar.caption),
    },
    {
      id: "goal-pace",
      ...summary.value.goalPace,
      displayLabel: metricLabel(summary.value.goalPace.label),
      caption: metricCaption(summary.value.goalPace.label, summary.value.goalPace.caption),
    },
  ];
});

const signalChartItems = computed(() =>
  metricCards.value.map((metric) => ({
    label: metric.displayLabel,
    value: metric.value,
    caption: metric.caption,
    progress: metric.progress,
    status: metric.status,
  })),
);

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

const spotlightCards = computed(() => {
  if (!summary.value) {
    return [];
  }

  return [
    {
      label: "Thế vận hành",
      value: postureStatusLabel(summary.value.operatingPosture.status),
      description: operatingPostureDescription(summary.value.operatingPosture.status),
    },
    {
      label: "Dự phòng",
      value: postureItemValue("Runway"),
      description: "Khả năng hấp thụ áp lực chi tiêu ngắn hạn trước khi cần điều chỉnh.",
    },
    {
      label: "ETA mục tiêu",
      value: postureItemValue("ETA"),
      description: "Mốc cán đích hiện tại để bạn biết kế hoạch đang nhanh hay chậm hơn kỳ vọng.",
    },
    {
      label: "Báo cáo ngày",
      value: reportStatusLabel(reports.value?.daily.status),
      description: reports.value?.daily.createdAt
        ? `Cập nhật ${formatTimestamp(reports.value.daily.createdAt)}`
        : "Chưa có bản đọc nhanh mới nhất.",
    },
  ];
});

const focusItems = computed(() => {
  if (!summary.value) {
    return [];
  }

  const prioritizedMetrics = metricCards.value
    .filter((metric) => metric.status !== "healthy")
    .sort((left, right) => severityRank(right.status) - severityRank(left.status))
    .map((metric) => ({
      title: `${metric.displayLabel}: ${statusLabel(metric.status)}`,
      body: focusMessage(metric.label, metric.value, metric.status),
    }));

  if (prioritizedMetrics.length > 0) {
    return prioritizedMetrics.slice(0, 3);
  }

  return [
    {
      title: "Nhịp tổng thể đang ổn",
      body: "Các tín hiệu chính chưa phát ra cảnh báo lớn, nên bạn có thể ưu tiên giữ nhịp thay vì xử lý sự cố.",
    },
    {
      title: `Đường chuẩn đang theo dõi ${summary.value.baselines.length} luồng`,
      body: "Dùng cụm đường chuẩn để xác nhận liệu thay đổi hôm nay là nhất thời hay đã trở thành xu hướng.",
    },
    {
      title: "Báo cáo ngày là lớp đọc đầu tiên",
      body: reports.value?.daily.summary ?? "Khi báo cáo ngày xuất hiện, hãy dùng nó để xác nhận hành động ngắn hạn.",
    },
  ];
});

const reportSnapshotItems = computed(() => [
  {
    label: "Đánh giá ngày",
    value: reports.value?.daily.verdict ?? "Đang chờ",
  },
  {
    label: "Đánh giá tháng",
    value: reports.value?.monthly?.verdict ?? "Tạo khi cần",
  },
  {
    label: "Lần cập nhật",
    value: formatTimestamp(reports.value?.daily.createdAt),
  },
]);

function severityRank(status?: string): number {
  switch (status) {
    case "critical":
      return 2;
    case "warning":
      return 1;
    default:
      return 0;
  }
}

function posturePillClass(status?: string): string {
  switch (status) {
    case "High alert":
      return "warn";
    case "Moderate risk":
      return "soft";
    default:
      return "ok";
  }
}

function heroClass(status?: string): string {
  switch (status) {
    case "High alert":
      return "hero-alert";
    case "Moderate risk":
      return "hero-watch";
    default:
      return "hero-stable";
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

function postureItemValue(label: string): string {
  return summary.value?.operatingPosture.items.find((item) => item.label === label)?.value ?? "Chưa có";
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

function metricCaption(label: string, fallback: string): string {
  switch (label) {
    case "STS":
      return "Số tiền còn có thể chi linh hoạt mỗi ngày sau khi trừ cam kết cố định và mục tiêu.";
    case "Anomaly":
      return "Mức lệch của chi tiêu hôm nay so với nhịp ngày thường trong 60 ngày gần đây.";
    case "TAR":
      return "Phần thu nhập tháng còn giữ lại sau chi tiêu thực tế, không cộng đúp các khoản chuyển nội bộ.";
    case "Goal Pace":
      return "So sánh tốc độ nạp mục tiêu hiện tại với tốc độ cần có để kịp đích.";
    default:
      return fallback;
  }
}

function focusMessage(label: string, value: string, status: string): string {
  switch (label) {
    case "STS":
      return status === "critical"
        ? `Mức chi linh hoạt an toàn chỉ còn khoảng ${value} mỗi ngày, nên vài khoản tùy hứng cũng có thể làm lệch kế hoạch tháng.`
        : `Mức chi linh hoạt còn khoảng ${value} mỗi ngày, đủ để vận hành nhưng vẫn nên quan sát nhịp chi từng ngày.`;
    case "Anomaly":
      return `Điểm ${value} cho thấy hôm nay đang lệch bao xa khỏi nhịp chi tiêu thường ngày, nên cần đọc cùng báo cáo ngày để xem đây là nhiễu hay thay đổi thật.`;
    case "TAR":
      return `Tỷ lệ tiết kiệm ròng đang ở ${value}, phản ánh bao nhiêu phần thu nhập tháng thực sự còn ở lại sau chi tiêu.`;
    case "Goal Pace":
      return `Tốc độ bám mục tiêu hiện ở ${value}, giúp biết bạn đang theo kịp hay chậm hơn nhịp cần có để cán đích.`;
    default:
      return `${label} hiện ở ${value} và đang cần được theo dõi thêm.`;
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

function operatingPostureDescription(status?: string): string {
  switch (status) {
    case "Stable":
      return "Cấu trúc hiện tại đủ cân bằng để tập trung vào duy trì nhịp và tối ưu hóa.";
    case "Moderate risk":
      return "Một vài thành phần đang lệch khỏi vùng ổn định, nên cần quan sát chặt hơn trong ngắn hạn.";
    case "High alert":
      return "Cấu trúc đang chịu áp lực rõ rệt và cần ưu tiên hành động trước các quyết định mở rộng.";
    default:
      return "Đang chờ đủ dữ liệu để đánh giá trạng thái vận hành.";
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
.dashboard-page {
  gap: 1.35rem;
}

.dashboard-hero {
  position: relative;
  overflow: hidden;
  display: grid;
  gap: 1.4rem;
  padding: 1.6rem;
}

.dashboard-hero::before {
  content: "";
  position: absolute;
  inset: -20% auto auto 58%;
  width: 18rem;
  height: 18rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tp-accent) 18%, transparent);
  filter: blur(14px);
  pointer-events: none;
}

.dashboard-hero::after {
  content: "";
  position: absolute;
  inset: auto auto -5rem -4rem;
  width: 14rem;
  height: 14rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tp-danger-soft) 34%, transparent);
  filter: blur(14px);
  pointer-events: none;
}

.hero-stable {
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--tp-accent) 18%, transparent), transparent 38%),
    linear-gradient(180deg, color-mix(in srgb, var(--tp-surface) 90%, white), color-mix(in srgb, var(--tp-surface-alt) 92%, white));
}

.hero-watch {
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--tp-danger-soft) 20%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--tp-surface) 90%, white), color-mix(in srgb, var(--tp-surface-alt) 88%, white));
}

.hero-alert {
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--tp-danger) 14%, transparent), transparent 42%),
    linear-gradient(180deg, color-mix(in srgb, var(--tp-surface) 90%, white), color-mix(in srgb, var(--tp-surface-alt) 86%, white));
}

.hero-topline,
.section-head,
.panel-head {
  position: relative;
  z-index: 1;
}

.hero-topline {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-start;
}

.hero-glossary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.85rem;
}

.dashboard-hero h2 {
  margin: 0.4rem 0 0.55rem;
  font-size: clamp(2.4rem, 4vw, 4.2rem);
  line-height: 0.9;
  letter-spacing: -0.06em;
}

.lede {
  max-width: 56rem;
  margin: 0;
  color: var(--tp-muted);
  font-size: 1rem;
}

.hero-actions {
  display: grid;
  justify-items: end;
  gap: 0.75rem;
  min-width: 13rem;
}

.secondary-link {
  background: color-mix(in srgb, var(--tp-accent-tint) 82%, white);
  color: var(--tp-text);
  box-shadow: none;
}

.detail-link,
.action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2.9rem;
  padding: 0.8rem 1.1rem;
  border-radius: 0.72rem;
  background: linear-gradient(135deg, var(--tp-accent-strong), var(--tp-accent));
  color: #f6f4ee;
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  box-shadow: 0 14px 26px color-mix(in srgb, var(--tp-accent-strong) 26%, transparent);
}

.detail-link {
  border: 0;
  cursor: pointer;
  font: inherit;
}

.hero-updated {
  margin: 0;
  font-size: 0.86rem;
  color: var(--tp-muted);
}

.status-strip {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.72rem 0.96rem;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: 1px solid var(--tp-line);
}

.ok {
  background: color-mix(in srgb, var(--tp-accent) 86%, white);
  color: var(--tp-text);
}

.soft {
  background: color-mix(in srgb, var(--tp-accent-soft) 88%, white);
  color: var(--tp-text);
}

.warn {
  background: color-mix(in srgb, var(--tp-danger-soft) 92%, white);
  color: color-mix(in srgb, var(--tp-danger) 82%, var(--tp-text) 18%);
}

.hero-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(18rem, 0.9fr);
  gap: 1rem;
}

.hero-highlights {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
}

.spotlight-card,
.hero-focus {
  border-radius: 1rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 84%, white);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.spotlight-card {
  padding: 1rem 1.05rem;
}

.spotlight-label {
  margin: 0;
  font-size: 0.76rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--tp-muted);
}

.spotlight-card strong {
  display: block;
  margin: 0.4rem 0 0.35rem;
  font-size: 1.55rem;
  letter-spacing: -0.04em;
}

.spotlight-card p:last-child {
  margin: 0;
  color: var(--tp-muted);
}

.hero-focus {
  padding: 1.05rem 1.1rem;
}

.hero-focus-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.8rem;
}

.hero-focus-head h3,
.section-head h3,
.panel-head h3 {
  margin: 0.28rem 0 0;
  font-size: 1.35rem;
  letter-spacing: -0.03em;
}

.focus-count,
.panel-kpi {
  color: var(--tp-muted);
  font-weight: 700;
  font-size: 0.88rem;
}

.focus-list,
.summary-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.focus-list {
  display: grid;
  gap: 0.8rem;
}

.focus-list li {
  padding: 0.85rem 0.95rem;
  border-radius: 0.9rem;
  background: color-mix(in srgb, var(--tp-surface-alt) 74%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 82%, transparent);
}

.focus-list strong {
  display: block;
  margin-bottom: 0.24rem;
  font-size: 0.95rem;
}

.focus-list p,
.section-copy,
.snapshot-summary,
.report-meta,
.summary-list span {
  margin: 0;
  color: var(--tp-muted);
}

.section-block {
  display: grid;
  gap: 1rem;
}

.section-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
}

.section-copy {
  max-width: 34rem;
  text-align: right;
}

.trend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.methodology-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.9rem;
}

.methodology-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: grid;
  place-items: center;
  padding: 1.5rem;
  background: rgba(20, 33, 38, 0.44);
  backdrop-filter: blur(10px);
}

.methodology-dialog {
  width: min(920px, 100%);
  max-height: min(80vh, 920px);
  overflow: auto;
  padding: 1.35rem;
  border-radius: 1rem;
  border: 1px solid var(--tp-line);
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--tp-accent-soft) 50%, transparent), transparent 38%),
    linear-gradient(180deg, color-mix(in srgb, var(--tp-surface) 94%, white), color-mix(in srgb, var(--tp-surface-alt) 90%, white));
  box-shadow: 0 28px 64px rgba(20, 33, 38, 0.22);
  display: grid;
  gap: 1rem;
}

.methodology-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.methodology-kicker {
  margin: 0 0 0.25rem;
  color: var(--tp-muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.methodology-head h3 {
  margin: 0;
}

.methodology-close {
  border: 1px solid var(--tp-line);
  background: transparent;
  color: var(--tp-text);
  border-radius: 0.72rem;
  padding: 0.7rem 0.85rem;
  cursor: pointer;
  font: inherit;
}

.methodology-item {
  padding: 0.95rem 1rem;
  border-radius: 0.78rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 90%, white);
}

.methodology-item strong {
  display: block;
  margin-bottom: 0.35rem;
}

.methodology-item p {
  margin: 0;
  color: var(--tp-muted);
}

.dashboard-columns {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(18rem, 0.95fr);
  gap: 1rem;
}

.insight-stack {
  display: grid;
  gap: 1rem;
}

.chat-panel,
.summary-panel,
.snapshot-panel,
.report-panel {
  min-height: 100%;
}

.chat-form {
  display: grid;
  gap: 0.9rem;
}

.chat-form label {
  display: grid;
  gap: 0.35rem;
}

.chat-form span {
  color: var(--tp-muted);
  font-size: 0.85rem;
}

.chat-form input,
.chat-form textarea {
  width: 100%;
  padding: 0.8rem 0.9rem;
  border-radius: 0.9rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 92%, white);
  color: var(--tp-text);
  font: inherit;
}

.chat-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.8rem;
}

.chat-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.chat-hints span {
  display: inline-flex;
  padding: 0.5rem 0.7rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tp-accent-soft) 74%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 72%, transparent);
  font-size: 0.8rem;
}

.chat-result {
  display: grid;
  gap: 0.3rem;
  padding: 0.9rem 1rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--tp-surface-alt) 78%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 82%, transparent);
}

.chat-result strong,
.chat-result p {
  margin: 0;
}

.inline-link {
  width: fit-content;
  color: var(--tp-text);
  font-weight: 700;
}

.helper-text,
.success-text,
.error-text {
  margin: 0;
}

.success-text {
  color: #1f7a63;
}

.error-text {
  color: #b85f4a;
}

.summary-list {
  display: grid;
  gap: 0.8rem;
}

.summary-list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  padding: 1rem 1.05rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--tp-surface-alt) 72%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 88%, transparent);
}

.summary-list strong {
  font-size: 1.02rem;
  color: var(--tp-text);
  text-align: right;
}

.summary-list.compact li {
  padding-block: 0.9rem;
}

.snapshot-summary {
  margin-bottom: 0.95rem;
  font-size: 0.98rem;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
}

.report-panel {
  display: grid;
  align-content: start;
}

.report-summary {
  margin: 0 0 1rem;
  font-size: 1rem;
  color: var(--tp-text);
}

.report-body {
  margin: 0;
  min-height: 12rem;
  white-space: pre-wrap;
  color: var(--tp-muted);
  font: 0.93rem/1.6 "IBM Plex Mono", monospace;
}

.report-meta {
  margin-top: 1rem;
}

.state-panel {
  margin: 0;
}

.state-error {
  color: color-mix(in srgb, var(--tp-danger) 86%, #7c2f28);
}

.action-button {
  border: 0;
  cursor: pointer;
  font: inherit;
}

.action-button:disabled {
  opacity: 0.6;
  cursor: wait;
}

@media (max-width: 1080px) {
  .hero-topline,
  .section-head,
  .dashboard-columns,
  .hero-layout {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .hero-actions {
    justify-items: start;
  }

  .section-copy {
    text-align: left;
  }

  .hero-highlights {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 720px) {
  .dashboard-hero {
    padding: 1.3rem;
  }

  .hero-highlights,
  .trend-grid,
  .report-grid {
    grid-template-columns: 1fr;
  }

  .chat-meta-grid {
    grid-template-columns: 1fr;
  }

  .summary-list li,
  .hero-focus-head,
  .panel-head,
  .hero-topline,
  .section-head,
  .methodology-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .summary-list li {
    flex-direction: column;
  }
}
</style>

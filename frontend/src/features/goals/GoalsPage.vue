<template>
  <section class="page goals-page">
    <header class="panel goals-hero">
      <div>
        <p class="eyebrow">Kế hoạch</p>
        <h2>Quản lý mục tiêu và điều chỉnh nhịp tích lũy</h2>
        <p class="hero-copy">
          Trang này gom cả phần nhập kế hoạch lẫn phần điều chỉnh mục tiêu đang chạy, để bạn không phải nhảy
          qua nhiều nơi chỉ để cập nhật tiến độ.
        </p>
      </div>

      <div class="goal-stats">
        <article class="stat-card">
          <span>Mục tiêu đang chạy</span>
          <strong>{{ activeGoalsCount }}</strong>
        </article>
        <article class="stat-card">
          <span>Tổng đích đến</span>
          <strong>{{ formatCurrency(totalTargetAmount) }}</strong>
        </article>
        <article class="stat-card">
          <span>Đã chuyển vào mục tiêu</span>
          <strong>{{ formatCurrency(totalTransferredAmount) }}</strong>
        </article>
        <article class="stat-card">
          <span>Sắp tới hạn</span>
          <strong>{{ goalsDueSoon }}</strong>
        </article>
      </div>
    </header>

    <div class="goals-layout">
      <article class="panel planner-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Nhập kế hoạch</p>
            <h3>Tạo mục tiêu mới</h3>
          </div>
          <span class="panel-kpi">Được dùng ngay trên dashboard</span>
        </div>

        <form class="planner-form" @submit.prevent="submitCreate">
          <label>
            <span>Tên mục tiêu</span>
            <input v-model.trim="createForm.name" placeholder="Quỹ khẩn cấp" required />
          </label>

          <label>
            <span>Mục tiêu tiền</span>
            <input v-model.number="createForm.targetAmount" min="1" required type="number" />
          </label>

          <label>
            <span>Ngày bắt đầu</span>
            <input v-model="createForm.startDate" type="date" />
          </label>

          <label>
            <span>Ngày đích</span>
            <input v-model="createForm.targetDate" type="date" />
          </label>

          <label>
            <span>Trạng thái</span>
            <select v-model="createForm.status">
              <option value="active">Đang chạy</option>
              <option value="paused">Tạm dừng</option>
              <option value="completed">Hoàn thành</option>
            </select>
          </label>

          <button :disabled="createMutation.isPending.value" type="submit">
            {{ createMutation.isPending.value ? "Đang lưu..." : "Tạo mục tiêu" }}
          </button>
        </form>

        <p v-if="createMessage" :class="createMessageTone">{{ createMessage }}</p>
      </article>

      <section class="goal-list-section">
        <p v-if="goalsQuery.isLoading.value || transactionsQuery.isLoading.value" class="panel">Đang tải kế hoạch...</p>
        <p v-else-if="goalsQuery.isError.value || transactionsQuery.isError.value" class="panel error-text">
          {{ ((goalsQuery.error.value ?? transactionsQuery.error.value) as Error).message }}
        </p>
        <article v-else-if="goalCards.length === 0" class="panel empty-panel">
          <h3>Chưa có kế hoạch nào</h3>
          <p>Hãy tạo mục tiêu đầu tiên để hệ thống bắt đầu tính tiến độ, ETA và tín hiệu goal pace.</p>
        </article>

        <div v-else class="goal-list">
          <article v-for="goal in goalCards" :key="goal.name" class="panel goal-card">
            <div class="goal-card-head">
              <div>
                <p class="eyebrow">{{ statusLabel(goal.status) }}</p>
                <h3>{{ goal.name }}</h3>
              </div>
              <button class="secondary-button" type="button" @click="toggleEdit(goal)">
                {{ editingGoalName === goal.name ? "Đóng chỉnh sửa" : "Điều chỉnh" }}
              </button>
            </div>

            <div class="goal-kpis">
              <div>
                <span>Đã đạt</span>
                <strong>{{ formatCurrency(goal.transferredAmount) }}</strong>
              </div>
              <div>
                <span>Còn lại</span>
                <strong>{{ formatCurrency(goal.remainingAmount) }}</strong>
              </div>
              <div>
                <span>Ngày đích</span>
                <strong>{{ goal.targetDateLabel }}</strong>
              </div>
            </div>

            <div class="progress-block">
              <div class="progress-copy">
                <span>Tiến độ</span>
                <strong>{{ goal.progress }}%</strong>
              </div>
              <div class="progress-track" aria-hidden="true">
                <span class="progress-fill" :style="{ width: `${goal.progress}%` }"></span>
              </div>
              <p class="progress-note">{{ goal.summary }}</p>
            </div>

            <dl class="goal-meta">
              <div>
                <dt>Bắt đầu</dt>
                <dd>{{ goal.startDateLabel }}</dd>
              </div>
              <div>
                <dt>Đích đến</dt>
                <dd>{{ formatCurrency(goal.targetAmount) }}</dd>
              </div>
              <div>
                <dt>Nhịp tháng gần đây</dt>
                <dd>{{ formatCurrency(goal.monthlyVelocity) }}</dd>
              </div>
            </dl>

            <form
              v-if="editingGoalName === goal.name && editForm"
              class="planner-form edit-form"
              @submit.prevent="submitUpdate(goal.name)"
            >
              <label>
                <span>Tên mục tiêu</span>
                <input :value="goal.name" disabled />
              </label>

              <label>
                <span>Mục tiêu tiền</span>
                <input v-model.number="editForm.targetAmount" min="1" required type="number" />
              </label>

              <label>
                <span>Ngày bắt đầu</span>
                <input v-model="editForm.startDate" type="date" />
              </label>

              <label>
                <span>Ngày đích</span>
                <input v-model="editForm.targetDate" type="date" />
              </label>

              <label>
                <span>Trạng thái</span>
                <select v-model="editForm.status">
                  <option value="active">Đang chạy</option>
                  <option value="paused">Tạm dừng</option>
                  <option value="completed">Hoàn thành</option>
                </select>
              </label>

              <div class="edit-actions">
                <button :disabled="updateMutation.isPending.value" type="submit">
                  {{ updateMutation.isPending.value ? "Đang cập nhật..." : "Lưu điều chỉnh" }}
                </button>
                <button class="ghost-button" type="button" @click="clearEdit">Hủy</button>
              </div>
            </form>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { createGoal, listGoals, updateGoal, type Goal, type GoalStatus } from "@/api/goals";
import { listTransactions } from "@/api/transactions";
import { formatCurrency } from "@/lib/formatCurrency";

type GoalForm = {
  name: string;
  targetAmount: number;
  startDate: string;
  targetDate: string;
  status: GoalStatus;
};

type GoalEditForm = {
  targetAmount: number;
  startDate: string;
  targetDate: string;
  status: GoalStatus;
};

const queryClient = useQueryClient();

const goalsQuery = useQuery({
  queryKey: ["goals"],
  queryFn: listGoals,
});

const transactionsQuery = useQuery({
  queryKey: ["transactions"],
  queryFn: listTransactions,
});

const createForm = reactive(defaultGoalForm());
const createMessage = ref("");
const createMessageTone = ref("helper-text");
const editingGoalName = ref("");
const editForm = ref<GoalEditForm | null>(null);

const goalCards = computed(() => {
  const goals = goalsQuery.data.value?.items ?? [];
  const transactions = transactionsQuery.data.value?.items ?? [];

  return goals.map((goal) => {
    const relatedTransfers = transactions.filter(
      (item) =>
        item.type === "TRANSFER" &&
        item.goalName === goal.name &&
        item.status !== "reverted",
    );

    const transferredAmount = relatedTransfers.reduce((total, item) => total + item.amount, 0);
    const lastThirtyDays = Date.now() - 30 * 24 * 60 * 60 * 1000;
    const monthlyVelocity = relatedTransfers
      .filter((item) => new Date(item.occurredAt).getTime() >= lastThirtyDays)
      .reduce((total, item) => total + item.amount, 0);
    const remainingAmount = Math.max(0, goal.targetAmount - transferredAmount);
    const progress = goal.targetAmount > 0 ? Math.min(100, Math.round((transferredAmount / goal.targetAmount) * 100)) : 0;

    return {
      ...goal,
      transferredAmount,
      monthlyVelocity,
      remainingAmount,
      progress,
      startDateLabel: formatDate(goal.startDate),
      targetDateLabel: goal.targetDate ? formatDate(goal.targetDate) : "Chưa đặt",
      summary: goalSummary(goal, transferredAmount, remainingAmount, monthlyVelocity, progress),
    };
  });
});

const activeGoalsCount = computed(() => goalCards.value.filter((goal) => goal.status === "active").length);
const totalTargetAmount = computed(() => goalCards.value.reduce((total, goal) => total + goal.targetAmount, 0));
const totalTransferredAmount = computed(() => goalCards.value.reduce((total, goal) => total + goal.transferredAmount, 0));
const goalsDueSoon = computed(
  () =>
    goalCards.value.filter((goal) => {
      if (!goal.targetDate) {
        return false;
      }

      const diff = new Date(goal.targetDate).getTime() - Date.now();
      return diff >= 0 && diff <= 30 * 24 * 60 * 60 * 1000;
    }).length,
);

const createMutation = useMutation({
  mutationFn: createGoal,
  onSuccess: async () => {
    Object.assign(createForm, defaultGoalForm());
    createMessage.value = "Đã tạo mục tiêu mới.";
    createMessageTone.value = "success-text";
    await refreshGoalViews();
  },
  onError: (error) => {
    createMessage.value = error instanceof Error ? error.message : "Không thể tạo mục tiêu";
    createMessageTone.value = "error-text";
  },
});

const updateMutation = useMutation({
  mutationFn: ({ name, input }: { name: string; input: GoalEditForm }) =>
    updateGoal(name, {
      targetAmount: input.targetAmount,
      startDate: dateInputToIso(input.startDate),
      targetDate: dateInputToIso(input.targetDate),
      status: input.status,
    }),
  onSuccess: async () => {
    clearEdit();
    await refreshGoalViews();
  },
});

function defaultGoalForm(): GoalForm {
  return {
    name: "",
    targetAmount: 0,
    startDate: todayInputValue(),
    targetDate: "",
    status: "active",
  };
}

function todayInputValue(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatDate(value?: string): string {
  if (!value) {
    return "Chưa đặt";
  }

  return new Date(value).toLocaleDateString("vi-VN");
}

function dateInputToIso(value: string): string | undefined {
  if (!value) {
    return undefined;
  }

  return `${value}T00:00:00`;
}

function dateTimeToInput(value?: string): string {
  if (!value) {
    return "";
  }

  return value.slice(0, 10);
}

function statusLabel(status: GoalStatus): string {
  switch (status) {
    case "active":
      return "Đang chạy";
    case "paused":
      return "Tạm dừng";
    case "completed":
      return "Hoàn thành";
  }
}

function goalSummary(
  goal: Goal,
  transferredAmount: number,
  remainingAmount: number,
  monthlyVelocity: number,
  progress: number,
): string {
  if (goal.status === "completed") {
    return "Mục tiêu đã được đánh dấu hoàn thành. Bạn có thể giữ lại để theo dõi lịch sử.";
  }

  if (goal.status === "paused") {
    return `Kế hoạch đang tạm dừng ở mức ${progress}%. Khi sẵn sàng, bạn có thể mở lại và chỉnh mốc đích.`;
  }

  if (remainingAmount === 0) {
    return "Bạn đã chạm đích số tiền hiện tại. Nếu muốn, hãy tăng đích hoặc đánh dấu hoàn thành.";
  }

  if (monthlyVelocity > 0) {
    const monthsLeft = Math.max(1, Math.ceil(remainingAmount / monthlyVelocity));
    return `Với nhịp gần đây, còn khoảng ${monthsLeft} tháng để chạm mục tiêu nếu bạn giữ đúng tốc độ hiện tại.`;
  }

  if (transferredAmount > 0) {
    return "Đã có tích lũy nhưng nhịp gần đây chưa rõ ràng. Nên bổ sung chuyển tiền định kỳ để ETA ổn định hơn.";
  }

  return "Mục tiêu đã được tạo nhưng chưa có giao dịch chuyển tiền liên quan. Hãy bắt đầu bằng một khoản chuyển đầu tiên.";
}

function toggleEdit(goal: Goal) {
  if (editingGoalName.value === goal.name) {
    clearEdit();
    return;
  }

  editingGoalName.value = goal.name;
  editForm.value = {
    targetAmount: goal.targetAmount,
    startDate: dateTimeToInput(goal.startDate),
    targetDate: dateTimeToInput(goal.targetDate),
    status: goal.status,
  };
}

function clearEdit() {
  editingGoalName.value = "";
  editForm.value = null;
}

async function refreshGoalViews() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["goals"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-reports"] }),
  ]);
}

function submitCreate() {
  createMessage.value = "";
  createMutation.mutate({
    name: createForm.name,
    targetAmount: createForm.targetAmount,
    startDate: dateInputToIso(createForm.startDate),
    targetDate: dateInputToIso(createForm.targetDate),
    status: createForm.status,
  });
}

function submitUpdate(goalName: string) {
  if (!editForm.value) {
    return;
  }

  updateMutation.mutate({
    name: goalName,
    input: { ...editForm.value },
  });
}
</script>

<style scoped>
.goals-page {
  gap: 1.25rem;
}

.goals-hero {
  display: grid;
  gap: 1.2rem;
}

.goals-hero h2 {
  margin: 0.3rem 0 0.5rem;
  font-size: clamp(2rem, 3.6vw, 3.2rem);
  line-height: 1;
  letter-spacing: -0.05em;
}

.hero-copy {
  max-width: 54rem;
  margin: 0;
  color: var(--tp-muted);
}

.goal-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 0.9rem;
}

.stat-card {
  padding: 1rem 1.05rem;
  border-radius: 1rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 88%, white);
}

.stat-card span {
  display: block;
  color: var(--tp-muted);
  font-size: 0.84rem;
}

.stat-card strong {
  display: block;
  margin-top: 0.45rem;
  font-size: 1.25rem;
}

.goals-layout {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 1rem;
}

.planner-panel,
.goal-list {
  display: grid;
  gap: 1rem;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.panel-head h3,
.goal-card h3 {
  margin: 0.3rem 0 0;
  font-size: 1.3rem;
  letter-spacing: -0.03em;
}

.panel-kpi {
  color: var(--tp-muted);
  font-size: 0.88rem;
  font-weight: 700;
}

.planner-form {
  display: grid;
  gap: 0.9rem;
}

.planner-form label {
  display: grid;
  gap: 0.35rem;
}

.planner-form span,
.goal-kpis span,
.goal-meta dt {
  color: var(--tp-muted);
  font-size: 0.85rem;
}

.planner-form input,
.planner-form select,
.planner-form button,
.secondary-button,
.ghost-button {
  font: inherit;
}

.planner-form input,
.planner-form select {
  width: 100%;
  padding: 0.78rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 92%, white);
  color: var(--tp-text);
}

.planner-form button,
.secondary-button,
.ghost-button {
  border: 0;
  border-radius: 0.9rem;
  padding: 0.85rem 1rem;
  cursor: pointer;
}

.planner-form button {
  background: var(--tp-text);
  color: #f6f4ee;
}

.secondary-button {
  background: color-mix(in srgb, var(--tp-accent-soft) 78%, white);
  color: var(--tp-text);
}

.ghost-button {
  background: transparent;
  border: 1px solid var(--tp-line);
  color: var(--tp-text);
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

.empty-panel h3 {
  margin: 0 0 0.4rem;
}

.empty-panel p {
  margin: 0;
  color: var(--tp-muted);
}

.goal-list {
  grid-auto-rows: min-content;
}

.goal-card {
  display: grid;
  gap: 1rem;
}

.goal-card-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.goal-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.8rem;
}

.goal-kpis div,
.goal-meta div {
  padding: 0.95rem 1rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--tp-surface-alt) 78%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 84%, transparent);
}

.goal-kpis strong,
.goal-meta dd {
  display: block;
  margin: 0.3rem 0 0;
}

.progress-block {
  display: grid;
  gap: 0.55rem;
}

.progress-copy {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}

.progress-track {
  width: 100%;
  height: 0.9rem;
  overflow: hidden;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tp-surface-alt) 72%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 76%, transparent);
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--tp-accent), color-mix(in srgb, var(--tp-accent-soft) 70%, white));
}

.progress-note {
  margin: 0;
  color: var(--tp-muted);
}

.goal-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.8rem;
  margin: 0;
}

.goal-meta dt,
.goal-meta dd {
  margin: 0;
}

.edit-form {
  padding-top: 0.25rem;
  border-top: 1px solid color-mix(in srgb, var(--tp-line) 82%, transparent);
}

.edit-actions {
  display: flex;
  gap: 0.75rem;
}

@media (max-width: 980px) {
  .goals-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .goal-card-head,
  .panel-head,
  .edit-actions {
    flex-direction: column;
  }
}
</style>

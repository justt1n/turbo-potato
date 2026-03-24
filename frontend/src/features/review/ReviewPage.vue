<template>
  <section class="page review-page">
    <header class="review-page-head">
      <p class="eyebrow">Kiểm duyệt</p>
      <h2>Hàng đợi xác nhận thủ công</h2>
      <p class="review-page-copy">
        Danh sách này chỉ giữ các bản nháp còn cần quyết định. Khi xác nhận hoặc hoàn tác xong, mục đó sẽ tự rời
        khỏi hàng đợi để bạn tiếp tục xử lý mục tiếp theo như một sổ cái tác vụ.
      </p>
    </header>

    <p v-if="query.isLoading.value" class="panel">Đang tải các bản ghi cần duyệt...</p>
    <p v-else-if="query.isError.value" class="panel review-error">
      {{ (query.error.value as Error).message }}
    </p>

    <article v-else-if="pendingItems.length === 0" class="card">
      <p>Chưa có bản ghi nào đang chờ kiểm duyệt.</p>
    </article>

    <div v-else class="review-list">
      <article v-for="item in pendingItems" :key="item.receipt.id" class="panel review-row">
        <div class="review-row-main">
          <div>
            <p class="eyebrow">Phiếu {{ item.receipt.id }}</p>
            <h3>{{ item.transaction?.note || item.receipt.rawInput }}</h3>
            <p class="review-raw">{{ item.receipt.rawInput }}</p>
          </div>

          <div class="review-summary-strip">
            <span>{{ formatCurrency(item.receipt.regexAmount) }}</span>
            <span>{{ item.transaction?.jarCode || "Chưa gắn hũ" }}</span>
            <span>{{ transactionStatusLabel(item.transaction?.status) }}</span>
            <span>{{ confidenceLabel(item.receipt.confidence) }}</span>
          </div>

          <div class="review-actions">
            <button class="secondary-button" :disabled="isActionBusy(item.receipt.id)" type="button" @click="toggleDetail(item.receipt.id)">
              {{ detailId === item.receipt.id ? "Ẩn chi tiết" : "Xem chi tiết" }}
            </button>
            <button :disabled="isActionBusy(item.receipt.id)" type="button" @click="confirm(item.receipt.id)">
              Xác nhận
            </button>
            <button :disabled="isActionBusy(item.receipt.id)" type="button" @click="toggleEditor(item)">
              {{ editingId === item.receipt.id ? "Đóng chỉnh sửa" : "Sửa" }}
            </button>
            <button :disabled="isActionBusy(item.receipt.id)" class="danger-button" type="button" @click="undo(item.receipt.id)">
              Hoàn tác
            </button>
          </div>
        </div>

        <div v-if="detailId === item.receipt.id || editingId === item.receipt.id" class="review-expand">
          <dl class="review-meta">
            <div>
              <dt>Số tiền từ regex</dt>
              <dd>{{ formatCurrency(item.receipt.regexAmount) }}</dd>
            </div>
            <div>
              <dt>Hũ</dt>
              <dd>{{ item.transaction?.jarCode || "Đang chờ" }}</dd>
            </div>
            <div>
              <dt>Trạng thái</dt>
              <dd>{{ transactionStatusLabel(item.transaction?.status) }}</dd>
            </div>
            <div>
              <dt>Prompt</dt>
              <dd>{{ item.receipt.promptSource }}</dd>
            </div>
          </dl>

          <p v-if="item.receipt.validationNote" class="review-note">{{ item.receipt.validationNote }}</p>

          <form
            v-if="editingId === item.receipt.id && editForm"
            class="review-form"
            @submit.prevent="saveCorrection(item.receipt.id)"
          >
            <label>
              <span>Loại</span>
              <select v-model="editForm.type">
                <option value="OUT">Chi tiêu</option>
                <option value="IN">Thu nhập</option>
                <option value="TRANSFER">Chuyển tiền</option>
              </select>
            </label>

            <label>
              <span>Số tiền</span>
              <input v-model.number="editForm.amount" min="1" required type="number" />
            </label>

            <label>
              <span>Mã hũ</span>
              <input v-model.trim="editForm.jarCode" list="jar-options" placeholder="ThietYeu" />
            </label>

            <label>
              <span>Tên mục tiêu</span>
              <input v-model.trim="editForm.goalName" list="goal-options" placeholder="Mua xe SH" />
            </label>

            <label>
              <span>Tài khoản</span>
              <input v-model.trim="editForm.accountName" list="source-options" placeholder="VCB_Main" />
            </label>

            <label class="review-form-wide">
              <span>Ghi chú</span>
              <textarea v-model.trim="editForm.note" rows="3" />
            </label>

            <label class="checkbox">
              <input v-model="editForm.isFixed" type="checkbox" />
              <span>Chi phí cố định</span>
            </label>

            <label class="review-form-wide">
              <span>Lý do</span>
              <input v-model.trim="editForm.reason" placeholder="Điều chỉnh sau khi kiểm duyệt" />
            </label>

            <div class="review-form-actions">
              <button :disabled="isActionBusy(item.receipt.id)" type="submit">Lưu chỉnh sửa</button>
              <button :disabled="isActionBusy(item.receipt.id)" class="ghost-button" type="button" @click="clearEditor()">
                Hủy
              </button>
            </div>
          </form>

          <pre v-else class="review-json">{{ prettyJson(item.receipt.llmOutputJson) }}</pre>
        </div>
      </article>
    </div>

    <datalist id="jar-options">
      <option v-for="jar in jarsQuery.data.value?.items ?? []" :key="jar.code" :value="jar.code">
        {{ jar.name }}
      </option>
    </datalist>

    <datalist id="goal-options">
      <option v-for="goal in goalsQuery.data.value?.items ?? []" :key="goal.name" :value="goal.name" />
    </datalist>

    <datalist id="source-options">
      <option v-for="source in sourcesQuery.data.value?.items ?? []" :key="source.code" :value="source.code">
        {{ source.name }}
      </option>
    </datalist>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { listGoals } from "@/api/goals";
import { listJars } from "@/api/jars";
import { listSources } from "@/api/sources";
import {
  confirmParsedReceipt,
  correctParsedReceipt,
  listParsedReceipts,
  type ParsedReceiptReviewItem,
  undoParsedReceipt,
} from "@/api/review";

const queryClient = useQueryClient();

type ReviewEditForm = {
  occurredAt: string;
  type: "IN" | "OUT" | "TRANSFER";
  amount: number;
  currency: string;
  jarCode: string;
  goalName: string;
  accountName: string;
  isFixed: boolean;
  note: string;
  reason: string;
};

const query = useQuery({
  queryKey: ["parsed-receipts"],
  queryFn: listParsedReceipts,
});

const jarsQuery = useQuery({
  queryKey: ["jars"],
  queryFn: listJars,
});

const goalsQuery = useQuery({
  queryKey: ["goals"],
  queryFn: listGoals,
});

const sourcesQuery = useQuery({
  queryKey: ["sources"],
  queryFn: listSources,
});

const items = computed(() => query.data.value?.items ?? []);
const pendingItems = computed(() =>
  items.value.filter((item) => !item.transaction || item.transaction.status === "draft"),
);
const editingId = ref("");
const detailId = ref("");
const editForm = ref<ReviewEditForm | null>(null);

const confirmMutation = useMutation({
  mutationFn: (receiptId: string) =>
    confirmParsedReceipt(receiptId, {
      actor: "review-ui",
      reason: "confirmed from review queue",
    }),
  onSuccess: async () => {
    await refreshAll();
  },
});

const undoMutation = useMutation({
  mutationFn: (receiptId: string) =>
    undoParsedReceipt(receiptId, {
      actor: "review-ui",
      reason: "reverted from review queue",
    }),
  onSuccess: async () => {
    clearEditor();
    await refreshAll();
  },
});

const correctMutation = useMutation({
  mutationFn: ({ receiptId, input }: { receiptId: string; input: ReviewEditForm }) =>
    correctParsedReceipt(receiptId, {
      ...input,
      status: "confirmed",
      actor: "review-ui",
      reason: input.reason || "corrected from review queue",
    }),
  onSuccess: async () => {
    clearEditor();
    await refreshAll();
  },
});

async function refreshAll() {
  await Promise.all([
    query.refetch(),
    queryClient.invalidateQueries({ queryKey: ["transactions"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-reports"] }),
    queryClient.invalidateQueries({ queryKey: ["assets-overview"] }),
  ]);
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN").format(value) + " VND";
}

function prettyJson(raw: string): string {
  try {
    return JSON.stringify(JSON.parse(raw), null, 2);
  } catch {
    return raw;
  }
}

function isActionBusy(receiptId: string): boolean {
  return (
    confirmMutation.isPending.value ||
    undoMutation.isPending.value ||
    correctMutation.isPending.value
  );
}

function confirm(receiptId: string) {
  confirmMutation.mutate(receiptId);
}

function undo(receiptId: string) {
  undoMutation.mutate(receiptId);
}

function toggleEditor(item: ParsedReceiptReviewItem) {
  if (!item.transaction) {
    return;
  }
  if (editingId.value === item.receipt.id) {
    clearEditor();
    return;
  }
  editingId.value = item.receipt.id;
  detailId.value = item.receipt.id;
  editForm.value = {
    occurredAt: item.transaction.occurredAt,
    type: item.transaction.type,
    amount: item.transaction.amount,
    currency: item.transaction.currency || "VND",
    jarCode: item.transaction.jarCode || "",
    goalName: item.transaction.goalName || "",
    accountName: item.transaction.accountName || "",
    isFixed: item.transaction.isFixed,
    note: item.transaction.note || item.receipt.rawInput,
    reason: "",
  };
}

function clearEditor() {
  editingId.value = "";
  editForm.value = null;
}

function toggleDetail(receiptId: string) {
  detailId.value = detailId.value === receiptId ? "" : receiptId;
}

function saveCorrection(receiptId: string) {
  if (!editForm.value) {
    return;
  }
  correctMutation.mutate({
    receiptId,
    input: { ...editForm.value },
  });
}

function transactionStatusLabel(status?: string): string {
  switch (status) {
    case "draft":
      return "Bản nháp";
    case "confirmed":
      return "Đã xác nhận";
    case "reverted":
      return "Đã hoàn tác";
    default:
      return "Không tìm thấy giao dịch";
  }
}

function confidenceLabel(value: string): string {
  return value.toUpperCase();
}
</script>

<style scoped>
.review-page {
  gap: 1rem;
}

.review-page-head {
  display: grid;
  gap: 0.35rem;
}

.review-page-copy {
  margin: 0;
  max-width: 56rem;
  color: var(--tp-muted);
}

.review-list {
  display: grid;
  gap: 1rem;
}

.review-row,
.review-row-main,
.review-expand {
  display: grid;
  gap: 1rem;
}

.review-row {
  padding: 1.2rem 1.25rem;
}

.review-row-main {
  grid-template-columns: minmax(0, 1.2fr) auto;
  align-items: start;
  gap: 1.25rem;
}

.review-row h3 {
  margin: 0.25rem 0 0;
  font-size: 1.3rem;
}

.review-summary-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  color: var(--tp-muted);
  font-size: 0.9rem;
  font-weight: 700;
}

.review-summary-strip span {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--tp-surface-alt) 72%, white);
  border: 1px solid var(--tp-line);
}

.review-raw,
.review-note {
  margin: 0;
  color: var(--tp-muted);
}

.review-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  justify-content: flex-end;
}

.review-actions button,
.review-form-actions button {
  border: 0;
  border-radius: 0.72rem;
  padding: 0.78rem 0.95rem;
  background: linear-gradient(135deg, var(--tp-accent-strong), var(--tp-accent));
  color: #f7faf7;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 24px color-mix(in srgb, var(--tp-accent-strong) 20%, transparent);
}

.review-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0;
}

.review-meta div {
  padding: 0.85rem;
  border-radius: 0.72rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 94%, white);
}

.review-meta dt {
  font-size: 0.75rem;
  color: var(--tp-muted);
  text-transform: uppercase;
}

.review-meta dd {
  margin: 0.35rem 0 0;
  font-weight: 700;
}

.review-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
  padding: 1rem 0 0;
  border-top: 1px solid var(--tp-line);
}

.review-form label {
  display: grid;
  gap: 0.35rem;
}

.review-form-wide {
  grid-column: 1 / -1;
}

.review-form span {
  font-size: 0.76rem;
  color: var(--tp-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.review-form input,
.review-form select,
.review-form textarea,
.review-actions button,
.review-form-actions button {
  font: inherit;
}

.review-form input,
.review-form select,
.review-form textarea {
  width: 100%;
  padding: 0.75rem 0.85rem;
  border-radius: 0.68rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 94%, white);
}

.checkbox {
  display: flex !important;
  align-items: center;
  gap: 0.5rem;
}

.checkbox input {
  width: auto;
}

.review-form-actions {
  grid-column: 1 / -1;
  display: flex;
  gap: 0.75rem;
}

.review-json {
  margin: 0;
  padding: 1rem;
  border-radius: 0.72rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 88%, white);
  font: 0.88rem/1.45 "IBM Plex Mono", monospace;
  white-space: pre-wrap;
  overflow: auto;
}

.review-actions .danger-button {
  background: color-mix(in srgb, var(--tp-danger) 82%, #9c334a);
}

.review-actions .secondary-button {
  background: color-mix(in srgb, var(--tp-accent-tint) 78%, white);
  color: var(--tp-text);
  border: 1px solid var(--tp-line);
  box-shadow: none;
}

.ghost-button {
  background: color-mix(in srgb, var(--tp-text) 84%, #3f5147);
  box-shadow: none;
}

.review-actions button:disabled,
.review-form-actions button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.review-error {
  color: #8f2438;
}

@media (max-width: 720px) {
  .review-row-main {
    grid-template-columns: 1fr;
  }

  .review-actions {
    justify-content: flex-start;
  }

  .review-form {
    grid-template-columns: 1fr;
  }
}
</style>

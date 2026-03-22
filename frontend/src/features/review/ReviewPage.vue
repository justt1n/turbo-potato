<template>
  <section class="page">
    <header>
      <p class="eyebrow">Kiểm duyệt</p>
      <h2>Hàng đợi xác nhận thủ công</h2>
    </header>

    <p v-if="query.isLoading.value" class="panel">Đang tải các bản ghi cần duyệt...</p>
    <p v-else-if="query.isError.value" class="panel review-error">
      {{ (query.error.value as Error).message }}
    </p>

    <article v-else-if="items.length === 0" class="card">
      <p>Chưa có bản ghi nào đang chờ kiểm duyệt.</p>
    </article>

    <div v-else class="review-grid">
      <article v-for="item in items" :key="item.receipt.id" class="panel review-card">
        <div class="review-head">
          <div>
            <p class="eyebrow">Phiếu {{ item.receipt.id }}</p>
            <h3>{{ item.transaction?.note || item.receipt.rawInput }}</h3>
          </div>
          <span class="review-pill">{{ item.receipt.confidence }}</span>
        </div>

        <p class="review-raw">{{ item.receipt.rawInput }}</p>

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

        <p class="review-note">{{ item.receipt.validationNote }}</p>

        <div v-if="item.transaction?.status === 'draft'" class="review-actions">
          <button :disabled="isActionBusy(item.receipt.id)" type="button" @click="confirm(item.receipt.id)">
            Xác nhận bản nháp
          </button>
          <button :disabled="isActionBusy(item.receipt.id)" type="button" @click="toggleEditor(item)">
            {{ editingId === item.receipt.id ? "Đóng chỉnh sửa" : "Sửa bản nháp" }}
          </button>
          <button :disabled="isActionBusy(item.receipt.id)" class="danger-button" type="button" @click="undo(item.receipt.id)">
            Hoàn tác bản nháp
          </button>
        </div>

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
            <input v-model.trim="editForm.jarCode" placeholder="ThietYeu" />
          </label>

          <label>
            <span>Tên mục tiêu</span>
            <input v-model.trim="editForm.goalName" placeholder="Mua xe SH" />
          </label>

          <label>
            <span>Tài khoản</span>
            <input v-model.trim="editForm.accountName" placeholder="Ví" />
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

        <pre class="review-json">{{ prettyJson(item.receipt.llmOutputJson) }}</pre>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useMutation, useQuery } from "@tanstack/vue-query";
import {
  confirmParsedReceipt,
  correctParsedReceipt,
  listParsedReceipts,
  type ParsedReceiptReviewItem,
  undoParsedReceipt,
} from "@/api/review";

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

const items = computed(() => query.data.value?.items ?? []);
const editingId = ref("");
const editForm = ref<ReviewEditForm | null>(null);

const confirmMutation = useMutation({
  mutationFn: (receiptId: string) =>
    confirmParsedReceipt(receiptId, {
      actor: "review-ui",
      reason: "confirmed from review queue",
    }),
  onSuccess: async () => {
    await query.refetch();
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
    await query.refetch();
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
    await query.refetch();
  },
});

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
</script>

<style scoped>
.review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
}

.review-card {
  display: grid;
  gap: 1rem;
}

.review-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.review-head h3 {
  margin: 0.25rem 0 0;
  font-size: 1.15rem;
}

.review-pill {
  padding: 0.45rem 0.7rem;
  border-radius: 999px;
  background: var(--tp-accent);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.review-raw,
.review-note {
  margin: 0;
  color: var(--tp-muted);
}

.review-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin: 0;
}

.review-meta div {
  padding: 0.85rem;
  border-radius: 0.75rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 90%, white);
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

.review-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.review-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
  padding: 1rem;
  border-radius: 0.9rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 86%, white);
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
  border-radius: 0.75rem;
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
  border-radius: 0.8rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 88%, white);
  font: 0.88rem/1.45 "IBM Plex Mono", monospace;
  white-space: pre-wrap;
  overflow: auto;
}

.review-actions button,
.review-form-actions button {
  border: 0;
  border-radius: 0.8rem;
  padding: 0.8rem 0.95rem;
  background: var(--tp-text);
  color: #f7faf7;
  font-weight: 700;
  cursor: pointer;
}

.review-actions .danger-button {
  background: color-mix(in srgb, var(--tp-danger) 82%, #9c334a);
}

.ghost-button {
  background: color-mix(in srgb, var(--tp-muted) 76%, #5f6b60);
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
  .review-form {
    grid-template-columns: 1fr;
  }
}
</style>

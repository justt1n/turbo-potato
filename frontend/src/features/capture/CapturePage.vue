<template>
  <section class="page capture-page">
    <header class="panel hero-panel">
      <div>
        <p class="eyebrow">Nhập liệu</p>
        <h1>Ghi nhanh một khoản phát sinh</h1>
        <p class="hero-copy">
          Chọn cách nhập phù hợp nhất với bạn: gõ câu tự nhiên để hệ thống parse, hoặc nhập trực tiếp bằng các
          trường cụ thể. Mặc định mọi thứ được giữ tối giản để dùng tốt trên laptop và vẫn ổn trên điện thoại.
        </p>
      </div>

      <div class="hero-meta">
        <span>{{ activeMode === "text" ? "Chế độ chat" : "Chế độ nhập cụ thể" }}</span>
        <span>{{ selectedJarName }}</span>
        <span>{{ todayLabel }}</span>
      </div>
    </header>

    <section class="panel switcher-panel">
      <div class="mode-slider" :class="activeMode">
        <button type="button" :class="{ active: activeMode === 'text' }" @click="switchMode('text')">
          Chat box
        </button>
        <button type="button" :class="{ active: activeMode === 'structured' }" @click="switchMode('structured')">
          Nhập cụ thể
        </button>
      </div>

      <p class="mode-copy">
        {{
          activeMode === "text"
            ? "Phù hợp khi bạn muốn ghi thật nhanh bằng ngôn ngữ tự nhiên, ví dụ: ăn trưa 50k #thiết_yếu."
            : "Phù hợp khi bạn muốn kiểm soát chính xác số tiền, hũ, nguồn tiền và loại giao dịch."
        }}
      </p>
    </section>

    <article v-if="activeMode === 'text'" class="panel input-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Chat box</p>
          <h2>Nhập như đang nhắn tin</h2>
        </div>
        <span class="panel-kpi">Tạo nháp để kiểm duyệt</span>
      </div>

      <form class="input-form" @submit.prevent="submitText">
        <label>
          <span>Nội dung</span>
          <textarea
            ref="textInputRef"
            v-model.trim="textForm.rawInput"
            rows="6"
            placeholder="ăn trưa 50k #thiết_yếu"
            required
          />
        </label>

        <div class="inline-grid">
          <label>
            <span>Actor</span>
            <input v-model.trim="textForm.actor" placeholder="web-user" />
          </label>

          <label>
            <span>Nguồn ghi nhận</span>
            <input v-model.trim="textForm.source" placeholder="capture-page" />
          </label>
        </div>

        <div class="example-row">
          <button type="button" @click="applyExample('ăn sáng 35k #thiết_yếu')">Ăn sáng</button>
          <button type="button" @click="applyExample('cafe 45k #linh_hoạt')">Cafe</button>
          <button type="button" @click="applyExample('chuyển 2tr vào quỹ khẩn cấp')">Chuyển quỹ</button>
        </div>

        <button class="submit-button" :disabled="textMutation.isPending.value || textForm.rawInput.length === 0" type="submit">
          {{ textMutation.isPending.value ? "Đang parse..." : "Tạo nháp" }}
        </button>
      </form>
    </article>

    <article v-else class="panel input-panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Nhập cụ thể</p>
          <h2>Điền số rồi chọn nhanh</h2>
        </div>
        <span class="panel-kpi">Lưu thẳng vào sổ</span>
      </div>

      <form class="input-form" @submit.prevent="submitStructured">
        <div class="amount-block">
          <label>
            <span>Số tiền</span>
            <input
              ref="amountInputRef"
              v-model="amountInput"
              inputmode="numeric"
              placeholder="50.000"
              required
            />
          </label>
          <strong>{{ formattedAmount }}</strong>
        </div>

        <div class="inline-grid three">
          <label>
            <span>Loại giao dịch</span>
            <select v-model="structuredForm.type">
              <option value="OUT">Chi tiêu</option>
              <option value="IN">Thu nhập</option>
              <option value="TRANSFER">Chuyển tiền</option>
            </select>
          </label>

          <label>
            <span>Ngày</span>
            <input v-model="structuredForm.occurredAt" type="date" />
          </label>

          <label>
            <span>Hũ</span>
            <select v-model="structuredForm.jarCode">
              <option value="">Chưa gắn hũ</option>
              <option v-for="jar in jars" :key="jar.code" :value="jar.code">{{ jar.name }}</option>
            </select>
          </label>
        </div>

        <div class="inline-grid">
          <label>
            <span>Nguồn tiền</span>
            <select v-model="structuredForm.accountName">
              <option value="">Chưa chọn nguồn</option>
              <option v-for="source in sources" :key="source.code" :value="source.code">{{ source.name }}</option>
            </select>
          </label>

          <label v-if="structuredForm.type === 'TRANSFER'">
            <span>Mục tiêu</span>
            <select v-model="structuredForm.goalName">
              <option value="">Chưa chọn mục tiêu</option>
              <option v-for="goal in goals" :key="goal.name" :value="goal.name">{{ goal.name }}</option>
            </select>
          </label>
        </div>

        <label>
          <span>Ghi chú</span>
          <textarea v-model.trim="structuredForm.note" rows="4" placeholder="Ví dụ: ăn trưa, mua sách, hoàn tiền..." />
        </label>

        <button class="submit-button" :disabled="structuredMutation.isPending.value || amountValue <= 0" type="submit">
          {{ structuredMutation.isPending.value ? "Đang lưu..." : "Lưu giao dịch" }}
        </button>
      </form>
    </article>

    <article v-if="successMessage" class="panel success-panel">
      <strong>{{ successMessage.title }}</strong>
      <p>{{ successMessage.body }}</p>
      <div class="success-links">
        <RouterLink to="/review">Mở kiểm duyệt</RouterLink>
        <RouterLink to="/dashboard">Xem dashboard</RouterLink>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { RouterLink } from "vue-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { listGoals } from "@/api/goals";
import { ingestChat } from "@/api/ingestion";
import { listJars } from "@/api/jars";
import { listSources } from "@/api/sources";
import { createTransaction, type TransactionType } from "@/api/transactions";
import { formatCurrency } from "@/lib/formatCurrency";
import { loadUserPreferences, saveUserPreferences } from "@/lib/preferences";

type Mode = "text" | "structured";

const queryClient = useQueryClient();
const preferences = loadUserPreferences();
const textInputRef = ref<HTMLTextAreaElement | null>(null);
const amountInputRef = ref<HTMLInputElement | null>(null);

const activeMode = ref<Mode>("text");
const amountInput = ref("");
const successMessage = ref<{ title: string; body: string } | null>(null);

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

const jars = computed(() => jarsQuery.data.value?.items ?? []);
const goals = computed(() => goalsQuery.data.value?.items ?? []);
const sources = computed(() => sourcesQuery.data.value?.items ?? []);

const textForm = reactive({
  rawInput: "",
  actor: preferences.actorName,
  source: preferences.chatSource || "capture-page",
});

const structuredForm = reactive({
  occurredAt: todayInputValue(),
  type: "OUT" as TransactionType,
  jarCode: "",
  goalName: "",
  accountName: "",
  note: "",
  isFixed: false,
  source: "capture-form",
});

const amountValue = computed(() => Number(amountInput.value.replace(/[^\d]/g, "") || "0"));
const formattedAmount = computed(() => formatCurrency(amountValue.value || 0));
const selectedJarName = computed(() => jars.value.find((item) => item.code === structuredForm.jarCode)?.name ?? "Thiết yếu");
const todayLabel = computed(() => new Date(`${structuredForm.occurredAt}T12:00:00`).toLocaleDateString("vi-VN"));

const textMutation = useMutation({
  mutationFn: ingestChat,
  onSuccess: async (result) => {
    saveUserPreferences({
      actorName: textForm.actor.trim() || "web-user",
      chatSource: textForm.source.trim() || "capture-page",
    });
    successMessage.value = {
      title: "Đã tạo nháp thành công",
      body: `Receipt ${result.receipt.id} đã được gửi vào hàng đợi kiểm duyệt.`,
    };
    textForm.rawInput = "";
    await refreshAfterSave();
  },
});

const structuredMutation = useMutation({
  mutationFn: createTransaction,
  onSuccess: async () => {
    successMessage.value = {
      title: "Đã lưu giao dịch",
      body: `Khoản ${formattedAmount.value} đã được ghi nhận vào hệ thống.`,
    };
    amountInput.value = "";
    structuredForm.note = "";
    structuredForm.goalName = "";
    structuredForm.type = "OUT";
    structuredForm.occurredAt = todayInputValue();
    await refreshAfterSave();
  },
});

watch(
  () => jars.value,
  (items) => {
    if (structuredForm.jarCode) {
      return;
    }
    const preferred = items.find((item) => /thi[eế]t|essential/i.test(item.name) || /thi[eế]t/i.test(item.code)) ?? items[0];
    structuredForm.jarCode = preferred?.code ?? "";
  },
  { immediate: true },
);

watch(
  () => sources.value,
  (items) => {
    if (structuredForm.accountName) {
      return;
    }
    structuredForm.accountName = items[0]?.code ?? "";
  },
  { immediate: true },
);

watch(amountInput, (value) => {
  const digits = value.replace(/[^\d]/g, "");
  amountInput.value = digits ? new Intl.NumberFormat("vi-VN").format(Number(digits)) : "";
});

onMounted(() => {
  focusCurrentMode();
});

function switchMode(mode: Mode) {
  activeMode.value = mode;
  successMessage.value = null;
  nextTick(() => focusCurrentMode());
}

function focusCurrentMode() {
  if (activeMode.value === "text") {
    textInputRef.value?.focus();
    return;
  }
  amountInputRef.value?.focus();
}

function applyExample(value: string) {
  textForm.rawInput = value;
  nextTick(() => textInputRef.value?.focus());
}

function submitText() {
  if (!textForm.rawInput.trim()) {
    return;
  }

  textMutation.mutate({
    rawInput: textForm.rawInput.trim(),
    actor: textForm.actor.trim() || "web-user",
    source: textForm.source.trim() || "capture-page",
  });
}

function submitStructured() {
  if (amountValue.value <= 0) {
    return;
  }

  structuredMutation.mutate({
    occurredAt: new Date(`${structuredForm.occurredAt}T12:00:00`).toISOString(),
    type: structuredForm.type,
    amount: amountValue.value,
    currency: "VND",
    jarCode: structuredForm.jarCode || undefined,
    goalName: structuredForm.goalName || undefined,
    accountName: structuredForm.accountName || undefined,
    isFixed: structuredForm.isFixed,
    note: structuredForm.note.trim() || defaultStructuredNote(),
    source: structuredForm.source,
  });
}

async function refreshAfterSave() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["transactions"] }),
    queryClient.invalidateQueries({ queryKey: ["parsed-receipts"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-reports"] }),
    queryClient.invalidateQueries({ queryKey: ["assets-overview"] }),
  ]);
}

function defaultStructuredNote(): string {
  return structuredForm.type === "IN" ? "Thu từ trang nhập liệu" : "Chi từ trang nhập liệu";
}

function todayInputValue(): string {
  const now = new Date();
  const tz = now.getTimezoneOffset();
  const local = new Date(now.getTime() - tz * 60_000);
  return local.toISOString().slice(0, 10);
}
</script>

<style scoped>
.capture-page {
  gap: 1rem;
  max-width: 1320px;
}

.hero-panel,
.switcher-panel,
.input-panel {
  display: grid;
  gap: 1rem;
  animation: section-enter 440ms cubic-bezier(0.22, 1, 0.36, 1);
}

.hero-panel {
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  align-items: end;
  padding: 1.9rem 2rem;
  border-radius: 1rem;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(250, 253, 251, 0.94) 100%);
  overflow: hidden;
}

.hero-panel::after {
  content: "";
  position: absolute;
  inset: -20% auto auto 62%;
  width: 14rem;
  height: 14rem;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(167, 243, 208, 0.42) 0%, transparent 72%);
  pointer-events: none;
  filter: blur(4px);
}

.hero-panel h1,
.input-panel h2 {
  margin: 0;
  letter-spacing: -0.05em;
}

.hero-panel h1 {
  font-size: clamp(2.6rem, 5vw, 4.6rem);
  line-height: 0.9;
  color: #13231a;
}

.hero-copy,
.mode-copy {
  margin: 0;
  color: var(--tp-muted);
  max-width: 48rem;
}

.hero-meta,
.success-links,
.example-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
}

.hero-meta span {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.45rem 0.7rem;
  border-radius: 0.7rem;
  border: 1px solid var(--tp-line);
  background: rgba(244, 249, 245, 0.98);
  color: var(--tp-text);
  font-size: 0.82rem;
  font-weight: 700;
  transition: transform 160ms ease, background 180ms ease, border-color 180ms ease;
}

.hero-meta span:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.12);
}

.mode-slider {
  position: relative;
  display: inline-grid;
  grid-template-columns: repeat(2, minmax(170px, 1fr));
  padding: 0.25rem;
  border-radius: 0.9rem;
  background: rgba(236, 244, 238, 0.96);
  border: 1px solid var(--tp-line);
  overflow: hidden;
}

.mode-slider button,
.submit-button,
.example-row button,
input,
textarea,
select {
  font: inherit;
}

.mode-slider button {
  min-height: 2.8rem;
  border: 0;
  border-radius: 0.7rem;
  background: transparent;
  color: rgba(81, 101, 86, 0.92);
  cursor: pointer;
  font-weight: 700;
  transition:
    color 180ms ease,
    transform 150ms ease,
    background 180ms ease,
    box-shadow 220ms ease;
}

.mode-slider button:hover {
  color: var(--tp-text);
  transform: translateY(-1px);
}

.mode-slider button.active {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.9) 100%);
  color: var(--tp-text);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.56),
    0 8px 20px rgba(72, 99, 81, 0.12);
}

.switcher-panel {
  align-items: start;
  padding: 1.1rem 1.25rem;
  border-radius: 0.95rem;
}

.input-panel {
  padding: 1.65rem 1.8rem;
  border-radius: 1rem;
  transform-origin: top center;
}

.input-panel h2 {
  font-size: clamp(1.5rem, 2vw, 2rem);
}

.input-form {
  display: grid;
  gap: 1rem;
  max-width: 1080px;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  padding-bottom: 0.55rem;
  border-bottom: 1px solid rgba(134, 164, 138, 0.14);
}

.inline-grid {
  display: grid;
  gap: 0.9rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.inline-grid.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

label {
  display: grid;
  gap: 0.4rem;
}

label span {
  color: var(--tp-muted);
  font-size: 0.84rem;
  font-weight: 700;
}

input,
textarea,
select {
  width: 100%;
  padding: 0.95rem 1rem;
  border-radius: 0.8rem;
  border: 1px solid rgba(122, 143, 129, 0.22);
  background: rgba(255, 255, 255, 0.98);
  color: var(--tp-text);
  transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}

input:focus,
textarea:focus,
select:focus {
  outline: none;
  border-color: rgba(16, 185, 129, 0.42);
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.14);
  background: rgba(255, 255, 255, 1);
}

input::placeholder,
textarea::placeholder {
  color: rgba(88, 111, 93, 0.46);
}

.amount-block {
  display: grid;
  gap: 0.65rem;
  padding: 1.15rem 1.2rem;
  border-radius: 0.95rem;
  border: 1px solid var(--tp-line);
  background: linear-gradient(135deg, rgba(238, 248, 242, 0.98) 0%, rgba(255, 255, 255, 0.94) 100%);
}

.amount-block strong {
  font-size: clamp(2.5rem, 7vw, 4.8rem);
  line-height: 0.92;
  letter-spacing: -0.07em;
}

.example-row button {
  border: 1px solid var(--tp-line);
  border-radius: 0.75rem;
  background: rgba(241, 248, 243, 0.96);
  color: var(--tp-text);
  padding: 0.65rem 0.85rem;
  cursor: pointer;
  transition:
    transform 150ms ease,
    background 180ms ease,
    border-color 180ms ease,
    box-shadow 220ms ease;
}

.example-row button:hover {
  background: rgba(255, 255, 255, 0.98);
  transform: translateY(-1px);
  box-shadow: 0 12px 26px rgba(72, 99, 81, 0.1);
}

.submit-button {
  min-height: 3.2rem;
  border: 0;
  border-radius: 0.8rem;
  background: linear-gradient(135deg, #059669 0%, #10b981 52%, #34d399 100%);
  color: #ffffff;
  padding: 0.9rem 1rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  cursor: pointer;
  box-shadow: 0 16px 30px rgba(5, 150, 105, 0.28);
  transition:
    transform 160ms ease,
    box-shadow 220ms ease,
    filter 180ms ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 20px 34px rgba(5, 150, 105, 0.32);
  filter: saturate(1.03);
}

.submit-button:active:not(:disabled) {
  transform: translateY(0);
}

.submit-button:disabled {
  opacity: 0.7;
  cursor: wait;
}

.success-panel strong {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 1.05rem;
}

.success-panel {
  animation: success-enter 360ms cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes section-enter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes success-enter {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.success-panel p {
  margin: 0 0 0.8rem;
}

.success-links a {
  color: var(--tp-text);
  font-weight: 700;
}

@media (max-width: 760px) {
  .hero-panel {
    grid-template-columns: 1fr;
  }

  .inline-grid,
  .inline-grid.three {
    grid-template-columns: 1fr;
  }

  .capture-page {
    max-width: none;
  }

  .mode-slider {
    width: 100%;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-panel,
  .switcher-panel,
  .input-panel,
  .success-panel {
    animation: none !important;
  }

  .hero-meta span,
  .mode-slider button,
  .example-row button,
  .submit-button {
    transition: none !important;
  }
}
</style>

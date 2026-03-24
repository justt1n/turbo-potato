<template>
  <section class="page assets-page">
    <header class="panel assets-hero">
      <div>
        <p class="eyebrow">Nguồn tiền</p>
        <h2>Quản lý tài sản theo nguồn vốn và giá trị ròng hiện có</h2>
        <p class="hero-copy">
          Tài khoản ngân hàng, tiền mặt trong ví, tiền cất trong tủ và vàng đều được quản lý như các nguồn vốn
          riêng. Với vàng, bạn nhập số lượng theo chỉ và giá hiện tại để hệ thống tự quy đổi ra giá trị ròng.
        </p>
        <div class="hero-glossary">
          <TermHintModal
            term="Nguồn tiền"
            summary="Nguồn tiền là nơi tài sản đang nằm thực tế, như tài khoản ngân hàng, ví tiền mặt hoặc vàng."
            detail="Đây là lớp phản ánh nơi giữ tài sản, khác với hũ là lớp kế hoạch phân bổ."
          />
          <TermHintModal
            term="Số cái"
            summary="Số cái là số dư tính theo luồng giao dịch đã ghi nhận trong hệ thống."
            detail="Nó phản ánh số liệu kế toán nội bộ sau khi cộng dòng vào và trừ dòng ra."
          />
          <TermHintModal
            term="Độ lệch"
            summary="Độ lệch là chênh lệch giữa số thực tế và số cái."
            detail="Đây là chỉ báo quan trọng để đối soát và phát hiện sai số nhập liệu hoặc tài sản chưa được ghi sổ."
          />
        </div>
      </div>

      <div class="asset-stats">
        <article class="stat-card">
          <span>Số cái</span>
          <strong>{{ formatCurrency(overview?.totalBookBalance ?? 0) }}</strong>
        </article>
        <article class="stat-card">
          <span>Số thực tế</span>
          <strong>{{ formatCurrency(overview?.totalActualBalance ?? 0) }}</strong>
        </article>
        <article class="stat-card">
          <span>Độ lệch tổng</span>
          <strong :class="discrepancyTone(overview?.totalDiscrepancy ?? 0)">
            {{ formatSignedCurrency(overview?.totalDiscrepancy ?? 0) }}
          </strong>
        </article>
        <article class="stat-card">
          <span>Nguồn đang hoạt động</span>
          <strong>{{ overview?.activeSources ?? 0 }}</strong>
        </article>
      </div>
    </header>

    <div class="assets-layout">
      <article class="panel source-form-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Nguồn tiền</p>
            <h3>Thêm nguồn mới</h3>
          </div>
          <span class="panel-kpi">Lưu vào sheet Sources</span>
        </div>

        <form class="source-form" @submit.prevent="submitCreate">
          <label>
            <span>Mã nguồn</span>
            <input v-model.trim="createForm.code" placeholder="VCB_Main" required />
          </label>

          <label>
            <span>Tên hiển thị</span>
            <input v-model.trim="createForm.name" placeholder="VCB tài khoản lương" required />
          </label>

          <label>
            <span>Loại nguồn</span>
            <select v-model="createForm.kind">
              <option value="bank_account">Bank account</option>
              <option value="wallet">Tiền trong ví</option>
              <option value="cash_box">Tiền trong tủ</option>
              <option value="reserve_cash">Tiền dự phòng</option>
              <option value="gold">Vàng</option>
              <option value="other">Khác</option>
            </select>
          </label>

          <label>
            <span>{{ providerLabel(createForm.kind) }}</span>
            <input v-model.trim="createForm.provider" :placeholder="providerPlaceholder(createForm.kind)" />
          </label>

          <label>
            <span>Gắn vào hũ</span>
            <select v-model="createForm.linkedJarCode">
              <option value="">Chưa gắn</option>
              <option v-for="jar in jars" :key="jar.code" :value="jar.code">{{ jar.name }} ({{ jar.code }})</option>
            </select>
          </label>

          <label v-if="createForm.kind !== 'gold'">
            <span>Số dư đầu kỳ</span>
            <input v-model.number="createForm.openingBalance" min="0" required type="number" />
          </label>

          <label v-if="createForm.kind !== 'gold'">
            <span>Số dư thực tế</span>
            <input v-model.number="createForm.actualBalance" min="0" required type="number" />
          </label>

          <label v-if="createForm.kind === 'gold'">
            <span>Số lượng vàng (chỉ)</span>
            <input v-model.number="createForm.goldQuantityChi" min="0" step="0.1" required type="number" />
          </label>

          <label v-if="createForm.kind === 'gold'">
            <span>Giá vàng / chỉ</span>
            <input v-model.number="createForm.goldPricePerChi" min="0" required type="number" />
          </label>

          <div v-if="createForm.kind === 'gold'" class="gold-preview">
            Giá trị hiện tại: <strong>{{ formatCurrency(goldNet(createForm.goldQuantityChi, createForm.goldPricePerChi)) }}</strong>
          </div>

          <label class="full-width">
            <span>Ghi chú</span>
            <textarea v-model.trim="createForm.note" rows="3" placeholder="Ví dụ: tài khoản dùng để giữ quỹ dự phòng" />
          </label>

          <label class="checkbox">
            <input v-model="createForm.isActive" type="checkbox" />
            <span>Đang hoạt động</span>
          </label>

          <button :disabled="createMutation.isPending.value" type="submit">
            {{ createMutation.isPending.value ? "Đang lưu..." : "Tạo nguồn tiền" }}
          </button>
        </form>

        <p v-if="formMessage" :class="formMessageTone">{{ formMessage }}</p>
      </article>

      <section class="source-list-section">
        <p v-if="assetsQuery.isLoading.value || sourcesQuery.isLoading.value || jarsQuery.isLoading.value" class="panel">Đang tải nguồn tiền...</p>
        <p v-else-if="assetsQuery.isError.value || sourcesQuery.isError.value || jarsQuery.isError.value" class="panel error-text">
          {{ ((assetsQuery.error.value ?? sourcesQuery.error.value ?? jarsQuery.error.value) as Error).message }}
        </p>
        <article v-else-if="assetItems.length === 0" class="panel empty-panel">
          <h3>Chưa có nguồn tiền nào</h3>
          <p>Hãy thêm nguồn tiền đầu tiên để bắt đầu theo dõi tổng tài sản và độ lệch hiện tại.</p>
        </article>

        <div v-else class="source-list">
          <article v-for="item in assetItems" :key="item.code" class="panel source-card">
            <div class="source-card-head">
              <div>
                <p class="eyebrow">{{ kindLabel(item.kind) }}</p>
                <h3>{{ item.name }}</h3>
                <small>{{ item.code }}<span v-if="item.provider"> · {{ item.provider }}</span></small>
              </div>

              <div class="source-card-actions">
                <button class="secondary-button" type="button" @click="syncActualToBook(item)">
                  Khớp theo sổ
                </button>
                <button class="secondary-button" type="button" @click="toggleEdit(item)">
                  {{ editingSourceCode === item.code ? "Đóng chỉnh sửa" : "Chỉnh sửa" }}
                </button>
              </div>
            </div>

            <div class="source-kpi-grid">
              <div>
                <span>So cai</span>
                <strong>{{ formatCurrency(item.bookBalance) }}</strong>
              </div>
              <div>
                <span>So thuc te</span>
                <strong>{{ formatCurrency(item.actualBalance) }}</strong>
              </div>
              <div>
                <span>Độ lệch</span>
                <strong :class="discrepancyTone(item.discrepancy)">{{ formatSignedCurrency(item.discrepancy) }}</strong>
              </div>
              <div>
                <span>Hũ đang gắn</span>
                <strong>{{ jarName(item.linkedJarCode) }}</strong>
              </div>
            </div>

            <dl class="source-meta">
              <div>
                <dt>Dòng vào</dt>
                <dd>{{ formatCurrency(item.inflowTotal) }}</dd>
              </div>
              <div>
                <dt>Dòng ra</dt>
                <dd>{{ formatCurrency(item.outflowTotal) }}</dd>
              </div>
              <div>
                <dt>Trạng thái</dt>
                <dd>{{ item.isActive ? "Đang hoạt động" : "Tạm dừng" }}</dd>
              </div>
              <div>
                <dt>Lần cuối có giao dịch</dt>
                <dd>{{ formatDateTime(item.lastActivityAt) }}</dd>
              </div>
            </dl>

            <p v-if="item.kind === 'gold'" class="gold-meta">
              {{ item.goldQuantityChi }} chi x {{ formatCurrency(item.goldPricePerChi) }} / chi
            </p>
            <p v-if="item.note" class="source-note">{{ item.note }}</p>

            <form
              v-if="editingSourceCode === item.code && editForm"
              class="source-form edit-form"
              @submit.prevent="submitUpdate(item.code)"
            >
              <label>
                <span>Ten hien thi</span>
                <input v-model.trim="editForm.name" required />
              </label>

              <label>
                <span>Loai nguon</span>
                <select v-model="editForm.kind">
                  <option value="bank_account">Bank account</option>
                  <option value="wallet">Tien trong vi</option>
                  <option value="cash_box">Tien trong tu</option>
                  <option value="reserve_cash">Tien du phong</option>
                  <option value="gold">Vang</option>
                  <option value="other">Khac</option>
                </select>
              </label>

              <label>
                <span>{{ providerLabel(editForm.kind) }}</span>
                <input v-model.trim="editForm.provider" :placeholder="providerPlaceholder(editForm.kind)" />
              </label>

              <label>
                <span>Gan vao hu</span>
                <select v-model="editForm.linkedJarCode">
                  <option value="">Chua gan</option>
                  <option v-for="jar in jars" :key="jar.code" :value="jar.code">{{ jar.name }} ({{ jar.code }})</option>
                </select>
              </label>

              <label v-if="editForm.kind !== 'gold'">
                <span>So du dau ky</span>
                <input v-model.number="editForm.openingBalance" min="0" required type="number" />
              </label>

              <label v-if="editForm.kind !== 'gold'">
                <span>So du thuc te</span>
                <input v-model.number="editForm.actualBalance" min="0" required type="number" />
              </label>

              <label v-if="editForm.kind === 'gold'">
                <span>So luong vang (chi)</span>
                <input v-model.number="editForm.goldQuantityChi" min="0" step="0.1" required type="number" />
              </label>

              <label v-if="editForm.kind === 'gold'">
                <span>Gia vang / chi</span>
                <input v-model.number="editForm.goldPricePerChi" min="0" required type="number" />
              </label>

              <div v-if="editForm.kind === 'gold'" class="gold-preview">
                Gia tri hien tai: <strong>{{ formatCurrency(goldNet(editForm.goldQuantityChi, editForm.goldPricePerChi)) }}</strong>
              </div>

              <label class="full-width">
                <span>Ghi chu</span>
                <textarea v-model.trim="editForm.note" rows="3" />
              </label>

              <label class="checkbox">
                <input v-model="editForm.isActive" type="checkbox" />
                <span>Dang hoat dong</span>
              </label>

              <div class="edit-actions">
                <button :disabled="updateMutation.isPending.value" type="submit">
                  {{ updateMutation.isPending.value ? "Dang cap nhat..." : "Luu thay doi" }}
                </button>
                <button class="ghost-button" type="button" @click="clearEditor">Huy</button>
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
import { getAssetsOverview, type AssetItem } from "@/api/assets";
import { listJars } from "@/api/jars";
import { createSource, listSources, updateSource } from "@/api/sources";
import TermHintModal from "@/components/TermHintModal.vue";
import { formatCurrency } from "@/lib/formatCurrency";

type SourceForm = {
  code: string;
  name: string;
  kind: string;
  provider: string;
  linkedJarCode: string;
  openingBalance: number;
  actualBalance: number;
  goldQuantityChi: number;
  goldPricePerChi: number;
  isActive: boolean;
  note: string;
};

type SourceEditForm = {
  name: string;
  kind: string;
  provider: string;
  linkedJarCode: string;
  openingBalance: number;
  actualBalance: number;
  goldQuantityChi: number;
  goldPricePerChi: number;
  isActive: boolean;
  note: string;
};

const queryClient = useQueryClient();

const assetsQuery = useQuery({
  queryKey: ["assets-overview"],
  queryFn: getAssetsOverview,
});

const sourcesQuery = useQuery({
  queryKey: ["sources"],
  queryFn: listSources,
});

const jarsQuery = useQuery({
  queryKey: ["jars"],
  queryFn: listJars,
});

const overview = computed(() => assetsQuery.data.value);
const assetItems = computed(() => overview.value?.items ?? []);
const jars = computed(() => jarsQuery.data.value?.items ?? []);
const createForm = reactive(defaultForm());
const formMessage = ref("");
const formMessageTone = ref("helper-text");
const editingSourceCode = ref("");
const editForm = ref<SourceEditForm | null>(null);

const createMutation = useMutation({
  mutationFn: createSource,
  onSuccess: async () => {
    Object.assign(createForm, defaultForm());
    formMessage.value = "Da tao nguon tien moi.";
    formMessageTone.value = "success-text";
    await refreshAll();
  },
  onError: (error) => {
    formMessage.value = error instanceof Error ? error.message : "Khong the tao nguon tien";
    formMessageTone.value = "error-text";
  },
});

const updateMutation = useMutation({
  mutationFn: ({ code, input }: { code: string; input: SourceEditForm }) => updateSource(code, input),
  onSuccess: async () => {
    clearEditor();
    formMessage.value = "Da cap nhat nguon tien.";
    formMessageTone.value = "success-text";
    await refreshAll();
  },
  onError: (error) => {
    formMessage.value = error instanceof Error ? error.message : "Khong the cap nhat nguon tien";
    formMessageTone.value = "error-text";
  },
});

function defaultForm(): SourceForm {
  return {
    code: "",
    name: "",
    kind: "bank_account",
    provider: "",
    linkedJarCode: "",
    openingBalance: 0,
    actualBalance: 0,
    goldQuantityChi: 0,
    goldPricePerChi: 0,
    isActive: true,
    note: "",
  };
}

async function refreshAll() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["assets-overview"] }),
    queryClient.invalidateQueries({ queryKey: ["sources"] }),
    queryClient.invalidateQueries({ queryKey: ["jars"] }),
  ]);
}

function submitCreate() {
  formMessage.value = "";
  createMutation.mutate({
    ...createForm,
    actualBalance: createForm.kind === "gold" ? 0 : createForm.actualBalance,
  });
}

function toggleEdit(item: AssetItem) {
  if (editingSourceCode.value === item.code) {
    clearEditor();
    return;
  }

  editingSourceCode.value = item.code;
  editForm.value = {
    name: item.name,
    kind: item.kind,
    provider: item.provider || "",
    linkedJarCode: item.linkedJarCode || "",
    openingBalance: item.openingBalance,
    actualBalance: item.actualBalance,
    goldQuantityChi: item.goldQuantityChi,
    goldPricePerChi: item.goldPricePerChi,
    isActive: item.isActive,
    note: item.note || "",
  };
}

function clearEditor() {
  editingSourceCode.value = "";
  editForm.value = null;
}

function submitUpdate(code: string) {
  if (!editForm.value) {
    return;
  }

  updateMutation.mutate({
    code,
    input: {
      ...editForm.value,
      actualBalance: editForm.value.kind === "gold" ? 0 : editForm.value.actualBalance,
    },
  });
}

function syncActualToBook(item: AssetItem) {
  updateMutation.mutate({
    code: item.code,
    input: {
      name: item.name,
      kind: item.kind,
      provider: item.provider || "",
      linkedJarCode: item.linkedJarCode || "",
      openingBalance: item.openingBalance,
      actualBalance: item.bookBalance,
      goldQuantityChi: item.goldQuantityChi,
      goldPricePerChi: item.goldPricePerChi,
      isActive: item.isActive,
      note: item.note || "",
    },
  });
}

function goldNet(quantityChi: number, pricePerChi: number): number {
  return Math.round(quantityChi * pricePerChi);
}

function kindLabel(value: string): string {
  switch (value) {
    case "bank_account":
      return "Bank account";
    case "wallet":
      return "Tiền trong ví";
    case "cash_box":
      return "Tiền trong tủ";
    case "reserve_cash":
      return "Tiền dự phòng";
    case "gold":
      return "Vàng";
    default:
      return value;
  }
}

function providerLabel(kind: string): string {
  return kind === "gold" ? "Thương hiệu / nơi giữ" : "Ngân hàng / nơi giữ";
}

function providerPlaceholder(kind: string): string {
  if (kind === "bank_account") {
    return "Vietcombank, Techcombank...";
  }
  if (kind === "gold") {
    return "SJC, PNJ, cất giữ tại nhà...";
  }
  return "Ví dụ: ví cá nhân, tủ phòng ngủ...";
}

function jarName(code: string): string {
  if (!code) {
    return "Chưa gắn";
  }
  return jars.value.find((item) => item.code === code)?.name ?? code;
}

function formatSignedCurrency(value: number): string {
  if (value === 0) {
    return formatCurrency(0);
  }
  return `${value > 0 ? "+" : "-"}${formatCurrency(Math.abs(value))}`;
}

function discrepancyTone(value: number): string {
  if (value === 0) {
    return "balanced-text";
  }
  return value > 0 ? "positive-text" : "negative-text";
}

function formatDateTime(value?: string): string {
  if (!value) {
    return "Chưa có";
  }
  return new Date(value).toLocaleString("vi-VN");
}
</script>

<style scoped>
.assets-page {
  gap: 1.25rem;
}

.assets-hero {
  display: grid;
  gap: 1.2rem;
}

.assets-hero h2 {
  margin: 0.3rem 0 0.5rem;
  font-size: clamp(2rem, 3.8vw, 3.2rem);
  line-height: 1;
  letter-spacing: -0.05em;
}

.hero-copy {
  max-width: 56rem;
  margin: 0;
  color: var(--tp-muted);
}

.hero-glossary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.85rem;
}

.asset-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
  font-size: 1.2rem;
  overflow-wrap: anywhere;
}

.assets-layout {
  display: grid;
  grid-template-columns: minmax(300px, 380px) minmax(0, 1fr);
  gap: 1rem;
}

.source-form-panel,
.source-list-section,
.source-list,
.source-card {
  display: grid;
  gap: 1rem;
}

.panel-head,
.source-card-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.panel-head h3,
.source-card h3 {
  margin: 0.28rem 0 0;
  font-size: 1.3rem;
  letter-spacing: -0.03em;
}

.panel-kpi,
.source-card small {
  color: var(--tp-muted);
}

.source-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.9rem;
}

.source-form label {
  display: grid;
  gap: 0.35rem;
}

.source-form span,
.source-kpi-grid span,
.source-meta dt {
  color: var(--tp-muted);
  font-size: 0.85rem;
}

.source-form input,
.source-form select,
.source-form textarea,
.source-form button,
.secondary-button,
.ghost-button {
  font: inherit;
}

.source-form input,
.source-form select,
.source-form textarea {
  width: 100%;
  padding: 0.78rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 92%, white);
  color: var(--tp-text);
}

.source-form button,
.secondary-button,
.ghost-button {
  border: 0;
  border-radius: 0.9rem;
  padding: 0.85rem 1rem;
  cursor: pointer;
}

.source-form button {
  background: var(--tp-text);
  color: #f6f4ee;
}

.secondary-button {
  background: color-mix(in srgb, var(--tp-accent-soft) 76%, white);
  color: var(--tp-text);
}

.ghost-button {
  background: transparent;
  border: 1px solid var(--tp-line);
  color: var(--tp-text);
}

.full-width {
  grid-column: 1 / -1;
}

.checkbox {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.checkbox input {
  width: auto;
}

.gold-preview {
  align-self: end;
  padding: 0.9rem 1rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--tp-surface-alt) 78%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 82%, transparent);
}

.source-card-actions,
.edit-actions {
  display: flex;
  gap: 0.75rem;
}

.source-kpi-grid,
.source-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.8rem;
}

.source-kpi-grid div,
.source-meta div {
  padding: 0.95rem 1rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--tp-surface-alt) 78%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 84%, transparent);
}

.source-kpi-grid strong,
.source-meta dd {
  display: block;
  margin-top: 0.3rem;
}

.source-meta {
  margin: 0;
}

.source-meta dt,
.source-meta dd {
  margin: 0;
}

.gold-meta,
.source-note,
.empty-panel p,
.success-text,
.error-text,
.helper-text {
  margin: 0;
}

.gold-meta,
.source-note {
  color: var(--tp-muted);
}

.balanced-text {
  color: var(--tp-text);
}

.positive-text {
  color: #1f7a63;
}

.negative-text,
.error-text {
  color: #b85f4a;
}

.success-text {
  color: #1f7a63;
}

.edit-form {
  padding-top: 0.25rem;
  border-top: 1px solid color-mix(in srgb, var(--tp-line) 82%, transparent);
}

@media (max-width: 980px) {
  .assets-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .source-form,
  .source-kpi-grid,
  .source-meta {
    grid-template-columns: 1fr;
  }

  .panel-head,
  .source-card-head,
  .source-card-actions,
  .edit-actions {
    flex-direction: column;
  }
}
</style>

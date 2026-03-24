<template>
  <section class="page jars-page">
    <header class="panel jars-hero">
      <div>
        <p class="eyebrow">Hũ tài chính</p>
        <h2>Quản lý phân bổ nguồn tiền vào từng hũ mục tiêu</h2>
        <p class="hero-copy">
          Hũ là lớp kế hoạch, còn nguồn tiền là nơi tiền đang nằm thực tế. Ở đây bạn tạo hũ, xem tổng tiền theo
          từng hũ và quyết định nguồn vốn nào đang được tính vào từng mục tiêu tài chính.
        </p>
        <div class="hero-glossary">
          <TermHintModal
            term="Hũ"
            summary="Hũ là lớp phân bổ ngân sách hoặc mục tiêu tài chính."
            detail="Một hũ không nhất thiết tương ứng với một tài khoản thật; nó đại diện cho mục đích sử dụng vốn."
          />
          <TermHintModal
            term="Nguồn đã gắn"
            summary="Đây là số nguồn tiền đang được tính vào một hoặc nhiều hũ."
            detail="Việc gắn nguồn giúp hệ thống biết tổng tài sản nào đang phục vụ cho từng mục tiêu."
          />
          <TermHintModal
            term="Tổng thực tế đã gắn"
            summary="Đây là tổng số thực tế của các nguồn tiền đã được gán vào hũ."
            detail="Chỉ số này cho thấy bao nhiêu tài sản của bạn đã được đưa vào cấu trúc kế hoạch."
          />
        </div>
      </div>

      <div class="jar-stats">
        <article class="stat-card">
          <span>Số hũ</span>
          <strong>{{ jars.length }}</strong>
        </article>
        <article class="stat-card">
          <span>Nguồn đã gắn</span>
          <strong>{{ assignedSourcesCount }}</strong>
        </article>
        <article class="stat-card">
          <span>Tổng thực tế đã gắn</span>
          <strong>{{ formatCurrency(mappedActualBalance) }}</strong>
        </article>
        <article class="stat-card">
          <span>Nguồn chưa gắn</span>
          <strong>{{ formatCurrency(unassignedActualBalance) }}</strong>
        </article>
      </div>
    </header>

    <div class="jars-layout">
      <article class="panel jar-form-panel">
        <div class="panel-head">
          <div>
            <p class="eyebrow">Thêm hũ</p>
            <h3>Tạo hũ mới</h3>
          </div>
          <span class="panel-kpi">Dùng cho mục đích phân bổ</span>
        </div>

        <form class="jar-form" @submit.prevent="submitCreateJar">
          <label>
            <span>Mã hũ</span>
            <input v-model.trim="createJarForm.code" placeholder="ThietYeu" required />
          </label>

          <label>
            <span>Tên hiển thị</span>
            <input v-model.trim="createJarForm.name" placeholder="Hũ thiết yếu" required />
          </label>

          <label class="full-width">
            <span>Ghi chú</span>
            <textarea v-model.trim="createJarForm.note" rows="3" placeholder="Ví dụ: chi phí sống cơ bản và nhu cầu thiết yếu" />
          </label>

          <label class="checkbox">
            <input v-model="createJarForm.isActive" type="checkbox" />
            <span>Đang hoạt động</span>
          </label>

          <button :disabled="createJarMutation.isPending.value" type="submit">
            {{ createJarMutation.isPending.value ? "Đang tạo..." : "Tạo hũ" }}
          </button>
        </form>

        <p v-if="jarMessage" :class="jarMessageTone">{{ jarMessage }}</p>
      </article>

      <section class="jar-list-section">
        <p v-if="isLoading" class="panel">Đang tải hũ và mapping nguồn tiền...</p>
        <p v-else-if="loadError" class="panel error-text">{{ loadError }}</p>
        <article v-else-if="jars.length === 0" class="panel empty-panel">
          <h3>Chưa có hũ nào</h3>
          <p>Tạo hũ đầu tiên để bắt đầu phân bổ nguồn tiền và theo dõi tổng số thực tế theo từng mục đích.</p>
        </article>

        <div v-else class="jar-list">
          <article v-for="jar in jars" :key="jar.code" class="panel jar-card">
            <div class="jar-card-head">
              <div>
                <p class="eyebrow">{{ jar.isActive ? "Đang hoạt động" : "Tạm dừng" }}</p>
                <h3>{{ jar.name }}</h3>
                <small>{{ jar.code }}</small>
              </div>

              <button class="secondary-button" type="button" @click="toggleEditJar(jar)">
                {{ editingJarCode === jar.code ? "Đóng chỉnh sửa" : "Chỉnh sửa" }}
              </button>
            </div>

            <div class="jar-kpi-grid">
              <div>
                <span>Tổng số cái</span>
                <strong>{{ formatCurrency(jarTotalFor(jar.code).totalBookBalance) }}</strong>
              </div>
              <div>
                <span>Tổng thực tế</span>
                <strong>{{ formatCurrency(jarTotalFor(jar.code).totalActualBalance) }}</strong>
              </div>
              <div>
                <span>Độ lệch</span>
                <strong :class="discrepancyTone(jarDiscrepancy(jar.code))">{{ formatSignedCurrency(jarDiscrepancy(jar.code)) }}</strong>
              </div>
              <div>
                <span>Nguồn đang gắn</span>
                <strong>{{ jarTotalFor(jar.code).sourceCount }}</strong>
              </div>
            </div>

            <p v-if="jar.note" class="jar-note">{{ jar.note }}</p>

            <form
              v-if="editingJarCode === jar.code && editJarForm"
              class="jar-form edit-form"
              @submit.prevent="submitUpdateJar(jar)"
            >
              <label>
                <span>Tên hiển thị</span>
                <input v-model.trim="editJarForm.name" required />
              </label>

              <label class="full-width">
                <span>Ghi chú</span>
                <textarea v-model.trim="editJarForm.note" rows="3" />
              </label>

              <label class="checkbox">
                <input v-model="editJarForm.isActive" type="checkbox" />
                <span>Đang hoạt động</span>
              </label>

              <div class="edit-actions">
                <button :disabled="updateJarMutation.isPending.value" type="submit">
                  {{ updateJarMutation.isPending.value ? "Đang cập nhật..." : "Lưu thay đổi" }}
                </button>
                <button class="ghost-button" type="button" @click="clearJarEditor">Huy</button>
              </div>
            </form>

            <div class="assignment-block">
              <div class="assignment-head">
                <h4>Nguồn đang tính vào hũ này</h4>
                <span>{{ assignedAssets(jar.code).length }} nguồn</span>
              </div>

              <p v-if="assignedAssets(jar.code).length === 0" class="empty-inline">
                Chưa có nguồn tiền nào đang gắn vào hũ này.
              </p>

              <div v-else class="assignment-list">
                <div v-for="item in assignedAssets(jar.code)" :key="item.code" class="assignment-row">
                  <div class="assignment-copy">
                    <strong>{{ item.name }}</strong>
                    <span>{{ kindLabel(item.kind) }}<template v-if="item.provider"> · {{ item.provider }}</template></span>
                    <small>{{ formatCurrency(item.actualBalance) }} thuc te</small>
                  </div>

                  <div class="assignment-controls">
                    <select :value="assignmentDrafts[item.code] ?? item.linkedJarCode" @change="updateAssignmentDraft(item.code, $event)">
                      <option value="">Chưa gắn</option>
                      <option v-for="option in jars" :key="option.code" :value="option.code">
                        {{ option.name }} ({{ option.code }})
                      </option>
                    </select>
                    <button
                      class="ghost-button"
                      :disabled="assignmentMutation.isPending.value || isAssignmentUnchanged(item.code, item.linkedJarCode)"
                      type="button"
                      @click="saveAssignment(item.code)"
                    >
                      Lưu
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </article>

          <article class="panel unassigned-panel">
            <div class="assignment-head">
              <div>
                <p class="eyebrow">Chưa gắn hũ</p>
                <h3>Nguồn tiền chưa được tính vào hũ nào</h3>
              </div>
              <span class="panel-kpi">{{ unassignedAssets.length }} nguồn</span>
            </div>

            <p v-if="unassignedAssets.length === 0" class="empty-inline">
              Tất cả nguồn tiền đã được map vào hũ.
            </p>

            <div v-else class="assignment-list">
              <div v-for="item in unassignedAssets" :key="item.code" class="assignment-row">
                <div class="assignment-copy">
                  <strong>{{ item.name }}</strong>
                  <span>{{ kindLabel(item.kind) }}<template v-if="item.provider"> · {{ item.provider }}</template></span>
                  <small>{{ formatCurrency(item.actualBalance) }} thuc te</small>
                </div>

                <div class="assignment-controls">
                  <select :value="assignmentDrafts[item.code] ?? item.linkedJarCode" @change="updateAssignmentDraft(item.code, $event)">
                    <option value="">Chưa gắn</option>
                    <option v-for="option in jars" :key="option.code" :value="option.code">
                      {{ option.name }} ({{ option.code }})
                    </option>
                  </select>
                  <button
                    :disabled="assignmentMutation.isPending.value || isAssignmentUnchanged(item.code, item.linkedJarCode)"
                    type="button"
                    @click="saveAssignment(item.code)"
                  >
                    Gắn vào hũ
                  </button>
                </div>
              </div>
            </div>

            <p v-if="assignmentMessage" :class="assignmentMessageTone">{{ assignmentMessage }}</p>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { getAssetsOverview, type AssetItem, type JarTotal } from "@/api/assets";
import TermHintModal from "@/components/TermHintModal.vue";
import { createJar, listJars, updateJar, type Jar } from "@/api/jars";
import { listSources, updateSource, type Source } from "@/api/sources";
import { formatCurrency } from "@/lib/formatCurrency";

type CreateJarForm = {
  code: string;
  name: string;
  note: string;
  isActive: boolean;
};

type EditJarForm = {
  name: string;
  kind: string;
  openingBalance: number;
  actualBalance: number;
  note: string;
  isActive: boolean;
};

const queryClient = useQueryClient();

const jarsQuery = useQuery({
  queryKey: ["jars"],
  queryFn: listJars,
});

const sourcesQuery = useQuery({
  queryKey: ["sources"],
  queryFn: listSources,
});

const assetsQuery = useQuery({
  queryKey: ["assets-overview"],
  queryFn: getAssetsOverview,
});

const jars = computed(() => jarsQuery.data.value?.items ?? []);
const sourceItems = computed(() => sourcesQuery.data.value?.items ?? []);
const assetItems = computed(() => assetsQuery.data.value?.items ?? []);
const jarTotals = computed(() => {
  const map = new Map<string, JarTotal>();
  for (const item of assetsQuery.data.value?.jarTotals ?? []) {
    map.set(item.jarCode, item);
  }
  return map;
});
const unassignedAssets = computed(() => assetItems.value.filter((item) => !item.linkedJarCode));
const assignedSourcesCount = computed(() => assetItems.value.filter((item) => item.linkedJarCode).length);
const mappedActualBalance = computed(() =>
  (assetsQuery.data.value?.jarTotals ?? []).reduce((total, item) => total + item.totalActualBalance, 0),
);
const unassignedActualBalance = computed(() =>
  unassignedAssets.value.reduce((total, item) => total + item.actualBalance, 0),
);
const isLoading = computed(
  () => jarsQuery.isLoading.value || sourcesQuery.isLoading.value || assetsQuery.isLoading.value,
);
const loadError = computed(() => {
  const error = jarsQuery.error.value ?? sourcesQuery.error.value ?? assetsQuery.error.value;
  return error instanceof Error ? error.message : "";
});

const createJarForm = reactive<CreateJarForm>(defaultCreateJarForm());
const editingJarCode = ref("");
const editJarForm = ref<EditJarForm | null>(null);
const assignmentDrafts = reactive<Record<string, string>>({});
const jarMessage = ref("");
const jarMessageTone = ref("helper-text");
const assignmentMessage = ref("");
const assignmentMessageTone = ref("helper-text");

const sourceMap = computed(() => {
  const map = new Map<string, Source>();
  for (const item of sourceItems.value) {
    map.set(item.code, item);
  }
  return map;
});

watch(
  () => sourceItems.value,
  (items) => {
    for (const key of Object.keys(assignmentDrafts)) {
      delete assignmentDrafts[key];
    }
    for (const item of items) {
      assignmentDrafts[item.code] = item.linkedJarCode || "";
    }
  },
  { immediate: true },
);

const createJarMutation = useMutation({
  mutationFn: createJar,
  onSuccess: async () => {
    Object.assign(createJarForm, defaultCreateJarForm());
    jarMessage.value = "Da tao hu moi.";
    jarMessageTone.value = "success-text";
    await refreshAll();
  },
  onError: (error) => {
    jarMessage.value = error instanceof Error ? error.message : "Khong the tao hu";
    jarMessageTone.value = "error-text";
  },
});

const updateJarMutation = useMutation({
  mutationFn: ({ code, jar }: { code: string; jar: EditJarForm }) => updateJar(code, jar),
  onSuccess: async () => {
    clearJarEditor();
    jarMessage.value = "Da cap nhat hu.";
    jarMessageTone.value = "success-text";
    await refreshAll();
  },
  onError: (error) => {
    jarMessage.value = error instanceof Error ? error.message : "Khong the cap nhat hu";
    jarMessageTone.value = "error-text";
  },
});

const assignmentMutation = useMutation({
  mutationFn: ({ sourceCode, linkedJarCode }: { sourceCode: string; linkedJarCode: string }) => {
    const source = sourceMap.value.get(sourceCode);
    if (!source) {
      throw new Error(`source ${sourceCode} not found`);
    }

    return updateSource(sourceCode, {
      name: source.name,
      kind: source.kind,
      provider: source.provider,
      linkedJarCode,
      openingBalance: source.openingBalance,
      actualBalance: source.actualBalance,
      goldQuantityChi: source.goldQuantityChi,
      goldPricePerChi: source.goldPricePerChi,
      isActive: source.isActive,
      note: source.note,
    });
  },
  onSuccess: async () => {
    assignmentMessage.value = "Da cap nhat mapping nguon tien vao hu.";
    assignmentMessageTone.value = "success-text";
    await refreshAll();
  },
  onError: (error) => {
    assignmentMessage.value = error instanceof Error ? error.message : "Khong the cap nhat mapping";
    assignmentMessageTone.value = "error-text";
  },
});

function defaultCreateJarForm(): CreateJarForm {
  return {
    code: "",
    name: "",
    note: "",
    isActive: true,
  };
}

async function refreshAll() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["jars"] }),
    queryClient.invalidateQueries({ queryKey: ["sources"] }),
    queryClient.invalidateQueries({ queryKey: ["assets-overview"] }),
  ]);
}

function submitCreateJar() {
  jarMessage.value = "";
  createJarMutation.mutate({
    code: createJarForm.code,
    name: createJarForm.name,
    kind: "bucket",
    openingBalance: 0,
    actualBalance: 0,
    isActive: createJarForm.isActive,
    note: createJarForm.note,
  });
}

function toggleEditJar(jar: Jar) {
  if (editingJarCode.value === jar.code) {
    clearJarEditor();
    return;
  }

  editingJarCode.value = jar.code;
  editJarForm.value = {
    name: jar.name,
    kind: jar.kind,
    openingBalance: jar.openingBalance,
    actualBalance: jar.actualBalance,
    note: jar.note || "",
    isActive: jar.isActive,
  };
}

function clearJarEditor() {
  editingJarCode.value = "";
  editJarForm.value = null;
}

function submitUpdateJar(jar: Jar) {
  if (!editJarForm.value) {
    return;
  }

  updateJarMutation.mutate({
    code: jar.code,
    jar: {
      ...editJarForm.value,
    },
  });
}

function assignedAssets(jarCode: string): AssetItem[] {
  return assetItems.value.filter((item) => item.linkedJarCode === jarCode);
}

function jarTotalFor(jarCode: string): JarTotal {
  return (
    jarTotals.value.get(jarCode) ?? {
      jarCode,
      totalBookBalance: 0,
      totalActualBalance: 0,
      sourceCount: 0,
    }
  );
}

function jarDiscrepancy(jarCode: string): number {
  const total = jarTotalFor(jarCode);
  return total.totalActualBalance - total.totalBookBalance;
}

function updateAssignmentDraft(sourceCode: string, event: Event) {
  assignmentDrafts[sourceCode] = (event.target as HTMLSelectElement).value;
}

function isAssignmentUnchanged(sourceCode: string, currentJarCode: string): boolean {
  return (assignmentDrafts[sourceCode] ?? "") === (currentJarCode || "");
}

function saveAssignment(sourceCode: string) {
  assignmentMessage.value = "";
  assignmentMutation.mutate({
    sourceCode,
    linkedJarCode: assignmentDrafts[sourceCode] ?? "",
  });
}

function kindLabel(value: string): string {
  switch (value) {
    case "bank_account":
      return "Bank account";
    case "wallet":
      return "Tien trong vi";
    case "cash_box":
      return "Tien trong tu";
    case "reserve_cash":
      return "Tien du phong";
    case "gold":
      return "Vang";
    default:
      return value;
  }
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
</script>

<style scoped>
.jars-page {
  display: grid;
  gap: 1.25rem;
}

.jars-hero,
.jar-card,
.unassigned-panel {
  display: grid;
  gap: 1.25rem;
}

.hero-copy {
  max-width: 56rem;
  color: var(--tp-text-soft);
}

.hero-glossary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.85rem;
}

.jar-stats,
.jar-kpi-grid {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
}

.stat-card,
.jar-kpi-grid div {
  padding: 1rem;
  border-radius: 1rem;
  background: color-mix(in srgb, var(--tp-panel) 82%, white);
  border: 1px solid var(--tp-line);
}

.stat-card span,
.jar-kpi-grid span,
.assignment-copy span,
.assignment-copy small {
  display: block;
}

.stat-card span,
.jar-kpi-grid span,
.assignment-copy span {
  color: var(--tp-text-soft);
}

.stat-card strong,
.jar-kpi-grid strong,
.assignment-copy strong {
  font-size: 1.05rem;
}

.jars-layout {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  align-items: start;
}

.jar-form-panel,
.jar-list-section,
.jar-list {
  display: grid;
  gap: 1rem;
}

.jar-form-panel {
  align-self: start;
}

.panel-head,
.jar-card-head,
.assignment-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: start;
}

.jar-form {
  display: grid;
  gap: 0.9rem;
}

label {
  display: grid;
  gap: 0.35rem;
}

input,
textarea,
select,
button {
  font: inherit;
}

input,
textarea,
select {
  width: 100%;
  padding: 0.8rem 0.9rem;
  border-radius: 0.9rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-panel) 90%, white);
}

button {
  border: 0;
  border-radius: 0.85rem;
  padding: 0.85rem 1rem;
  background: var(--tp-text);
  color: white;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.secondary-button,
.ghost-button {
  background: transparent;
  color: var(--tp-text);
  border: 1px solid var(--tp-line);
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.checkbox input {
  width: auto;
}

.full-width {
  grid-column: 1 / -1;
}

.edit-form {
  padding-top: 1rem;
  border-top: 1px solid var(--tp-line);
}

.edit-actions,
.assignment-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.assignment-block {
  display: grid;
  gap: 0.85rem;
  padding-top: 1rem;
  border-top: 1px solid var(--tp-line);
}

.assignment-list {
  display: grid;
  gap: 0.75rem;
}

.assignment-row {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 320px);
  padding: 0.9rem 1rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--tp-bg) 72%, white);
  border: 1px solid var(--tp-line);
}

.assignment-copy {
  display: grid;
  gap: 0.2rem;
}

.jar-note,
.empty-inline {
  margin: 0;
  color: var(--tp-text-soft);
}

.helper-text,
.success-text,
.error-text {
  margin: 0;
}

@media (max-width: 980px) {
  .jars-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .assignment-row {
    grid-template-columns: 1fr;
  }

  .assignment-controls {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

<template>
  <section class="page settings-page">
    <header class="panel settings-hero">
      <div>
        <p class="eyebrow">Cài đặt</p>
        <h2>Điều chỉnh vận hành, kết nối dữ liệu và quy tắc tài chính</h2>
        <p class="hero-copy">
          Đây là trung tâm thiết lập vận hành: bạn có thể cấu hình nơi frontend gọi API, lưu thói quen nhập liệu,
          đồng bộ schema Google Sheets và quản lý các quy tắc chi phí cố định đang chi phối bảng điều khiển.
        </p>
        <div class="hero-glossary">
          <TermHintModal
            term="Schema sheet"
            summary="Schema sheet là cấu trúc cột chuẩn mà ứng dụng kỳ vọng trên Google Sheets."
            detail="Khi bấm cập nhật schema, hệ thống sẽ tạo sheet còn thiếu và đồng bộ lại hàng tiêu đề."
          />
          <TermHintModal
            term="Migration"
            summary="Migration ở đây là bước chuyển dữ liệu lịch sử từ cấu trúc cũ sang cấu trúc mới."
            detail="Luồng hiện tại chỉ tạo thêm Sources từ Jars legacy, không xóa dữ liệu cũ."
          />
          <TermHintModal
            term="Rule cố định"
            summary="Rule cố định là quy tắc mô tả một khoản chi lặp lại theo chu kỳ."
            detail="Chúng giúp dashboard đánh giá sức chịu tải chi phí cố định và cảnh báo khi nhịp chi vượt chuẩn."
          />
        </div>
      </div>

      <div class="settings-stats">
        <article class="stat-card">
          <span>API đang dùng</span>
          <strong>{{ currentApiBaseUrl }}</strong>
        </article>
        <article class="stat-card">
          <span>Actor mặc định</span>
          <strong>{{ preferencesForm.actorName }}</strong>
        </article>
        <article class="stat-card">
          <span>Chat source</span>
          <strong>{{ preferencesForm.chatSource }}</strong>
        </article>
        <article class="stat-card">
          <span>Fixed-cost rules</span>
          <strong>{{ rules.length }}</strong>
        </article>
      </div>
    </header>

    <div class="settings-layout">
      <div class="settings-stack">
        <article class="panel settings-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Kết nối</p>
              <h3>API Base URL</h3>
            </div>
            <span class="panel-kpi">Áp dụng ngay cho các request mới</span>
          </div>

          <form class="settings-form" @submit.prevent="saveApiBaseUrl">
            <label>
              <span>Địa chỉ backend</span>
              <input v-model.trim="apiBaseUrlForm" placeholder="http://127.0.0.1:8080" />
            </label>

            <div class="inline-actions">
              <button type="submit">Lưu địa chỉ</button>
              <button class="ghost-button" type="button" @click="resetApiBaseUrl">Khôi phục mặc định</button>
            </div>
          </form>

          <p v-if="apiMessage" class="success-text">{{ apiMessage }}</p>
        </article>

        <article class="panel settings-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Google Sheets</p>
              <h3>Schema và migration</h3>
            </div>
            <span class="panel-kpi">Cập nhật header và tách dữ liệu legacy</span>
          </div>

          <div class="admin-actions">
            <button :disabled="initializeSystemMutation.isPending.value" type="button" @click="runInitializeSystem">
              {{ initializeSystemMutation.isPending.value ? "Đang khởi tạo..." : "Khởi tạo hệ thống lần đầu" }}
            </button>
            <button :disabled="bootstrapMutation.isPending.value" type="button" @click="runBootstrap">
              {{ bootstrapMutation.isPending.value ? "Đang cập nhật schema..." : "Cập nhật sheet schema" }}
            </button>
            <button class="secondary-button" :disabled="seedDefaultJarsMutation.isPending.value" type="button" @click="runSeedDefaultJars">
              {{ seedDefaultJarsMutation.isPending.value ? "Đang tạo hũ mẫu..." : "Tạo 6 hũ mặc định" }}
            </button>
            <button class="ghost-button" :disabled="migrationPreviewMutation.isPending.value" type="button" @click="previewMigration">
              {{ migrationPreviewMutation.isPending.value ? "Đang xem trước..." : "Xem trước migration" }}
            </button>
            <button class="secondary-button" :disabled="migrationRunMutation.isPending.value" type="button" @click="runMigration">
              {{ migrationRunMutation.isPending.value ? "Đang migration..." : "Chạy migration dữ liệu cũ" }}
            </button>
          </div>

          <p class="helper-text">
            Migration hiện tại chỉ tạo thêm `Sources` từ các `Jars` legacy có số dư hoặc không phải `bucket`.
            Hệ thống không xóa dữ liệu cũ trong sheet `Jars`.
          </p>
          <p class="helper-text">
            `Khởi tạo hệ thống lần đầu` sẽ gộp cập nhật schema và tạo 6 hũ mặc định chỉ trong một lần bấm.
          </p>
          <p class="helper-text">
            Bộ 6 hũ mặc định gồm: Chi tiêu thiết yếu, Tự do tài chính, Giáo dục, Hưởng thụ, Tiết kiệm mục tiêu, Cho đi.
          </p>

          <p v-if="adminMessage" :class="adminMessageTone">{{ adminMessage }}</p>

          <div v-if="migrationSummary" class="migration-summary">
            <strong>{{ migrationSummary.title }}</strong>
            <span>
              Ứng viên: {{ migrationSummary.result.candidates }} · Tạo mới: {{ migrationSummary.result.created }} ·
              Bỏ qua: {{ migrationSummary.result.skipped }}
            </span>

            <ul v-if="migrationSummary.result.items.length > 0" class="migration-list">
              <li v-for="item in migrationSummary.result.items.slice(0, 6)" :key="`${item.jarCode}-${item.status}`">
                {{ item.jarCode }} -> {{ item.sourceCode }} · {{ item.status }} · {{ item.reason }}
              </li>
            </ul>
          </div>
        </article>

        <article class="panel settings-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Preference cá nhân</p>
              <h3>Nhập liệu nhanh</h3>
            </div>
            <span class="panel-kpi">Dùng lại ở dashboard chat</span>
          </div>

          <form class="settings-form" @submit.prevent="savePreferences">
            <label>
              <span>Tên actor mặc định</span>
              <input v-model.trim="preferencesForm.actorName" placeholder="web-user" />
            </label>

            <label>
              <span>Source mặc định</span>
              <input v-model.trim="preferencesForm.chatSource" placeholder="dashboard-chat" />
            </label>

            <button type="submit">Lưu preference</button>
          </form>

          <p v-if="preferencesMessage" class="success-text">{{ preferencesMessage }}</p>
        </article>

        <article class="panel settings-panel hint-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Gợi ý</p>
              <h3>Những gì trang này đang điều khiển</h3>
            </div>
          </div>

          <ul class="hint-list">
            <li>Fixed-cost rule ảnh hưởng đến dashboard summary và cách hệ thống đánh giá tải chi phí cố định.</li>
            <li>API Base URL giúp frontend trỏ sang backend khác mà không cần sửa mã hay rebuild.</li>
            <li>Preference actor/source được dùng lại khi bạn nhập giao dịch bằng chat ngay trên dashboard.</li>
          </ul>
        </article>
      </div>

      <section class="rules-section">
        <article class="panel settings-panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Ngưỡng và rule</p>
              <h3>Thêm fixed-cost rule</h3>
            </div>
            <span class="panel-kpi">Dùng cho đánh giá cấu trúc</span>
          </div>

          <form class="settings-form rule-form" @submit.prevent="submitCreateRule">
            <label>
              <span>Tên rule</span>
              <input v-model.trim="createRuleForm.name" placeholder="Tiền nhà" required />
            </label>

            <label>
              <span>Số tiền dự kiến</span>
              <input v-model.number="createRuleForm.expectedAmount" min="1" required type="number" />
            </label>

            <label>
              <span>Từ ngày</span>
              <input v-model.number="createRuleForm.windowStartDay" max="31" min="1" required type="number" />
            </label>

            <label>
              <span>Đến ngày</span>
              <input v-model.number="createRuleForm.windowEndDay" max="31" min="1" required type="number" />
            </label>

            <label>
              <span>Jar liên kết</span>
              <input v-model.trim="createRuleForm.linkedJarCode" list="jar-options" placeholder="NhaO" />
            </label>

            <label class="checkbox">
              <input v-model="createRuleForm.isActive" type="checkbox" />
              <span>Đang hoạt động</span>
            </label>

            <button :disabled="createRuleMutation.isPending.value" type="submit">
              {{ createRuleMutation.isPending.value ? "Đang lưu..." : "Tạo rule" }}
            </button>
          </form>

          <p v-if="ruleMessage" :class="ruleMessageTone">{{ ruleMessage }}</p>
        </article>

        <p v-if="rulesQuery.isLoading.value" class="panel">Đang tải fixed-cost rules...</p>
        <p v-else-if="rulesQuery.isError.value" class="panel error-text">
          {{ (rulesQuery.error.value as Error).message }}
        </p>
        <article v-else-if="rules.length === 0" class="panel empty-panel">
          <h3>Chưa có rule nào</h3>
          <p>Tạo fixed-cost rule đầu tiên để hệ thống hiểu khoản chi cố định nào cần được theo dõi theo khung ngày.</p>
        </article>

        <div v-else class="rules-list">
          <article v-for="rule in rules" :key="rule.name" class="panel rule-card">
            <div class="rule-card-head">
              <div>
                <p class="eyebrow">{{ rule.isActive ? "Đang hoạt động" : "Tạm tắt" }}</p>
                <h3>{{ rule.name }}</h3>
              </div>
              <button class="secondary-button" type="button" @click="toggleEditRule(rule)">
                {{ editingRuleName === rule.name ? "Đóng chỉnh sửa" : "Điều chỉnh" }}
              </button>
            </div>

            <dl class="rule-meta">
              <div>
                <dt>Số tiền dự kiến</dt>
                <dd>{{ formatCurrency(rule.expectedAmount) }}</dd>
              </div>
              <div>
                <dt>Cửa sổ ngày</dt>
                <dd>{{ rule.windowStartDay }} - {{ rule.windowEndDay }}</dd>
              </div>
              <div>
                <dt>Jar liên kết</dt>
                <dd>{{ rule.linkedJarCode || "Chưa gắn" }}</dd>
              </div>
            </dl>

            <form
              v-if="editingRuleName === rule.name && editRuleForm"
              class="settings-form rule-form edit-form"
              @submit.prevent="submitUpdateRule(rule.name)"
            >
              <label>
                <span>Tên rule</span>
                <input :value="rule.name" disabled />
              </label>

              <label>
                <span>Số tiền dự kiến</span>
                <input v-model.number="editRuleForm.expectedAmount" min="1" required type="number" />
              </label>

              <label>
                <span>Từ ngày</span>
                <input v-model.number="editRuleForm.windowStartDay" max="31" min="1" required type="number" />
              </label>

              <label>
                <span>Đến ngày</span>
                <input v-model.number="editRuleForm.windowEndDay" max="31" min="1" required type="number" />
              </label>

              <label>
                <span>Jar liên kết</span>
                <input v-model.trim="editRuleForm.linkedJarCode" list="jar-options" placeholder="NhaO" />
              </label>

              <label class="checkbox">
                <input v-model="editRuleForm.isActive" type="checkbox" />
                <span>Đang hoạt động</span>
              </label>

              <div class="inline-actions">
                <button :disabled="updateRuleMutation.isPending.value" type="submit">
                  {{ updateRuleMutation.isPending.value ? "Đang cập nhật..." : "Lưu điều chỉnh" }}
                </button>
                <button class="ghost-button" type="button" @click="clearRuleEditor">Hủy</button>
              </div>
            </form>
          </article>
        </div>
      </section>
    </div>

    <datalist id="jar-options">
      <option v-for="jar in jarsQuery.data.value?.items ?? []" :key="jar.code" :value="jar.code">
        {{ jar.name }}
      </option>
    </datalist>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { bootstrapSheets, initializeSystem, migrateLegacyJars, seedDefaultJars, type MigrationResult } from "@/api/admin";
import TermHintModal from "@/components/TermHintModal.vue";
import {
  createFixedCostRule,
  listFixedCostRules,
  updateFixedCostRule,
  type FixedCostRule,
} from "@/api/rules";
import { getApiBaseUrl, getStoredApiBaseUrl, setStoredApiBaseUrl } from "@/api/http";
import { listJars } from "@/api/jars";
import { formatCurrency } from "@/lib/formatCurrency";
import { loadUserPreferences, saveUserPreferences } from "@/lib/preferences";

type RuleForm = {
  name: string;
  expectedAmount: number;
  windowStartDay: number;
  windowEndDay: number;
  linkedJarCode: string;
  isActive: boolean;
};

type RuleEditForm = {
  expectedAmount: number;
  windowStartDay: number;
  windowEndDay: number;
  linkedJarCode: string;
  isActive: boolean;
};

const queryClient = useQueryClient();
const prefs = loadUserPreferences();

const apiBaseUrlForm = ref(getStoredApiBaseUrl() || getApiBaseUrl());
const apiMessage = ref("");
const adminMessage = ref("");
const adminMessageTone = ref("helper-text");
const preferencesForm = reactive({
  actorName: prefs.actorName,
  chatSource: prefs.chatSource,
});
const preferencesMessage = ref("");
const createRuleForm = reactive(defaultRuleForm());
const ruleMessage = ref("");
const ruleMessageTone = ref("helper-text");
const editingRuleName = ref("");
const editRuleForm = ref<RuleEditForm | null>(null);
const migrationSummary = ref<{ title: string; result: MigrationResult } | null>(null);

const rulesQuery = useQuery({
  queryKey: ["fixed-cost-rules"],
  queryFn: listFixedCostRules,
});

const jarsQuery = useQuery({
  queryKey: ["jars"],
  queryFn: listJars,
});

const rules = computed(() => rulesQuery.data.value?.items ?? []);
const currentApiBaseUrl = ref(getApiBaseUrl());

const createRuleMutation = useMutation({
  mutationFn: createFixedCostRule,
  onSuccess: async () => {
    Object.assign(createRuleForm, defaultRuleForm());
    ruleMessage.value = "Đã tạo fixed-cost rule.";
    ruleMessageTone.value = "success-text";
    await refreshRules();
  },
  onError: (error) => {
    ruleMessage.value = error instanceof Error ? error.message : "Không thể tạo rule";
    ruleMessageTone.value = "error-text";
  },
});

const updateRuleMutation = useMutation({
  mutationFn: ({ name, input }: { name: string; input: RuleEditForm }) => updateFixedCostRule(name, input),
  onSuccess: async () => {
    ruleMessage.value = "Đã cập nhật fixed-cost rule.";
    ruleMessageTone.value = "success-text";
    clearRuleEditor();
    await refreshRules();
  },
  onError: (error) => {
    ruleMessage.value = error instanceof Error ? error.message : "Không thể cập nhật rule";
    ruleMessageTone.value = "error-text";
  },
});

const bootstrapMutation = useMutation({
  mutationFn: bootstrapSheets,
  onSuccess: async () => {
    adminMessage.value = "Đã cập nhật sheet schema theo phiên bản hiện tại.";
    adminMessageTone.value = "success-text";
    await refreshOperations();
  },
  onError: (error) => {
    adminMessage.value = error instanceof Error ? error.message : "Không thể cập nhật sheet schema";
    adminMessageTone.value = "error-text";
  },
});

const initializeSystemMutation = useMutation({
  mutationFn: initializeSystem,
  onSuccess: async (result) => {
    adminMessage.value =
      `Đã khởi tạo hệ thống: schema sẵn sàng, tạo ${result.defaultJars.created} hũ mặc định, bỏ qua ${result.defaultJars.skipped} hũ đã tồn tại.`;
    adminMessageTone.value = "success-text";
    await refreshOperations();
  },
  onError: (error) => {
    adminMessage.value = error instanceof Error ? error.message : "Không thể khởi tạo hệ thống lần đầu";
    adminMessageTone.value = "error-text";
  },
});

const migrationPreviewMutation = useMutation({
  mutationFn: () => migrateLegacyJars(true),
  onSuccess: async (result) => {
    migrationSummary.value = {
      title: "Xem trước migration",
      result,
    };
    adminMessage.value = `Đã xem trước: ${result.candidates} ứng viên legacy jar.`;
    adminMessageTone.value = "success-text";
    await refreshOperations();
  },
  onError: (error) => {
    adminMessage.value = error instanceof Error ? error.message : "Không thể xem trước migration";
    adminMessageTone.value = "error-text";
  },
});

const migrationRunMutation = useMutation({
  mutationFn: () => migrateLegacyJars(false),
  onSuccess: async (result) => {
    migrationSummary.value = {
      title: "Kết quả migration",
      result,
    };
    adminMessage.value = `Đã tạo ${result.created} source mới từ dữ liệu cũ.`;
    adminMessageTone.value = "success-text";
    await refreshOperations();
  },
  onError: (error) => {
    adminMessage.value = error instanceof Error ? error.message : "Không thể migration dữ liệu cũ";
    adminMessageTone.value = "error-text";
  },
});

const seedDefaultJarsMutation = useMutation({
  mutationFn: seedDefaultJars,
  onSuccess: async (result) => {
    adminMessage.value = `Đã tạo ${result.created} hũ mặc định, bỏ qua ${result.skipped} hũ đã tồn tại.`;
    adminMessageTone.value = "success-text";
    await refreshOperations();
  },
  onError: (error) => {
    adminMessage.value = error instanceof Error ? error.message : "Không thể tạo bộ hũ mặc định";
    adminMessageTone.value = "error-text";
  },
});

function defaultRuleForm(): RuleForm {
  return {
    name: "",
    expectedAmount: 0,
    windowStartDay: 1,
    windowEndDay: 5,
    linkedJarCode: "",
    isActive: true,
  };
}

async function refreshRules() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ["fixed-cost-rules"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }),
    queryClient.invalidateQueries({ queryKey: ["dashboard-reports"] }),
  ]);
}

async function refreshOperations() {
  await Promise.all([
    refreshRules(),
    queryClient.invalidateQueries({ queryKey: ["jars"] }),
    queryClient.invalidateQueries({ queryKey: ["sources"] }),
    queryClient.invalidateQueries({ queryKey: ["assets-overview"] }),
  ]);
}

function saveApiBaseUrl() {
  setStoredApiBaseUrl(apiBaseUrlForm.value);
  apiBaseUrlForm.value = getStoredApiBaseUrl() || getApiBaseUrl();
  currentApiBaseUrl.value = getApiBaseUrl();
  apiMessage.value = "Đã lưu API Base URL cho các request tiếp theo.";
}

function resetApiBaseUrl() {
  setStoredApiBaseUrl("");
  apiBaseUrlForm.value = getApiBaseUrl();
  currentApiBaseUrl.value = getApiBaseUrl();
  apiMessage.value = "Đã quay về API Base URL mặc định từ môi trường.";
}

function runBootstrap() {
  adminMessage.value = "";
  bootstrapMutation.mutate();
}

function runInitializeSystem() {
  adminMessage.value = "";
  initializeSystemMutation.mutate();
}

function previewMigration() {
  adminMessage.value = "";
  migrationPreviewMutation.mutate();
}

function runMigration() {
  if (typeof window !== "undefined") {
    const confirmed = window.confirm(
      "Migration sẽ tạo thêm Sources từ các Jars legacy. Dữ liệu cũ trong Jars không bị xóa. Tiếp tục?",
    );
    if (!confirmed) {
      return;
    }
  }

  adminMessage.value = "";
  migrationRunMutation.mutate();
}

function runSeedDefaultJars() {
  adminMessage.value = "";
  seedDefaultJarsMutation.mutate();
}

function savePreferences() {
  const saved = saveUserPreferences({
    actorName: preferencesForm.actorName.trim() || "web-user",
    chatSource: preferencesForm.chatSource.trim() || "dashboard-chat",
  });
  preferencesForm.actorName = saved.actorName;
  preferencesForm.chatSource = saved.chatSource;
  preferencesMessage.value = "Đã lưu preference cá nhân.";
}

function submitCreateRule() {
  ruleMessage.value = "";
  createRuleMutation.mutate({ ...createRuleForm });
}

function toggleEditRule(rule: FixedCostRule) {
  if (editingRuleName.value === rule.name) {
    clearRuleEditor();
    return;
  }

  editingRuleName.value = rule.name;
  editRuleForm.value = {
    expectedAmount: rule.expectedAmount,
    windowStartDay: rule.windowStartDay,
    windowEndDay: rule.windowEndDay,
    linkedJarCode: rule.linkedJarCode || "",
    isActive: rule.isActive,
  };
}

function clearRuleEditor() {
  editingRuleName.value = "";
  editRuleForm.value = null;
}

function submitUpdateRule(ruleName: string) {
  if (!editRuleForm.value) {
    return;
  }

  updateRuleMutation.mutate({
    name: ruleName,
    input: { ...editRuleForm.value },
  });
}
</script>

<style scoped>
.settings-page {
  gap: 1.25rem;
}

.settings-hero {
  display: grid;
  gap: 1.2rem;
}

.settings-hero h2 {
  margin: 0.3rem 0 0.5rem;
  font-size: clamp(2rem, 3.6vw, 3.1rem);
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

.settings-stats {
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
  font-size: 1.02rem;
  overflow-wrap: anywhere;
}

.settings-layout {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 1rem;
}

.settings-stack,
.rules-section,
.rules-list {
  display: grid;
  gap: 1rem;
}

.settings-panel,
.rule-card {
  display: grid;
  gap: 1rem;
}

.panel-head,
.rule-card-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.panel-head h3,
.rule-card h3 {
  margin: 0.3rem 0 0;
  font-size: 1.3rem;
  letter-spacing: -0.03em;
}

.panel-kpi {
  color: var(--tp-muted);
  font-size: 0.88rem;
  font-weight: 700;
}

.settings-form {
  display: grid;
  gap: 0.9rem;
}

.admin-actions,
.migration-summary {
  display: grid;
  gap: 0.75rem;
}

.settings-form label {
  display: grid;
  gap: 0.35rem;
}

.settings-form span,
.rule-meta dt {
  color: var(--tp-muted);
  font-size: 0.85rem;
}

.settings-form input:not([type="checkbox"]),
.settings-form button,
.secondary-button,
.ghost-button {
  font: inherit;
}

.migration-list {
  margin: 0;
  padding-left: 1.2rem;
  color: var(--tp-muted);
}

.settings-form input:not([type="checkbox"]) {
  width: 100%;
  padding: 0.78rem 0.9rem;
  border-radius: 0.85rem;
  border: 1px solid var(--tp-line);
  background: color-mix(in srgb, var(--tp-surface) 92%, white);
  color: var(--tp-text);
}

.settings-form button,
.secondary-button,
.ghost-button {
  border: 0;
  border-radius: 0.9rem;
  padding: 0.85rem 1rem;
  cursor: pointer;
}

.settings-form button {
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

.inline-actions {
  display: flex;
  gap: 0.75rem;
}

.checkbox {
  display: flex;
  gap: 0.6rem;
  align-items: center;
}

.checkbox input {
  width: auto;
}

.hint-list {
  margin: 0;
  padding-left: 1.1rem;
  color: var(--tp-muted);
}

.hint-list li + li {
  margin-top: 0.5rem;
}

.empty-panel h3,
.empty-panel p,
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

.rule-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.8rem;
  margin: 0;
}

.rule-meta div {
  padding: 0.95rem 1rem;
  border-radius: 0.95rem;
  background: color-mix(in srgb, var(--tp-surface-alt) 78%, white);
  border: 1px solid color-mix(in srgb, var(--tp-line) 84%, transparent);
}

.rule-meta dt,
.rule-meta dd {
  margin: 0;
}

.rule-meta dd {
  margin-top: 0.3rem;
}

.edit-form {
  padding-top: 0.25rem;
  border-top: 1px solid color-mix(in srgb, var(--tp-line) 82%, transparent);
}

@media (max-width: 980px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .panel-head,
  .rule-card-head,
  .inline-actions {
    flex-direction: column;
  }
}
</style>

<template>
  <section class="page">
    <header>
      <p class="eyebrow">Giao dịch</p>
      <h2>Sổ cái giao dịch</h2>
    </header>

    <div class="layout">
      <article class="card">
        <h3>Thêm giao dịch</h3>
        <form class="form" @submit.prevent="submit">
          <label>
            <span>Loại</span>
            <select v-model="form.type">
              <option value="OUT">Chi tiêu</option>
              <option value="IN">Thu nhập</option>
              <option value="TRANSFER">Chuyển tiền</option>
            </select>
          </label>

          <label>
            <span>Số tiền</span>
            <input v-model.number="form.amount" type="number" min="1" required />
          </label>

          <label>
            <span>Mã hũ</span>
            <input v-model.trim="form.jarCode" list="jar-options" placeholder="HuongThu" />
          </label>

          <label>
            <span>Tên mục tiêu</span>
            <input v-model.trim="form.goalName" list="goal-options" placeholder="Mua xe SH" />
          </label>

          <label>
            <span>Tài khoản</span>
            <input v-model.trim="form.accountName" list="source-options" placeholder="VCB_Main" />
          </label>

          <label>
            <span>Ghi chú</span>
            <textarea v-model.trim="form.note" rows="3" placeholder="Ghi chú nhanh" />
          </label>

          <label class="checkbox">
            <input v-model="form.isFixed" type="checkbox" />
            <span>Chi phí cố định</span>
          </label>

          <button :disabled="mutation.isPending.value" type="submit">
            {{ mutation.isPending.value ? "Đang lưu..." : "Tạo giao dịch" }}
          </button>
        </form>

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

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </article>

      <article class="card">
        <div class="section-head">
          <h3>Giao dịch gần đây</h3>
          <button @click="refetch">Tải lại</button>
        </div>

        <p v-if="query.isLoading.value">Đang tải giao dịch...</p>
        <p v-else-if="query.isError.value" class="error">
          {{ (query.error.value as Error).message }}
        </p>
        <ul v-else class="list">
          <li v-for="item in query.data.value?.items ?? []" :key="item.id">
            <div>
              <strong>{{ typeLabel(item.type) }}</strong>
              <span>{{ item.note || "Không có ghi chú" }}</span>
            </div>
            <div class="meta">
              <span>{{ formatCurrency(item.amount, item.currency) }}</span>
              <span>{{ item.jarCode || item.goalName || "-" }}</span>
            </div>
          </li>
        </ul>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useMutation, useQuery, useQueryClient } from "@tanstack/vue-query";
import { listGoals } from "@/api/goals";
import { listJars } from "@/api/jars";
import { listSources } from "@/api/sources";
import { createTransaction, listTransactions } from "@/api/transactions";
import { formatCurrency } from "@/lib/formatCurrency";

const queryClient = useQueryClient();

const defaultForm = () => ({
  type: "OUT" as const,
  amount: 0,
  currency: "VND",
  jarCode: "",
  goalName: "",
  accountName: "",
  isFixed: false,
  note: "",
  source: "manual-web",
});

const form = reactive(defaultForm());
const errorMessage = ref("");

const query = useQuery({
  queryKey: ["transactions"],
  queryFn: listTransactions,
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

const mutation = useMutation({
  mutationFn: createTransaction,
  onSuccess: async () => {
    Object.assign(form, defaultForm());
    errorMessage.value = "";
    await Promise.all([
      query.refetch(),
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard-reports"] }),
      queryClient.invalidateQueries({ queryKey: ["assets-overview"] }),
    ]);
  },
  onError: (error) => {
    errorMessage.value = error instanceof Error ? error.message : "Tạo giao dịch thất bại";
  },
});

function refetch() {
  query.refetch();
}

function submit() {
  errorMessage.value = "";
  mutation.mutate({
    ...form,
  });
}

function typeLabel(type: "IN" | "OUT" | "TRANSFER"): string {
  switch (type) {
    case "IN":
      return "Thu";
    case "OUT":
      return "Chi";
    case "TRANSFER":
      return "Chuyển";
  }
}
</script>

<style scoped>
.layout {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(280px, 360px) 1fr;
}

.form {
  display: grid;
  gap: 0.9rem;
}

label {
  display: grid;
  gap: 0.35rem;
}

input,
select,
textarea,
button {
  font: inherit;
}

input,
select,
textarea {
  width: 100%;
  padding: 0.75rem 0.85rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(31, 41, 55, 0.12);
  background: rgba(255, 255, 255, 0.9);
}

button {
  border: 0;
  border-radius: 0.8rem;
  padding: 0.85rem 1rem;
  background: #1f2937;
  color: #f9fafb;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox input {
  width: auto;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.list {
  list-style: none;
  padding: 0;
  margin: 1rem 0 0;
  display: grid;
  gap: 0.75rem;
}

.list li {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1rem;
  border-radius: 0.8rem;
  background: rgba(255, 255, 255, 0.65);
}

.list strong,
.meta {
  display: block;
}

.meta {
  text-align: right;
}

.error {
  color: #b42318;
}

@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
</style>

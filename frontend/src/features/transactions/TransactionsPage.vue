<template>
  <section class="page">
    <header>
      <p class="eyebrow">Transactions</p>
      <h2>Ledger foundation</h2>
    </header>

    <div class="layout">
      <article class="card">
        <h3>Add transaction</h3>
        <form class="form" @submit.prevent="submit">
          <label>
            <span>Type</span>
            <select v-model="form.type">
              <option value="OUT">Expense</option>
              <option value="IN">Income</option>
              <option value="TRANSFER">Transfer</option>
            </select>
          </label>

          <label>
            <span>Amount</span>
            <input v-model.number="form.amount" type="number" min="1" required />
          </label>

          <label>
            <span>Jar code</span>
            <input v-model.trim="form.jarCode" placeholder="HuongThu" />
          </label>

          <label>
            <span>Goal name</span>
            <input v-model.trim="form.goalName" placeholder="Mua xe SH" />
          </label>

          <label>
            <span>Account</span>
            <input v-model.trim="form.accountName" placeholder="Wallet" />
          </label>

          <label>
            <span>Note</span>
            <textarea v-model.trim="form.note" rows="3" placeholder="Quick note" />
          </label>

          <label class="checkbox">
            <input v-model="form.isFixed" type="checkbox" />
            <span>Fixed cost</span>
          </label>

          <button :disabled="mutation.isPending.value" type="submit">
            {{ mutation.isPending.value ? "Saving..." : "Create transaction" }}
          </button>
        </form>

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </article>

      <article class="card">
        <div class="section-head">
          <h3>Recent transactions</h3>
          <button @click="refetch">Refresh</button>
        </div>

        <p v-if="query.isLoading.value">Loading transactions...</p>
        <p v-else-if="query.isError.value" class="error">
          {{ (query.error.value as Error).message }}
        </p>
        <ul v-else class="list">
          <li v-for="item in query.data.value?.items ?? []" :key="item.id">
            <div>
              <strong>{{ item.type }}</strong>
              <span>{{ item.note || "No note" }}</span>
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
import { useMutation, useQuery } from "@tanstack/vue-query";
import { createTransaction, listTransactions } from "@/api/transactions";
import { formatCurrency } from "@/lib/formatCurrency";

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

const mutation = useMutation({
  mutationFn: createTransaction,
  onSuccess: async () => {
    Object.assign(form, defaultForm());
    errorMessage.value = "";
    await query.refetch();
  },
  onError: (error) => {
    errorMessage.value = error instanceof Error ? error.message : "Create transaction failed";
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

import { createRouter, createWebHistory } from "vue-router";
import DashboardPage from "@/features/dashboard/DashboardPage.vue";
import TransactionsPage from "@/features/transactions/TransactionsPage.vue";
import ReviewPage from "@/features/review/ReviewPage.vue";
import GoalsPage from "@/features/goals/GoalsPage.vue";
import SettingsPage from "@/features/settings/SettingsPage.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: DashboardPage },
    { path: "/transactions", component: TransactionsPage },
    { path: "/review", component: ReviewPage },
    { path: "/goals", component: GoalsPage },
    { path: "/settings", component: SettingsPage },
  ],
});


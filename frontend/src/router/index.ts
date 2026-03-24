import { createRouter, createWebHistory } from "vue-router";
import CapturePage from "@/features/capture/CapturePage.vue";
import DashboardPage from "@/features/dashboard/DashboardPage.vue";
import DashboardDetailPage from "@/features/dashboard/DashboardDetailPage.vue";
import TransactionsPage from "@/features/transactions/TransactionsPage.vue";
import ReviewPage from "@/features/review/ReviewPage.vue";
import GoalsPage from "@/features/goals/GoalsPage.vue";
import SettingsPage from "@/features/settings/SettingsPage.vue";
import AssetsPage from "@/features/assets/AssetsPage.vue";
import JarsPage from "@/features/jars/JarsPage.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: CapturePage },
    { path: "/dashboard", component: DashboardPage },
    { path: "/dashboard/detail", component: DashboardDetailPage },
    { path: "/transactions", component: TransactionsPage },
    { path: "/review", component: ReviewPage },
    { path: "/jars", component: JarsPage },
    { path: "/goals", component: GoalsPage },
    { path: "/assets", component: AssetsPage },
    { path: "/settings", component: SettingsPage },
  ],
});

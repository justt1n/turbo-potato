import { createApp } from "vue";
import { createPinia } from "pinia";
import { VueQueryPlugin } from "@tanstack/vue-query";
import App from "./app/App.vue";
import { router } from "./router";
import { applyPalette } from "./app/theme";
import "./styles.css";

applyPalette("springRadar");

const app = createApp(App);

app.use(createPinia());
app.use(VueQueryPlugin);
app.use(router);
app.mount("#app");

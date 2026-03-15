<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark"></span>
        <div>
          <p>Turbo Potato</p>
          <small>Personal Life OS</small>
        </div>
      </div>
      <nav>
        <RouterLink to="/">Dashboard</RouterLink>
        <RouterLink to="/transactions">Transactions</RouterLink>
        <RouterLink to="/review">Review</RouterLink>
        <RouterLink to="/goals">Goals</RouterLink>
        <RouterLink to="/settings">Settings</RouterLink>
      </nav>
    </aside>

    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 240px 1fr;
  background:
    radial-gradient(circle at top left, color-mix(in srgb, var(--tp-accent) 28%, transparent), transparent 24%),
    radial-gradient(circle at bottom right, color-mix(in srgb, var(--tp-danger) 20%, transparent), transparent 20%),
    linear-gradient(180deg, var(--tp-bg) 0%, #f7fbf4 55%, #f4f6f3 100%);
  color: var(--tp-text);
}

.sidebar {
  padding: 2rem 1.25rem;
  border-right: 1px solid var(--tp-line);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--tp-text) 98%, black) 0%, color-mix(in srgb, var(--tp-text) 90%, #111) 100%);
  color: #f7faf7;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 1.75rem;
}

.brand-mark {
  width: 0.9rem;
  height: 3rem;
  border-radius: 0.3rem;
  background: linear-gradient(180deg, var(--tp-accent) 0%, var(--tp-danger) 100%);
  box-shadow: 0 8px 24px color-mix(in srgb, var(--tp-danger) 34%, transparent);
}

.brand p,
.brand small {
  margin: 0;
}

.brand p {
  font-size: 1.2rem;
  font-weight: 700;
}

.brand small {
  color: rgba(247, 250, 247, 0.64);
}

.sidebar nav {
  display: grid;
  gap: 0.75rem;
}

.sidebar a {
  color: inherit;
  text-decoration: none;
  padding: 0.85rem 0.95rem;
  border-radius: 0.55rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-size: 0.78rem;
  font-weight: 700;
}

.sidebar a.router-link-active {
  background: linear-gradient(135deg, var(--tp-accent) 0%, color-mix(in srgb, var(--tp-accent-soft) 72%, white) 100%);
  color: var(--tp-text);
  border-color: transparent;
  box-shadow: 0 12px 22px color-mix(in srgb, var(--tp-accent) 26%, transparent);
}

.content {
  padding: 2rem;
}

@media (max-width: 800px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    border-right: 0;
    border-bottom: 1px solid rgba(31, 41, 55, 0.08);
  }
}
</style>

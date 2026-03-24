<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark"></span>
        <div>
          <p>Turbo Potato</p>
          <small>Trung tâm tài chính cá nhân</small>
        </div>
      </div>
      <nav>
        <RouterLink to="/">Nhập liệu</RouterLink>
        <RouterLink to="/dashboard">Tổng quan</RouterLink>
        <RouterLink to="/transactions">Giao dịch</RouterLink>
        <RouterLink to="/review">Kiểm duyệt</RouterLink>
        <RouterLink to="/jars">Hũ</RouterLink>
        <RouterLink to="/goals">Mục tiêu</RouterLink>
        <RouterLink to="/assets">Nguồn tiền</RouterLink>
        <RouterLink to="/settings">Cài đặt</RouterLink>
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
  grid-template-columns: 228px 1fr;
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.18), transparent 22%),
    radial-gradient(circle at bottom left, rgba(241, 220, 198, 0.18), transparent 26%),
    radial-gradient(circle at right, rgba(179, 223, 215, 0.2), transparent 30%);
  color: var(--tp-text);
}

.sidebar {
  position: sticky;
  top: 0;
  min-height: 100vh;
  padding: 1.8rem 1.05rem;
  border-right: 1px solid rgba(255, 255, 255, 0.28);
  background:
    linear-gradient(180deg, rgba(124, 174, 138, 0.36) 0%, rgba(168, 210, 183, 0.22) 100%);
  color: var(--tp-text);
  backdrop-filter: blur(14px) saturate(116%);
  -webkit-backdrop-filter: blur(14px) saturate(116%);
  transition: background 220ms ease, border-color 220ms ease;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    10px 0 32px rgba(80, 104, 86, 0.08);
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  margin-bottom: 1.5rem;
}

.brand-mark {
  width: 0.5rem;
  height: 2.6rem;
  border-radius: 0.18rem;
  background: linear-gradient(180deg, #ffffff 0%, #d1fae5 100%);
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.22);
}

.brand p,
.brand small {
  margin: 0;
}

.brand p {
  font-size: 1.26rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.brand small {
  color: var(--tp-muted);
}

.sidebar nav {
  display: grid;
  gap: 0.35rem;
}

.sidebar a {
  color: inherit;
  text-decoration: none;
  padding: 0.82rem 0.95rem;
  border-radius: 0.7rem;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid transparent;
  letter-spacing: 0.01em;
  font-size: 0.92rem;
  font-weight: 700;
  color: rgba(35, 53, 42, 0.84);
  transition:
    transform 150ms ease,
    background 180ms ease,
    color 180ms ease,
    border-color 180ms ease,
    box-shadow 220ms ease;
}

.sidebar a:hover {
  transform: translateX(3px);
  background: rgba(255, 255, 255, 0.18);
  color: var(--tp-text);
  border-color: rgba(255, 255, 255, 0.2);
}

.sidebar a.router-link-active {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.86) 0%, rgba(247, 252, 249, 0.72) 100%);
  color: var(--tp-text);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.74),
    0 14px 28px rgba(72, 99, 81, 0.12);
}

.content {
  padding: 1.9rem 2.5rem 2.5rem;
}

@media (max-width: 800px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    min-height: auto;
    border-right: 0;
    border-bottom: 1px solid var(--tp-line);
  }
}
</style>

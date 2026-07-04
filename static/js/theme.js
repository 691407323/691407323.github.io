/* M-01: 暗色模式主题切换 + Mermaid 主题同步（为 M-09 预留） */
(function() {
  const KEY = 'blog-theme';
  const root = document.documentElement;

  function init() {
    const saved = localStorage.getItem(KEY);
    if (saved) { root.setAttribute('data-theme', saved); return saved; }
    const dark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme', dark ? 'dark' : 'light');
    return dark ? 'dark' : 'light';
  }

  const current = init();
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.textContent = current === 'dark' ? '☼' : '☽';
    btn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem(KEY, next);
      btn.textContent = next === 'dark' ? '☼' : '☽';
      /* M-09: Mermaid 主题同步 */
      if (typeof mermaid !== 'undefined' && mermaid.run) {
        mermaid.run({ theme: next === 'dark' ? 'dark' : 'default' });
      }
    });
  }

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem(KEY)) {
      root.setAttribute('data-theme', e.matches ? 'dark' : 'light');
      if (btn) btn.textContent = e.matches ? '☼' : '☽';
    }
  });
})();

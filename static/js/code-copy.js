/* M-02: 代码块一键复制 — 含 Clipboard API fallback */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.codehilite').forEach(block => {
    const btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.textContent = '复制';
    btn.setAttribute('aria-label', '复制代码');

    btn.addEventListener('click', async () => {
      const code = block.querySelector('code');
      if (!code) return;
      try {
        await navigator.clipboard.writeText(code.textContent);
      } catch (_) {
        /* Fallback: 兼容 file:// 协议 */
        const ta = document.createElement('textarea');
        ta.value = code.textContent;
        ta.style.cssText = 'position:fixed;opacity:0;left:-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      btn.textContent = '已复制 ✓';
      setTimeout(() => btn.textContent = '复制', 2000);
    });

    block.style.position = 'relative';
    block.appendChild(btn);
  });
});

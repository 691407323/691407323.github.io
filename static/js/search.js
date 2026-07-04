/* M-11: 站内搜索 — FlexSearch 轻量全文搜索 */
let idxObj = null;

async function loadIndex() {
  const res = await fetch('/search-index.json');
  const data = await res.json();
  const idx = new FlexSearch.Index({
    tokenize: 'forward',
    resolution: 9,
    context: { resolution: 2, depth: 1 }
  });
  data.forEach(d => idx.add(d.slug, d.title + ' ' + d.content));
  return { idx, data };
}

function renderResults(results, data, el) {
  if (!results.length) {
    el.innerHTML = '<p style="color:var(--text-secondary)">未找到相关文章</p>';
    return;
  }
  el.innerHTML = results.map(slug => {
    const d = data.find(x => x.slug === slug);
    if (!d) return '';
    return '<article class="post" style="padding:16px 0; border-bottom:1px solid var(--border-color);">' +
      '<h3><a href="/posts/' + d.slug + '.html" style="color:var(--text-primary); text-decoration:none;">' + d.title + '</a></h3>' +
      '<p class="post-meta">' + d.date + (d.tags.length ? ' · ' + d.tags.join(', ') : '') + '</p>' +
      '<p style="color:var(--text-secondary);">' + d.excerpt + '...</p>' +
    '</article>';
  }).join('');
}

function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

document.addEventListener('DOMContentLoaded', async () => {
  const input = document.getElementById('search-input');
  const resultsDiv = document.getElementById('search-results');
  const statusDiv = document.getElementById('search-status');
  if (!input) return;

  try {
    idxObj = await loadIndex();
  } catch (_) {
    resultsDiv.innerHTML = '<p style="color:#c00;">搜索索引加载失败，请刷新页面重试。</p>';
    return;
  }

  const doSearch = debounce(q => {
    const qTrim = q.trim();
    if (!qTrim) { resultsDiv.innerHTML = ''; statusDiv.textContent = ''; return; }
    const r = idxObj.idx.search(qTrim);
    statusDiv.textContent = r.length + ' 条结果';
    // 标题命中优先排序
    const titleHits = r.filter(s => {
      const d = idxObj.data.find(x => x.slug === s);
      return d && d.title.toLowerCase().includes(qTrim.toLowerCase());
    });
    renderResults(titleHits.concat(r.filter(s => !titleHits.includes(s))), idxObj.data, resultsDiv);
  }, 200);

  input.addEventListener('input', e => doSearch(e.target.value));
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const r = idxObj.idx.search(input.value.trim());
      if (r.length) location.href = '/posts/' + r[0] + '.html';
    }
  });
});

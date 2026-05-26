const state = {
  items: [],
  query: '',
  source: 'all',
  character: 'all',
};

const itemsEl = document.querySelector('#items');
const emptyEl = document.querySelector('#empty');
const generatedEl = document.querySelector('#generated');
const countEl = document.querySelector('#item-count');
const searchEl = document.querySelector('#search');
const sourceEl = document.querySelector('#source-filter');
const characterEl = document.querySelector('#character-filter');

const sourceLabels = {
  gashapon: 'Bandai Gashapon',
  ichiban_kuji: 'Ichiban Kuji',
  takaratomy_arts: 'Takara Tomy Arts',
  qualia: 'Qualia',
  ken_elephant: 'Ken Elephant',
};

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;',
  }[char]));
}

function formatDate(value) {
  if (!value) return '갱신 시간 알 수 없음';
  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function option(value, label) {
  const el = document.createElement('option');
  el.value = value;
  el.textContent = label;
  return el;
}

function populateFilters(items) {
  const sources = [...new Set(items.map((item) => item.source).filter(Boolean))].sort();
  const characters = [...new Set(items.map((item) => item.character).filter(Boolean))].sort();
  for (const source of sources) sourceEl.append(option(source, sourceLabels[source] || source));
  for (const character of characters) characterEl.append(option(character, character));
}

function displayValue(item, field) {
  return item[`${field}_ko`] || item[field];
}

function matches(item) {
  const haystack = [
    item.title,
    item.title_ko,
    item.character,
    item.keyword,
    item.source,
    item.release_text,
    item.release_text_ko,
    item.status_text,
    item.status_text_ko,
    item.price,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
  return (!state.query || haystack.includes(state.query.toLowerCase()))
    && (state.source === 'all' || item.source === state.source)
    && (state.character === 'all' || item.character === state.character);
}

function render() {
  const items = state.items.filter(matches);
  countEl.textContent = items.length.toLocaleString('ko-KR');
  emptyEl.hidden = items.length > 0;
  itemsEl.innerHTML = items.map((item) => {
    const title = displayValue(item, 'title');
    const releaseText = displayValue(item, 'release_text');
    const statusText = displayValue(item, 'status_text');
    return `
    <article class="card">
      ${item.image_url ? `<img class="thumb" src="${escapeHtml(item.image_url)}" alt="" loading="lazy" />` : ''}
      <div class="card-body">
        <div class="badges">
          <span class="badge">${escapeHtml(sourceLabels[item.source] || item.source)}</span>
          <span class="badge">${escapeHtml(item.character)}</span>
        </div>
        <h2>${escapeHtml(title)}</h2>
        <p class="meta">
          ${releaseText ? `발매: ${escapeHtml(releaseText)}<br />` : ''}
          ${statusText ? `판매: ${escapeHtml(statusText)}<br />` : ''}
          ${item.price ? `가격: ${escapeHtml(item.price)}<br />` : ''}
          검색어: ${escapeHtml(item.keyword)}
          ${item.title_ko && item.title_ko !== item.title ? `<br /><span class="original-title">원문: ${escapeHtml(item.title)}</span>` : ''}
        </p>
        <a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">공식 페이지 보기 →</a>
      </div>
    </article>
  `;
  }).join('');
}

async function boot() {
  try {
    const response = await fetch('data/releases.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    state.items = data.items || [];
    generatedEl.textContent = `마지막 갱신: ${formatDate(data.generated_at)} · 총 ${data.count ?? state.items.length}개`;
    populateFilters(state.items);
    render();
  } catch (error) {
    generatedEl.textContent = `데이터를 불러오지 못했습니다: ${error.message}`;
    emptyEl.hidden = false;
  }
}

searchEl.addEventListener('input', (event) => { state.query = event.target.value.trim(); render(); });
sourceEl.addEventListener('change', (event) => { state.source = event.target.value; render(); });
characterEl.addEventListener('change', (event) => { state.character = event.target.value; render(); });

boot();

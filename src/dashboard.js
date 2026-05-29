export const sourceLabels = {
  gashapon: 'Bandai Gashapon',
  ichiban_kuji: 'Ichiban Kuji',
  takaratomy_arts: 'Takara Tomy Arts',
  qualia: 'Qualia',
  ken_elephant: 'Ken Elephant',
  kitan_club: 'Kitan Club',
  toys_cabin: 'Toys Cabin',
  rement: 'Re-Ment',
};

export function getDisplayValue(item, field) {
  return item?.[`${field}_ko`] || item?.[field] || '';
}

export function getFilterOptions(items) {
  return {
    sources: [...new Set(items.map((item) => item.source).filter(Boolean))].sort(),
    characters: [...new Set(items.map((item) => item.character).filter(Boolean))].sort(),
  };
}

function searchableText(item) {
  return [
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
}

export function filterItems(items, filters) {
  const query = filters.query.trim().toLowerCase();
  const selectedSources = filters.sources || (filters.source && filters.source !== 'all' ? [filters.source] : []);
  return items.filter((item) => {
    return (!query || searchableText(item).includes(query))
      && (selectedSources.length === 0 || selectedSources.includes(item.source))
      && (filters.character === 'all' || item.character === filters.character);
  });
}

export function formatDate(value) {
  if (!value) return '갱신 시간 알 수 없음';
  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function formatGeneratedText(data, items) {
  return `마지막 갱신: ${formatDate(data.generated_at)} · 총 ${data.count ?? items.length}개`;
}

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

function dateFromParts(year, month, day) {
  return new Date(Number(year), Number(month) - 1, Number(day));
}

function lastDayOfMonth(year, month) {
  return new Date(Number(year), Number(month), 0).getDate();
}

export function parseReleaseDate(item) {
  const value = [item?.release_text, item?.release_text_ko].filter(Boolean).join(' ');
  if (!value) return null;

  const exactMatch = value.match(/(\d{4})\s*[年년]\s*(\d{1,2})\s*[月월]\s*(\d{1,2})\s*[日일]?/);
  if (exactMatch) return dateFromParts(exactMatch[1], exactMatch[2], exactMatch[3]);

  const monthMatch = value.match(/(\d{4})\s*[年년]\s*(\d{1,2})\s*[月월]\s*(上旬|中旬|下旬|상순|중순|하순)?/);
  if (!monthMatch) return null;

  const [, year, month, period] = monthMatch;
  let day = 1;
  if (period === '上旬' || period === '상순') day = 10;
  if (period === '中旬' || period === '중순') day = 20;
  if (period === '下旬' || period === '하순') day = lastDayOfMonth(year, month);
  return dateFromParts(year, month, day);
}

export function sortItemsByReleaseDate(items) {
  return [...items].sort((left, right) => {
    const leftDate = parseReleaseDate(left);
    const rightDate = parseReleaseDate(right);

    if (leftDate && rightDate) return rightDate - leftDate;
    if (leftDate) return -1;
    if (rightDate) return 1;
    return 0;
  });
}

function startOfLocalDate(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function formatReleaseDday(item, today = new Date()) {
  const releaseDate = parseReleaseDate(item);
  if (!releaseDate) return '';

  const daysUntilRelease = Math.ceil(
    (startOfLocalDate(releaseDate) - startOfLocalDate(today)) / 86_400_000,
  );
  if (daysUntilRelease < 0) return '';
  if (daysUntilRelease === 0) return 'D-Day';
  return `D-${daysUntilRelease}`;
}

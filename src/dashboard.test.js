import { describe, expect, it } from 'vitest';
import { filterItems, formatGeneratedText, getDisplayValue, getFilterOptions, sourceLabels } from './dashboard';

const items = [
  {
    source: 'gashapon',
    character: '짱구',
    keyword: 'クレヨンしんちゃん',
    title: 'Crayon Shinchan Capsule',
    title_ko: '짱구 캡슐토이',
    release_text: '2026年5月',
    release_text_ko: '2026년 5월',
    status_text: '発売中',
    price: '300円',
  },
  {
    source: 'ichiban_kuji',
    character: '산리오',
    keyword: 'サンリオ',
    title: 'Sanrio Lottery',
    title_ko: '산리오 복권',
    release_text: '2026年6月',
    status_text_ko: '판매 예정',
  },
];

describe('dashboard helpers', () => {
  it('uses localized labels and values when available', () => {
    expect(sourceLabels.gashapon).toBe('Bandai Gashapon');
    expect(sourceLabels.takaratomy_arts).toBe('Takara Tomy Arts');
    expect(sourceLabels.qualia).toBe('Qualia');
    expect(sourceLabels.ken_elephant).toBe('Ken Elephant');
    expect(sourceLabels.kitan_club).toBe('Kitan Club');
    expect(sourceLabels.toys_cabin).toBe('Toys Cabin');
    expect(sourceLabels.rement).toBe('Re-Ment');
    expect(getDisplayValue(items[0], 'title')).toBe('짱구 캡슐토이');
    expect(getDisplayValue(items[0], 'release_text')).toBe('2026년 5월');
    expect(getDisplayValue(items[1], 'release_text')).toBe('2026年6月');
  });

  it('builds sorted source and character filter options', () => {
    expect(getFilterOptions(items)).toEqual({
      sources: ['gashapon', 'ichiban_kuji'],
      characters: ['산리오', '짱구'],
    });
  });

  it('filters by query, multiple selected sources, and character across localized fields', () => {
    expect(filterItems(items, { query: '복권', sources: [], character: 'all' })).toEqual([items[1]]);
    expect(filterItems(items, { query: '300', sources: ['gashapon'], character: '짱구' })).toEqual([items[0]]);
    expect(filterItems(items, { query: '', sources: ['gashapon', 'ichiban_kuji'], character: 'all' })).toEqual(items);
    expect(filterItems(items, { query: '짱구', sources: ['ichiban_kuji'], character: 'all' })).toEqual([]);
  });

  it('formats generated metadata in Korean with stable count fallback', () => {
    expect(formatGeneratedText({ generated_at: '2026-05-26T12:30:00+09:00', count: 2 }, items)).toContain('총 2개');
    expect(formatGeneratedText({}, items)).toBe('마지막 갱신: 갱신 시간 알 수 없음 · 총 2개');
  });
});

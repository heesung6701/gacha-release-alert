import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from './App';

const payload = {
  generated_at: '2026-05-26T12:30:00+09:00',
  count: 2,
  items: [
    {
      source: 'gashapon',
      character: '짱구',
      keyword: 'クレヨンしんちゃん',
      title: 'Crayon Shinchan Capsule',
      title_ko: '짱구 캡슐토이',
      release_text_ko: '2026년 5월',
      status_text_ko: '판매중',
      price: '300円',
      url: 'https://example.com/shinchan',
    },
    {
      source: 'ichiban_kuji',
      character: '산리오',
      keyword: 'サンリオ',
      title: 'Sanrio Lottery',
      title_ko: '산리오 복권',
      release_text_ko: '2026년 6월',
      status_text_ko: '판매 예정',
      url: 'https://example.com/sanrio',
    },
  ],
};

afterEach(() => {
  vi.restoreAllMocks();
});

describe('App', () => {
  it('loads release data and renders searchable cards', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => payload }));

    render(<App />);

    expect(screen.getByText('데이터를 불러오는 중…')).toBeInTheDocument();
    await screen.findByRole('heading', { name: '짱구 캡슐토이' });

    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText(/마지막 갱신:/)).toHaveTextContent('총 2개');
    expect(screen.getByLabelText('소스 필터')).toHaveDisplayValue('전체 소스');
    expect(screen.getByRole('heading', { name: '산리오 복권' })).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText('상품명, 캐릭터, 키워드 검색'), {
      target: { value: '짱구' },
    });

    expect(screen.getByRole('heading', { name: '짱구 캡슐토이' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: '산리오 복권' })).not.toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('shows an error when release data cannot be loaded', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));

    render(<App />);

    await waitFor(() => expect(screen.getByText(/데이터를 불러오지 못했습니다: HTTP 404/)).toBeInTheDocument());
    expect(screen.getByText('조건에 맞는 항목이 없습니다.')).toBeInTheDocument();
  });
});

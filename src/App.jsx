import { useEffect, useMemo, useState } from 'react';
import {
  filterItems,
  formatGeneratedText,
  getDisplayValue,
  getFilterOptions,
  sourceLabels,
} from './dashboard';
import './styles.css';

const initialFilters = {
  query: '',
  sources: [],
  character: 'all',
};

function Card({ item }) {
  const title = getDisplayValue(item, 'title');
  const releaseText = getDisplayValue(item, 'release_text');
  const statusText = getDisplayValue(item, 'status_text');

  return (
    <article className="card">
      {item.image_url ? <img className="thumb" src={item.image_url} alt="" loading="lazy" /> : null}
      <div className="card-body">
        <div className="badges">
          <span className="badge">{sourceLabels[item.source] || item.source}</span>
          <span className="badge">{item.character}</span>
        </div>
        <h2>{title}</h2>
        <p className="meta">
          {releaseText ? <>{`발매: ${releaseText}`}<br /></> : null}
          {statusText ? <>{`판매: ${statusText}`}<br /></> : null}
          {item.price ? <>{`가격: ${item.price}`}<br /></> : null}
          검색어: {item.keyword}
          {item.title_ko && item.title_ko !== item.title ? (
            <>
              <br />
              <span className="original-title">원문: {item.title}</span>
            </>
          ) : null}
        </p>
        <a href={item.url} target="_blank" rel="noreferrer">공식 페이지 보기 →</a>
      </div>
    </article>
  );
}

function App() {
  const [items, setItems] = useState([]);
  const [filters, setFilters] = useState(initialFilters);
  const [generatedText, setGeneratedText] = useState('데이터를 불러오는 중…');
  const [error, setError] = useState('');

  useEffect(() => {
    let ignore = false;

    async function loadData() {
      try {
        const response = await fetch('data/releases.json', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const releaseItems = data.items || [];
        if (!ignore) {
          setItems(releaseItems);
          setGeneratedText(formatGeneratedText(data, releaseItems));
        }
      } catch (loadError) {
        if (!ignore) {
          setError(`데이터를 불러오지 못했습니다: ${loadError.message}`);
          setGeneratedText(`데이터를 불러오지 못했습니다: ${loadError.message}`);
        }
      }
    }

    loadData();
    return () => {
      ignore = true;
    };
  }, []);

  const options = useMemo(() => getFilterOptions(items), [items]);
  const visibleItems = useMemo(() => filterItems(items, filters), [items, filters]);
  const isEmpty = visibleItems.length === 0;

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
  }

  function toggleSource(source) {
    setFilters((current) => {
      const selectedSources = current.sources.length ? current.sources : options.sources;
      const nextSources = selectedSources.includes(source)
        ? selectedSources.filter((selectedSource) => selectedSource !== source)
        : [...selectedSources, source];
      return {
        ...current,
        sources: nextSources.length === options.sources.length ? [] : nextSources,
      };
    });
  }

  function isSourceSelected(source) {
    return filters.sources.length === 0 || filters.sources.includes(source);
  }

  return (
    <>
      <header className="hero">
        <div>
          <p className="eyebrow">Bandai Gashapon / Ichiban Kuji</p>
          <h1>가챠 발매 알리미</h1>
          <p className="subtitle">짱구·산리오 등 관심 캐릭터의 공식 발매 정보를 한눈에 봅니다.</p>
        </div>
        <div className="stats" aria-live="polite">
          <span>{visibleItems.length.toLocaleString('ko-KR')}</span>
          <small>개 항목</small>
        </div>
      </header>

      <main>
        <section className="toolbar" aria-label="필터">
          <input
            type="search"
            placeholder="상품명, 캐릭터, 키워드 검색"
            autoComplete="off"
            value={filters.query}
            onChange={(event) => updateFilter('query', event.target.value.trim())}
          />
          <fieldset className="source-filter" aria-label="소스 필터">
            <legend>소스 필터</legend>
            {options.sources.map((source) => (
              <label key={source} className="check-option">
                <input
                  type="checkbox"
                  checked={isSourceSelected(source)}
                  onChange={() => toggleSource(source)}
                />
                <span>{sourceLabels[source] || source}</span>
              </label>
            ))}
          </fieldset>
          <select
            aria-label="캐릭터 필터"
            value={filters.character}
            onChange={(event) => updateFilter('character', event.target.value)}
          >
            <option value="all">전체 캐릭터</option>
            {options.characters.map((character) => (
              <option key={character} value={character}>{character}</option>
            ))}
          </select>
        </section>

        <p className="generated">{generatedText}</p>
        <section className="grid" aria-live="polite">
          {visibleItems.map((item) => <Card key={`${item.source}:${item.url}:${item.keyword}`} item={item} />)}
        </section>
        {isEmpty ? <p className="empty">조건에 맞는 항목이 없습니다.</p> : null}
        {error ? null : null}
      </main>

      <footer>
        GitHub Actions가 주기적으로 데이터를 가져와 갱신합니다.
      </footer>
    </>
  );
}

export default App;

import { describe, expect, it } from 'vitest';
import config from './vite.config';

describe('Vite GitHub Pages config', () => {
  it('uses relative asset paths so the repo subpath is not blank on Pages', () => {
    expect(config.base).toBe('./');
  });
});

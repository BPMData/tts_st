// The two prompts AllHail uses: Quick look (describe) and Full detail (detail).
// The versions under test live in variants.ts; CURRENT picks the one the app uses.
// Re-test with the bake-off before changing it.

import { VARIANTS } from './variants.ts';

export type PromptName = 'describe' | 'detail';

export const CURRENT = 'v5';
export const PROMPTS = VARIANTS[CURRENT];

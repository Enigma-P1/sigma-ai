// October 21, 2026 security floors. Keep provider runtime verification separate from builds.
import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const pkg = JSON.parse(readFileSync(resolve(root, 'package.json'), 'utf8'));
const parse = value => /^v?(\d+)\.(\d+)\.(\d+)$/.exec(value)?.slice(1).map(Number);
const atLeast = (value, floor) => {
  const current = parse(value), minimum = parse(floor);
  if (!current || current[0] !== minimum[0]) return false;
  return current[1] > minimum[1] || current[1] === minimum[1] && current[2] >= minimum[2];
};
const minimumNode = { 22: '22.23.4', 24: '24.22.1', 26: '26.12.1' }[parse(process.version)?.[0]];
if (!minimumNode || !atLeast(process.version, minimumNode)) throw new Error(`Unpatched Node ${process.version}; use 22.23.4+, 24.22.1+, or 26.12.1+ on the corresponding supported major.`);
const deps = { ...pkg.dependencies, ...pkg.devDependencies };
for (const name of ['next', 'astro', 'sharp', 'vite', 'vitest']) {
  if (!deps[name]) continue;
  const installed = JSON.parse(readFileSync(resolve(root, 'node_modules', name, 'package.json'), 'utf8')).version;
  const major = parse(installed)?.[0];
  const floor = { next: {15: '15.5.28', 16: '16.4.1'}, astro: {7: '7.4.2'}, sharp: {0: '0.35.5'}, vite: {7: '7.3.7', 8: '8.3.5'}, vitest: {4: '4.1.12', 5: '5.0.5'} }[name][major];
  if (!floor || !atLeast(installed, floor)) throw new Error(`Unreviewed security baseline: ${name}@${installed}`);
}
console.info(`[security] Node ${process.version} and installed framework/tool versions meet the October 2026 baseline`);

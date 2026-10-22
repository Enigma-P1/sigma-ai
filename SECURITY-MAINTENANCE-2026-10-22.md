# October 2026 security maintenance

Checked against the October 14 Next.js advisories, October 21 Node.js security release, and the npm advisory database. Patched framework and tool dependencies are locked; each package has a reviewed security floor and a reproducible Node version. The build gate checks the installed versions rather than trusting manifest ranges.

Desktop TypeScript and Vite production build passed; full npm audit is clean. Pinned direct Python dependencies also checked, with no reported findings (not a complete transitive/environment audit).

Static deployments do not run a request-time Node/PHP server. A repository audit does not establish the patch level of a provider-managed runtime or an unrelated service. No PHP source or Composer manifest was found in the repository inventory.

Primary references:
- https://nextjs.org/blog/nextjs-security-update-october-14-2026
- https://nodejs.org/en/blog/vulnerability/october-2026-security-releases
- https://github.com/withastro/astro/security/advisories/GHSA-26w7-cxv4-gfx2
- https://github.com/lovell/sharp/security/advisories/GHSA-wq5f-xc86-pv6w

# Next.js article integration

These are the article-specific files used by the portfolio site, not a second
copy of the portfolio. The model and publication pipeline live at the repository
root. The self-contained article can be built without Next.js with `npm run article`.

For the portfolio integration:

1. Install `katex`, `@types/katex` and `sharp` in the host Next.js project.
2. Copy `midterms-2026.tsx` and `midterms-2026.module.css` into `src/content/`.
3. Copy generated `reports/article.json` to `src/content/midterms-2026.json`.
4. Copy `reports/web/*.svg` and result CSVs to `public/assets/writings/midterms-2026/`.
   Save `reports/2026-house-map.png` there as `preview.png` for link previews.
5. Copy `embed-midterm-figures.cjs` into the host `scripts/` directory and run it.
6. Place `page.tsx` in `src/app/writings/2026-us-midterm-election-model/`.

The component uses the host site's layout classes and `--strong`, `--muted` and
`--line` CSS variables. Equations render on the server with KaTeX. Responsive
figures are embedded WebP images; original SVGs remain available for download.

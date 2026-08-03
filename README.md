# nestwork — site branch

This orphan branch holds the GitHub Pages landing page only. It shares no
history with `main`, so the template repo stays pure markdown and nobody who
clicks **Use this template** inherits a frontend project.

- `index.html` — the whole site: one self-contained file, no build step, no
  dependencies, no external requests. Edit it and push; Pages redeploys.
- Language switching (EN / 中文) is client-side, persisted in `localStorage`.

Protocol source of truth lives on `main` — if `VERSION` or the protocol
version changes, update the badges in `index.html` to match.

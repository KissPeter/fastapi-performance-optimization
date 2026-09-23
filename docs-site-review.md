# Docs site review — fastapi-performance-optimization

> Date: 2026-09-23. Internal findings document. **Not part of the rendered site** (excluded in `_config.yml`).
> Scope: site navigation/structure, `workers_and_threads.md`, and SEO / GEO / AEO considerations.

## 1. TL;DR

The content is strong and CI-verified, but the site is hard to navigate and hard for search/answer
engines to consume:

- **Navigation has no order or grouping.** The sidebar is auto-generated from `site.pages` in
  `_layouts/template.html` — the list is a flat, arbitrary dump with no notion of "start here",
  "transport", "concurrency", "robustness", etc.
- **The live page is stale.** The deployed index still shows old copy ("Stay tuned for new ideas…")
  and the sidebar is missing the Profiling page. The site needs a rebuild after the recent `docs:` commits.
- **Every topic page hides its answer at the bottom.** `workers_and_threads.md` is the clearest example:
  190 lines of measurement tables before a 4-bullet Verdict.
- **SEO meta is empty** — no `description:` front matter anywhere; titles are inconsistent between
  front matter, sidebar link text, and the H1 of the page.

## 2. Site-wide findings

Ref: `_layouts/template.html:23-28` (sidebar), `_includes/toc.html`, `index.md`, `_config.yml`.

### 2.1 Navigation (sidebar)

- Built by iterating `site.pages`, so ordering is whatever Jekyll produces (effectively filename
  order), not a logical order: Connection Pool → index → Response class → Keepalive → …
- The **index page appears as a normal topic link** ("FastAPI performance optimisation") among the topics.
- **`markmap.md` has no `title`** in front matter yet leaks into the nav as an odd unlinked entry; it is a demo artifact and should be removed or excluded.
- No grouping sections (concurrency / transport / response / robustness), no section headers, no "start here" emphasis.

**Fix:** move navigation to `_data/navigation.yml` (ordered, grouped) and render the sidebar from it.

### 2.2 Index page (`index.md`)

- `## [Page title](url)` headings are used for the topic links. kramdown gives a heading that contains
  only a link an empty `id`, which makes the auto-TOC emit junk entries like
  `[](#fastapi-middleware-performance-tuning)[Fastapi Middleware performance tuning]`.
- The "All optimization topics" section **duplicates the sidebar** and uses link text that disagrees with
  the page titles (e.g. "Fastapi Middleware performance tuning" vs `title: Middleware` vs H1 "Middleware").
- No descriptions next to links — a visitor cannot tell what a page is about or what to read first.
- Multiple `#` level-1 headings on one page (`# FastAPI performance tuning`, `# Use these techniques…`,
  `# Robustness & Reliability…`, `# Test environment`). Multiple H1s hurt SEO; the page should have
  exactly one H1.

**Fix:** index becomes a categorized catalog (group, one-line description, key numbers, link), links as
bullet lists (not headings), single H1.

### 2.3 Auto-TOC (`_includes/toc.html`)

- Included on every page with defaults `h_min=1 h_max=6` (`_layouts/template.html:36`), so long pages
  produce deep, noisy TOCs. Restrict to `h_min=2 h_max=3`.

### 2.4 Titles / meta

- Front-matter title ≠ H1 in several pages: `title: Workers and threads` vs H1 *Gunicorn Workers and
  Threads*, `title: Response class` vs previous H1 *FastAPI JSON response classes*, etc.
- No `description:` in any front matter → `{% seo %}` has nothing for the meta description /
  social description. Add a 1–2 sentence description per page.

## 3. `workers_and_threads.md` review

### 3.1 Structure problem

Current order (212 lines):

1. Intro/links to Gunicorn, Uvicorn, Workers, Threads (lines 10–35)
2. Four full 25-row measurement tables with observations (lines 37–200)
3. **Verdict — last section** (line 202)

The answer ("2–3 workers, threads barely matter, >3 workers degrades") is what everyone comes for, but
it is the **last thing on the page**. Readers scroll ~190 lines of tables to learn the recommendation.
For answer engines this is inverted: the reply must be near the top or it will be missed.

### 3.2 Other issues

- Weak opening line for SEO/AEO: *"Not strictly FastAPI performance tuning…"* — no keyword-rich,
  answer-first opener, and it undersells the page's own content.
- The verdict already exists (4 clean bullets) — it just needs to move up, and be followed by the evidence.
- Tables are great for AEO (structured data, exact numbers), but outlier cells flagged as
  "intermittent performance issue" in prose are not marked in the tables; an extractor can pick up noise.
- Image hotlinked from `miro.medium.com` (line 33) — external dependency, may break / be blocked; could
  be removed or self-hosted.
- No internal cross-links to related topics (`server_runners`, `nginx_port_socket`,
  `thread_pool_sizing`, `per_worker_connection_pool`) — hurts crawl/discovery and user journey.
- "It is highly recommended making a measurement like this" closes weakly; recommend + link the test code.

### 3.3 Proposed restructure

```
# Gunicorn Workers and Threads
> TL;DR — on a 2-core container use 2-3 workers / 1-2 threads. Threads barely matter.
> More than 3 workers degrades throughput. A single worker is a 6-7x bottleneck on 1MB responses.

## Verdict  (direct answer, ~50 words)
  bullets: 2-3 workers best / threads minimal / >3 degrades / 6-7x gain on big responses

## Why it works   (Gunicorn, Uvicorn, Workers, Threads - short)
## Measurements   (4 tables + "key takeaway" callout above each table)
## Reproduce   (test code link, CI workflow, container specs)
```

## 4. SEO / GEO / AEO recommendations

### 4.1 SEO (search engines)

- One H1 per page; make front-matter `title` match the H1 exactly.
- Add `description:` to every page's front matter (shown in search snippets).
- Use descriptive internal link anchors ("Gunicorn Workers and Threads" not "workers_and_threads.md",
  not the raw URL as visible text).
- Keep index's link lists as `<ul>`/`<dl>` with keyword text, not `## [url]` headings.
- Structured data: add JSON-LD `Article`/`TechArticle` (+ `FAQPage` where a real FAQ exists) via a
  head include.
- Fix the stale build so the deployed site matches `main`.

### 4.2 GEO (generative / LLM engines)

- LLMs read the page front-to-back; putting the conclusion up top makes the page **citable** — a model
  answering "how many Gunicorn workers for FastAPI?" can quote the verdict directly.
- Strong entity language: name concrete things ("Gunicorn", "UvicornWorker", "2 CPU cores",
  "ORJSON", "BaseHTTPMiddleware") in headings and first paragraph.
- Keep tables (models parse them well) with consistent, explicit column headers and units
  (RPS, ms, workers/threads).
- Self-contained pages: each topic page should carry its TL;DR and key numbers, not only the index
  (models often land directly on sub-pages).

### 4.3 AEO (answer engines / featured snippets)

- Answer-first: an H2 **Verdict** blockquote directly under the H1, answer in ≤ 50 words →
  maximizes featured-snippet eligibility.
- Use lists/tables for the answer, "Question" phrasing in headings where natural
  ("How many workers should FastAPI use?").
- Flag outliers in tables (e.g. `*` noted as unreliable measurement) so the answer doesn't get polluted.
- Add FAQ schema for the questions each page answers.

## 5. Prioritized action list

1. Rebuild/deploy current `main` (fixes stale content, missing Profiling).
2. Move sidebar to `_data/navigation.yml` with grouped, ordered sections.
3. Restructure `workers_and_threads` (verdict up, TL;DR blockquote, key-takeaway callouts).
4. Fix index: one H1, categorized catalog with descriptions, links as lists.
5. Add `description:` front matter to every page; align titles across front matter / sidebar / H1.
6. Harden TOC (`h_min=2 h_max=3`); remove/exclude `markmap.md`; un-hotlink the Medium image.
7. Add JSON-LD (Article + FAQ) once structure is stable.
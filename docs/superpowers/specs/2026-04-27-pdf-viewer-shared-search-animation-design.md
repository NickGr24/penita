# PDF Viewer: Shared Module + Full-Document Search + Slide Animation

**Date:** 2026-04-27
**Status:** Approved by user
**Scope:** Both `templates/articles/article_detail.html` and `templates/books/book_detail.html`

## Context

Currently the PDF viewer is duplicated as ~600 lines of inline JS + ~300 lines of inline CSS in **two** templates (`article_detail.html`, `book_detail.html`). Both copies are 95% identical — only the URL endpoint and title differ. Each new PDF feature has to be implemented twice and risks divergence.

We want to add two PDF features:
1. **Full-document text search** through `PDFFindController` from PDF.js
2. **Slide animation** when navigating between pages (left/right depending on direction)

Adding these to the duplicated code would compound the existing tech debt. So **the same change introduces the third user-facing feature: a shared module that both pages use.**

## Decisions

| # | Decision | Why |
|---|---|---|
| 1 | Search uses PDF.js `PDFFindController` API | Battle-tested, supports highlighting, pagination, all-document scope. |
| 2 | Animation = slide left/right (not 3D flip, not fade) | Consistent with existing swipe-gesture UX, no library dependency, GPU-accelerated. |
| 3 | Refactor PDF viewer into shared `static/js/pdf-viewer.js` + `static/css/pdf-viewer.css` | Removes ~1200 lines of duplicated code; future PDF changes happen once. |
| 4 | Search UX = MVP + keyboard shortcuts (Cmd/Ctrl+F, Esc, Enter, Shift+Enter) + "no results" hint | Cmd+F prevents user confusion (Chrome's built-in find can't search PDF canvas). |
| 5 | Single viewer per page, IIFE with `querySelectorAll` for forward-compatibility | YAGNI for multi-viewer now, but extension is trivial. |
| 6 | Use `data-*` attributes on wrapper for template-specific data (`data-pdf-url`, `data-pdf-title`) | Decouples JS from Django templates. |
| 7 | Buttons use `data-action="prev-page"` + delegated `addEventListener` (no inline `onclick`) | CSP-friendly, modern; inline `onclick` is being phased out. |
| 8 | URL hash `#page=N` for shareable deep-links | Cheap (~10 lines), supports back/forward browser navigation. |
| 9 | Lazy-load `pdf.min.js` via `IntersectionObserver` (already in place) | Saves Google crawl budget + improves TTI on mobile. |

## File Layout (after refactor)

**New files:**
- `main/static/js/pdf-viewer.js` — single source of truth for PDF viewer behaviour (~700 lines)
- `main/static/css/pdf-viewer.css` — extracted styles (~300 lines)
- `templates/partials/pdf_viewer_assets.html` — partial that includes the JS+CSS (so both detail templates only need `{% include %}`)

**Modified templates:**
- `templates/articles/article_detail.html` — drop ~600 lines of inline `<script>`, drop ~300 lines of inline `<style>`, use `<div class="pdf-viewer-wrapper" data-...>` + `{% include 'partials/pdf_viewer_assets.html' %}`
- `templates/books/book_detail.html` — same

## Module Structure (`pdf-viewer.js`)

```
IIFE
├── State (per-instance): pdfDoc, pageNum, scale, currentZoomMode,
│                          findController, eventBus, container refs
├── init() — query DOM, attach listeners, lazy-load pdf.js
│
├── Lifecycle
│   ├── setupLazyLoad()           — IntersectionObserver → loadPdfJs() → initPdfViewer()
│   ├── initPdfViewer()           — pdfjsLib.getDocument(url).then(...) → first render
│   └── handleHashChange()        — read #page=N → goToPage()
│
├── Page navigation (with slide animation)
│   ├── goToPage(num)             — central entry point
│   ├── animateAndRender(num, direction)
│   ├── previousPage()            — direction='right' (incoming page slides from right)
│   └── nextPage()                — direction='left'
│
├── Render
│   ├── renderPage(num)           — PDF.js getPage().render(canvas)
│   └── queueRenderPage(num)
│
├── Search (full-document via PDFFindController)
│   ├── setupSearchUI()           — create input + match counter + nav buttons
│   ├── search(query)             — eventBus.dispatch('find', { query, ... })
│   ├── nextMatch() / prevMatch() — dispatch('findagain', { findPrevious })
│   ├── closeSearch()             — clear highlights, reset UI
│   └── handleFindResults(state)  — update "X of Y" counter or "Niciun rezultat"
│
├── Zoom — setZoom, zoomIn, zoomOut (current logic)
├── Fullscreen — toggleFullscreen + iOS pseudo-fullscreen fallback (current logic)
│
├── Keyboard shortcuts (document-level)
│   ├── ArrowLeft / PageUp        — prev page
│   ├── ArrowRight / PageDown / Space — next page
│   ├── Cmd/Ctrl+F                — open search (preventDefault)
│   ├── Esc                       — close search OR exit fullscreen
│   ├── Enter / Shift+Enter       — when search active: next / prev match
│   └── Home / End                — first / last page
│
├── Touch gestures (mobile)
│   ├── handleSwipe()             — calls nextPage()/previousPage() (animation triggered there)
│   └── pinch-to-zoom             — current logic
│
└── DOMContentLoaded → init
```

## HTML Wrapper Contract

Both templates use the same wrapper structure:

```html
<div class="pdf-viewer-wrapper"
     data-pdf-url="{% url 'serve_article_pdf' article.slug %}"
     data-pdf-title="{{ article.name|escapejs }}"
     data-pdf-type="article">
    <div class="pdf-controls">
        <div class="pdf-search">
            <button data-action="toggle-search" aria-label="Căutare"><i class="fas fa-search"></i></button>
            <input type="search" data-pdf-search-input placeholder="Căutare în document..." aria-label="Căutare în document">
            <span data-pdf-match-counter></span>
            <button data-action="prev-match" aria-label="Match anterior"><i class="fas fa-chevron-up"></i></button>
            <button data-action="next-match" aria-label="Match următor"><i class="fas fa-chevron-down"></i></button>
            <button data-action="close-search" aria-label="Închide căutare">&times;</button>
        </div>
        <div class="page-navigation">
            <button data-action="prev-page" aria-label="Pagina anterioară"><i class="fas fa-chevron-left"></i></button>
            <span class="page-info"><span data-pdf-current-page>1</span> / <span data-pdf-total-pages>-</span></span>
            <button data-action="next-page" aria-label="Pagina următoare"><i class="fas fa-chevron-right"></i></button>
        </div>
        <div class="zoom-controls">
            <button data-action="zoom-out"><i class="fas fa-minus"></i></button>
            <select data-pdf-zoom-level aria-label="Nivel de zoom">...</select>
            <button data-action="zoom-in"><i class="fas fa-plus"></i></button>
        </div>
    </div>
    <div class="pdf-viewer-container" data-pdf-viewer>
        <div data-pdf-canvas-container>
            <div class="loading">...</div>
        </div>
    </div>
    <button class="fullscreen-btn" data-action="toggle-fullscreen" aria-label="Ecran complet">
        <i class="fas fa-expand"></i>
    </button>
</div>
```

JS uses event delegation on `.pdf-viewer-wrapper` for `[data-action]` clicks → calls the right handler.

## Slide Animation Spec

CSS classes added to `[data-pdf-canvas-container]`:
- `.slide-leaving-left` (page leaves to the left, when going to next)
- `.slide-leaving-right` (page leaves to the right, when going to prev)
- `.slide-entering-left` (new page slides in from the right) — applied after old page exits
- `.slide-entering-right` (new page slides in from the left)

```css
[data-pdf-canvas-container] {
    transition: transform 0.25s ease-out, opacity 0.25s ease-out;
}
.slide-leaving-left  { transform: translateX(-30%); opacity: 0; }
.slide-leaving-right { transform: translateX( 30%); opacity: 0; }
.slide-entering-left { animation: slide-from-right 0.25s ease-out; }
.slide-entering-right { animation: slide-from-left 0.25s ease-out; }

@keyframes slide-from-right {
    from { transform: translateX(30%); opacity: 0; }
    to   { transform: translateX(0);   opacity: 1; }
}
@keyframes slide-from-left {
    from { transform: translateX(-30%); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
    [data-pdf-canvas-container],
    .slide-leaving-left, .slide-leaving-right,
    .slide-entering-left, .slide-entering-right {
        transition: none !important;
        animation: none !important;
    }
}
```

JS sequence inside `animateAndRender(num, direction)`:
1. Set `isAnimating = true` flag; ignore further nav clicks until cleared
2. Add `.slide-leaving-{direction}` class to canvas container
3. Wait for `transitionend` event (with 300ms timeout fallback in case event doesn't fire)
4. Trigger PDF.js render (returns promise) → `await renderTask.promise`
5. Replace `.slide-leaving-{direction}` with `.slide-entering-{direction}` class
6. Wait for `animationend` (with 300ms fallback)
7. Remove `.slide-entering-*` class; clear `isAnimating = false`

If `prefers-reduced-motion: reduce` — skip steps 2-3 and 5-6 — just `await renderTask.promise`.

If user clicks next/prev rapidly while animating: ignore (don't queue). This avoids visual glitches and feels responsive.

## Search Feature Spec

### Initialization

When `pdfjsLib.getDocument(...)` resolves, also create:
```js
eventBus = new pdfjsViewer.EventBus();
findController = new pdfjsViewer.PDFFindController({
    linkService: new pdfjsViewer.PDFLinkService({ eventBus }),
    eventBus,
});
findController.setDocument(pdfDoc);
eventBus.on('updatefindmatchescount', handleFindResults);
eventBus.on('updatefindcontrolstate', handleFindResults);
```

### UI States

The search bar starts **hidden**. States:
- **Closed** — only search button is visible in `.pdf-search`
- **Open empty** — input is focused, no counter, no "no results"
- **Open with query, found** — input + "3 of 12" + nav buttons + close
- **Open with query, no results** — input + "Niciun rezultat" + close
- **Searching** — input + "Caut..." (transient, < 200ms usually)

### Highlight Rendering

PDF.js render the text layer via `page.getTextContent()` → text divs absolute-positioned over canvas. `PDFFindController` injects `<span class="highlight">` and `<span class="highlight selected">` into these text divs.

CSS:
```css
.textLayer .highlight { background: rgba(255, 235, 59, 0.5); }
.textLayer .highlight.selected { background: rgba(255, 152, 0, 0.7); }
```

This requires us to **render the text layer**, not just the canvas — slight render-time addition (~10-30ms per page) but unlocks both search AND text-selection (a UX win).

### Keyboard Shortcuts

```js
document.addEventListener('keydown', e => {
    // Don't intercept if user is typing in an input not in our search
    if (e.target.matches('input, textarea') && !e.target.matches('[data-pdf-search-input]')) return;

    if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
        e.preventDefault();
        openSearch();
    } else if (e.key === 'Escape' && isSearchOpen()) {
        e.preventDefault();
        closeSearch();
    } else if (e.key === 'Enter' && document.activeElement.matches('[data-pdf-search-input]')) {
        e.preventDefault();
        e.shiftKey ? prevMatch() : nextMatch();
    } else if (!isSearchOpen()) {
        if (e.key === 'ArrowLeft' || e.key === 'PageUp') previousPage();
        else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
            e.preventDefault(); nextPage();
        }
        else if (e.key === 'Home') goToPage(1);
        else if (e.key === 'End') goToPage(pdfDoc.numPages);
    }
});
```

## Edge Cases & Error Handling

| Case | Behavior |
|---|---|
| User opens article/book with `#page=999` (out of range) | Clamp to last page silently |
| `pdf.min.js` fails to load (network) | Show error message in viewer, log to console |
| Search query shorter than 1 char | Don't trigger find, show counter as empty |
| Animation triggered while previous still in flight | Queue or cancel — use a `isAnimating` flag, ignore clicks while animating (UX: feels responsive even on slow devices) |
| Browser doesn't support `IntersectionObserver` (old Safari < 12.1) | Fallback to immediate `loadPdfJs()` call (current behaviour preserved) |
| User has `prefers-reduced-motion: reduce` | Skip all transitions, render directly |
| Cmd+F pressed when input is already focused | Browser's default behavior takes over (acceptable; rare case) |
| Mobile: viewport too narrow for inline search bar | Use full-width row in `pdf-controls` (responsive layout already supports flex-wrap) |

## Verification (Manual + Tools)

After deploy:

1. **Smoke test via chrome-devtools**
   - Open `/articles/audierea-martorilor/` → check search button visible in pdf-controls
   - Click search → input appears, focus jumps in
   - Type "drept" → highlights appear, counter shows match count
   - Press Enter → jumps to next match (auto-scrolls if on different page)
   - Press Esc → search closes, highlights gone
   - Click next-page → page slides left, new page slides in from right
   - Same on `/books/caile-de-atac-in-procesul-penal/` (paid book — accessible after purchase, but pdf-viewer lazy-loads only when accessible)

2. **Lighthouse run** — Performance + Accessibility shouldn't regress. Targets:
   - LCP unchanged (lazy-load preserved)
   - Accessibility ≥ current (79 → maybe higher with proper ARIA labels on new search buttons)
   - SEO 100 (no change, JS doesn't affect SEO)

3. **`prefers-reduced-motion` test** — Chrome DevTools → Rendering → Emulate prefers-reduced-motion: reduce → check that pages change instantly without animation

4. **URL hash test** — `/articles/audierea-martorilor/#page=5` → loads on page 5; clicking next → URL updates to `#page=6`; back button → returns to #page=5

5. **Search edge cases** — empty query (no error); query with no matches ("zzzzzz" → "Niciun rezultat"); query with 1 match (counter "1 of 1"); query with 100+ matches (counter doesn't break)

## Out of Scope (for this iteration)

- Saving search history in `localStorage`
- "Case sensitive" / "whole word" toggle checkboxes
- Search results dropdown showing context snippets (Chrome-style preview)
- 3D flip animation (we explicitly chose slide instead)
- Multi-viewer per page (architecture supports it via `querySelectorAll`, but no UI uses this yet)
- Replacing inline `onclick` in OTHER (non-PDF) parts of the codebase

## Critical Files Modified

**Created:**
- `main/static/js/pdf-viewer.js`
- `main/static/css/pdf-viewer.css`
- `templates/partials/pdf_viewer_assets.html`

**Modified:**
- `templates/articles/article_detail.html` — strip inline JS/CSS, replace with wrapper + include
- `templates/books/book_detail.html` — same

**Unchanged (just verified):**
- `articles/views.py` (no context changes needed)
- `books/views.py` (no context changes needed)
- `articles/urls.py` / `books/urls.py` (PDF endpoints stay)
- `penita/settings.py` (no new middleware)

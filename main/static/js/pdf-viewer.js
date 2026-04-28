/* Penița Dreptului — Shared PDF Viewer
 *
 * Powers the PDF viewer on /articles/<slug>/ and /books/<slug>/.
 * Replaces ~600 lines of duplicated inline JS in each detail template.
 *
 * Features:
 *   - Lazy-load pdf.min.js + pdf_viewer.min.js via IntersectionObserver
 *     (only when the user scrolls down to the viewer)
 *   - Page navigation with slide animation (left/right by direction)
 *   - Full-document text search via PDFFindController (Cmd/Ctrl+F, Esc, Enter, Shift+Enter)
 *   - Text layer rendering (enables search highlights AND text selection)
 *   - Zoom controls (preset + page-width auto-fit)
 *   - Native fullscreen + iOS Safari pseudo-fullscreen fallback
 *   - URL hash deep-links (#page=N)
 *   - Keyboard shortcuts: Arrows / PageUp / PageDown / Space / Home / End
 *   - Touch gestures: swipe to flip page, pinch to zoom
 *   - prefers-reduced-motion respect (skips slide animation)
 *
 * Configuration via data-* attributes on .pdf-viewer-wrapper:
 *   - data-pdf-url:   URL to fetch the PDF from
 *   - data-pdf-title: human-readable title (used for log messages, future analytics)
 *   - data-pdf-type:  "article" | "book" (for analytics / debugging)
 */
(function () {
    'use strict';

    var PDF_JS_URL = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
    var PDF_VIEWER_JS_URL = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf_viewer.min.js';
    var PDF_WORKER_URL = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    var ANIMATION_DURATION_MS = 250;
    var SWIPE_THRESHOLD_PX = 50;

    function init() {
        var wrappers = document.querySelectorAll('.pdf-viewer-wrapper');
        wrappers.forEach(function (wrapper) {
            // Each wrapper gets its own viewer instance.
            new PdfViewer(wrapper);
        });
    }

    /* =========================================================
     * PdfViewer — one instance per .pdf-viewer-wrapper element
     * ========================================================= */
    function PdfViewer(wrapper) {
        var self = this;

        // === DOM refs ===
        this.wrapper = wrapper;
        this.viewer = wrapper.querySelector('[data-pdf-viewer]');
        this.canvasContainer = wrapper.querySelector('[data-pdf-canvas-container]');
        this.searchInput = wrapper.querySelector('[data-pdf-search-input]');
        // .pdf-search is the parent containing the toggle button + the inner [data-pdf-search-bar]
        // We add `is-open` class here so CSS selectors like `.pdf-search.is-open [data-pdf-search-bar]` match
        this.searchBar = wrapper.querySelector('.pdf-search');
        this.matchCounter = wrapper.querySelector('[data-pdf-match-counter]');
        this.currentPageEl = wrapper.querySelector('[data-pdf-current-page]');
        this.totalPagesEl = wrapper.querySelector('[data-pdf-total-pages]');
        this.zoomSelect = wrapper.querySelector('[data-pdf-zoom-level]');
        this.progressBar = document.getElementById('reading-progress');

        // === State ===
        this.config = {
            url: wrapper.dataset.pdfUrl,
            title: wrapper.dataset.pdfTitle || '',
            type: wrapper.dataset.pdfType || 'document',
            // Phase 3: server-side sync — нужны для API endpoints
            contentId: wrapper.dataset.pdfContentId || null,
            userAuthenticated: wrapper.dataset.pdfUserAuthenticated === '1',
        };
        // Annotations cached at init (1 fetch for whole document)
        this.annotations = [];
        // Debounce timer для save reading-progress
        this._syncProgressTimer = null;
        this.pdfDoc = null;
        // URL hash > localStorage > 1.
        // localStorage позволяет вернуться на ту же страницу при повторном визите.
        this.pageNum = this.readPageFromHash() || this.readSavedPage() || 1;
        this.scale = 1;
        this.currentZoomMode = 'page-width';
        this.isDarkMode = this.readSavedDarkMode();
        this.isAnimating = false;
        this.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        this.prefersReducedMotion = window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Search state (custom implementation — PDFFindController requires full
        // PDFViewer setup which doesn't fit our custom canvas rendering)
        this.searchIndex = null;        // [{pageNum, text}] across all pages
        this.searchQuery = '';
        this.searchMatches = [];        // [{pageNum, indexInPage}]
        this.currentMatchIdx = -1;      // index into searchMatches

        // === Lazy-load PDF.js when viewer is visible ===
        this.setupLazyLoad();

        // Click delegation for [data-action] buttons
        wrapper.addEventListener('click', function (e) {
            var btn = e.target.closest('[data-action]');
            if (!btn || !wrapper.contains(btn)) return;
            self.handleAction(btn.dataset.action, e);
        });

        // Zoom select change
        if (this.zoomSelect) {
            this.zoomSelect.addEventListener('change', function () {
                self.setZoom(self.zoomSelect.value);
            });
        }

        // Search input — live search on each keystroke (debounced)
        if (this.searchInput) {
            var searchDebounce = null;
            this.searchInput.addEventListener('input', function () {
                clearTimeout(searchDebounce);
                searchDebounce = setTimeout(function () {
                    self.search(self.searchInput.value);
                }, 200);
            });
            this.searchInput.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    if (e.shiftKey) self.prevMatch();
                    else self.nextMatch();
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    self.closeSearch();
                }
            });
        }

        // Document-level keyboard shortcuts
        document.addEventListener('keydown', function (e) { self.handleKeydown(e); });

        // URL hash navigation
        window.addEventListener('hashchange', function () {
            var page = self.readPageFromHash();
            if (page && self.pdfDoc && page !== self.pageNum && page >= 1 && page <= self.pdfDoc.numPages) {
                self.goToPage(page);
            }
        });

        // Touch gestures (mobile)
        if (this.isMobile) this.setupTouchGestures();

        // Window resize → re-render in auto/page-width modes
        var resizeTimeout;
        window.addEventListener('resize', function () {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function () {
                if (self.currentZoomMode === 'auto' || self.currentZoomMode === 'page-width') {
                    self.queueRenderPage(self.pageNum);
                }
            }, 300);
        });

        // Fullscreen change events (user pressed F11 / Esc / system gesture)
        ['fullscreenchange', 'webkitfullscreenchange'].forEach(function (ev) {
            document.addEventListener(ev, function () {
                self.updateFullscreenBtnIcon();
                setTimeout(function () { self.queueRenderPage(self.pageNum); }, 120);
            });
        });
    }

    /* ---------- Lifecycle ---------- */

    PdfViewer.prototype.setupLazyLoad = function () {
        var self = this;
        if (!this.viewer || !this.config.url) return;

        if ('IntersectionObserver' in window) {
            var io = new IntersectionObserver(function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        self.loadPdfJs();
                        io.disconnect();
                    }
                });
            }, { rootMargin: '300px' });
            io.observe(this.viewer);
        } else {
            this.loadPdfJs();
        }
    };

    PdfViewer.prototype.loadPdfJs = function () {
        var self = this;
        if (window.pdfjsLib && window.pdfjsViewer) {
            this.initPdf();
            return;
        }
        loadScript(PDF_JS_URL, function () {
            // pdf_viewer.js depends on pdfjsLib being defined
            loadScript(PDF_VIEWER_JS_URL, function () {
                self.initPdf();
            });
        });
    };

    PdfViewer.prototype.initPdf = function () {
        var self = this;
        window.pdfjsLib.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL;

        window.pdfjsLib.getDocument({
            url: this.config.url,
            withCredentials: true,
        }).promise.then(function (pdf) {
            self.pdfDoc = pdf;
            if (self.totalPagesEl) self.totalPagesEl.textContent = pdf.numPages;
            // Clamp pageNum to valid range
            if (self.pageNum > pdf.numPages) self.pageNum = pdf.numPages;
            if (self.pageNum < 1) self.pageNum = 1;
            // Clear loading message
            self.canvasContainer.innerHTML = '';
            // Build search index in background (extract text from all pages)
            self.buildSearchIndex();
            // Restore dark mode (if previously enabled)
            if (self.isDarkMode) self.applyDarkMode(true);
            // Phase 3: server-side sync — server progress overrides local if newer
            self.syncFromServer().then(function () {
                // Render with possibly-updated pageNum
                self.renderPage(self.pageNum);
                self.updateNavButtons();
                self.updateProgress();
                self.updateHash();
                self.updateBookmarkButton();
                self.updateAnnotationButton();
                self.setupQuoteExport();
            });
            // For mobile: 100% (fit-width)
            if (self.isMobile && self.zoomSelect) {
                self.zoomSelect.value = '1';
                self.setZoom('1');
            }
        }).catch(function (error) {
            self.canvasContainer.innerHTML = '<div class="pdf-error-message">' +
                '<i class="fas fa-exclamation-triangle"></i> ' +
                'Nu am putut încărca documentul. Vă rugăm încercați mai târziu.</div>';
            console.error('[pdf-viewer] Error loading PDF:', error);
        });
    };

    /* ---------- Action dispatcher (data-action) ---------- */

    PdfViewer.prototype.handleAction = function (action, event) {
        switch (action) {
            case 'prev-page':       this.previousPage(); break;
            case 'next-page':       this.nextPage(); break;
            case 'zoom-in':         this.zoomIn(); break;
            case 'zoom-out':        this.zoomOut(); break;
            case 'toggle-fullscreen': this.toggleFullscreen(); break;
            case 'toggle-dark':     this.toggleDarkMode(); break;
            case 'toggle-search':   this.openSearch(); break;
            case 'close-search':    this.closeSearch(); break;
            case 'next-match':      this.nextMatch(); break;
            case 'prev-match':      this.prevMatch(); break;
            case 'toggle-bookmarks': this.toggleBookmarksPanel(); break;
            case 'bookmark-current': this.toggleBookmarkCurrentPage(); break;
            case 'goto-bookmark':   this.gotoBookmark(parseInt(event.target.closest('[data-page]').dataset.page, 10)); break;
            case 'remove-bookmark': this.removeBookmark(parseInt(event.target.closest('[data-page]').dataset.page, 10), event); break;
            case 'highlight-selection': this.createAnnotationFromSelection(); break;
            case 'toggle-annotations': this.toggleAnnotationsPanel(); break;
            case 'goto-annotation':    this.gotoAnnotation(parseInt(event.target.closest('[data-annotation-id]').dataset.annotationId, 10)); break;
            case 'remove-annotation':  this.removeAnnotation(parseInt(event.target.closest('[data-annotation-id]').dataset.annotationId, 10), event); break;
        }
    };

    /* ---------- Page navigation with slide animation ---------- */

    PdfViewer.prototype.previousPage = function () {
        if (!this.pdfDoc || this.pageNum <= 1 || this.isAnimating) return;
        this.animateAndRender(this.pageNum - 1, 'right');
    };

    PdfViewer.prototype.nextPage = function () {
        if (!this.pdfDoc || this.pageNum >= this.pdfDoc.numPages || this.isAnimating) return;
        this.animateAndRender(this.pageNum + 1, 'left');
    };

    PdfViewer.prototype.goToPage = function (num) {
        if (!this.pdfDoc) return;
        num = Math.max(1, Math.min(num, this.pdfDoc.numPages));
        if (num === this.pageNum || this.isAnimating) return;
        var direction = num > this.pageNum ? 'left' : 'right';
        this.animateAndRender(num, direction);
    };

    /**
     * Slide animation flow:
     *   1. Add .slide-leaving-{direction} → existing page slides out
     *   2. After transitionend → render new page
     *   3. Replace with .slide-entering-{direction} → new page slides in
     *   4. After animationend → cleanup
     *
     * For prefers-reduced-motion: skip animations, just render.
     */
    PdfViewer.prototype.animateAndRender = function (newPageNum, direction) {
        var self = this;
        this.isAnimating = true;
        this.pageNum = newPageNum;
        this.updateNavButtons();
        this.updateProgress();
        this.updateHash();
        this.savePage();
        this.syncProgressDebounced();
        // Refresh bookmarks panel header (so "Add/Remove bookmark for page X" reflects new page)
        var panel = this.wrapper.querySelector('[data-bookmarks-panel]');
        if (panel && panel.classList.contains('is-open')) this.renderBookmarksPanel();

        if (this.prefersReducedMotion) {
            this.renderPage(newPageNum).then(function () { self.isAnimating = false; });
            return;
        }

        var leaveClass = 'slide-leaving-' + direction;
        var enterClass = 'slide-entering-' + direction;

        // Phase 1: slide current page out
        this.canvasContainer.classList.add(leaveClass);
        var leaveDone = onceTransitionEnd(this.canvasContainer, ANIMATION_DURATION_MS + 50);

        leaveDone.then(function () {
            // Phase 2: render new page (without animation classes)
            self.canvasContainer.classList.remove(leaveClass);
            return self.renderPage(newPageNum);
        }).then(function () {
            // Phase 3: slide new page in
            self.canvasContainer.classList.add(enterClass);
            return onceAnimationEnd(self.canvasContainer, ANIMATION_DURATION_MS + 50);
        }).then(function () {
            self.canvasContainer.classList.remove(enterClass);
            self.isAnimating = false;
        }).catch(function (err) {
            console.error('[pdf-viewer] Animation error:', err);
            self.canvasContainer.classList.remove(leaveClass, enterClass);
            self.isAnimating = false;
        });
    };

    /* ---------- Render (canvas + text layer for search) ---------- */

    PdfViewer.prototype.renderPage = function (num) {
        var self = this;
        return this.pdfDoc.getPage(num).then(function (page) {
            var canvas = document.createElement('canvas');
            var ctx = canvas.getContext('2d');
            var outputScale = window.devicePixelRatio || 1;

            // Calculate viewport.
            // baseScale = scale at which page exactly fits container width — used as 100% reference
            // for percentage-based zoom (so "150%" means 1.5× fit-width, not 1.5× PDF native).
            var containerWidth = self.canvasContainer.clientWidth - 4;
            var tempViewport = page.getViewport({ scale: 1 });
            var fitWidthScale = containerWidth / tempViewport.width;
            self.baseScale = fitWidthScale;

            var viewport;
            if (self.currentZoomMode === 'page-width') {
                viewport = page.getViewport({ scale: fitWidthScale });
                self.scale = fitWidthScale;
            } else if (self.currentZoomMode === 'auto') {
                var fitHeightScale = (window.innerHeight - 200) / tempViewport.height;
                var autoScale = Math.min(fitWidthScale, fitHeightScale);
                viewport = page.getViewport({ scale: autoScale });
                self.scale = autoScale;
            } else {
                // Numeric zoom: % relative to fit-width baseline (1 = fits container; 1.5 = 1.5×)
                var pct = parseFloat(self.currentZoomMode);
                if (isNaN(pct) || pct <= 0) pct = 1;
                self.scale = fitWidthScale * pct;
                viewport = page.getViewport({ scale: self.scale });
            }

            // Canvas dimensions (high-DPI aware)
            canvas.width = Math.floor(viewport.width * outputScale);
            canvas.height = Math.floor(viewport.height * outputScale);
            canvas.style.width = Math.floor(viewport.width) + 'px';
            canvas.style.height = Math.floor(viewport.height) + 'px';
            ctx.scale(outputScale, outputScale);

            var renderContext = {
                canvasContext: ctx,
                viewport: viewport,
                enableWebGL: true,
                renderInteractiveForms: false,
            };

            return page.render(renderContext).promise.then(function () {
                // Build page DOM: canvas + text layer (text layer enables search highlights AND text selection)
                self.canvasContainer.innerHTML = '';
                var pageDiv = document.createElement('div');
                pageDiv.className = 'pdf-page';
                pageDiv.style.position = 'relative';
                pageDiv.style.width = Math.floor(viewport.width) + 'px';
                pageDiv.style.height = Math.floor(viewport.height) + 'px';
                pageDiv.appendChild(canvas);

                // Text layer for search + text selection.
                // CRITICAL для PDF.js 3.x: --scale-factor CSS variable должна быть
                // установлена ДО renderTextLayer. Без неё text-span позиции
                // вычисляются с дефолтным scale=1, и реальные позиции дрейфуют
                // вниз страницы кумулятивно — выделение в нижней части кликает
                // спан, который "думает", что он выше → выделяется не тот текст.
                var textLayerDiv = document.createElement('div');
                textLayerDiv.className = 'textLayer';
                textLayerDiv.style.position = 'absolute';
                textLayerDiv.style.top = '0';
                textLayerDiv.style.left = '0';
                textLayerDiv.style.width = Math.floor(viewport.width) + 'px';
                textLayerDiv.style.height = Math.floor(viewport.height) + 'px';
                textLayerDiv.style.setProperty('--scale-factor', viewport.scale);
                pageDiv.appendChild(textLayerDiv);

                self.canvasContainer.appendChild(pageDiv);

                if (self.currentPageEl) self.currentPageEl.textContent = num;
                self.updateProgress();
                self.canvasContainer.scrollTop = 0;

                // Render text layer asynchronously (doesn't block UI)
                return page.getTextContent().then(function (textContent) {
                    if (!window.pdfjsLib.renderTextLayer) return;
                    var task = window.pdfjsLib.renderTextLayer({
                        textContent: textContent,
                        container: textLayerDiv,
                        viewport: viewport,
                        textDivs: [],
                    });
                    // After text layer is ready, re-apply search highlights AND user annotations
                    var promise = task && task.promise ? task.promise : Promise.resolve();
                    return promise.then(function () {
                        if (self.searchQuery) self.highlightMatchesOnCurrentPage();
                        self.applyAnnotationsToCurrentPage();
                    });
                }).catch(function (e) {
                    console.warn('[pdf-viewer] textLayer render failed:', e);
                });
            });
        });
    };

    PdfViewer.prototype.queueRenderPage = function (num) {
        // Simplified queueing — renderPage returns promise, callers can chain.
        // For non-animated paths (zoom, resize) we just render immediately.
        return this.renderPage(num);
    };

    /* ---------- Nav helpers ---------- */

    PdfViewer.prototype.updateNavButtons = function () {
        var prev = this.wrapper.querySelector('[data-action="prev-page"]');
        var next = this.wrapper.querySelector('[data-action="next-page"]');
        if (prev) prev.disabled = this.pageNum <= 1;
        if (next) next.disabled = !this.pdfDoc || this.pageNum >= this.pdfDoc.numPages;
    };

    PdfViewer.prototype.updateProgress = function () {
        if (this.pdfDoc && this.progressBar) {
            this.progressBar.style.width = ((this.pageNum / this.pdfDoc.numPages) * 100) + '%';
        }
    };

    /* ---------- URL hash (shareable deep-links) ---------- */

    PdfViewer.prototype.readPageFromHash = function () {
        var m = window.location.hash.match(/[#&]page=(\d+)/);
        return m ? parseInt(m[1], 10) : null;
    };

    PdfViewer.prototype.updateHash = function () {
        // Use replaceState — don't pollute browser history with each page flip
        var newHash = '#page=' + this.pageNum;
        if (window.location.hash !== newHash && window.history.replaceState) {
            window.history.replaceState(null, '', window.location.pathname + window.location.search + newHash);
        }
    };

    /* ---------- Bookmarks (localStorage per-PDF) ---------- */

    PdfViewer.prototype.readBookmarks = function () {
        try {
            var v = window.localStorage.getItem(this._storageKey('bookmarks'));
            return v ? JSON.parse(v) : [];
        } catch (e) { return []; }
    };

    PdfViewer.prototype.saveBookmarks = function (bookmarks) {
        try {
            window.localStorage.setItem(this._storageKey('bookmarks'), JSON.stringify(bookmarks));
        } catch (e) { /* ignore */ }
    };

    PdfViewer.prototype.toggleBookmarkCurrentPage = function () {
        var bookmarks = this.readBookmarks();
        var page = this.pageNum;
        var existing = bookmarks.findIndex(function (b) { return b.page === page; });
        if (existing >= 0) {
            bookmarks.splice(existing, 1);
        } else {
            bookmarks.push({ page: page, addedAt: Date.now() });
            bookmarks.sort(function (a, b) { return a.page - b.page; });
        }
        this.saveBookmarks(bookmarks);
        this.renderBookmarksPanel();
        this.updateBookmarkButton();
    };

    PdfViewer.prototype.removeBookmark = function (page, event) {
        if (event) { event.stopPropagation(); }
        var bookmarks = this.readBookmarks().filter(function (b) { return b.page !== page; });
        this.saveBookmarks(bookmarks);
        this.renderBookmarksPanel();
        this.updateBookmarkButton();
    };

    PdfViewer.prototype.gotoBookmark = function (page) {
        if (!isNaN(page)) this.goToPage(page);
        // Закрываем панель после перехода, чтобы не мешала чтению
        var panel = this.wrapper.querySelector('[data-bookmarks-panel]');
        if (panel) panel.classList.remove('is-open');
    };

    PdfViewer.prototype.toggleBookmarksPanel = function () {
        var panel = this.wrapper.querySelector('[data-bookmarks-panel]');
        if (!panel) return;
        var willOpen = !panel.classList.contains('is-open');
        panel.classList.toggle('is-open', willOpen);
        if (willOpen) this.renderBookmarksPanel();
    };

    PdfViewer.prototype.renderBookmarksPanel = function () {
        var panel = this.wrapper.querySelector('[data-bookmarks-panel]');
        if (!panel) return;
        var bookmarks = this.readBookmarks();
        var page = this.pageNum;
        var isBookmarked = bookmarks.some(function (b) { return b.page === page; });

        var html = '<div class="bookmarks-panel-header">' +
            '<button type="button" data-action="bookmark-current" class="bookmark-toggle' + (isBookmarked ? ' is-active' : '') + '">' +
            '<i class="fas ' + (isBookmarked ? 'fa-bookmark' : 'fa-bookmark') + '"></i> ' +
            (isBookmarked ? 'Elimină marcaj de la pag. ' : 'Adaugă marcaj la pag. ') + page +
            '</button></div>';

        if (bookmarks.length === 0) {
            html += '<div class="bookmarks-empty">Niciun marcaj salvat încă</div>';
        } else {
            html += '<ul class="bookmarks-list">';
            bookmarks.forEach(function (b) {
                html += '<li data-page="' + b.page + '">' +
                    '<button type="button" data-action="goto-bookmark" class="bookmark-item">' +
                    '<i class="fas fa-bookmark"></i> Pagina ' + b.page +
                    '</button>' +
                    '<button type="button" data-action="remove-bookmark" class="bookmark-remove" aria-label="Șterge marcaj" title="Șterge">' +
                    '<i class="fas fa-times"></i>' +
                    '</button>' +
                    '</li>';
            });
            html += '</ul>';
        }
        panel.innerHTML = html;
    };

    PdfViewer.prototype.updateBookmarkButton = function () {
        var bookmarks = this.readBookmarks();
        var btn = this.wrapper.querySelector('[data-action="toggle-bookmarks"]');
        if (!btn) return;
        var count = bookmarks.length;
        var badge = btn.querySelector('.bookmark-count');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'bookmark-count';
                btn.appendChild(badge);
            }
            badge.textContent = count;
        } else if (badge) {
            badge.remove();
        }
    };

    /* ---------- Quote export (text selection → copy with citation) ---------- */

    PdfViewer.prototype.setupQuoteExport = function () {
        var self = this;
        // Используем mouseup на canvasContainer, чтобы поймать конец выделения
        // (выделение происходит в textLayer внутри)
        this.canvasContainer.addEventListener('mouseup', function () { self.maybeShowQuoteButton(); });
        this.canvasContainer.addEventListener('touchend', function () {
            // Mobile: чуть подождать, чтобы system selection menu появился
            setTimeout(function () { self.maybeShowQuoteButton(); }, 200);
        });
        // Hide on click outside
        document.addEventListener('mousedown', function (e) {
            if (self.quoteBtn && !self.quoteBtn.contains(e.target)) self.hideQuoteButton();
        });
    };

    PdfViewer.prototype.maybeShowQuoteButton = function () {
        var sel = window.getSelection();
        if (!sel || sel.isCollapsed) {
            this.hideQuoteButton();
            return;
        }
        var text = sel.toString().trim();
        if (text.length < 5) { this.hideQuoteButton(); return; }
        // Verify selection is inside our textLayer
        var range = sel.getRangeAt(0);
        var ancestor = range.commonAncestorContainer;
        var node = ancestor.nodeType === 1 ? ancestor : ancestor.parentNode;
        if (!node || !this.canvasContainer.contains(node)) {
            this.hideQuoteButton();
            return;
        }
        this.showQuoteButton(range, text);
    };

    PdfViewer.prototype.showQuoteButton = function (range, text) {
        if (!this.quoteBtn) {
            // Контейнер с двумя действиями: Citează (всегда) + Subliniază (только auth)
            this.quoteBtn = document.createElement('div');
            this.quoteBtn.className = 'pdf-quote-btn';
            var quoteAction = document.createElement('button');
            quoteAction.type = 'button';
            quoteAction.className = 'pdf-quote-btn-action';
            quoteAction.innerHTML = '<i class="fas fa-quote-right"></i> Citează';
            this.quoteBtn.appendChild(quoteAction);
            var self = this;
            quoteAction.addEventListener('click', function () { self.copyCitation(); });
            // Subliniază (highlight) — только для авторизованных
            if (this.config.userAuthenticated && this.config.contentId) {
                var highlightAction = document.createElement('button');
                highlightAction.type = 'button';
                highlightAction.className = 'pdf-quote-btn-action';
                highlightAction.innerHTML = '<i class="fas fa-highlighter"></i> Subliniază';
                highlightAction.addEventListener('click', function () { self.createAnnotationFromSelection(); });
                this.quoteBtn.appendChild(highlightAction);
            }
            // Append to wrapper (а не body) — иначе в native fullscreen будет невидим:
            // браузер рендерит только fullscreen-элемент + его потомков, всё снаружи скрыто.
            this.wrapper.appendChild(this.quoteBtn);
        }
        // position: fixed → viewport-relative coords, без window.scrollY.
        // Работает одинаково в обычном режиме, native fullscreen и pseudo-fullscreen.
        var rect = range.getBoundingClientRect();
        var top = rect.top - 46;
        if (top < 10) top = rect.bottom + 8;
        var left = rect.left + (rect.width / 2) - 60;
        this.quoteBtn.style.top = Math.max(10, top) + 'px';
        this.quoteBtn.style.left = Math.max(10, Math.min(left, window.innerWidth - 220)) + 'px';
        this.quoteBtn.classList.add('is-visible');
        this.quoteBtn.dataset.selectedText = text;
    };

    PdfViewer.prototype.hideQuoteButton = function () {
        if (this.quoteBtn) this.quoteBtn.classList.remove('is-visible');
    };

    PdfViewer.prototype._copyToClipboard = function (text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }
        return new Promise(function (resolve, reject) {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand('copy'); resolve(); } catch (e) { reject(e); }
            document.body.removeChild(ta);
        });
    };

    PdfViewer.prototype._flashQuoteBtn = function (label, ok) {
        if (!this.quoteBtn) return;
        var firstBtn = this.quoteBtn.querySelector('.pdf-quote-btn-action');
        if (!firstBtn) return;
        var orig = firstBtn.innerHTML;
        firstBtn.innerHTML = (ok ? '<i class="fas fa-check"></i> ' : '<i class="fas fa-times"></i> ') + label;
        var self = this;
        setTimeout(function () {
            if (firstBtn) firstBtn.innerHTML = orig;
            self.hideQuoteButton();
        }, 1500);
    };

    PdfViewer.prototype.copyCitation = function () {
        var text = this.quoteBtn ? this.quoteBtn.dataset.selectedText : '';
        if (!text) return;
        var citation = '"' + text + '"\n— ' + (this.config.title || 'Document') + ', pag. ' + this.pageNum;
        var self = this;
        this._copyToClipboard(citation)
            .then(function () { self._flashQuoteBtn('Copiat', true); })
            .catch(function () { self._flashQuoteBtn('Eroare', false); });
    };

    /* ---------- Server sync (Phase 3 — cross-device + annotations) ---------- */

    PdfViewer.prototype._getCsrfToken = function () {
        var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    };

    PdfViewer.prototype._apiFetch = function (url, options) {
        options = options || {};
        options.credentials = 'same-origin';
        options.headers = options.headers || {};
        if (options.method && options.method !== 'GET') {
            options.headers['Content-Type'] = 'application/json';
            options.headers['X-CSRFToken'] = this._getCsrfToken();
        }
        return fetch(url, options).then(function (resp) {
            if (resp.status === 401) {
                // User вышел из системы — fall back на localStorage без шума
                return Promise.reject({ silent: true, status: 401 });
            }
            return resp;
        });
    };

    PdfViewer.prototype._canSync = function () {
        return this.config.userAuthenticated && this.config.contentId &&
               (this.config.type === 'article' || this.config.type === 'book');
    };

    /**
     * On init: fetch server progress + annotations.
     * Server progress overrides local pageNum if present (cross-device source of truth),
     * unless URL hash is explicitly set (user shared a deep link).
     */
    PdfViewer.prototype.syncFromServer = function () {
        var self = this;
        if (!this._canSync()) return Promise.resolve();
        var hashPage = this.readPageFromHash();
        var url = '/api/reading-progress/' + this.config.type + '/' + this.config.contentId + '/';
        var p1 = this._apiFetch(url).then(function (resp) {
            if (!resp.ok) return null;
            return resp.json();
        }).then(function (data) {
            if (data && data.page && !hashPage) {
                // Только если URL hash не задан — иначе hash имеет приоритет
                self.pageNum = Math.max(1, Math.min(data.page, self.pdfDoc.numPages));
            }
        }).catch(function () { /* silent — fall back to local */ });

        var p2 = this._apiFetch('/api/annotations/' + this.config.type + '/' + this.config.contentId + '/')
            .then(function (resp) { return resp.ok ? resp.json() : { annotations: [] }; })
            .then(function (data) { self.annotations = (data && data.annotations) || []; })
            .catch(function () { self.annotations = []; });

        return Promise.all([p1, p2]);
    };

    PdfViewer.prototype.syncProgressDebounced = function () {
        if (!this._canSync()) return;
        var self = this;
        clearTimeout(this._syncProgressTimer);
        this._syncProgressTimer = setTimeout(function () {
            self._apiFetch('/api/reading-progress/save/', {
                method: 'POST',
                body: JSON.stringify({
                    type: self.config.type,
                    id: parseInt(self.config.contentId, 10),
                    page: self.pageNum,
                }),
            }).catch(function () { /* silent */ });
        }, 500);
    };

    /* ---------- Annotations (highlights, server-backed) ---------- */

    PdfViewer.prototype.createAnnotationFromSelection = function () {
        if (!this._canSync()) return;
        var sel = window.getSelection();
        if (!sel || sel.isCollapsed) return;
        var text = sel.toString().trim();
        if (text.length < 5) return;

        // КРИТИЧНО: захватываем span'ы из Range ДО async fetch.
        // На текущей странице мы знаем точные DOM-узлы, попавшие в selection —
        // text-based matching (для page-reload) не нужен здесь, всё уже в руке.
        var range = sel.getRangeAt(0);
        var textLayer = this.canvasContainer.querySelector('.textLayer');
        var spansToMark = [];
        if (textLayer) {
            var allSpans = textLayer.querySelectorAll('span');
            for (var i = 0; i < allSpans.length; i++) {
                if (range.intersectsNode(allSpans[i])) {
                    spansToMark.push(allSpans[i]);
                }
            }
        }

        var self = this;
        this._apiFetch('/api/annotations/save/', {
            method: 'POST',
            body: JSON.stringify({
                type: this.config.type,
                id: parseInt(this.config.contentId, 10),
                page: this.pageNum,
                text: text,
                color: 'yellow',
            }),
        }).then(function (resp) { return resp.json(); })
          .then(function (data) {
              if (data && data.ok && data.id) {
                  self.annotations.push({
                      id: data.id, page: data.page, text: data.text,
                      color: data.color, note: data.note || '',
                  });
                  // Применяем highlight на захваченные ранее span'ы — точное соответствие
                  // тому, что юзер реально выделил, без всякого text-matching.
                  spansToMark.forEach(function (span) {
                      span.classList.add('annotation-highlight', 'annotation-color-' + data.color);
                      span.dataset.annotationId = data.id;
                  });
                  self.updateAnnotationButton();
                  // Clear selection so quote button hides
                  if (window.getSelection) window.getSelection().removeAllRanges();
                  self._flashQuoteBtn('Salvat', true);
              } else {
                  self._flashQuoteBtn('Eroare', false);
              }
          }).catch(function () { self._flashQuoteBtn('Eroare', false); });
    };

    PdfViewer.prototype.removeAnnotation = function (id, event) {
        if (event) event.stopPropagation();
        if (!this._canSync()) return;
        var self = this;
        this._apiFetch('/api/annotations/' + id + '/', { method: 'DELETE' })
            .then(function (resp) {
                if (resp.ok) {
                    self.annotations = self.annotations.filter(function (a) { return a.id !== id; });
                    self.applyAnnotationsToCurrentPage();
                    self.renderAnnotationsPanel();
                    self.updateAnnotationButton();
                }
            }).catch(function () { /* silent */ });
    };

    PdfViewer.prototype.gotoAnnotation = function (id) {
        var ann = this.annotations.find(function (a) { return a.id === id; });
        if (!ann) return;
        var panel = this.wrapper.querySelector('[data-annotations-panel]');
        if (panel) panel.classList.remove('is-open');
        // Помним целевой annotationId — после рендера применяем scrollIntoView
        // (см. _scrollToTargetAnnotation, вызывается в конце applyAnnotationsToCurrentPage)
        this._pendingScrollAnnotationId = id;
        if (ann.page === this.pageNum) {
            // Уже на нужной странице — текстLayer уже в DOM, можно скроллить сразу
            this._scrollToTargetAnnotation();
        } else {
            this.goToPage(ann.page);
        }
    };

    PdfViewer.prototype._scrollToTargetAnnotation = function () {
        var id = this._pendingScrollAnnotationId;
        if (!id) return;
        this._pendingScrollAnnotationId = null;
        var span = this.canvasContainer.querySelector('[data-annotation-id="' + id + '"]');
        if (span && span.scrollIntoView) {
            span.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
    };

    PdfViewer.prototype.toggleAnnotationsPanel = function () {
        var panel = this.wrapper.querySelector('[data-annotations-panel]');
        if (!panel) return;
        var willOpen = !panel.classList.contains('is-open');
        panel.classList.toggle('is-open', willOpen);
        if (willOpen) this.renderAnnotationsPanel();
    };

    PdfViewer.prototype.renderAnnotationsPanel = function () {
        var panel = this.wrapper.querySelector('[data-annotations-panel]');
        if (!panel) return;
        if (!this._canSync()) {
            panel.innerHTML = '<div class="bookmarks-empty">Conectează-te pentru a folosi evidențieri sincronizate.</div>';
            return;
        }
        var html = '';
        if (this.annotations.length === 0) {
            html = '<div class="bookmarks-empty">Nicio evidențiere salvată. Selectează text și apasă "Subliniază".</div>';
        } else {
            html = '<ul class="bookmarks-list">';
            this.annotations.forEach(function (a) {
                var snippet = a.text.length > 80 ? a.text.slice(0, 77) + '...' : a.text;
                html += '<li data-annotation-id="' + a.id + '">' +
                    '<button type="button" data-action="goto-annotation" class="bookmark-item annotation-item annotation-color-' + a.color + '">' +
                    '<i class="fas fa-highlighter"></i> Pag. ' + a.page +
                    '<span class="annotation-snippet">' + escapeHtml(snippet) + '</span>' +
                    '</button>' +
                    '<button type="button" data-action="remove-annotation" class="bookmark-remove" aria-label="Șterge" title="Șterge">' +
                    '<i class="fas fa-times"></i>' +
                    '</button>' +
                    '</li>';
            });
            html += '</ul>';
        }
        panel.innerHTML = html;
    };

    PdfViewer.prototype.updateAnnotationButton = function () {
        var btn = this.wrapper.querySelector('[data-action="toggle-annotations"]');
        if (!btn) return;
        var count = this.annotations.length;
        var badge = btn.querySelector('.bookmark-count');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'bookmark-count';
                btn.appendChild(badge);
            }
            badge.textContent = count;
        } else if (badge) {
            badge.remove();
        }
    };

    /**
     * After renderPage(): mark all textLayer spans that overlap the saved annotation
     * text. Algorithm:
     *   1. Build fullText = concatenation of all span textContents on the page.
     *   2. Normalize whitespace (PDFs split text across spans with \n / extra spaces;
     *      Selection.toString() does the same — without normalization, indexOf
     *      misses real matches).
     *   3. Find FULL annotation text in normalized fullText (not just first N chars
     *      — short prefixes match similar phrases earlier on the page, so old impl
     *      highlighted wrong content way above the actual selection).
     *   4. Map matched [startNorm, endNorm] back to raw character offsets, then
     *      highlight every span whose range overlaps [startRaw, endRaw].
     * Avoids false positives + handles multi-span selections correctly.
     */
    PdfViewer.prototype.applyAnnotationsToCurrentPage = function () {
        if (!this.annotations || !this.annotations.length) return;
        var textLayer = this.canvasContainer.querySelector('.textLayer');
        if (!textLayer) return;
        var pageAnnotations = this.annotations.filter(function (a) { return a.page === this.pageNum; }, this);
        if (!pageAnnotations.length) return;

        var spans = textLayer.querySelectorAll('span');
        if (!spans.length) return;

        // Step 1: concat per-span text + record each span's raw character range
        var fullText = '';
        var spanRanges = [];
        for (var i = 0; i < spans.length; i++) {
            var t = spans[i].textContent || '';
            spanRanges.push({ span: spans[i], start: fullText.length, end: fullText.length + t.length });
            fullText += t;
        }

        // Step 2: build normalized text + raw↔norm position maps for resilient matching
        var rawToNorm = new Array(fullText.length);
        var normToRaw = [];
        var fullNorm = '';
        var prevWasSpace = true;
        for (var k = 0; k < fullText.length; k++) {
            var c = fullText.charAt(k);
            if (/\s/.test(c)) {
                if (prevWasSpace) {
                    rawToNorm[k] = -1;
                } else {
                    rawToNorm[k] = fullNorm.length;
                    normToRaw[fullNorm.length] = k;
                    fullNorm += ' ';
                }
                prevWasSpace = true;
            } else {
                rawToNorm[k] = fullNorm.length;
                normToRaw[fullNorm.length] = k;
                fullNorm += c;
                prevWasSpace = false;
            }
        }
        var fullNormLower = fullNorm.toLowerCase();

        pageAnnotations.forEach(function (ann) {
            var needleRaw = ann.text || '';
            if (needleRaw.length < 3) return;
            var needleNorm = needleRaw.replace(/\s+/g, ' ').trim();
            if (!needleNorm) return;
            var needleLower = needleNorm.toLowerCase();
            var startNorm = fullNormLower.indexOf(needleLower);
            if (startNorm === -1) {
                // Не нашли точное совпадение — annotation остаётся в БД, просто не подсвечивается на этой странице
                return;
            }
            var endNorm = startNorm + needleNorm.length - 1;  // inclusive
            var startRaw = normToRaw[startNorm];
            var endRaw = normToRaw[endNorm] !== undefined ? normToRaw[endNorm] : (fullText.length - 1);
            // Highlight every span whose raw range overlaps [startRaw, endRaw]
            spanRanges.forEach(function (sr) {
                if (sr.end > startRaw && sr.start <= endRaw) {
                    sr.span.classList.add('annotation-highlight', 'annotation-color-' + ann.color);
                    sr.span.dataset.annotationId = ann.id;
                }
            });
        });

        // Если кликнули по аннотации в списке и навигировали на эту страницу — скроллим к ней
        this._scrollToTargetAnnotation();
    };

    /* ---------- Persistence (last-read page + dark mode pref) ---------- */

    PdfViewer.prototype._storageKey = function (suffix) {
        // Per-PDF key — different documents track their own last page.
        // Падаем тихо если localStorage недоступен (Safari private, отключённые cookies).
        return 'pdf:' + this.config.url + ':' + suffix;
    };

    PdfViewer.prototype.readSavedPage = function () {
        try {
            var v = window.localStorage.getItem(this._storageKey('page'));
            return v ? parseInt(v, 10) : null;
        } catch (e) { return null; }
    };

    PdfViewer.prototype.savePage = function () {
        try {
            window.localStorage.setItem(this._storageKey('page'), String(this.pageNum));
        } catch (e) { /* ignore */ }
    };

    PdfViewer.prototype.readSavedDarkMode = function () {
        // Dark mode — глобальная настройка (не per-PDF), чтобы пользователь
        // выставил один раз и она работала для всех документов.
        try {
            return window.localStorage.getItem('pdf:dark-mode') === '1';
        } catch (e) { return false; }
    };

    PdfViewer.prototype.saveDarkMode = function () {
        try {
            window.localStorage.setItem('pdf:dark-mode', this.isDarkMode ? '1' : '0');
        } catch (e) { /* ignore */ }
    };

    PdfViewer.prototype.toggleDarkMode = function () {
        this.isDarkMode = !this.isDarkMode;
        this.applyDarkMode(this.isDarkMode);
        this.saveDarkMode();
    };

    PdfViewer.prototype.applyDarkMode = function (isDark) {
        this.viewer.classList.toggle('pdf-dark', !!isDark);
        // Update icon (moon ↔ sun)
        var icon = this.wrapper.querySelector('[data-action="toggle-dark"] i');
        if (icon) icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        var btn = this.wrapper.querySelector('[data-action="toggle-dark"]');
        if (btn) btn.title = isDark ? 'Mod luminos' : 'Mod întunecat';
    };

    /* ---------- Zoom ---------- */

    PdfViewer.prototype.setZoom = function (value) {
        this.currentZoomMode = value;
        // Числовые значения интерпретируются как множитель fit-width (см. renderPage).
        this.queueRenderPage(this.pageNum);
    };

    PdfViewer.prototype._currentZoomNumeric = function () {
        // Возвращает текущий зум как число (множитель fit-width).
        // Для page-width / auto возвращает 1 (это и есть 100% fit).
        var v = parseFloat(this.currentZoomMode);
        return isNaN(v) ? 1 : v;
    };

    PdfViewer.prototype.zoomIn = function () {
        if (!this.zoomSelect) return;
        var current = this._currentZoomNumeric();
        var newPct = Math.min(current + 0.25, 3);
        var newStr = newPct.toString();
        this.currentZoomMode = newStr;
        // Sync select if value matches an option, otherwise select stays at current selection
        var matched = false;
        for (var i = 0; i < this.zoomSelect.options.length; i++) {
            if (this.zoomSelect.options[i].value === newStr) { matched = true; break; }
        }
        if (matched) this.zoomSelect.value = newStr;
        this.queueRenderPage(this.pageNum);
    };

    PdfViewer.prototype.zoomOut = function () {
        if (!this.zoomSelect) return;
        var current = this._currentZoomNumeric();
        var newPct = Math.max(current - 0.25, 0.25);
        var newStr = newPct.toString();
        this.currentZoomMode = newStr;
        var matched = false;
        for (var i = 0; i < this.zoomSelect.options.length; i++) {
            if (this.zoomSelect.options[i].value === newStr) { matched = true; break; }
        }
        if (matched) this.zoomSelect.value = newStr;
        this.queueRenderPage(this.pageNum);
    };

    /* ---------- Fullscreen (native + iOS pseudo fallback) ---------- */

    PdfViewer.prototype.isNativeFSActive = function () {
        var fsEl = document.fullscreenElement || document.webkitFullscreenElement;
        return !!fsEl && (fsEl === this.wrapper || this.wrapper.contains(fsEl));
    };
    PdfViewer.prototype.isPseudoFSActive = function () {
        return this.wrapper.classList.contains('is-pseudo-fullscreen');
    };
    PdfViewer.prototype.updateFullscreenBtnIcon = function () {
        var btn = this.wrapper.querySelector('.fullscreen-btn i');
        if (!btn) return;
        if (this.isNativeFSActive() || this.isPseudoFSActive()) {
            btn.className = 'fas fa-compress';
            btn.parentElement.title = 'Ieșire din ecran complet';
        } else {
            btn.className = 'fas fa-expand';
            btn.parentElement.title = 'Ecran complet';
        }
    };
    PdfViewer.prototype.enterPseudoFullscreen = function () {
        var self = this;
        // Класс на wrapper (а не на viewer) — потому что controls/bookmarks/dark-toggle
        // живут ВНЕ pdf-viewer-container, в самом wrapper. Иначе в fullscreen они невидимы.
        this.wrapper.classList.add('is-pseudo-fullscreen');
        document.body.classList.add('pdf-fullscreen-open');
        this.updateFullscreenBtnIcon();
        setTimeout(function () { self.queueRenderPage(self.pageNum); }, 60);
    };
    PdfViewer.prototype.exitPseudoFullscreen = function () {
        var self = this;
        this.wrapper.classList.remove('is-pseudo-fullscreen');
        document.body.classList.remove('pdf-fullscreen-open');
        this.updateFullscreenBtnIcon();
        setTimeout(function () { self.queueRenderPage(self.pageNum); }, 60);
    };
    PdfViewer.prototype.toggleFullscreen = function () {
        var self = this;
        if (this.isPseudoFSActive()) { this.exitPseudoFullscreen(); return; }
        if (this.isNativeFSActive()) {
            (document.exitFullscreen || document.webkitExitFullscreen).call(document);
            return;
        }
        // Запрашиваем fullscreen на wrapper, а не на pdf-viewer-container —
        // чтобы pdf-controls (search/zoom/bookmarks/annotations/dark-mode) тоже попали внутрь.
        var req = this.wrapper.requestFullscreen || this.wrapper.webkitRequestFullscreen;
        if (req) {
            var p = req.call(this.wrapper);
            if (p && typeof p.catch === 'function') {
                p.catch(function () { self.enterPseudoFullscreen(); });
            }
            setTimeout(function () { self.queueRenderPage(self.pageNum); }, 250);
        } else {
            this.enterPseudoFullscreen();
        }
    };

    /* ---------- Search (custom implementation) ----------
     * We don't use pdfjsViewer.PDFFindController because it's tightly coupled
     * to PDFViewer (full pdf.js viewer), and we have custom canvas rendering.
     * Our impl is simpler and works with our setup:
     *   1. buildSearchIndex(): on PDF load, extract text from every page
     *      (cached in this.searchIndex = [{pageNum, text}])
     *   2. search(query): scan index for case-insensitive matches, build
     *      this.searchMatches = [{pageNum, indexInPage}]
     *   3. nextMatch / prevMatch: navigate this.currentMatchIdx, jump to
     *      that page, then highlight on render
     *   4. After each renderPage(): scan textLayer spans on the visible
     *      page and mark matching spans with .highlight (and .selected
     *      for current match)
     */

    PdfViewer.prototype.buildSearchIndex = function () {
        var self = this;
        if (!this.pdfDoc) return;
        this.searchIndex = [];
        var promises = [];
        for (var i = 1; i <= this.pdfDoc.numPages; i++) {
            (function (pageNum) {
                promises.push(
                    self.pdfDoc.getPage(pageNum)
                        .then(function (page) { return page.getTextContent(); })
                        .then(function (textContent) {
                            var text = textContent.items.map(function (item) {
                                return item.str;
                            }).join(' ');
                            self.searchIndex[pageNum - 1] = { pageNum: pageNum, text: text };
                        })
                );
            })(i);
        }
        Promise.all(promises).then(function () {
            // Index ready — if user already typed something while indexing, re-run search
            if (self.searchQuery) self.search(self.searchQuery);
        }).catch(function (e) {
            console.warn('[pdf-viewer] Failed to build search index:', e);
        });
    };

    PdfViewer.prototype.openSearch = function () {
        if (!this.searchBar) return;
        this.searchBar.classList.add('is-open');
        if (this.searchInput) {
            this.searchInput.focus();
            this.searchInput.select();
        }
    };

    PdfViewer.prototype.closeSearch = function () {
        if (!this.searchBar) return;
        this.searchBar.classList.remove('is-open');
        if (this.searchInput) this.searchInput.value = '';
        if (this.matchCounter) this.matchCounter.textContent = '';
        this.searchQuery = '';
        this.searchMatches = [];
        this.currentMatchIdx = -1;
        this.clearHighlights();
    };

    PdfViewer.prototype.isSearchOpen = function () {
        return this.searchBar && this.searchBar.classList.contains('is-open');
    };

    PdfViewer.prototype.search = function (query) {
        query = (query || '').trim();
        this.searchQuery = query;
        this.searchMatches = [];
        this.currentMatchIdx = -1;
        if (!query) {
            this.updateMatchCounter();
            this.clearHighlights();
            return;
        }
        if (!this.searchIndex || !this.searchIndex.length) {
            // Index not ready yet — show pending state
            if (this.matchCounter) this.matchCounter.textContent = 'Caut...';
            return;
        }
        var queryLower = query.toLowerCase();
        for (var i = 0; i < this.searchIndex.length; i++) {
            var entry = this.searchIndex[i];
            if (!entry || !entry.text) continue;
            var textLower = entry.text.toLowerCase();
            var idx = 0;
            while ((idx = textLower.indexOf(queryLower, idx)) !== -1) {
                this.searchMatches.push({ pageNum: entry.pageNum, indexInPage: idx });
                idx += queryLower.length;
            }
        }
        if (this.searchMatches.length > 0) {
            this.currentMatchIdx = 0;
            this.jumpToCurrentMatch();
        }
        this.updateMatchCounter();
        this.highlightMatchesOnCurrentPage();
    };

    PdfViewer.prototype.nextMatch = function () {
        if (!this.searchMatches.length) return;
        this.currentMatchIdx = (this.currentMatchIdx + 1) % this.searchMatches.length;
        this.jumpToCurrentMatch();
        this.updateMatchCounter();
    };

    PdfViewer.prototype.prevMatch = function () {
        if (!this.searchMatches.length) return;
        this.currentMatchIdx = (this.currentMatchIdx - 1 + this.searchMatches.length) % this.searchMatches.length;
        this.jumpToCurrentMatch();
        this.updateMatchCounter();
    };

    PdfViewer.prototype.jumpToCurrentMatch = function () {
        var match = this.searchMatches[this.currentMatchIdx];
        if (!match) return;
        if (match.pageNum !== this.pageNum) {
            this.goToPage(match.pageNum);
            // highlight will be applied after render via highlightMatchesOnCurrentPage()
        } else {
            this.highlightMatchesOnCurrentPage();
        }
    };

    PdfViewer.prototype.updateMatchCounter = function () {
        if (!this.matchCounter) return;
        if (!this.searchQuery) {
            this.matchCounter.textContent = '';
            this.matchCounter.classList.remove('is-empty');
        } else if (this.searchMatches.length === 0) {
            this.matchCounter.textContent = 'Niciun rezultat';
            this.matchCounter.classList.add('is-empty');
        } else {
            this.matchCounter.textContent = (this.currentMatchIdx + 1) + ' / ' + this.searchMatches.length;
            this.matchCounter.classList.remove('is-empty');
        }
    };

    PdfViewer.prototype.clearHighlights = function () {
        var spans = this.canvasContainer.querySelectorAll('.textLayer .highlight');
        spans.forEach(function (s) { s.classList.remove('highlight', 'selected'); });
    };

    PdfViewer.prototype.highlightMatchesOnCurrentPage = function () {
        // Wait for textLayer to render (a few async frames)
        var self = this;
        setTimeout(function () { self._doHighlight(); }, 50);
    };

    PdfViewer.prototype._doHighlight = function () {
        if (!this.searchQuery) return;
        var queryLower = this.searchQuery.toLowerCase();
        var textLayer = this.canvasContainer.querySelector('.textLayer');
        if (!textLayer) return;

        // Clear previous highlights
        var oldHighlights = textLayer.querySelectorAll('.highlight');
        oldHighlights.forEach(function (s) { s.classList.remove('highlight', 'selected'); });

        // Find which match index is the "selected" one (if on current page)
        var currentMatchOnPage = null;
        if (this.searchMatches[this.currentMatchIdx] &&
            this.searchMatches[this.currentMatchIdx].pageNum === this.pageNum) {
            // Count which match-on-page index this is
            var pageMatchCount = 0;
            for (var i = 0; i <= this.currentMatchIdx; i++) {
                if (this.searchMatches[i].pageNum === this.pageNum) {
                    if (i === this.currentMatchIdx) {
                        currentMatchOnPage = pageMatchCount;
                    }
                    pageMatchCount++;
                }
            }
        }

        // Highlight all matching spans on this page
        var spans = textLayer.querySelectorAll('span');
        var matchOnPageIdx = 0;
        var firstSelectedSpan = null;
        spans.forEach(function (span) {
            var spanTextLower = (span.textContent || '').toLowerCase();
            var idx = spanTextLower.indexOf(queryLower);
            if (idx !== -1) {
                span.classList.add('highlight');
                if (matchOnPageIdx === currentMatchOnPage) {
                    span.classList.add('selected');
                    if (!firstSelectedSpan) firstSelectedSpan = span;
                }
                matchOnPageIdx++;
            }
        });

        // Scroll selected match into view
        if (firstSelectedSpan && firstSelectedSpan.scrollIntoView) {
            firstSelectedSpan.scrollIntoView({ block: 'center', behavior: 'smooth' });
        }
    };

    /* ---------- Keyboard ---------- */

    PdfViewer.prototype.handleKeydown = function (e) {
        // Don't interfere when typing in non-search inputs
        if (e.target.matches && e.target.matches('input, textarea, [contenteditable]')
            && !e.target.matches('[data-pdf-search-input]')) {
            return;
        }

        // Cmd/Ctrl+F → open our search (preventDefault avoids browser's text-find which can't see PDF canvas)
        if ((e.metaKey || e.ctrlKey) && (e.key === 'f' || e.key === 'F')) {
            // Only intercept if we have a search bar (i.e. PDF viewer is on this page)
            if (this.searchBar) {
                e.preventDefault();
                this.openSearch();
                return;
            }
        }

        // Esc closes search OR exits pseudo-fullscreen
        if (e.key === 'Escape') {
            if (this.isSearchOpen()) {
                e.preventDefault();
                this.closeSearch();
                return;
            }
            if (this.isPseudoFSActive()) {
                this.exitPseudoFullscreen();
                return;
            }
        }

        // Don't paginate while search is focused (Enter/Shift+Enter handled in search input listener)
        if (this.isSearchOpen() && document.activeElement === this.searchInput) return;

        if (!this.pdfDoc) return;

        switch (e.key) {
            case 'ArrowLeft':
            case 'PageUp':
                this.previousPage();
                break;
            case 'ArrowRight':
            case 'PageDown':
            case ' ':
                e.preventDefault();
                this.nextPage();
                break;
            case 'Home':
                this.goToPage(1);
                break;
            case 'End':
                this.goToPage(this.pdfDoc.numPages);
                break;
        }
    };

    /* ---------- Touch (mobile) ---------- */

    PdfViewer.prototype.setupTouchGestures = function () {
        var self = this;
        var touchStartX = 0, touchStartY = 0;
        var touchEndX = 0, touchEndY = 0;
        var initialDistance = 0, initialScale = 1;

        this.viewer.addEventListener('touchstart', function (e) {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
            if (e.touches.length === 2) {
                initialDistance = Math.hypot(
                    e.touches[0].pageX - e.touches[1].pageX,
                    e.touches[0].pageY - e.touches[1].pageY
                );
                initialScale = self.scale;
            }
        }, { passive: true });

        this.viewer.addEventListener('touchend', function (e) {
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            var deltaX = touchEndX - touchStartX;
            var deltaY = touchEndY - touchStartY;
            // Only horizontal swipes count
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > SWIPE_THRESHOLD_PX) {
                if (deltaX < 0) self.nextPage();
                else self.previousPage();
            }
        }, { passive: true });

        this.viewer.addEventListener('touchmove', function (e) {
            if (e.touches.length === 2) {
                var distance = Math.hypot(
                    e.touches[0].pageX - e.touches[1].pageX,
                    e.touches[0].pageY - e.touches[1].pageY
                );
                var newScale = Math.min(3, Math.max(0.5, initialScale * (distance / initialDistance)));
                if (Math.abs(newScale - self.scale) > 0.1) {
                    self.scale = newScale;
                    self.currentZoomMode = newScale.toString();
                    self.queueRenderPage(self.pageNum);
                }
            }
        }, { passive: true });
    };

    /* ===================================================
     * Helper functions
     * =================================================== */

    function loadScript(src, onload) {
        var existing = document.querySelector('script[data-src="' + src + '"]');
        if (existing) {
            existing.addEventListener('load', onload);
            return;
        }
        var s = document.createElement('script');
        s.src = src;
        s.dataset.src = src;
        s.onload = onload;
        s.onerror = function () { console.error('[pdf-viewer] Failed to load:', src); };
        document.head.appendChild(s);
    }

    function onceTransitionEnd(el, fallbackMs) {
        return new Promise(function (resolve) {
            var done = false;
            var finish = function () { if (!done) { done = true; resolve(); } };
            el.addEventListener('transitionend', finish, { once: true });
            setTimeout(finish, fallbackMs);
        });
    }

    function onceAnimationEnd(el, fallbackMs) {
        return new Promise(function (resolve) {
            var done = false;
            var finish = function () { if (!done) { done = true; resolve(); } };
            el.addEventListener('animationend', finish, { once: true });
            setTimeout(finish, fallbackMs);
        });
    }

    function escapeHtml(s) {
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /* ===================================================
     * Boot
     * =================================================== */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

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
        };
        this.pdfDoc = null;
        this.pageNum = this.readPageFromHash() || 1;
        this.scale = 1;
        this.currentZoomMode = 'page-width';
        this.isAnimating = false;
        this.isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        this.prefersReducedMotion = window.matchMedia &&
            window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        // Search state
        this.findController = null;
        this.eventBus = null;
        this.pdfViewerComponents = null;  // pdfjsViewer module reference

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
        this.pdfViewerComponents = window.pdfjsViewer;

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
            // Setup search controller
            self.initSearch();
            // Render first page
            self.renderPage(self.pageNum);
            self.updateNavButtons();
            self.updateProgress();
            // For mobile: page-width zoom
            if (self.isMobile && self.zoomSelect) {
                self.zoomSelect.value = 'page-width';
                self.setZoom('page-width');
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
            case 'toggle-search':   this.openSearch(); break;
            case 'close-search':    this.closeSearch(); break;
            case 'next-match':      this.nextMatch(); break;
            case 'prev-match':      this.prevMatch(); break;
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

            // Calculate viewport
            var viewport;
            if (self.currentZoomMode === 'auto' || self.currentZoomMode === 'page-width') {
                var containerWidth = self.canvasContainer.clientWidth - 10;
                var tempViewport = page.getViewport({ scale: 1 });
                var desiredScale = self.currentZoomMode === 'page-width'
                    ? (containerWidth * 0.98) / tempViewport.width
                    : Math.min(containerWidth / tempViewport.width,
                              (window.innerHeight - 200) / tempViewport.height);
                viewport = page.getViewport({ scale: desiredScale });
                self.scale = desiredScale;
            } else {
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

                // Text layer for search + text selection
                var textLayerDiv = document.createElement('div');
                textLayerDiv.className = 'textLayer';
                textLayerDiv.style.position = 'absolute';
                textLayerDiv.style.top = '0';
                textLayerDiv.style.left = '0';
                textLayerDiv.style.width = Math.floor(viewport.width) + 'px';
                textLayerDiv.style.height = Math.floor(viewport.height) + 'px';
                pageDiv.appendChild(textLayerDiv);

                self.canvasContainer.appendChild(pageDiv);

                if (self.currentPageEl) self.currentPageEl.textContent = num;
                self.updateProgress();
                self.canvasContainer.scrollTop = 0;

                // Render text layer asynchronously (doesn't block UI)
                return page.getTextContent().then(function (textContent) {
                    if (!window.pdfjsLib.renderTextLayer) return;
                    window.pdfjsLib.renderTextLayer({
                        textContent: textContent,
                        container: textLayerDiv,
                        viewport: viewport,
                        textDivs: [],
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

    /* ---------- Zoom ---------- */

    PdfViewer.prototype.setZoom = function (value) {
        this.currentZoomMode = value;
        if (value !== 'auto' && value !== 'page-width') {
            this.scale = parseFloat(value);
        }
        this.queueRenderPage(this.pageNum);
    };

    PdfViewer.prototype.zoomIn = function () {
        if (!this.zoomSelect) return;
        var current = parseFloat(this.zoomSelect.value);
        if (!isNaN(current) && current < 3) {
            var newScale = Math.min(current + 0.25, 3);
            this.scale = newScale;
            this.currentZoomMode = newScale.toString();
            this.zoomSelect.value = newScale.toString();
            this.queueRenderPage(this.pageNum);
        }
    };

    PdfViewer.prototype.zoomOut = function () {
        if (!this.zoomSelect) return;
        var current = parseFloat(this.zoomSelect.value);
        if (!isNaN(current) && current > 0.25) {
            var newScale = Math.max(current - 0.25, 0.25);
            this.scale = newScale;
            this.currentZoomMode = newScale.toString();
            this.zoomSelect.value = newScale.toString();
            this.queueRenderPage(this.pageNum);
        }
    };

    /* ---------- Fullscreen (native + iOS pseudo fallback) ---------- */

    PdfViewer.prototype.isNativeFSActive = function () {
        return !!(document.fullscreenElement || document.webkitFullscreenElement);
    };
    PdfViewer.prototype.isPseudoFSActive = function () {
        return document.body.classList.contains('pdf-fullscreen-open');
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
        this.viewer.classList.add('is-pseudo-fullscreen');
        document.body.classList.add('pdf-fullscreen-open');
        this.updateFullscreenBtnIcon();
        setTimeout(function () { self.queueRenderPage(self.pageNum); }, 60);
    };
    PdfViewer.prototype.exitPseudoFullscreen = function () {
        var self = this;
        this.viewer.classList.remove('is-pseudo-fullscreen');
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
        var req = this.viewer.requestFullscreen || this.viewer.webkitRequestFullscreen;
        if (req) {
            var p = req.call(this.viewer);
            if (p && typeof p.catch === 'function') {
                p.catch(function () { self.enterPseudoFullscreen(); });
            }
            setTimeout(function () { self.queueRenderPage(self.pageNum); }, 250);
        } else {
            this.enterPseudoFullscreen();
        }
    };

    /* ---------- Search (PDFFindController) ---------- */

    PdfViewer.prototype.initSearch = function () {
        if (!this.pdfViewerComponents || !this.searchInput) return;
        var self = this;
        this.eventBus = new this.pdfViewerComponents.EventBus();
        var linkService = new this.pdfViewerComponents.PDFLinkService({ eventBus: this.eventBus });
        this.findController = new this.pdfViewerComponents.PDFFindController({
            linkService: linkService,
            eventBus: this.eventBus,
        });
        this.findController.setDocument(this.pdfDoc);

        var handler = function (state) { self.handleFindResults(state); };
        this.eventBus.on('updatefindmatchescount', handler);
        this.eventBus.on('updatefindcontrolstate', handler);

        // When search jumps to a different page, sync our viewer
        this.eventBus.on('updatefindmatchescount', function (state) {
            if (self.findController.pageMatches && self.findController.selected) {
                var targetPage = self.findController.selected.pageIdx + 1;
                if (targetPage && targetPage !== self.pageNum) {
                    self.goToPage(targetPage);
                }
            }
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
        if (this.findController && this.eventBus) {
            this.eventBus.dispatch('find', {
                source: this,
                type: '',
                query: '',
                phraseSearch: true,
                caseSensitive: false,
                entireWord: false,
                highlightAll: false,
                findPrevious: false,
            });
        }
    };

    PdfViewer.prototype.isSearchOpen = function () {
        return this.searchBar && this.searchBar.classList.contains('is-open');
    };

    PdfViewer.prototype.search = function (query) {
        if (!this.findController || !this.eventBus) return;
        this.eventBus.dispatch('find', {
            source: this,
            type: '',
            query: query || '',
            phraseSearch: true,
            caseSensitive: false,
            entireWord: false,
            highlightAll: true,
            findPrevious: false,
        });
    };

    PdfViewer.prototype.nextMatch = function () {
        if (!this.eventBus) return;
        this.eventBus.dispatch('findagain', {
            source: this,
            type: 'again',
            query: this.searchInput ? this.searchInput.value : '',
            phraseSearch: true,
            caseSensitive: false,
            entireWord: false,
            highlightAll: true,
            findPrevious: false,
        });
    };

    PdfViewer.prototype.prevMatch = function () {
        if (!this.eventBus) return;
        this.eventBus.dispatch('findagain', {
            source: this,
            type: 'again',
            query: this.searchInput ? this.searchInput.value : '',
            phraseSearch: true,
            caseSensitive: false,
            entireWord: false,
            highlightAll: true,
            findPrevious: true,
        });
    };

    PdfViewer.prototype.handleFindResults = function (state) {
        if (!this.matchCounter) return;
        // state.matchesCount = { current, total }
        var mc = state && state.matchesCount;
        if (mc && mc.total > 0) {
            this.matchCounter.textContent = mc.current + ' / ' + mc.total;
            this.matchCounter.classList.remove('is-empty');
        } else if (this.searchInput && this.searchInput.value.length > 0) {
            this.matchCounter.textContent = 'Niciun rezultat';
            this.matchCounter.classList.add('is-empty');
        } else {
            this.matchCounter.textContent = '';
            this.matchCounter.classList.remove('is-empty');
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

    /* ===================================================
     * Boot
     * =================================================== */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

/* Cookie consent / GDPR banner.
 *
 * Stores user choice in localStorage under STORAGE_KEY for CONSENT_TTL_DAYS.
 * Loads analytics (GTM, Clarity) ONLY after user opts in.
 * Re-prompts after expiration.
 *
 * Public API on window:
 *   window.loadGTM()     — defined in base.html, called on analytics consent
 *   window.loadClarity() — defined in base.html, called on analytics consent
 *   window.openCookieSettings() — re-open banner from footer link
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'cookie_consent_v1';
    var CONSENT_TTL_DAYS = 365;

    function readConsent() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            var parsed = JSON.parse(raw);
            if (!parsed || !parsed.timestamp) return null;
            var ageMs = Date.now() - new Date(parsed.timestamp).getTime();
            if (ageMs > CONSENT_TTL_DAYS * 24 * 60 * 60 * 1000) return null;
            return parsed;
        } catch (e) {
            return null;
        }
    }

    function writeConsent(choice) {
        var payload = {
            essential: true,
            analytics: !!choice.analytics,
            marketing: !!choice.marketing,
            timestamp: new Date().toISOString()
        };
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
        } catch (e) { /* private mode etc. — silent */ }
        return payload;
    }

    function applyConsent(consent) {
        if (consent.analytics) {
            if (typeof window.loadGTM === 'function') window.loadGTM();
            if (typeof window.loadClarity === 'function') window.loadClarity();
        }
        // Marketing reserved for future ad platforms.
    }

    function showBanner(banner) {
        banner.hidden = false;
        // Force reflow then add visible class for slide-up animation
        // eslint-disable-next-line no-unused-expressions
        banner.offsetHeight;
        banner.classList.add('is-visible');
    }

    function hideBanner(banner) {
        banner.classList.remove('is-visible');
        setTimeout(function () { banner.hidden = true; }, 320);
    }

    function readCategoryChoices(banner) {
        return {
            analytics: !!banner.querySelector('[data-category="analytics"]').checked,
            marketing: !!banner.querySelector('[data-category="marketing"]').checked
        };
    }

    function bindBanner(banner) {
        var choicesEl = banner.querySelector('#cookie-choices');
        var customizeBtn = banner.querySelector('[data-cookie-action="customize"]');
        var saveBtn = banner.querySelector('[data-cookie-action="save"]');
        var acceptAllBtn = banner.querySelector('[data-cookie-action="accept-all"]');

        customizeBtn.addEventListener('click', function () {
            choicesEl.hidden = false;
            customizeBtn.hidden = true;
            saveBtn.hidden = false;
        });

        saveBtn.addEventListener('click', function () {
            var consent = writeConsent(readCategoryChoices(banner));
            applyConsent(consent);
            hideBanner(banner);
        });

        acceptAllBtn.addEventListener('click', function () {
            var consent = writeConsent({ analytics: true, marketing: true });
            applyConsent(consent);
            hideBanner(banner);
        });
    }

    function reopenForReview(banner) {
        var existing = readConsent();
        if (existing) {
            banner.querySelector('[data-category="analytics"]').checked = !!existing.analytics;
            banner.querySelector('[data-category="marketing"]').checked = !!existing.marketing;
            // jump straight to customize panel
            banner.querySelector('#cookie-choices').hidden = false;
            banner.querySelector('[data-cookie-action="customize"]').hidden = true;
            banner.querySelector('[data-cookie-action="save"]').hidden = false;
        }
        showBanner(banner);
    }

    document.addEventListener('DOMContentLoaded', function () {
        var banner = document.getElementById('cookie-banner');
        if (!banner) return;

        bindBanner(banner);

        var consent = readConsent();
        if (consent) {
            applyConsent(consent);
        } else {
            // small delay so banner doesn't jump in before page paint
            setTimeout(function () { showBanner(banner); }, 600);
        }

        window.openCookieSettings = function () { reopenForReview(banner); };
    });
})();

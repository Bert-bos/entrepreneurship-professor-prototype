/*!
 * ep-brand-library.js
 * The Editorial Index — Brand Library nav item, per CREATIVE decision package
 * "CREATIVE DECISION PACKAGE — EP BRAND LIBRARY + MOBILE HEADER" (approved
 * direction: The Editorial Index), Bert's approval 2026-09-08.
 *
 * Implements EP Brand Library Requirements Package v3's six canonical
 * collections as a read-only, synthetic-data-only preview surface. No real
 * Drive URLs, no student data, no write-back controls, no third-party
 * requests. All source-open actions are inert ("Available after
 * classification") per v3 R3/§3 until each record type clears its own
 * privacy/classification pass.
 *
 * Registers a new `brandlibrary` page into the existing `pages` object
 * defined in app.js (shared top-level scope across classic <script> tags,
 * same pattern already used by enhancements.js in this app).
 */
(function () {
  'use strict';

  var brandLibraryCollections = [
    { id: 'story-bank', mono: '❝', name: 'Story, Experience & Content Bank',
      purpose: 'What happened, why it matters, and how it could be used.',
      samples: [
        { a: 'Aug 14, 2026', b: 'A founder underestimated legal cost before it derailed a launch.', c: 'Short-form warning story' },
        { a: 'Jul 30, 2026', b: 'A student pivoted after one blunt customer conversation.', c: 'Classroom case study' },
        { a: 'Jul 2, 2026', b: 'A mentor’s one-line reframe changed a pricing decision.', c: 'Quote card' }
      ] },
    { id: 'content-pipeline', mono: '→', name: 'Content Pipeline',
      purpose: 'Production-ready ideas waiting for their next step.',
      samples: [
        { a: 'Ready to record', b: 'Short-form video', c: 'This week’s Reel' },
        { a: 'Scripted', b: 'LinkedIn post', c: 'Monday send' },
        { a: 'Needs a hook', b: 'YouTube Short', c: 'Queued' }
      ] },
    { id: 'story-radar', mono: '◉', name: 'Personal Brand Story Radar',
      purpose: 'Outside signals worth a Personal Brand reaction, tracked until they age out.',
      samples: [
        { a: 'Founder-education trend piece', b: 'High relevance', c: '48-hour window' },
        { a: 'Creator-economy shift', b: 'Medium relevance', c: '5-day window' },
        { a: 'Campus entrepreneurship survey', b: 'High relevance', c: '2-week window' }
      ] },
    { id: 'audience-outreach', mono: '◇', name: 'Audience Growth Outreach',
      purpose: 'Accounts and openings worth a deliberate next touch.',
      samples: [
        { a: 'Podcast host', b: 'Guest slot open', c: 'Warm intro ready' },
        { a: 'Creator peer', b: 'Collaboration proposed', c: 'Awaiting reply' },
        { a: 'Media contact', b: 'Recurring source request', c: 'Quarterly check-in' }
      ] },
    { id: 'teaching-bank', mono: '▤', name: 'Teaching Story Bank',
      purpose: 'Class-ready examples drawn from real teaching moments.',
      flagged: true,
      samples: [
        { a: 'ENT 330', b: 'When a team ignored its first negative signal', c: 'Classification required' },
        { a: 'ENT 410', b: 'Why a pricing test beat a pricing debate', c: 'Classification required' },
        { a: 'Guest lecture', b: 'A cold outreach that actually worked', c: 'Classification required' }
      ] },
    { id: 'researcher-db', mono: '▥', name: 'Researcher & Seminal Literature Database',
      purpose: 'Foundational research and attribution for classroom and content use.',
      samples: [
        { a: 'Effectuation literature', b: 'Means-driven decision making', c: 'Attribution verified' },
        { a: 'Lean startup research', b: 'Validated learning', c: 'Attribution verified' },
        { a: 'Bricolage studies', b: 'Resource constraints as advantage', c: 'Attribution pending' }
      ] }
  ];

  function card(c) {
    var flagHtml = c.flagged
      ? '<span class="bl-flag">Classification required · student-identifiable material may be present</span>'
      : '';
    var previewHtml = c.samples.slice(0, 2).map(function (s) {
      return '<li><b>' + s.a + '</b><span>' + s.b + '</span><small>' + s.c + '</small></li>';
    }).join('');
    var panelHtml = c.samples.map(function (s) {
      return '<div class="bl-sample-row"><b>' + s.a + '</b><span>' + s.b + '</span><small>' + s.c + '</small></div>';
    }).join('');
    return '<article class="bl-card' + (c.flagged ? ' bl-card-flagged' : '') + '" data-bl-card="' + c.id + '">' +
      '<div class="bl-card-head"><span class="bl-mono" aria-hidden="true">' + c.mono + '</span><h3>' + c.name + '</h3></div>' +
      '<p class="bl-purpose">' + c.purpose + '</p>' +
      flagHtml +
      '<ul class="bl-samples">' + previewHtml + '</ul>' +
      '<button type="button" class="bl-expand" data-bl-expand="' + c.id + '" aria-expanded="false" aria-controls="bl-panel-' + c.id + '">Show all ' + c.samples.length + ' sample records</button>' +
      '<div class="bl-panel" id="bl-panel-' + c.id + '" hidden>' + panelHtml + '</div>' +
      '<button type="button" class="bl-source" disabled title="Available after classification">Open source · Available after classification</button>' +
      '</article>';
  }

  function brandlibrary() {
    return '' +
      '<div class="bl-head">' +
        '<div><h1>Brand Library</h1><p>Your source-backed stories, ideas, audiences, and research—organized for reuse.</p></div>' +
        '<div class="bl-status"><span class="pill">Interactive design · sample data</span><small>Preview only. Source links remain unavailable until each library is cleared.</small></div>' +
      '</div>' +
      '<div class="bl-overview">' +
        '<span>' + brandLibraryCollections.length + ' collections</span>' +
        '<span>Recently refreshed · sample data</span>' +
        '<span class="bl-readonly">Read-only preview · no create, edit, save, upload, or write-back controls</span>' +
      '</div>' +
      '<div class="bl-featured">' +
        '<article class="bl-feature">' +
          '<span class="eyebrow">Ready to use</span>' +
          '<h2>Three-part follow-up: “How do I get my first ten customers?”</h2>' +
          '<p>Content Pipeline · scripted and ready to record this week.</p>' +
          '<span class="bl-sample-tag">Sample record</span>' +
        '</article>' +
        '<article class="bl-feature bl-feature-alt">' +
          '<span class="eyebrow">Worth revisiting</span>' +
          '<h2>A founder underestimated legal cost before it derailed a launch</h2>' +
          '<p>Story Bank · strong warning story, unused since August.</p>' +
          '<span class="bl-sample-tag">Sample record</span>' +
        '</article>' +
      '</div>' +
      '<div class="bl-cards">' + brandLibraryCollections.map(card).join('') + '</div>' +
      '<div class="bl-reuse"><span>Capture</span><span aria-hidden="true">→</span><span>Develop</span><span aria-hidden="true">→</span><span>Publish / Teach</span><span aria-hidden="true">→</span><span>Learn</span><span aria-hidden="true">→</span><span>Reuse</span></div>';
  }

  function bindBrandLibrary() {
    document.querySelectorAll('[data-bl-expand]').forEach(function (b) {
      b.onclick = function () {
        var panel = document.getElementById('bl-panel-' + b.dataset.blExpand);
        if (!panel) return;
        var open = b.getAttribute('aria-expanded') === 'true';
        b.setAttribute('aria-expanded', String(!open));
        panel.hidden = open;
        b.textContent = open
          ? 'Show all ' + panel.querySelectorAll('.bl-sample-row').length + ' sample records'
          : 'Hide sample records';
      };
    });
  }

  function checkBrandLibrary() {
    if ((location.hash.slice(1) || 'today') === 'brandlibrary') bindBrandLibrary();
  }

  // `pages` is declared with top-level `const` in app.js; classic (non-module)
  // <script> tags on the same document share one global lexical scope, so
  // this identifier is reachable here exactly as enhancements.js already
  // reaches `drawer`, `toast`, and `priorities` from app.js.
  if (typeof pages === 'object' && pages) pages.brandlibrary = brandlibrary;

  // app.js's own trailing `navigate(location.hash.slice(1)||'today')` runs
  // to completion (including a `history.replaceState` to '#today') before
  // this later-loaded script ever executes, because classic <script src>
  // tags run fully in document order. That means a fresh load or reload
  // with '#brandlibrary' already in the URL gets silently rewritten to
  // '#today' before pages.brandlibrary even exists yet. window.__initialHash
  // is stashed by an inline <script> at the very top of <head> (before
  // app.js loads) specifically to survive that clobber; correct it here.
  if (window.__initialHash === '#brandlibrary' && typeof navigate === 'function') {
    navigate('brandlibrary');
  }

  window.addEventListener('hashchange', function () { setTimeout(checkBrandLibrary, 0); });
  setTimeout(checkBrandLibrary, 0);
})();

/*!
 * ep-mobile-header.v1.js
 * Builds the single full-width workspace selector button used below 640px,
 * per the CREATIVE-approved mobile header resolution (Bert's approval
 * 2026-09-08). Does not replace or rewire the real workspace-switcher
 * buttons — cc-workspace-switcher.v2.js still owns navigation. This script
 * only adds a visual toggle that opens/closes that same switcher as a
 * dropdown menu at narrow widths (see ep-mobile-header.v1.css).
 */
(function () {
  'use strict';

  function buildToggle() {
    var switcher = document.querySelector('.workspace-switcher');
    if (!switcher || document.querySelector('.ws-toggle')) return;

    if (!switcher.id) switcher.id = 'workspaceSwitcher';

    var active = switcher.querySelector('button.active, [aria-current="page"]');
    var label = active ? active.textContent.trim() : 'Entrepreneurship Professor';

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'ws-toggle';
    toggle.setAttribute('aria-haspopup', 'true');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-controls', switcher.id);

    var labelSpan = document.createElement('span');
    labelSpan.className = 'ws-label';
    labelSpan.textContent = label;
    var chevron = document.createElement('span');
    chevron.className = 'ws-chevron';
    chevron.setAttribute('aria-hidden', 'true');
    chevron.textContent = '⌄';
    toggle.appendChild(labelSpan);
    toggle.appendChild(chevron);

    switcher.parentElement.insertBefore(toggle, switcher.nextSibling);

    function closeMenu() {
      switcher.classList.remove('ws-menu-open');
      toggle.setAttribute('aria-expanded', 'false');
    }

    toggle.addEventListener('click', function () {
      var open = switcher.classList.toggle('ws-menu-open');
      toggle.setAttribute('aria-expanded', String(open));
    });

    // Close after choosing any pill inside the open menu (including the
    // already-active one, which the switcher script leaves inert).
    switcher.addEventListener('click', function (e) {
      if (e.target.closest('button')) closeMenu();
    });

    document.addEventListener('click', function (e) {
      if (switcher.classList.contains('ws-menu-open') &&
          !switcher.contains(e.target) && !toggle.contains(e.target)) {
        closeMenu();
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && switcher.classList.contains('ws-menu-open')) {
        closeMenu();
        toggle.focus();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildToggle);
  } else {
    buildToggle();
  }
})();

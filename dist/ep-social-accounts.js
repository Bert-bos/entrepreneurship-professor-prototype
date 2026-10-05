/* Live account inventory and read-only analytics. Credentials stay on the server. */
(function () {
  'use strict';

  var activeRequest = null;
  var activeStatisticsRequest = null;
  var metricLabels = {
    posts: 'Posts', impressions: 'Impressions', reach: 'Reach', likes: 'Likes',
    comments: 'Comments', shares: 'Shares', followers: 'Followers'
  };
  var countFormat = new Intl.NumberFormat('en-US', { maximumFractionDigits: 20 });
  var platformNames = {
    instagram: 'Instagram', linkedin: 'LinkedIn', tiktok: 'TikTok',
    youtube: 'YouTube', facebook: 'Facebook'
  };
  var dateFormat = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York', month: 'short', day: 'numeric',
    year: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short'
  });

  function node(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }

  function value(text, fallback) {
    return typeof text === 'string' && text.trim() ? text : fallback;
  }

  function platformLabel(platform) {
    var name = value(platform, 'Unknown platform');
    return platformNames[name.toLowerCase()] || name;
  }

  function displayDate(raw) {
    if (typeof raw !== 'string' || !raw.trim()) return null;
    var date = new Date(raw);
    return Number.isFinite(date.getTime()) ? dateFormat.format(date) : null;
  }

  function statusFor(account) {
    if (account.expirationDiscrepancy === true ||
        (account.isExpired === false && account.expirationTimestampPast === true)) {
      return { label: 'Expiration needs review', tone: 'review' };
    }
    if (account.isExpired === true) return { label: 'API reports expired', tone: 'expired' };
    if (account.isExpired === false) return { label: 'API reports not expired', tone: 'ok' };
    return { label: 'Expiration status unknown', tone: 'unknown' };
  }

  function accountCard(account) {
    var item = node('li', 'ep-sa-account');
    var top = node('div', 'ep-sa-account-top');
    var platform = platformLabel(account.platform);
    top.appendChild(node('span', 'ep-sa-platform', platform));
    var status = statusFor(account);
    top.appendChild(node('span', 'ep-sa-status ep-sa-status--' + status.tone, status.label));
    item.appendChild(top);
    item.appendChild(node('h3', '', value(account.name, 'Unnamed account')));
    item.appendChild(node('p', 'ep-sa-type', 'Account type: ' + value(account.type, 'Not supplied')));
    var expiration = displayDate(account.expire);
    item.appendChild(node('p', 'ep-sa-expiration', 'API expiration timestamp: ' + (expiration || 'Not supplied')));
    if (status.tone === 'review') {
      item.appendChild(node('p', 'ep-sa-account-note', account.isExpired === false && account.expirationTimestampPast === true
        ? 'The timestamp is past, while the API reports not expired. Its meaning remains unresolved.'
        : 'The expiration timestamp and API flag disagree. Their meaning needs review.'));
    } else if (account.isExpired == null) {
      item.appendChild(node('p', 'ep-sa-account-note', 'The API did not supply an expiration flag.'));
    }
    return item;
  }

  function renderResult(section, body, status, data) {
    body.replaceChildren();
    section.dataset.state = data.accounts.length ? 'ready' : 'empty';
    status.textContent = 'Verified account read';
    status.className = 'ep-sa-live-status ep-sa-status--ok';
    var summary = node('div', 'ep-sa-summary');
    summary.appendChild(node('b', '', data.accounts.length + (data.accounts.length === 1 ? ' account returned' : ' accounts returned')));
    var checked = displayDate(data.checkedAt);
    var time = node('time', '', (data.cache && data.cache.fromCache === true ? 'Cached result · checked ' : 'Checked ') + (checked || 'time unavailable'));
    if (checked) time.setAttribute('datetime', data.checkedAt);
    summary.appendChild(time);
    body.appendChild(summary);
    if (data.accounts.length) {
      var list = node('ul', 'ep-sa-accounts');
      data.accounts.forEach(function (account) { list.appendChild(accountCard(account)); });
      body.appendChild(list);
    } else {
      body.appendChild(node('p', 'ep-sa-message', 'GoHighLevel returned no social accounts for this location.'));
    }
    if (Array.isArray(data.missingPlatforms) && data.missingPlatforms.length) {
      body.appendChild(node('p', 'ep-sa-missing', 'Not returned in this inventory: ' + data.missingPlatforms.map(platformLabel).join(', ') + '.'));
    }
    body.appendChild(node('p', 'ep-sa-scope', 'Account identities only. Analytics and publishing access are checked separately.'));
    body.appendChild(node('p', 'ep-sa-freshness', 'Refresh checks may reuse results for up to 60 seconds.'));
  }

  async function loadAccounts(section, body, status, refresh) {
    if (activeRequest) activeRequest.abort();
    var controller = new AbortController();
    activeRequest = controller;
    var timedOut = false;
    var timeout = setTimeout(function () { timedOut = true; controller.abort(); }, 15000);
    section.dataset.state = 'loading';
    section.setAttribute('aria-busy', 'true');
    refresh.disabled = true;
    refresh.textContent = 'Refreshing…';
    status.textContent = 'Checking accounts';
    status.className = 'ep-sa-live-status';
    body.replaceChildren(node('p', 'ep-sa-message', 'Loading account identities from GoHighLevel…'));

    try {
      var response = await fetch('/api/social/accounts', {
        method: 'GET', credentials: 'same-origin', cache: 'no-store',
        headers: { Accept: 'application/json' }, signal: controller.signal
      });
      var data;
      try { data = await response.json(); }
      catch (parseError) {
        throw new Error('Account access is unavailable from this server. Start the project with its account API service.');
      }
      if (!response.ok) {
        throw new Error(value(data && data.error && data.error.message, 'Account access is temporarily unavailable. Try again later.'));
      }
      if (!data || data.source !== 'gohighlevel' || !Array.isArray(data.accounts) ||
          !data.capabilities || data.capabilities.accountRead !== 'verified' ||
          data.accounts.some(function (account) { return !account || typeof account !== 'object' || Array.isArray(account); })) {
        throw new Error('The account service returned an unexpected response. No account inventory is available.');
      }
      if (section.isConnected && activeRequest === controller) renderResult(section, body, status, data);
    } catch (error) {
      if (!section.isConnected || activeRequest !== controller) return;
      if (error.name === 'AbortError' && !timedOut) return;
      section.dataset.state = 'error';
      status.textContent = 'Account access unavailable';
      status.className = 'ep-sa-live-status ep-sa-status--review';
      body.replaceChildren(node('p', 'ep-sa-message ep-sa-error', timedOut
        ? 'The account check timed out. Try refreshing again.'
        : error.name === 'TypeError'
          ? 'The account service could not be reached. Try refreshing again.'
          : value(error.message, 'The account service could not be reached. Try refreshing again.')));
      body.appendChild(node('p', 'ep-sa-scope', 'No live account inventory was loaded. Preview data below is separate.'));
    } finally {
      clearTimeout(timeout);
      if (activeRequest === controller) activeRequest = null;
      if (section.isConnected) {
        section.setAttribute('aria-busy', 'false');
        refresh.disabled = false;
        refresh.textContent = 'Refresh accounts';
      }
    }
  }

  function statisticsReason(reason, fallback) {
    var reasons = {
      STATISTICS_ACCESS_DENIED: 'GoHighLevel denied analytics access. Review the integration’s analytics read permission to continue.',
      STATISTICS_CREDENTIAL_REJECTED: 'GoHighLevel could not authorize the analytics request. Review the integration’s analytics access to continue.',
      NOT_CONNECTED: 'No account was returned for this platform.',
      LINKEDIN_PAGE_REQUIRED: 'LinkedIn analytics requires a Page. The connected account is a personal profile.',
      TIKTOK_BUSINESS_REQUIRED: 'TikTok analytics requires a Business account.',
      PROFILE_ID_UNAVAILABLE: 'This account does not provide the identifier required for an analytics request.',
      ACCOUNT_EXPIRED: 'GoHighLevel reports this account expired. Reconnect it before loading analytics.',
      NO_METRICS_RETURNED: 'GoHighLevel did not return metrics for this platform.'
    };
    return Object.prototype.hasOwnProperty.call(reasons, reason)
      ? reasons[reason] : value(fallback, 'Analytics are unavailable for this platform.');
  }

  function reportedMetrics(metrics) {
    if (!metrics || typeof metrics !== 'object' || Array.isArray(metrics)) return [];
    return Object.keys(metricLabels).filter(function (key) {
      return Object.prototype.hasOwnProperty.call(metrics, key) &&
        typeof metrics[key] === 'number' && Number.isFinite(metrics[key]) && metrics[key] >= 0;
    });
  }

  function metricsList(metrics, keys) {
    var list = node('dl', 'ep-stats-metrics');
    keys.forEach(function (key) {
      var metric = node('div', 'ep-stats-metric');
      metric.appendChild(node('dt', '', metricLabels[key]));
      metric.appendChild(node('dd', '', countFormat.format(metrics[key])));
      list.appendChild(metric);
    });
    return list;
  }

  function renderStatistics(section, body, status, data) {
    body.replaceChildren();
    var blocked = data.httpStatus === 401 || data.httpStatus === 403;
    var available = data.platforms.filter(function (platform) {
      return data.status === 'available' && platform.status === 'available' && reportedMetrics(platform.metrics).length;
    });
    var totalKeys = data.status === 'available' ? reportedMetrics(data.totals).filter(function (key) {
      return ['posts', 'likes', 'followers', 'impressions', 'comments'].includes(key);
    }) : [];
    var hasMetrics = Boolean(available.length || totalKeys.length);
    section.dataset.state = blocked ? 'blocked' : hasMetrics ? 'ready' : 'unavailable';
    status.textContent = blocked ? 'Analytics access needs attention'
      : available.length ? (available.length < data.platforms.length ? 'Live analytics · partial coverage' : 'Live analytics available')
      : totalKeys.length ? 'Live analytics · reported totals'
      : 'No live analytics available';
    status.className = 'ep-sa-live-status ' + (hasMetrics && !blocked ? 'ep-sa-status--ok' : 'ep-sa-status--review');
    var checked = displayDate(data.checkedAt);
    if (checked) {
      var checkedTime = node('p', 'ep-sa-freshness', (data.cache && data.cache.fromCache === true ? 'Cached result · checked ' : 'Checked ') + checked);
      body.appendChild(checkedTime);
    }
    if (blocked) {
      body.appendChild(node('p', 'ep-sa-message', statisticsReason(data.error && data.error.code,
        'GoHighLevel has not authorized this analytics request. Review the integration’s analytics access.')));
      body.appendChild(node('p', 'ep-sa-scope', 'Connected-account inventory is checked separately.'));
      return;
    }
    if (hasMetrics) {
      body.appendChild(node('p', 'ep-stats-period', 'Activity report: last seven complete days, excluding today. Followers are provider-reported account totals.'));
      body.appendChild(node('p', 'ep-sa-freshness', 'Only metrics returned by GoHighLevel are shown.'));
    }
    if (totalKeys.length) {
      var totalsCard = node('div', 'ep-stats-platform ep-stats-totals');
      totalsCard.appendChild(node('h3', '', 'Reported totals across selected accounts'));
      totalsCard.appendChild(metricsList(data.totals, totalKeys));
      body.appendChild(totalsCard);
    }
    if (!data.platforms.length) {
      body.appendChild(node('p', 'ep-sa-message', 'No platform analytics were returned.'));
    } else {
      var list = node('ul', 'ep-stats-platforms');
      data.platforms.forEach(function (platform) {
        var item = node('li', 'ep-stats-platform');
        var head = node('div', 'ep-sa-account-top');
        head.appendChild(node('h3', '', platformLabel(platform.platform)));
        var keys = data.status === 'available' && platform.status === 'available' ? reportedMetrics(platform.metrics) : [];
        head.appendChild(node('span', 'ep-sa-status ' + (keys.length ? 'ep-sa-status--ok' : 'ep-sa-status--unknown'), keys.length ? 'Reported metrics' : 'Unavailable'));
        item.appendChild(head);
        if (keys.length) {
          item.appendChild(metricsList(platform.metrics, keys));
        } else {
          item.appendChild(node('p', 'ep-sa-message', statisticsReason(platform.unavailableReason, platform.message)));
        }
        list.appendChild(item);
      });
      body.appendChild(list);
    }
    if (Array.isArray(data.excludedAccounts) && data.excludedAccounts.length) {
      var excluded = node('ul', 'ep-stats-exclusions');
      data.excludedAccounts.forEach(function (account) {
        if (!account || typeof account !== 'object') return;
        excluded.appendChild(node('li', '', platformLabel(account.platform) + ': ' + statisticsReason(account.reason, account.message)));
      });
      body.appendChild(excluded);
    }
    body.appendChild(node('p', 'ep-sa-freshness', 'Refresh checks may reuse results for up to 60 seconds.'));
  }

  async function loadStatistics(section, body, status, refresh) {
    if (activeStatisticsRequest) activeStatisticsRequest.abort();
    var controller = new AbortController();
    activeStatisticsRequest = controller;
    var timedOut = false;
    var timeout = setTimeout(function () { timedOut = true; controller.abort(); }, 15000);
    section.dataset.state = 'loading';
    section.setAttribute('aria-busy', 'true');
    refresh.disabled = true;
    refresh.textContent = 'Refreshing…';
    status.textContent = 'Checking analytics';
    status.className = 'ep-sa-live-status';
    body.replaceChildren(node('p', 'ep-sa-message', 'Loading platform analytics from GoHighLevel…'));
    try {
      var response = await fetch('/api/social/statistics', {
        method: 'GET', credentials: 'same-origin', cache: 'no-store',
        headers: { Accept: 'application/json' }, signal: controller.signal
      });
      var data;
      try { data = await response.json(); }
      catch (parseError) { throw new Error('Analytics are unavailable from this server. Try again later.'); }
      var authBlocked = (response.status === 401 || response.status === 403) && data && data.status === 'unavailable';
      if (!response.ok && !authBlocked) {
        throw new Error(value(data && data.error && data.error.message, 'The analytics service is temporarily unavailable. Try again later.'));
      }
      if (!data || data.source !== 'gohighlevel' || !['available', 'unavailable'].includes(data.status) || !Array.isArray(data.platforms) ||
          data.platforms.some(function (platform) { return !platform || typeof platform !== 'object' || Array.isArray(platform); })) {
        throw new Error('The analytics service returned an unexpected response. No live metrics are available.');
      }
      if (data.status === 'available' && (data.httpStatus !== 200 || !data.period ||
          data.period.kind !== 'lastSevenCompleteDays' || data.period.excludeToday !== true)) {
        throw new Error('The analytics service did not provide a verified reporting period. No live metrics are available.');
      }
      if (section.isConnected && activeStatisticsRequest === controller) renderStatistics(section, body, status, data);
    } catch (error) {
      if (!section.isConnected || activeStatisticsRequest !== controller) return;
      if (error.name === 'AbortError' && !timedOut) return;
      section.dataset.state = 'error';
      status.textContent = 'Analytics unavailable';
      status.className = 'ep-sa-live-status ep-sa-status--review';
      body.replaceChildren(node('p', 'ep-sa-message ep-sa-error', timedOut
        ? 'The analytics check timed out. Try refreshing again.'
        : error.name === 'TypeError' ? 'The analytics service could not be reached. Try refreshing again.'
          : value(error.message, 'The analytics service could not be reached. Try refreshing again.')));
      body.appendChild(node('p', 'ep-sa-scope', 'No live analytics were loaded. Preview metrics below are separate.'));
    } finally {
      clearTimeout(timeout);
      if (activeStatisticsRequest === controller) activeStatisticsRequest = null;
      if (section.isConnected) {
        section.setAttribute('aria-busy', 'false');
        refresh.disabled = false;
        refresh.textContent = 'Refresh analytics';
      }
    }
  }

  function mountStatistics(accountsSection) {
    var section = node('section', 'card ep-sa ep-stats');
    section.id = 'ep-social-statistics';
    section.setAttribute('aria-labelledby', 'ep-stats-title');
    var head = node('div', 'card-head ep-sa-head');
    var title = node('div', '');
    title.appendChild(node('span', 'eyebrow', 'GoHighLevel · read-only analytics'));
    var heading = node('h2', '', 'Platform analytics');
    heading.id = 'ep-stats-title';
    title.appendChild(heading);
    head.appendChild(title);
    var refresh = node('button', 'btn light ep-sa-refresh', 'Refresh analytics');
    refresh.type = 'button';
    refresh.setAttribute('aria-controls', 'ep-stats-body');
    head.appendChild(refresh);
    section.appendChild(head);
    var status = node('p', 'ep-sa-live-status', 'Checking analytics');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    section.appendChild(status);
    var body = node('div', 'ep-sa-body');
    body.id = 'ep-stats-body';
    body.setAttribute('aria-live', 'polite');
    section.appendChild(body);
    accountsSection.after(section);
    refresh.onclick = function () { loadStatistics(section, body, status, refresh); };
    loadStatistics(section, body, status, refresh);
  }

  function markPreviews(app) {
    var chip = app.querySelector('.page-head .date-chip');
    if (chip) chip.textContent = 'Preview growth · +15.2% (sample)';
    var previewNotice = node('p', 'ep-sa-preview-notice');
    previewNotice.appendChild(node('b', '', 'Preview data below. '));
    previewNotice.appendChild(document.createTextNode('Metrics, audience insights, recommendations, and actions below are examples, separate from the live GoHighLevel sections above.'));
    app.querySelector('#ep-social-statistics').after(previewNotice);
    app.querySelectorAll('section.card:not(#ep-social-accounts):not(#ep-social-statistics)').forEach(function (card) {
      var head = card.querySelector('.card-head');
      if (head) head.appendChild(node('span', 'ep-sa-preview-label', 'Preview data'));
    });
    var growthStatus = app.querySelector('.growth-actions') && app.querySelector('.growth-actions').closest('.card').querySelector('.pill');
    if (growthStatus) {
      growthStatus.textContent = 'Example recommendations';
      growthStatus.classList.remove('green');
    }
    var insight = app.querySelector('.fresh-insight b');
    if (insight) insight.textContent = 'Sample insight';
  }

  function mountAudience() {
    if (location.hash !== '#audience') return;
    var app = document.querySelector('#app');
    if (!app || app.querySelector('#ep-social-accounts')) return;
    var section = node('section', 'card ep-sa');
    section.id = 'ep-social-accounts';
    section.setAttribute('aria-labelledby', 'ep-sa-title');
    var head = node('div', 'card-head ep-sa-head');
    var title = node('div', '');
    title.appendChild(node('span', 'eyebrow', 'GoHighLevel · live account inventory'));
    var heading = node('h2', '', 'Connected social accounts');
    heading.id = 'ep-sa-title';
    title.appendChild(heading);
    head.appendChild(title);
    var refresh = node('button', 'btn light ep-sa-refresh', 'Refresh accounts');
    refresh.type = 'button';
    refresh.setAttribute('aria-controls', 'ep-sa-body');
    head.appendChild(refresh);
    section.appendChild(head);
    var status = node('p', 'ep-sa-live-status', 'Checking accounts');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    section.appendChild(status);
    var body = node('div', 'ep-sa-body');
    body.id = 'ep-sa-body';
    body.setAttribute('aria-live', 'polite');
    section.appendChild(body);
    var pageHead = app.querySelector('.page-head');
    if (pageHead) pageHead.after(section);
    else app.prepend(section);
    mountStatistics(section);
    markPreviews(app);
    refresh.onclick = function () { loadAccounts(section, body, status, refresh); };
    loadAccounts(section, body, status, refresh);
  }

  // navigate() renders from pages and uses replaceState; it does not emit hashchange.
  if (typeof pages === 'object' && typeof pages.audience === 'function') {
    var originalAudience = pages.audience;
    pages.audience = function () {
      setTimeout(mountAudience, 0);
      return originalAudience();
    };
  }
  document.addEventListener('click', function (event) {
    if (location.hash !== '#audience' || !event.target.closest('.metric-button')) return;
    setTimeout(function () {
      var body = document.querySelector('#drawerBody');
      if (body && !body.querySelector('.ep-sa-preview-notice')) {
        body.prepend(node('p', 'ep-sa-preview-notice', 'Preview analytics and recommendations. Live GoHighLevel results appear in the Platform analytics section.'));
      }
    }, 0);
  });
  setTimeout(mountAudience, 0);
})();

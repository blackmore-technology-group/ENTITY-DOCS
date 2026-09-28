(() => {
  'use strict';

  const esc = (value) => String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const money = (value, currency) => {
    const n = Number(value || 0);
    if (!currency) return String(n);
    try {
      return new Intl.NumberFormat('en-CA', { style: 'currency', currency }).format(n);
    } catch (_) {
      return `${n} ${currency}`;
    }
  };

  const label = (value) => String(value || 'UNKNOWN').replaceAll('_', ' ');

  const statusClass = (state) => {
    const s = String(state || '').toUpperCase();
    if (s.includes('ACCEPTED') || s === 'PASS' || s.includes('APPROVED')) return 'ledger-good';
    if (s.includes('FAIL') || s.includes('CLOSED') || s.includes('CHANGES REQUESTED')) return 'ledger-bad';
    return 'ledger-neutral';
  };

  const link = (href, text) => href ? `<a href="${esc(href)}">${esc(text)} →</a>` : '';

  function renderCard(item, index) {
    const issue = item.issue || {};
    const upstream = item.upstream || {};
    const economic = item.economic || {};
    const rights = item.rights || {};
    const source = item.source || {};
    const technical = label(upstream.live_technical_state);
    const entityState = label(item.entity_evidence_state);
    const contributionClass = label(item.contribution_class);
    const checks = upstream.check_counts || {};

    return `
      <article class="card ledger-card">
        <div class="eyebrow">Public example ${String(index + 1).padStart(3, '0')} · ${esc(contributionClass)}</div>
        <h3>${esc(item.repository)} #${esc(issue.number)} — ${esc(issue.title)}</h3>
        <div class="ledger-status-row">
          <span class="ledger-pill ${statusClass(upstream.live_technical_state)}">LIVE: ${esc(technical)}</span>
          <span class="ledger-pill ledger-neutral">ENTITY: ${esc(entityState)}</span>
          <span class="ledger-pill ${statusClass(upstream.ci_state)}">CI: ${esc(label(upstream.ci_state))}</span>
          <span class="ledger-pill ${statusClass(upstream.review_state)}">REVIEW: ${esc(label(upstream.review_state))}</span>
        </div>
        <p><strong>Contributor:</strong> ${esc(item.contributor?.human_author || '')} / ${esc(item.contributor?.corporate_contributor || '')}<br>
        <strong>Licence:</strong> ${esc(rights.license || 'UNKNOWN')}<br>
        <strong>Recorded cash:</strong> ${esc(money(economic.realized_cash, economic.currency))}<br>
        <strong>Head SHA:</strong> <code>${esc(upstream.head_sha || upstream.recorded_commit || 'not recorded')}</code></p>
        <p><strong>Live upstream observation:</strong> ${esc(technical)}. <strong>ENTITY recorded state:</strong> ${esc(entityState)}. These are deliberately separate: the site may observe a later public GitHub event, but it does not rewrite the underlying ENTITY evidence record.</p>
        <p class="muted">Checks observed: ${esc(checks.success || 0)} successful, ${esc(checks.failure || 0)} failing, ${esc(checks.pending || 0)} pending. Source record: <code>${esc(item.record_id)}</code>.</p>
        <div class="actions">
          ${link(issue.url, 'Issue')}
          ${link(upstream.pull_request, 'Pull request')}
          ${link(source.record_url, 'ENTITY record')}
          ${link(source.experiment_url, 'ENTITY experiment')}
        </div>
      </article>`;
  }

  async function loadLedger() {
    const status = document.getElementById('ledger-load-status');
    const cards = document.getElementById('contribution-ledger');
    try {
      const response = await fetch('./contributions.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const ledger = await response.json();
      const items = Array.isArray(ledger.contributions) ? ledger.contributions : [];
      const accepted = items.filter(x => x.upstream?.live_technical_state === 'UPSTREAM_ACCEPTED').length;
      const validated = items.filter(x => x.upstream?.live_technical_state === 'REVIEW_APPROVED_CI_GREEN').length;
      const proBono = items.filter(x => x.contribution_class === 'PRO_BONO').length;

      document.getElementById('ledger-total').textContent = String(items.length);
      document.getElementById('ledger-accepted').textContent = String(accepted);
      document.getElementById('ledger-validated').textContent = String(validated);
      document.getElementById('ledger-probono').textContent = String(proBono);
      document.getElementById('ledger-updated').textContent = ledger.generated_at_utc || 'unknown';

      if (!items.length) {
        cards.innerHTML = '<div class="notice">No public contribution records have been published yet.</div>';
      } else {
        cards.innerHTML = items.map(renderCard).join('');
      }
      status.textContent = 'Live ledger loaded from machine-readable ENTITY contribution evidence.';
    } catch (err) {
      cards.innerHTML = '<div class="notice"><strong>Ledger unavailable:</strong> the last generated public data file could not be loaded. The linked GitHub repositories remain authoritative.</div>';
      status.textContent = `Ledger load error: ${err.message}`;
    }
  }

  document.addEventListener('DOMContentLoaded', loadLedger);
})();

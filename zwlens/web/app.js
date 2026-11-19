'use strict';
// Phone layout: narrow screens, or a phone/tablet browser in portrait. Sets html.phone (see style.css).
(() => {
  const narrow = matchMedia('(max-width: 700px)');
  const mobileUA = navigator.userAgentData?.mobile ?? /Mobi|Android|iPhone|iPod/i.test(navigator.userAgent);
  const set = () => document.documentElement.classList.toggle('phone', narrow.matches || (mobileUA && innerWidth < 900));
  set(); narrow.addEventListener('change', set); addEventListener('resize', set);
})();
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const SEVLABEL = { ok: 'OK', info: 'Note', warn: 'Warning', crit: 'Critical', fail: 'Failed' };
const LOGO = document.querySelector('.brand .logo').outerHTML;
const HEALTH = { Healthy: 'ok', Marginal: 'warn', Failing: 'crit', Unknown: 'plain' };

let A = null, version = 0, names = {};
const S = { tab: 'data', conv: null, convFrames: null, cq: '', cnode: '', cstatus: '', fq: '', fnode: '', fkind: '',
  foff: 0, frames: null, edit: null, open: {}, notes: [], foreign: false, dirty: false, kq: '', kcat: '', ctrl: (() => { try { return localStorage.getItem('zwlens.ctrl') || ''; } catch (e) { return ''; } })(), ports: null, port: null };
let done = {};
try { done = JSON.parse(localStorage.getItem('zwlens.done') || '{}'); } catch (e) { done = {}; }

async function api(path, opt) {
  const r = await fetch(path, opt);
  const j = await r.json().catch(() => ({ error: 'bad response' }));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
const post = (path, body) => api(path, { method: 'POST', headers: { 'X-ZWLens': '1', 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });

let toastTimer;
function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.classList.add('on');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('on'), 4000);
}
const pill = (sev, text) => `<span class="pill ${esc(sev)}">${esc(text ?? SEVLABEL[sev] ?? sev)}</span>`;
function fmtTime(ts) {
  if (ts == null) return '';
  const p = (n, w = 2) => String(n).padStart(w, '0');
  if (ts > 1e9) { const d = new Date(ts * 1000); return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}.${p(d.getMilliseconds(), 3)}`; }
  const s = ((ts % 86400) + 86400) % 86400;
  return `${p(Math.floor(s / 3600))}:${p(Math.floor(s / 60) % 60)}:${p(Math.floor(s % 60))}.${p(Math.round((s % 1) * 1000) % 1000, 3)}`;
}
function fmtDur(s) {
  if (s == null) return 'n/a';
  if (s < 1) return Math.round(s * 1000) + ' ms';
  if (s < 120) return s.toFixed(1) + ' s';
  if (s < 7200) return (s / 60).toFixed(1) + ' min';
  return (s / 3600).toFixed(1) + ' h';
}
const nameOf = (home, id) => id === 255 ? 'Broadcast' : (names[(home || '') + ':' + id] || 'Node ' + id);
const pct = v => v == null ? 'n/a' : v + '%';

async function load() {
  A = await api('/api/analysis');
  version = A.version;
  A.catalog = A.catalog || [];
  A.settings = A.settings || { chip: '700' };
  A.guides = A.guides || { actions: {}, issue_actions: {}, controllers: [] };
  if (A.controller_model) S.ctrl = A.controller_model;  // saved per network; browser storage is only a fallback
  names = {};
  for (const n of A.nodes) names[n.home + ':' + n.id] = n.name;
  if (S.conv != null && !A.conversations.some(c => c.id === S.conv)) { S.conv = null; S.convFrames = null; }
  if (S.conv != null) await loadConv(S.conv, false);
  if (S.tab === 'frames') await loadFrames(false);
  render();
}
async function loadConv(id, rerender = true) {
  S.conv = id;
  S.convFrames = (await api('/api/frames?limit=1000&conv=' + id)).frames;
  if (rerender) render();
}
async function loadFrames(rerender = true) {
  const q = new URLSearchParams({ offset: S.foff, limit: 200, q: S.fq, node: S.fnode, kind: S.fkind });
  S.frames = await api('/api/frames?' + q);
  if (rerender) render();
}

function render() {
  document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === S.tab));
  const all = [...A.issues.flatMap(i => i.findings), ...A.catalog.flatMap(e => e.hits)];
  const nCrit = all.filter(f => f.severity === 'crit').length, nWarn = all.filter(f => f.severity === 'warn').length;
  $('#tabs [data-tab=troubleshoot]').innerHTML = 'Troubleshoot' + (nCrit ? `<span class="count">${nCrit}</span>` : nWarn ? `<span class="count warn">${nWarn}</span>` : '');
  const live = A.live;
  $('#status').innerHTML = (live ? pill(live.state === 'connected' ? 'ok' : live.state === 'connecting' ? 'info' : 'crit', (document.documentElement.classList.contains('phone') && live.state === 'connected' ? 'Live' : 'Live: ' + live.state)) : '')
    + `<span>${A.network.frames} frames</span>`;
  if (S.tab === 'help') { if (!$('#view > .help')) $('#view').innerHTML = help(); return; }  // help does not depend on the capture
  const empty = !A.network.frames;
  const views = { overview, conversations, troubleshoot, nodes, frames, data };
  $('#view').innerHTML = (empty && S.tab !== 'data')
    ? `<div class="panel empty">${LOGO}<h3>No capture loaded</h3><p>Capture live from a Zniffer stick, add a log or capture file, or connect to a live controller.</p><button class="btn primary" data-act="tab" data-tab="data">Add data</button> <button class="btn" data-act="sample" data-kind="zniffer">Try with sample data</button></div>`
    : views[S.tab]();
}

// ---------------------------------------------------------------- overview
function chips(obj) {
  return `<div class="chips">${Object.entries(obj || {}).map(([k, v]) => `<span class="pill ${HEALTH[k] || 'plain'}">${esc(k)}: ${esc(v)}</span>`).join('') || '<span class="muted">n/a</span>'}</div>`;
}
function overview() {
  const n = A.network;
  const sev = n.score >= 85 ? 'ok' : n.score >= 60 ? 'warn' : 'crit';
  // each card jumps to the view that explains its number; status pre-filters Conversations
  const card = (v, k, tab, status = '', hint = '') => `<button class="card go" data-act="card" data-tab="${tab}" data-status="${status}" title="${esc(hint)}"><div class="v">${esc(v)}</div><div class="k">${esc(k)}</div></button>`;
  const sug = A.suggestions.map((s, i) => `<div class="finding">${pill(s.severity)} <b>${esc(s.area)}</b><div>${esc(s.why)}</div><div class="fix">${esc(s.do)}</div>${hubStep(s.action)}
    ${s.issue ? `<button class="link small" data-act="issue" data-id="${esc(s.issue)}">${s.issue.startsWith('kb-') ? 'Causes and fixes' : 'Open troubleshooter'}</button>` : ''}</div>`).join('');
  return `
  <div class="grid cards">
    <button class="card hero go" data-act="card" data-tab="troubleshoot" data-status="" title="See what is lowering the score"><svg class="ring" viewBox="0 0 72 72" role="img" aria-label="Health score ${n.score} of 100"><circle class="track" cx="36" cy="36" r="30"/><circle class="val" cx="36" cy="36" r="30" style="stroke:var(--${sev})" stroke-dasharray="${(n.score / 100 * 188.5).toFixed(1)} 188.5"/><text x="36" y="43" text-anchor="middle">${n.score}</text></svg>
      <div><div class="v" style="color:var(--${sev})">${esc(n.grade)}</div><div class="k">Network health score</div></div></button>
    ${card(n.nodes, 'Nodes', 'nodes', '', 'Show every node')}${card(n.messages, 'Messages', 'frames', '', 'Show the frames')}${card(A.conv_total, 'Conversations', 'conversations', '', 'Show all conversations')}
    ${card(pct(n.fail_pct), 'Not delivered', 'conversations', 'fail', 'Show failed conversations')}${card(pct(n.retx_pct), 'Needed a retry', 'conversations', 'warn', 'Show conversations with retries')}
    ${card(n.airtime_pct != null ? n.airtime_pct + '%' : (n.msgs_per_min != null ? n.msgs_per_min + '/min' : 'n/a'), n.airtime_pct != null ? 'Channel busy' : 'Message rate', 'frames', '', 'Show the frames')}
    ${card(n.noise_floor != null ? n.noise_floor + ' dBm' : 'n/a', 'Noise floor', 'troubleshoot', '', 'Interference and range checks')}
  </div>
  <div class="grid cols2">
    <div>
      <div class="panel"><h2>Network category</h2>
        <dl class="kv">
          <dt>Home ID</dt><dd class="mono">${esc(n.home || 'unknown')}${n.foreign_nodes ? ` <span class="muted">(+${n.homes.length - 1} other network${n.homes.length > 2 ? 's' : ''} in range)</span>` : ''}</dd>
          <dt>Size</dt><dd>${esc(n.size)}</dd>
          <dt>Topology</dt><dd>${esc(n.topology)}</dd>
          <dt>Controller</dt><dd>${n.controller != null ? esc(nameOf(n.home, n.controller)) : 'unknown'}${ctrlGuide() ? ` · ${esc(ctrlGuide().name)}` : ''} <button class="link small" data-act="tab" data-tab="nodes">${ctrlGuide() ? 'change' : 'set model'}</button></dd>
          <dt>Captured</dt><dd>${esc(fmtDur(n.duration))}, from ${esc(Object.entries(n.sources).map(([k, v]) => `${k} (${v})`).join(', '))}</dd>
          <dt>Health</dt><dd>${chips(n.by_health)}</dd>
          <dt>Power</dt><dd>${chips(n.by_power)}</dd>
          <dt>Security</dt><dd>${chips(n.by_security)}</dd>
          <dt>Device types</dt><dd>${chips(n.by_type)}</dd>
          <dt>Roles</dt><dd>${chips(n.by_role)}</dd>
          <dt>Data rates</dt><dd>${chips(n.speeds)}</dd>
          ${n.long_range ? `<dt>Long Range</dt><dd>${n.long_range} node(s)</dd>` : ''}
        </dl>
      </div>
      <div class="panel"><h2>Network map</h2>${netmap()}
        <div class="legend"><span><i class="dot" style="background:var(--ok)"></i>Healthy</span><span><i class="dot" style="background:var(--warn)"></i>Marginal</span>
        <span><i class="dot" style="background:var(--crit)"></i>Failing</span><span><i class="dot" style="background:var(--muted)"></i>Unknown</span>
        <span>Solid line: observed route · dashed: assumed direct · click a node for its conversations</span></div>
      </div>
    </div>
    <div class="panel"><h2>Suggestions, most important first</h2>${sug}</div>
  </div>`;
}
function netmap() {
  const ns = A.nodes.filter(n => !n.foreign);
  const ctrl = ns.find(n => n.controller);
  const W = 760, H = 500, cx = W / 2, cy = H / 2;
  const rings = {};
  let maxRing = 1;
  for (const n of ns) {
    if (n === ctrl) continue;
    const r = n.route ? n.route.length + 1 : 1;
    (rings[r] = rings[r] || []).push(n); maxRing = Math.max(maxRing, r);
  }
  const step = Math.min(105, 225 / maxRing), pos = {};
  if (ctrl) pos[ctrl.id] = { x: cx, y: cy, a: 0 };
  let svg = '';
  for (let r = 1; r <= maxRing; r++) {
    const list = rings[r] || [];
    svg += `<ellipse class="ring" cx="${cx}" cy="${cy}" rx="${r * step * 1.5}" ry="${r * step}"/>`;
    const parent = n => (n.route && n.route.length ? pos[n.route[n.route.length - 1]] : null);
    list.sort((a, b) => ((parent(a) || {}).a || 0) - ((parent(b) || {}).a || 0) || a.id - b.id);
    const sibs = {};
    list.forEach(n => { const p = parent(n); if (r > 1 && p) (sibs[p.a] = sibs[p.a] || []).push(n); });
    list.forEach((n, i) => {
      // Outer rings sit behind their repeater so the route line does not cross other nodes.
      const p = r > 1 ? parent(n) : null, group = p ? sibs[p.a] : null;
      const a = p ? p.a + (group.indexOf(n) - (group.length - 1) / 2) * (0.5 / r)
        : (2 * Math.PI * (i + 0.5)) / list.length - Math.PI / 2;
      pos[n.id] = { x: cx + Math.cos(a) * r * step * 1.5, y: cy + Math.sin(a) * r * step, a };
    });
  }
  let edges = '', dots = '';
  for (const n of ns) {
    const p = pos[n.id]; if (!p) continue;
    if (n !== ctrl && ctrl) {
      const par = (n.route && n.route.length && pos[n.route[n.route.length - 1]]) || pos[ctrl.id];
      edges += `<line class="edge ${n.route ? '' : 'guess'}" x1="${p.x}" y1="${p.y}" x2="${par.x}" y2="${par.y}"/>`;
    }
    const col = { ok: 'ok', warn: 'warn', crit: 'crit', plain: 'muted' }[HEALTH[n.health] || 'plain'];
    const label = n.name.length > 18 ? n.name.slice(0, 17) + '…' : n.name;
    dots += `<g><circle class="n" data-act="mapnode" data-id="${n.id}" cx="${p.x}" cy="${p.y}" r="${n === ctrl ? 13 : 9}" style="fill:var(--${n === ctrl ? 'accent' : col})"><title>${esc(n.name)} · ${esc(n.type)} · ${esc(n.health)}</title></circle>
      <text x="${p.x}" y="${p.y + (n === ctrl ? 27 : 22)}" text-anchor="middle">${esc(label)}</text></g>`;
  }
  return `<svg class="map" viewBox="0 0 ${W} ${H}" role="img" aria-label="Network map">${svg}${edges}${dots}</svg>`;
}

// ---------------------------------------------------------------- conversations
function nodeOptions(sel) {
  return '<option value="">All nodes</option>' + A.nodes.filter(n => !n.foreign || S.foreign).map(n => `<option value="${n.id}" ${String(sel) === String(n.id) ? 'selected' : ''}>${esc(n.name)}</option>`).join('');
}
function conversations() {
  const q = S.cq.toLowerCase();
  const list = A.conversations.filter(c => (S.foreign || !c.foreign) &&
    (!S.cnode || String(c.a) === S.cnode || String(c.b) === S.cnode) && (!S.cstatus || c.status === S.cstatus)
    && (!q || (c.title + ' ' + c.a_name + ' ' + c.b_name + ' ' + c.flags.join(' ')).toLowerCase().includes(q)));
  const shown = list.slice(-600).reverse();
  const items = shown.map(c => `<div class="conv ${c.status} ${c.id === S.conv ? 'on' : ''}" data-act="conv" data-id="${c.id}">
      <span class="t">${esc(fmtTime(c.start))}</span><div class="who">${esc(c.a_name)} ⇄ ${esc(c.b_name)}</div>
      <div class="what">${esc(c.title)}</div>
      <div class="small muted">${c.frames} frames · ${esc(fmtDur(c.duration))}${c.flags.length ? ' · ' + esc(c.flags.join(' · ')) : ''}</div></div>`).join('');
  return `<div class="bar">
      <input type="search" class="grow" id="cq" placeholder="Search conversations (command, node, flag)…" value="${esc(S.cq)}">
      <select id="cnode">${nodeOptions(S.cnode)}</select>
      <select id="cstatus"><option value="">Any outcome</option>${['ok', 'warn', 'fail'].map(s => `<option value="${s}" ${S.cstatus === s ? 'selected' : ''}>${{ ok: 'Clean', warn: 'With retries or warnings', fail: 'Failed' }[s]}</option>`).join('')}</select>
      ${A.network.foreign_nodes ? `<label class="small"><input type="checkbox" data-act="foreign" ${S.foreign ? 'checked' : ''}> Other networks</label>` : ''}
      <span class="muted small">${list.length} of ${A.conv_total}${list.length > 600 ? ' (latest 600 shown)' : ''}</span></div>
    <div class="split"><div class="panel convlist">${items || '<div class="empty">No conversations match.</div>'}</div>
    <div class="panel">${convDetail()}</div></div>`;
}
function frameMeta(f, prev) {
  const m = [fmtTime(f.ts)];
  if (prev && f.ts != null && prev.ts != null) m.push('+' + fmtDur(f.ts - prev.ts));
  if (f.speed) m.push(f.speed);
  if (f.rssi != null) m.push(f.rssi.toFixed(0) + ' dBm');
  if (f.ack_rssi != null) m.push('ACK ' + f.ack_rssi.toFixed(0) + ' dBm');
  if (f.routed && f.repeaters.length) m.push('via ' + f.repeaters.map(r => nameOf(f.home, r)).join(' → ') + (f.hop != null ? ` (hop ${f.hop}/${f.repeaters.length})` : ''));
  if (f.wake) m.push('asks for a ' + f.wake + ' wake-up beam');
  if (f.rep_rssi && f.rep_rssi.length) m.push('repeater heard it at ' + f.rep_rssi.join(', ') + ' dBm');
  if (f.scheme) m.push(f.scheme);
  if (f.seq != null) m.push('seq ' + f.seq);
  if (f.role === 'retx') m.push('RETRANSMISSION');
  if (f.role === 'fwd') m.push('forwarded by ' + nameOf(f.home, f.txn));
  if (f.tx_status) m.push(f.tx_status === 'OK' ? `delivered${f.tx_ms != null ? ' in ' + f.tx_ms + ' ms' : ''}` : 'NOT delivered (' + f.tx_status + ')');
  if (f.attempts > 1) m.push(f.attempts + ' attempts');
  if (f.route_failed) m.push('route failed at ' + f.route_failed);
  for (const e of f.errors) m.push('⚠ ' + e);
  return m;
}
function convDetail() {
  const c = A.conversations.find(c => c.id === S.conv);
  if (!c || !S.convFrames) return '<div class="empty">Select a conversation to see it message by message.</div>';
  let prev = null;
  const rows = S.convFrames.map(f => {
    const side = f.src === c.a ? 'l' : 'r';
    let h;
    if (f.kind === 'event' || f.kind === 'beam') h = `<div class="evt ${f.kind}">${esc(fmtTime(f.ts))} · ${esc(f.label)}${f.kind === 'beam' ? ' to ' + esc(nameOf(f.home, f.dst)) : ''}</div>`;
    else if (f.kind === 'ack' || f.kind === 'routed_ack') h = `<div class="tick ${side}">✓ ${esc(f.label)} from ${esc(nameOf(f.home, f.src))} · ${esc(frameMeta(f, prev).slice(1, 4).join(' · '))}</div>`;
    else {
      const bad = f.kind === 'routed_err' || (f.tx_status && f.tx_status !== 'OK') || f.errors.includes('bad checksum');
      h = `<div class="msg ${side} ${f.role === 'retx' ? 'retx' : ''} ${bad ? 'bad' : ''}" data-act="raw">
        <div class="h">${esc(f.label)} ${f.encap.map(e => pill('plain', e)).join(' ')}${f.encrypted ? ' ' + pill('plain', 'encrypted') : ''}</div>
        ${f.summary ? `<div>${esc(f.summary)}</div>` : ''}
        <div class="meta">${esc(frameMeta(f, prev).join(' · '))}</div>
        <div class="raw">#${f.idx} · ${esc(f.source)}${f.raw ? ' · ' + esc(f.raw) : ''}</div></div>`;
    }
    prev = f; return h;
  }).join('');
  return `<h2>${esc(c.title)}</h2><p class="muted small">${c.frames} frames · ${c.n_msgs} messages · ${esc(fmtDur(c.duration))} · ${pill(c.status === 'ok' ? 'ok' : c.status, { ok: 'Clean', warn: 'Warnings', fail: 'Failed' }[c.status])} ${esc(c.flags.join(' · '))}</p>
    <div class="lanes"><span>◀ ${esc(c.a_name)}</span><span>${esc(c.b_name)} ▶</span></div>
    <div class="chat">${rows}</div><p class="muted small" style="margin-top:8px">Click a message to show its raw bytes.</p>`;
}

// ---------------------------------------------------------------- troubleshoot
function troubleshoot() {
  const guide = ctrlGuide();
  return controllerPanel() + `<p class="muted">The five most common Z-Wave problems, checked against this capture. Each one lists what was found and a guided checklist.</p>` +
    A.issues.map(iss => {
      const open = S.open[iss.id] ?? iss.findings.length > 0;
      const finds = iss.findings.map(f => `<div class="finding">${pill(f.severity)} ${esc(f.text)}<div class="fix"><b>What to do:</b> ${esc(f.fix)}</div>${hubStep(f.action)}
        ${f.node ? `<button class="link small" data-act="nodeconv" data-id="${esc(f.node.split(':')[1])}">Show this node's conversations</button>` : ''}</div>`).join('');
      const steps = iss.steps.map((s, i) => { const k = iss.id + ':' + i; return `<li class="${done[k] ? 'done' : ''}"><input type="checkbox" data-act="step" data-k="${esc(k)}" ${done[k] ? 'checked' : ''} aria-label="Step done"> ${esc(s)}</li>`; }).join('');
      return `<div class="panel issue ${iss.severity}" id="issue-${esc(iss.id)}">
        <div class="head" data-act="toggle" data-id="${esc(iss.id)}" role="button" tabindex="0" aria-expanded="${open}"><h3>${esc(iss.title)}</h3><span class="muted small">${esc(iss.summary)}</span>${pill(iss.severity)}<span class="muted">${open ? '▾' : '▸'}</span></div>
        ${open ? `<p class="muted small" style="margin-top:6px">${esc(iss.what)}</p>${finds}
          <h3 style="margin-top:12px">Troubleshooting checklist</h3><ol class="steps">${steps}</ol>
          ${guide ? `<h3 style="margin-top:12px">How to do this on ${esc(guide.name)}</h3>${howTo(guide, A.guides.issue_actions[iss.id] || []) || '<p class="muted small">No documented steps for this controller.</p>'}` : ''}` : ''}</div>`;
    }).join('') + library();
}

function ctrlGuide() { return A.guides.controllers.find(c => c.id === S.ctrl); }
function ctrlOptions(placeholder) {
  return `<option value="">${esc(placeholder)}</option>${A.guides.controllers.map(c => `<option value="${esc(c.id)}" ${c.id === S.ctrl ? 'selected' : ''}>${esc(c.name)}</option>`).join('')}
    <option value="other" ${S.ctrl === 'other' ? 'selected' : ''}>Not listed</option>`;
}
async function saveCtrl(model) {
  const key = A.controller_key || { home: '*', node: 0 };
  await post('/api/controller', { home: key.home, node: key.node, model });
  S.ctrl = model;
  try { localStorage.setItem('zwlens.ctrl', model); } catch (e) { /* storage unavailable */ }
  const g = ctrlGuide();
  toast(g ? `Troubleshooting steps now show how to do each fix on ${g.name}` : model === 'other' ? 'Showing general advice only' : 'Controller model cleared');
  await load();
}
// One line under a piece of advice: how to carry it out on the chosen controller.
function hubStep(action) {
  const g = ctrlGuide(), a = g && action && g.actions[action];
  if (!a) return '';
  return `<div class="hub"><b>On ${esc(g.name)}:</b> ${esc(a.how)}${a.note ? ` <span class="muted">${esc(a.note)}</span>` : ''}${a.src && /^https:\/\//.test(a.src) ? ` <a href="${esc(a.src)}" target="_blank" rel="noopener noreferrer">Source</a>` : ''}</div>`;
}
function howTo(g, ids) {
  return ids.filter(id => g.actions[id]).map(id => { const a = g.actions[id]; return `<div class="finding"><b>${esc(A.guides.actions[id])}</b>
    <div>${esc(a.how)}</div>${a.note ? `<div class="fix">${esc(a.note)}</div>` : ''}
    ${a.src && /^https:\/\//.test(a.src) ? `<div class="src"><a href="${esc(a.src)}" target="_blank" rel="noopener noreferrer">Source</a></div>` : ''}</div>`; }).join('');
}
function controllerPanel() {
  const G = A.guides; if (!G.controllers.length) return '';
  const g = ctrlGuide();
  const body = g ? `<p style="margin-top:10px">${esc(g.summary)}</p>
      ${g.quirks.length ? `<div class="warnbox"><b>Good to know</b><ul style="margin:4px 0 0;padding-left:18px">${g.quirks.map(q => `<li>${esc(q)}</li>`).join('')}</ul></div>` : ''}
      <details style="margin-top:10px"><summary>All directions for ${esc(g.name)}</summary>${howTo(g, Object.keys(G.actions))}</details>
      ${g.docs.length ? `<p class="small muted" style="margin-top:8px">Documentation: ${g.docs.map(d => `<a href="${esc(d.url)}" target="_blank" rel="noopener noreferrer">${esc(d.label)}</a>`).join(' · ')}</p>` : ''}`
    : S.ctrl === 'other' ? '<p class="muted small" style="margin-top:8px">zwlens has no guide for your controller yet, so the advice below is general. Look for the same actions (rebuild routes, remove failed node, exclusion) in its manual.</p>'
    : '<p class="muted small" style="margin-top:8px">Pick your controller (here or on the Nodes tab) to see its exact menu paths under every finding below.</p>';
  return `<div class="panel"><h2>Your controller</h2>
    <div class="bar" style="margin:0"><select id="ctrl" aria-label="Controller model">${ctrlOptions('Choose your controller…')}</select>
    <span class="muted small">Directions are quoted from the makers' documentation; menus can change with firmware.</span></div>${body}</div>`;
}

function library() {
  const q = S.kq.toLowerCase();
  const cats = [...new Map(A.catalog.map(e => [e.category, e.category_name])).entries()].sort((a, b) => a[1].localeCompare(b[1]));
  const list = A.catalog.filter(e => (!S.kcat || e.category === S.kcat || (S.kcat === '!detected' && e.hits.length))
    && (!q || (e.title + ' ' + e.what + ' ' + e.causes.join(' ') + ' ' + e.fixes.join(' ')).toLowerCase().includes(q)));
  const found = A.catalog.filter(e => e.hits.length);
  const statusPill = e => e.hits.length ? pill(e.hits.some(h => h.severity === 'crit') ? 'crit' : e.hits.some(h => h.severity === 'warn') ? 'warn' : 'info', 'Detected')
    : e.status === 'clear' ? pill('ok', 'Not seen') : pill('plain', 'Check by hand');
  const items = list.map(e => `<div class="kbitem ${e.hits.length ? 'hit' : ''}" id="issue-kb-${esc(e.id)}">
      <div class="bar" style="margin-bottom:4px"><h3 class="grow" style="margin:0">${esc(e.title)}</h3>${statusPill(e)}</div>
      <div class="small muted">${esc(e.category_name)} · checked from ${esc(e.how)}</div>
      ${e.hits.map(h => `<div class="finding">${pill(h.severity)} ${esc(h.text)}${h.node ? ` <button class="link small" data-act="nodeconv" data-id="${esc(h.node.split(':')[1])}">conversations</button>` : ''}</div>`).join('')}
      <p style="margin-top:6px">${esc(e.what)}</p>
      <details ${e.hits.length ? 'open' : ''}><summary class="small muted">Causes and fixes</summary>
        ${e.causes.length ? `<div class="small muted" style="margin-top:6px">Likely causes</div><ul>${e.causes.map(c => `<li>${esc(c)}</li>`).join('')}</ul>` : ''}
        ${e.fixes.length ? `<div class="small muted" style="margin-top:6px">What to do</div><ul>${e.fixes.map(c => `<li>${esc(c)}</li>`).join('')}</ul>` : ''}
        ${hubStep(e.action)}
        ${e.sources.length ? `<div class="src muted">Sources: ${e.sources.map((u, i) => /^https:\/\//.test(u) ? `<a href="${esc(u)}" target="_blank" rel="noopener noreferrer">[${i + 1}]</a>` : esc(u)).join(' ')}</div>` : ''}
      </details></div>`).join('');
  return `<div class="panel"><h2>Known-issue library</h2>
    <p class="muted">${A.catalog.length} failure modes from Z-Wave JS and Silicon Labs documentation and user forums. ${found.length} detected in this capture, ${A.catalog.filter(e => e.status === 'clear').length} checked and not seen, ${A.catalog.filter(e => e.status === 'manual').length} that traffic cannot show.</p>
    <div class="bar"><input type="search" class="grow" id="kq" placeholder="Search issues, causes and fixes…" value="${esc(S.kq)}">
      <select id="kcat"><option value="">All categories</option><option value="!detected" ${S.kcat === '!detected' ? 'selected' : ''}>Detected only</option>${cats.map(([k, v]) => `<option value="${esc(k)}" ${S.kcat === k ? 'selected' : ''}>${esc(v)}</option>`).join('')}</select>
      <span class="muted small">${list.length} shown</span></div>
    <div class="kb">${items || '<div class="empty">No issues match.</div>'}</div></div>`;
}

// ---------------------------------------------------------------- nodes
function nodes() {
  const list = A.nodes.filter(n => S.foreign || !n.foreign);
  const rows = list.map(n => {
    const al = A.aliases[n.key] || A.aliases['*:' + n.id] || {};
    const row = `<tr>
      <td><b>${esc(n.name)}</b>${n.foreign ? ' <span class="pill plain">other network</span>' : ''}<div class="small muted">${esc([al.location || n.location, n.product, al.notes].filter(Boolean).join(' · '))}</div></td>
      <td>${esc(n.type)}</td><td>${esc(n.role)}</td><td>${esc(n.power)}${n.battery ? `<div class="small muted">battery ${esc(n.battery)}</div>` : ''}</td>
      <td>${esc(n.security)}</td><td>${pill(HEALTH[n.health] || 'plain', n.health)}</td>
      <td>${n.traffic === 'Chatty' ? pill('warn', 'Chatty') : esc(n.traffic)}</td>
      <td class="num">${n.rssi != null ? n.rssi.toFixed(0) + ' dBm' : ''}</td>
      <td class="num">${n.tx}</td><td class="num">${n.rx}</td>
      <td class="num">${n.attempts ? Math.round(n.fail_rate * 100) + '%' : ''}</td>
      <td>${n.controller ? '' : n.route ? (n.route.length ? esc('via ' + n.route.map(r => nameOf(n.home, r)).join(' → ')) : 'direct') : '<span class="muted">unknown</span>'}${n.route_changes ? `<div class="small muted">${n.route_changes} route changes</div>` : ''}</td>
      <td><button class="link" data-act="edit" data-key="${esc(n.key)}">Rename</button></td></tr>`;
    const edit = S.edit === n.key ? `<tr class="editrow"><td colspan="13"><div class="bar" style="margin:0">
      <input type="text" id="al-name" placeholder="Alias, e.g. Kitchen light" value="${esc(al.name || '')}" maxlength="80">
      <input type="text" id="al-loc" placeholder="Location" value="${esc(al.location || '')}" maxlength="80">
      <input type="text" id="al-notes" class="grow" placeholder="Notes" value="${esc(al.notes || '')}" maxlength="200">
      <button class="btn primary" data-act="savealias" data-key="${esc(n.key)}">Save</button><button class="btn" data-act="edit" data-key="">Cancel</button>
      <span class="muted small">Leave everything empty to remove the alias.</span></div></td></tr>` : '';
    return row + edit;
  }).join('');
  const g = ctrlGuide();
  return `<div class="panel"><div class="bar" style="margin:0"><label for="nodectrl"><b>Controller model</b></label>
      <select id="nodectrl">${ctrlOptions('Choose your controller model…')}</select>
      <span class="muted small grow">${g ? `Troubleshooting shows how to carry out each fix on ${esc(g.name)}.` : S.ctrl === 'other' ? 'No guide for this controller yet; troubleshooting shows general advice.' : 'Choose it once and every troubleshooting step shows the exact menus for your hub.'} Saved for this network.</span></div></div>
    <div class="bar"><span class="muted grow">Every node, categorised by what its traffic shows. Aliases are saved to <span class="mono">${esc(A.alias_file)}</span> and reused for every capture.</span>
    ${A.network.foreign_nodes ? `<label class="small"><input type="checkbox" data-act="foreign" ${S.foreign ? 'checked' : ''}> Show ${A.network.foreign_nodes} nodes from other networks</label>` : ''}</div>
    <div class="panel tablewrap"><table><thead><tr><th>Node</th><th>Type</th><th>Role</th><th>Power</th><th>Security</th><th>Health</th><th>Traffic</th>
    <th class="num">Signal</th><th class="num">Sent</th><th class="num">Received</th><th class="num">Undelivered</th><th>Route from controller</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

// ---------------------------------------------------------------- frames
function frames() {
  const F = S.frames || { total: 0, frames: [], offset: 0 };
  const rows = F.frames.map(f => {
    const bad = f.errors.length || f.role === 'retx' || f.kind === 'routed_err' || (f.tx_status && f.tx_status !== 'OK');
    return `<tr class="${f.conv != null ? 'click' : ''}" data-act="${f.conv != null ? 'gotoconv' : ''}" data-id="${f.conv ?? ''}">
      <td class="num muted">${f.idx}</td><td class="mono">${esc(fmtTime(f.ts))}</td>
      <td>${f.src != null ? esc(nameOf(f.home, f.src)) : ''}${f.dst != null ? ' → ' + esc(nameOf(f.home, f.dst)) : ''}</td>
      <td>${bad ? pill('warn', '!') + ' ' : ''}<b>${esc(f.label)}</b> ${f.encap.map(e => pill('plain', e)).join(' ')}<div class="small muted">${esc(f.summary)}</div></td>
      <td class="small muted">${esc(frameMeta(f, null).slice(1).join(' · '))}</td>
      <td class="mono small muted" style="max-width:260px;word-break:break-all">${esc(f.raw)}</td></tr>`;
  }).join('');
  return `<div class="bar"><input type="search" class="grow" id="fq" placeholder="Filter frames (command, hex bytes, text)… press Enter" value="${esc(S.fq)}">
      <select id="fnode">${nodeOptions(S.fnode)}</select>
      <select id="fkind"><option value="">All frames</option><option value="problems" ${S.fkind === 'problems' ? 'selected' : ''}>Problems only</option></select>
      <button class="btn" data-act="fpage" data-d="-200" ${F.offset <= 0 ? 'disabled' : ''}>◀</button>
      <span class="muted small">${F.total ? F.offset + 1 : 0}–${Math.min(F.offset + 200, F.total)} of ${F.total}</span>
      <button class="btn" data-act="fpage" data-d="200" ${F.offset + 200 >= F.total ? 'disabled' : ''}>▶</button></div>
    <div class="panel tablewrap"><table><thead><tr><th class="num">#</th><th>Time</th><th>From → To</th><th>Frame</th><th>Details</th><th>Raw</th></tr></thead><tbody>${rows}</tbody></table>
    ${rows ? '' : '<div class="empty">No frames match.</div>'}</div>`;
}

// ---------------------------------------------------------------- data
async function loadPorts() {
  try { S.ports = (await api('/api/ports')).ports; } catch (e) { S.ports = []; }
  if (S.tab === 'data') render();
}
async function checkPort(path, rerender = true) {
  if (!path) { S.port = null; } else {
    try { S.port = await api('/api/port?path=' + encodeURIComponent(path)); } catch (e) { S.port = null; }
  }
  if (rerender && S.tab === 'data') render();
}
function portBusy() {
  if (!S.port || !S.port.holders.length || A.live) return '';
  return S.port.holders.map(h => `<div class="warnbox"><b>${esc(S.port.path)} is in use by ${esc(h.name)}</b> (process ${h.pid}). Only one program can use the stick at a time.
    <div class="bar" style="margin:8px 0 4px"><button class="btn primary" data-act="release" data-pid="${h.pid}">Stop ${esc(h.name)} and capture</button><button class="btn" data-act="recheck">Check again</button></div>
    <div class="small">Stopping it closes that whole program. To free the stick yourself instead: ${h.name === 'Z-Wave JS UI' ? 'in Z-Wave JS UI open Settings, turn off Zniffer (or the Z-Wave driver using this port) and save; or ' : ''}run <span class="mono">kill ${h.pid}</span> in a terminal, then press Check again.</div></div>`).join('');
}
function data() {
  const live = A.live;
  if (S.ports === null) { S.ports = []; loadPorts(); }
  const lsGet = k => { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } };
  const liveState = live ? `<p>${pill(live.state === 'connected' ? 'ok' : live.state === 'connecting' ? 'info' : 'crit', live.state)} ${live.frames} frames received${live.info ? ' · ' + esc(live.info) : ''}</p>${live.error ? `<div class="warnbox">${esc(live.error)}</div>` : ''}` : '';
  const isZ = live && live.kind === 'zniffer', isWs = live && live.kind === 'live';
  const portValue = isZ ? live.url : (S.port ? S.port.path : lsGet('zwlens.port'));
  if (S.port === null && portValue && !live) { S.port = { path: portValue, holders: [] }; checkPort(portValue); }
  const caps = A.captures.map(c => `<tr><td><b>${esc(c.name)}</b>${c.warnings.map(w => `<div class="warnbox">${esc(w)}</div>`).join('')}</td>
    <td>${esc({ log: 'Z-Wave JS log', zniffer: 'Zniffer capture', sdr: 'SDR capture', live: 'Live session' }[c.kind] || c.kind)}</td><td class="num">${c.frames}</td>
    <td><button class="link" data-act="remove" data-id="${c.id}">Remove</button></td></tr>`).join('');
  return `<div class="grid cols2">
    <div class="panel"><h2>Add capture files</h2>
      <div class="dropzone"><p>Drop files anywhere on this page, or</p><button class="btn primary" data-act="pick">Choose files…</button>
      <p class="muted small" style="margin-top:10px">Z-Wave JS driver logs (.log, .txt) · Zniffer captures (.zlf) · SDR output (text with hex frames, or .pcap).<br>Files stay on this computer.</p></div>
      ${S.notes.map(n => `<div class="warnbox">${esc(n)}</div>`).join('')}
      <div class="bar" style="margin:12px 0 0"><span class="muted small grow">No capture yet? Load invented sample data:</span>
        <button class="btn" data-act="sample" data-kind="zniffer">Sample Zniffer capture</button><button class="btn" data-act="sample" data-kind="log">Sample Z-Wave JS log</button></div>
      <div class="bar" style="margin:10px 0 0"><label class="muted small grow" for="chip">Signal conversion for .zlf files recorded with a</label>
        <select id="chip"><option value="700" ${A.settings.chip === '700' ? 'selected' : ''}>700/800-series Zniffer</option><option value="500" ${A.settings.chip === '500' ? 'selected' : ''}>500-series Zniffer</option></select></div>
    </div>
    <div class="panel"><h2>Live from a controller</h2>
      <p class="muted small">Connects read-only to a Z-Wave JS server (Z-Wave JS UI or the Home Assistant add-on, usually port 3000). Set the driver log level to <b>debug</b> to see commands.</p>
      <div class="bar"><input type="text" class="grow" id="liveurl" placeholder="ws://localhost:3000" value="${esc(isWs ? live.url : (lsGet('zwlens.live') || 'ws://localhost:3000'))}" ${live ? 'disabled' : ''}>
      ${isWs ? '<button class="btn" data-act="livestop">Disconnect</button>' : `<button class="btn primary" data-act="livestart" ${live ? 'disabled' : ''}>Connect</button>`}</div>
      ${isWs ? liveState : ''}
      <h2 style="margin-top:16px">Live from a Zniffer stick</h2>
      <p class="muted small">Captures everything on air through a Zniffer USB stick's serial port. Close any other program using the stick first.</p>
      <div class="bar"><input type="text" class="grow" id="zport" list="zports" placeholder="/dev/ttyUSB0 or COM5" value="${esc(portValue)}" ${live ? 'disabled' : ''}>
      <datalist id="zports">${(S.ports || []).map(p => `<option value="${esc(p.path)}">${esc(p.label)}</option>`).join('')}</datalist>
      <button class="btn" data-act="ports" ${live ? 'disabled' : ''}>Rescan</button>
      ${isZ ? '<button class="btn" data-act="livestop">Stop</button>' : `<button class="btn primary" data-act="zstart" ${live ? 'disabled' : ''}>Capture</button>`}</div>
      ${S.ports && S.ports.length ? `<p class="muted small">Found: ${esc(S.ports.map(p => p.path).join(', '))}</p>` : '<p class="muted small">No serial ports detected; type the port name.</p>'}
      ${portBusy()}${isZ ? liveState : ''}
      ${isZ && live.regions && live.regions.length ? `<div class="bar" style="margin:8px 0 0"><label class="muted small" for="zregion">Radio region (must match your network)</label>
        <select id="zregion">${live.regions.map(r => `<option value="${r.id}" ${r.id === live.region ? 'selected' : ''}>${esc(r.name)}</option>`).join('')}</select></div>` : ''}
    </div></div>
    <div class="panel"><div class="bar"><h2 class="grow" style="margin:0">Loaded captures</h2>
      ${(A.network.sources.zniffer || A.network.sources.sdr) ? '<a class="btn" href="/api/capture.zlf" download="zwlens-capture.zlf">Save as .zlf</a>' : ''}
      <a class="btn" href="/api/report.md" target="_blank" rel="noopener">Export report</a><a class="btn" href="/api/analysis" download="zwlens-analysis.json">Export JSON</a><button class="btn" data-act="clear" ${A.captures.length || live ? '' : 'disabled'}>Clear all</button></div>
      ${caps ? `<table><thead><tr><th>Name</th><th>Type</th><th class="num">Frames</th><th></th></tr></thead><tbody>${caps}</tbody></table>` : '<p class="muted">Nothing loaded yet.</p>'}
    </div>`;
}

// ---------------------------------------------------------------- actions
async function upload(files) {
  S.notes = [];
  for (const file of files) {
    try {
      const r = await api('/api/upload?name=' + encodeURIComponent(file.name), { method: 'POST', headers: { 'X-ZWLens': '1' }, body: file });
      if (!r.loaded) S.notes.push(`${file.name}: nothing loaded. ${r.warnings.join(' ')}`);
      else toast(`${file.name}: ${r.frames} frames loaded`);
    } catch (e) { S.notes.push(`${file.name}: ${e.message}`); }
  }
  await load();
  if (A.network.frames && !S.notes.length && S.tab === 'data') { S.tab = 'overview'; render(); }
}
const actions = {
  tab: async el => { S.tab = el.dataset.tab; if (S.tab === 'frames') await loadFrames(false); render(); },
  card: async el => {
    if (el.dataset.tab === 'conversations') { S.cq = ''; S.cnode = ''; S.cstatus = el.dataset.status; }
    await actions.tab(el); window.scrollTo(0, 0);
  },
  conv: el => loadConv(+el.dataset.id),
  gotoconv: async el => { S.tab = 'conversations'; S.cq = ''; S.cnode = ''; S.cstatus = ''; await loadConv(+el.dataset.id); },
  raw: el => el.classList.toggle('open'),
  toggle: el => { const i = A.issues.find(i => i.id === el.dataset.id); S.open[i.id] = !(S.open[i.id] ?? i.findings.length > 0); render(); },
  issue: el => { S.tab = 'troubleshoot'; S.open[el.dataset.id] = true; if (el.dataset.id.startsWith('kb-')) { S.kq = ''; S.kcat = ''; } render(); const t = document.getElementById('issue-' + el.dataset.id); if (t) t.scrollIntoView({ block: 'start' }); },
  step: el => { done[el.dataset.k] = el.checked; try { localStorage.setItem('zwlens.done', JSON.stringify(done)); } catch (e) { /* storage unavailable */ } el.parentElement.classList.toggle('done', el.checked); },
  nodeconv: el => { S.tab = 'conversations'; S.cnode = el.dataset.id; S.cq = ''; S.cstatus = ''; render(); },
  mapnode: el => actions.nodeconv(el),
  edit: el => { S.edit = el.dataset.key || null; render(); const i = $('#al-name'); if (i) i.focus(); },
  savealias: async el => { await post('/api/alias', { key: el.dataset.key, name: $('#al-name').value, location: $('#al-loc').value, notes: $('#al-notes').value }); S.edit = null; toast('Alias saved'); await load(); },
  foreign: el => { S.foreign = el.checked; render(); },
  fpage: async el => { S.foff = Math.max(0, S.foff + +el.dataset.d); await loadFrames(); },
  pick: () => $('#file').click(),
  sample: async el => { const r = await post('/api/sample', { kind: el.dataset.kind }); toast(`${r.name}: ${r.frames} frames loaded`); await load(); if (S.tab === 'data' || !A.network.frames) { S.tab = 'overview'; } render(); },
  remove: async el => { await post('/api/remove', { id: +el.dataset.id }); await load(); },
  clear: async () => { if (confirm('Remove all loaded captures? Aliases are kept.')) { await post('/api/clear'); S.notes = []; await load(); } },
  livestart: async () => { const url = $('#liveurl').value.trim(); try { localStorage.setItem('zwlens.live', url); } catch (e) { /* ignore */ } await post('/api/live/start', { url }); await load(); },
  zstart: async () => {
    const url = $('#zport').value.trim();
    try { localStorage.setItem('zwlens.port', url); } catch (e) { /* ignore */ }
    await checkPort(url, false);
    if (S.port && S.port.holders.length) { render(); return; }  // busy: show who has it instead of failing
    await post('/api/live/start', { url }); await load();
  },
  recheck: () => checkPort($('#zport').value.trim()),
  release: async el => {
    const h = S.port.holders.find(h => String(h.pid) === el.dataset.pid);
    if (!confirm(`Stop ${h.name} (process ${h.pid})? This closes that program; anything it was capturing or controlling stops.`)) return;
    const r = await post('/api/port/release', { path: S.port.path, pid: h.pid });
    await checkPort(S.port.path, false);
    if (!r.freed || S.port.holders.length) { toast('The program did not exit. Close it manually, then press Check again.'); render(); return; }
    await post('/api/live/start', { url: S.port.path }); await load();
  },
  ports: () => loadPorts(),
  livestop: async () => { await post('/api/live/stop'); await load(); },
};
document.addEventListener('click', async ev => {
  const el = ev.target.closest('[data-act]');
  if (!el || !el.dataset.act || el.tagName === 'INPUT' && el.type === 'checkbox') return;
  try { await actions[el.dataset.act](el); } catch (e) { toast(e.message); }
});
document.addEventListener('change', async ev => {
  const el = ev.target;
  try {
    if (el.dataset.act && el.type === 'checkbox') return actions[el.dataset.act](el);
    if (el.id === 'file') { await upload([...el.files]); el.value = ''; }
    if (el.id === 'zport') { await checkPort(el.value.trim()); }
    if (el.id === 'kcat') { S.kcat = el.value; render(); }
    if (el.id === 'chip') { await post('/api/settings', { chip: el.value }); toast('Applies to .zlf files you load from now on'); await load(); }
    if (el.id === 'zregion') { await post('/api/live/region', { id: +el.value }); toast('Switching region…'); setTimeout(() => load().catch(() => {}), 1500); }
    if (el.id === 'ctrl' || el.id === 'nodectrl') await saveCtrl(el.value);
    if (el.id === 'cnode') { S.cnode = el.value; render(); }
    if (el.id === 'cstatus') { S.cstatus = el.value; render(); }
    if (el.id === 'fnode') { S.fnode = el.value; S.foff = 0; await loadFrames(); }
    if (el.id === 'fkind') { S.fkind = el.value; S.foff = 0; await loadFrames(); }
    if (el.id === 'fq') { S.fq = el.value; S.foff = 0; await loadFrames(); }
  } catch (e) { toast(e.message); }
});
document.addEventListener('input', ev => {
  const id = ev.target.id;
  if (id !== 'cq' && id !== 'kq') return;
  S[id] = ev.target.value; render();
  const i = $('#' + id); i.focus(); i.setSelectionRange(i.value.length, i.value.length);
});
document.addEventListener('keydown', ev => { if ((ev.key === 'Enter' || ev.key === ' ') && ev.target.matches('.issue .head')) { ev.preventDefault(); ev.target.click(); }
  if (ev.key === 'Enter' && ev.target.id === 'al-name') { const b = document.querySelector('[data-act=savealias]'); if (b) b.click(); } });
$('#tabs').addEventListener('click', ev => { const b = ev.target.closest('button'); if (b) actions.tab(b); });
$('.brand').addEventListener('click', () => $('#tabs [data-tab=overview]').click());  // title = home
$('.brand').addEventListener('keydown', ev => { if (ev.key === 'Enter') $('.brand').click(); });

let dragDepth = 0;
window.addEventListener('dragenter', ev => { if (ev.dataTransfer && [...ev.dataTransfer.types].includes('Files')) { dragDepth++; $('#drop').classList.add('on'); ev.preventDefault(); } });
window.addEventListener('dragover', ev => ev.preventDefault());
window.addEventListener('dragleave', () => { if (--dragDepth <= 0) { dragDepth = 0; $('#drop').classList.remove('on'); } });
window.addEventListener('drop', ev => { ev.preventDefault(); dragDepth = 0; $('#drop').classList.remove('on'); if (ev.dataTransfer.files.length) upload([...ev.dataTransfer.files]).catch(e => toast(e.message)); });

setInterval(async () => {
  try {
    const v = await api('/api/version');
    const typing = document.activeElement && ['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName);
    if (v.version !== version && !typing) await load();
  } catch (e) { /* server stopped; keep the page usable */ }
}, 2000);

load().then(() => { if (A.network.frames && S.tab !== 'help') { S.tab = 'overview'; render(); } }).catch(e => toast(e.message));

// ---------------------------------------------------------------- help
// The Help tab: sections and glossary from /api/help, a searchable table of contents, and deep links
// such as #help/routing. Everything here is self-contained; other views only gain "?" buttons, added
// after each render by helpDecorate() so the view code itself stays untouched.
let HELP = null, helpLoading = false;
S.help = 'start'; S.hq = '';
const helpBtn = (id, what) => `<button class="qhelp" data-act="help" data-id="${esc(id)}" aria-label="Help: ${esc(what)}" title="Help: ${esc(what)}">?</button>`;
const helpPlain = s => String(s).replace(/\*|`/g, '').replace(/\[\[[\w-]+\|(.+?)\]\]/g, '$1').replace(/\[\[([\w-]+)\]\]/g, (m, id) => helpTitle(id));
function helpTitle(id) {
  const s = HELP && (HELP.sections.find(x => x.id === id) || HELP.glossary.find(x => x.id === id));
  return s ? (s.title || s.term) : id;
}
function helpInline(s) {
  return esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\*(.+?)\*/g, '<em>$1</em>').replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\[\[([\w-]+)(?:\|(.+?))?\]\]/g, (m, id, text) => `<a href="#help/${id}">${text || esc(helpTitle(id))}</a>`);
}
const helpBlocks = body => body.map(b => Array.isArray(b) ? `<ul>${b.map(li => `<li>${helpInline(li)}</li>`).join('')}</ul>` : `<p>${helpInline(b)}</p>`).join('');
async function loadHelp() {
  if (helpLoading) return;
  helpLoading = true;
  try {
    HELP = await api('/api/help');
    for (const s of HELP.sections) s._text = [s.title, s.summary, ...s.body.flat()].map(helpPlain).join(' ').toLowerCase();
    for (const g of HELP.glossary) g._text = (g.term + ' ' + g.text).toLowerCase();
  } catch (e) { toast('Could not load help: ' + e.message); }
  helpLoading = false;
  if (S.tab === 'help') helpShow(false);
}
function helpMatches() {
  const words = S.hq.toLowerCase().split(/\s+/).filter(Boolean);
  const hit = x => words.every(w => x._text.includes(w));
  return { words, sections: HELP.sections.filter(hit), glossary: HELP.glossary.filter(hit) };
}
function helpCurrent() {
  if (S.help.startsWith('g-')) return HELP.sections.find(s => s.id === 'glossary');
  return HELP.sections.find(s => s.id === S.help) || HELP.sections[0];
}
function helpToc() {
  const m = S.hq.trim() ? helpMatches() : null;
  const cur = helpCurrent().id;
  const shown = m ? new Set(m.sections.map(s => s.id).concat(m.glossary.length ? ['glossary'] : [])) : null;
  const toc = HELP.groups.map(g => {
    const list = HELP.sections.filter(s => s.group === g.id && (!shown || shown.has(s.id)));
    return list.length ? `<h3>${esc(g.title)}</h3><ul>${list.map(s => `<li><a href="#help/${s.id}" ${s.id === cur && !m ? 'aria-current="page"' : ''}>${esc(s.title)}</a></li>`).join('')}</ul>` : '';
  }).join('');
  return toc || '<p class="muted small">No topics match.</p>';
}
function helpSelect() {
  const cur = helpCurrent().id;
  return HELP.groups.map(g => `<optgroup label="${esc(g.title)}">${HELP.sections.filter(s => s.group === g.id).map(s => `<option value="${s.id}" ${s.id === cur ? 'selected' : ''}>${esc(s.title)}</option>`).join('')}</optgroup>`).join('');
}
function helpLinks(links) {
  const ok = (links || []).filter(l => /^https:\/\//.test(l.url));
  return ok.length ? `<div class="help-more"><h2>Further reading</h2><ul>${ok.map(l => `<li><a href="${esc(l.url)}" target="_blank" rel="noopener noreferrer">${esc(l.label)}</a></li>`).join('')}</ul></div>` : '';
}
function helpGlossary(list) {
  return `<dl class="gloss">${list.map(g => `<div class="gterm ${g.id === S.help ? 'on' : ''}" id="${g.id}"><dt>${esc(g.term)}</dt><dd>${esc(g.text)}${g.see && g.see !== 'glossary' ? ` <a href="#help/${g.see}">More: ${esc(helpTitle(g.see))}</a>` : ''}</dd></div>`).join('')}</dl>`;
}
function helpBody() {
  if (S.hq.trim()) {
    const m = helpMatches();
    const n = m.sections.length + m.glossary.length;
    return `<h1>${n ? n + ' result' + (n === 1 ? '' : 's') : 'No results'} for “${esc(S.hq.trim())}”</h1>
      ${n ? '' : '<p class="muted">Try fewer or shorter words, or pick a topic from the list.</p>'}
      ${m.glossary.length ? `<h2>Glossary</h2>${helpGlossary(m.glossary)}` : ''}
      ${m.sections.length ? `<h2>Topics</h2><ul class="help-results">${m.sections.map(s => `<li><a href="#help/${s.id}">${esc(s.title)}</a> <span class="muted small">· ${esc(HELP.groups.find(g => g.id === s.group).title)}</span><div class="muted">${esc(s.summary)}</div></li>`).join('')}</ul>` : ''}`;
  }
  const s = helpCurrent(), all = HELP.sections, i = all.indexOf(s);
  const prev = all[i - 1], next = all[i + 1];
  return `<div class="help-group">${esc(HELP.groups.find(g => g.id === s.group).title)}</div>
    <h1>${esc(s.title)}</h1>${s.summary ? `<p class="lead">${esc(s.summary)}</p>` : ''}
    ${helpBlocks(s.body)}${s.id === 'glossary' ? helpGlossary(HELP.glossary) : ''}${helpLinks(s.links)}
    <nav class="help-pager" aria-label="Previous and next topic">${prev ? `<a href="#help/${prev.id}">← ${esc(prev.title)}</a>` : '<span></span>'}${next ? `<a href="#help/${next.id}">${esc(next.title)} →</a>` : ''}</nav>`;
}
function help() {
  if (!HELP) { loadHelp(); return '<div class="panel empty help-loading">Loading help…</div>'; }
  return `<div class="help">
    <aside class="panel help-side">
      <input type="search" id="hq" placeholder="Search help and glossary…" aria-label="Search help and glossary" value="${esc(S.hq)}" autocomplete="off">
      <select id="helpsel" class="help-select" aria-label="Help topic">${helpSelect()}</select>
      <nav class="help-toc" id="helptoc" aria-label="Help topics">${helpToc()}</nav>
    </aside>
    <article class="panel help-body" id="helpbody" tabindex="-1" aria-live="polite">${helpBody()}</article></div>`;
}
function helpUpdate() {
  $('#helptoc').innerHTML = helpToc();
  $('#helpsel').innerHTML = helpSelect();
  $('#helpbody').innerHTML = helpBody();
  helpTocScroll();
}
function helpTocScroll() {  // keep the current topic visible in the sidebar
  const side = $('.help-side'), a = $('#helptoc a[aria-current]');
  if (side && a && side.scrollHeight > side.clientHeight) side.scrollTop = Math.max(0, a.offsetTop - side.clientHeight / 2);
}
function helpRoute() {
  const m = location.hash.match(/^#help(?:\/([\w-]+))?$/);
  if (!m) return false;
  S.tab = 'help'; S.hq = '';
  if (m[1]) S.help = m[1];
  return true;
}
function helpShow(focus) {
  if (!A) return;
  const hq = $('#hq');
  if (HELP && $('#view > .help')) {
    document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === 'help'));
    if (hq) hq.value = S.hq;
    helpUpdate();
  } else { render(); helpTocScroll(); }
  const g = S.help.startsWith('g-') && !S.hq && document.getElementById(S.help);
  if (g) g.scrollIntoView({ block: 'center' });
  else window.scrollTo(0, 0);
  if (focus && HELP) $('#helpbody').focus({ preventScroll: true });
}
function openHelp(id) {
  const h = '#help/' + id;
  if (location.hash === h) { helpRoute(); helpShow(true); } else location.hash = h;
}
actions.help = el => openHelp(el.dataset.id);
window.addEventListener('hashchange', () => { if (helpRoute()) helpShow(document.activeElement !== $('#hq')); });
$('#tabs').addEventListener('click', ev => {
  const b = ev.target.closest('button'); if (!b) return;
  if (b.dataset.tab === 'help') history.pushState(null, '', '#help/' + S.help);
  else if (location.hash.startsWith('#help')) history.replaceState(null, '', location.pathname + location.search);
});
document.addEventListener('input', ev => {
  if (ev.target.id !== 'hq' || !HELP) return;
  S.hq = ev.target.value; helpUpdate();
});
document.addEventListener('click', ev => {  // a link to the topic already in the address bar fires no hashchange
  const a = ev.target.closest('a[href^="#help/"]');
  if (a && a.getAttribute('href') === location.hash) { ev.preventDefault(); openHelp(a.getAttribute('href').slice(6)); }
});
document.addEventListener('change', ev => { if (ev.target.id === 'helpsel') openHelp(ev.target.value); });
document.addEventListener('keydown', ev => {
  if (ev.key === 'Escape' && ev.target.id === 'hq' && S.hq) { ev.target.value = ''; S.hq = ''; helpUpdate(); }
  if (ev.key === '/' && S.tab === 'help' && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) { const i = $('#hq'); if (i) { ev.preventDefault(); i.focus(); } }
});

// "?" buttons beside key concepts elsewhere. Matched by visible label, so a renamed label simply loses
// its button instead of breaking anything.
const HELP_TIPS = {
  th: { Power: ['sleeping', 'power and sleeping devices'], Security: ['security', 'security S0 and S2'], Health: ['faq-node-health', 'node health'],
    Signal: ['signal', 'signal strength'], 'Route from controller': ['routing', 'routing'], Undelivered: ['acks', 'delivery and retries'] },
  dt: { 'Home ID': ['ids', 'home ID'], Topology: ['mesh', 'mesh topology'], Security: ['security', 'security S0 and S2'],
    'Data rates': ['data-rates', 'data rates'], 'Long Range': ['long-range', 'Long Range'], Power: ['sleeping', 'battery devices'] },
  k: { 'Network health score': ['health-score', 'the health score'], 'Noise floor': ['signal', 'noise floor'], 'Not delivered': ['acks', 'delivery'],
    'Needed a retry': ['acks', 'retransmissions'], 'Channel busy': ['faq-congestion', 'channel busy'] },
  h2: { 'Live from a Zniffer stick': ['live-zniffer', 'capturing from a Zniffer'], 'Live from a controller': ['live-controller', 'following a controller'],
    'Add capture files': ['files', 'capture files'], 'Loaded captures': ['saving', 'saving and exporting'], 'Your controller': ['controller-guides', 'controller guides'],
    'Known-issue library': ['tab-troubleshoot', 'the known-issue library'], 'Network map': ['tab-overview', 'the network map'] },
};
function helpDecorate() {
  if (S.tab === 'help') return;
  const add = (sel, map) => document.querySelectorAll('#view ' + sel).forEach(el => {
    const tip = map[el.textContent.trim()];
    if (tip && !el.querySelector('.qhelp')) el.insertAdjacentHTML('beforeend', ' ' + helpBtn(...tip));
  });
  add('th', HELP_TIPS.th); add('.kv dt', HELP_TIPS.dt); add('.card .k', HELP_TIPS.k); add('h2', HELP_TIPS.h2);
  document.querySelectorAll('#view td').forEach(td => {
    if (td.firstChild && td.firstChild.nodeType === 3 && td.firstChild.textContent.startsWith('Battery, FLiRS')) td.firstChild.after(document.createRange().createContextualFragment(' ' + helpBtn('flirs', 'FLiRS devices')));
  });
  for (const iss of A.issues || []) {
    const p = document.querySelector(`#issue-${CSS.escape(iss.id)} > p.muted`);
    if (p && !p.querySelector('a')) p.insertAdjacentHTML('beforeend', ` <a href="#help/faq-${esc(iss.id)}">What this means</a>`);
  }
}
const helpBaseRender = render;
render = function () { helpBaseRender(); try { helpDecorate(); } catch (e) { /* help buttons are optional */ } };
helpRoute();

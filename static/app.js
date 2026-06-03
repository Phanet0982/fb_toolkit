/* ══════════════════════════════════════════════════════════════
   FB Toolkit — Web Dashboard JS
   ══════════════════════════════════════════════════════════════ */

// ══════ Navigation ══════════════════════════════════════════

function showPage(pageId) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  // Show target page
  const page = document.getElementById('page-' + pageId);
  if (page) page.classList.add('active');
  
  // Update nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.page === pageId);
  });
  
  // Close mobile sidebar
  document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ══════ Search Filter ══════════════════════════════════════

function filterTools(query) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll('.tool-card').forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(q) ? '' : 'none';
  });
}

// ══════ API Helper ══════════════════════════════════════════

async function apiCall(url, data = {}) {
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return await resp.json();
  } catch (err) {
    return { error: err.message };
  }
}

async function apiGet(url) {
  try {
    const resp = await fetch(url);
    return await resp.json();
  } catch (err) {
    return { error: err.message };
  }
}

// ══════ Copy to Clipboard ══════════════════════════════════

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Copied to clipboard!');
  });
}

function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'copy-toast';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2000);
}

// ══════ 2FA Generate ══════════════════════════════════════

let totpTimerInterval = null;

async function twofaGenerate() {
  const secret = document.getElementById('twofa-secret').value.trim();
  if (!secret) { showToast('Please enter a secret key'); return; }
  
  const data = await apiCall('/api/totp', { secret });
  if (data.error) { showToast(data.error); return; }
  
  const resultDiv = document.getElementById('twofa-result');
  resultDiv.style.display = 'block';
  
  document.getElementById('twofa-code').textContent = data.code;
  updateTimer(data.remaining);
  
  // Start timer
  if (totpTimerInterval) clearInterval(totpTimerInterval);
  let remaining = data.remaining;
  totpTimerInterval = setInterval(async () => {
    remaining--;
    if (remaining <= 0) {
      // Regenerate
      const newData = await apiCall('/api/totp', { secret });
      if (newData.code) {
        document.getElementById('twofa-code').textContent = newData.code;
        remaining = newData.remaining;
      }
    }
    updateTimer(remaining);
  }, 1000);
}

function updateTimer(remaining) {
  const pct = (remaining / 30) * 100;
  document.getElementById('twofa-timer-bar').style.width = pct + '%';
  document.getElementById('twofa-timer-text').textContent = remaining + 's';
}

// ══════ 2FA Extract ══════════════════════════════════════

async function extractCodes() {
  const text = document.getElementById('extract-text').value.trim();
  if (!text) { showToast('Please enter text'); return; }
  
  const data = await apiCall('/api/2fa/extract', { text });
  if (data.error) { showToast(data.error); return; }
  
  const resultDiv = document.getElementById('extract-result');
  resultDiv.style.display = 'block';
  document.getElementById('extract-latest').textContent = data.latest || 'None';
  document.getElementById('extract-codes').textContent = data.codes.join('\n') || 'No codes found';
}

// ══════ Drop 2FA ══════════════════════════════════════

async function dropCode() {
  const text = document.getElementById('drop-text').value.trim();
  if (!text) { showToast('Please enter text'); return; }
  
  const data = await apiCall('/api/2fa/drop', { text });
  if (data.error) { showToast(data.error); return; }
  
  const resultDiv = document.getElementById('drop-result');
  resultDiv.style.display = 'block';
  document.getElementById('drop-code').textContent = data.code || 'None';
  document.getElementById('drop-clean').textContent = data.cleaned || 'No 2FA found';
}

// ══════ FB → UID ══════════════════════════════════════

async function fbLookup() {
  const input = document.getElementById('fb-url').value.trim();
  const bulk = document.getElementById('fb-bulk').checked;
  if (!input) { showToast('Please enter a URL'); return; }
  
  const resultDiv = document.getElementById('fb-result');
  const contentDiv = document.getElementById('fb-result-content');
  resultDiv.style.display = 'block';
  contentDiv.innerHTML = '<div class="spinner"></div>';
  
  if (bulk) {
    const urls = input.split('\n').filter(u => u.trim());
    const data = await apiCall('/api/fb/uid/bulk', { urls });
    if (data.error) { showToast(data.error); return; }
    
    let html = '';
    data.results.forEach(r => {
      const statusClass = r.uid ? 'active' : 'deleted';
      html += `<div class="result-row">
        <span class="label">${escHtml(r.input || r.url)}</span>
        <span class="value">${r.uid || 'Not found'}</span>
        ${r.uid ? `<button class="btn-sm" onclick="copyText('${r.uid}')">Copy</button>` : ''}
      </div>`;
    });
    contentDiv.innerHTML = html;
  } else {
    const data = await apiCall('/api/fb/uid', { url: input });
    if (data.error) { showToast(data.error); return; }
    
    let html = '';
    if (data.uid) {
      html += `<div class="result-row">
        <span class="label">UID</span>
        <span class="value" style="font-size:18px;font-weight:700">${data.uid}</span>
        <button class="btn-sm" onclick="copyText('${data.uid}')">Copy</button>
      </div>`;
    }
    if (data.username) {
      html += `<div class="result-row"><span class="label">Username</span><span class="value">${escHtml(data.username)}</span></div>`;
    }
    if (data.phones && data.phones.length > 0) {
      html += `<div class="result-row"><span class="label">Phones</span><span class="value">${data.phones.join(', ')}</span></div>`;
    }
    if (!data.uid) {
      html = '<div style="color:var(--text-dim);text-align:center;padding:20px">Could not extract UID from this input</div>';
    }
    contentDiv.innerHTML = html;
  }
}

// ══════ Find Phones ══════════════════════════════════════

async function findPhones() {
  const text = document.getElementById('phone-text').value.trim();
  if (!text) { showToast('Please enter text'); return; }
  
  const data = await apiCall('/api/fb/phones', { text });
  if (data.error) { showToast(data.error); return; }
  
  const resultDiv = document.getElementById('phone-result');
  resultDiv.style.display = 'block';
  document.getElementById('phone-codes').textContent = data.phones.length > 0 
    ? data.phones.join('\n') 
    : 'No phone numbers found';
}

// ══════ Fake ID ══════════════════════════════════════

async function generateFakeID() {
  const data = await apiCall('/api/fakeid', { gender: 'Random' });
  if (data.error) { showToast(data.error); return; }
  
  const resultDiv = document.getElementById('fakeid-result');
  resultDiv.style.display = 'block';
  document.getElementById('fakeid-copy-btn').style.display = '';
  
  let text = '';
  for (const [key, val] of Object.entries(data)) {
    text += `${key.padEnd(16)}: ${val}\n`;
  }
  document.getElementById('fakeid-data').textContent = text;
}

// ══════ Email Parser ══════════════════════════════════════

async function parseEmails() {
  const text = document.getElementById('email-text').value.trim();
  if (!text) { showToast('Please enter text'); return; }
  
  const data = await apiCall('/api/email/parse', { text });
  if (data.error) { showToast(data.error); return; }
  
  const resultDiv = document.getElementById('email-result');
  const contentDiv = document.getElementById('email-result-content');
  resultDiv.style.display = 'block';
  
  let html = '';
  if (data.emails.length > 0) {
    html += `<div class="result-label">Emails (${data.emails.length})</div>`;
    data.emails.forEach(e => {
      html += `<div class="result-row"><span class="value">${escHtml(e)}</span>
        <button class="btn-sm" onclick="copyText('${escHtml(e)}')">Copy</button></div>`;
    });
  }
  if (data.subject) html += `<div class="result-row"><span class="label">Subject</span><span class="value">${escHtml(data.subject)}</span></div>`;
  if (data.from) html += `<div class="result-row"><span class="label">From</span><span class="value">${escHtml(data.from)}</span></div>`;
  if (data.date) html += `<div class="result-row"><span class="label">Date</span><span class="value">${escHtml(data.date)}</span></div>`;
  if (!html) html = '<div style="color:var(--text-dim);text-align:center;padding:20px">No emails found</div>';
  contentDiv.innerHTML = html;
}

// ══════ BM Tools ══════════════════════════════════════

async function checkBM(type) {
  const text = document.getElementById('bm-text').value.trim();
  if (!text) { showToast('Please enter BM IDs or URLs'); return; }
  
  const resultDiv = document.getElementById('bm-result');
  const contentDiv = document.getElementById('bm-result-content');
  resultDiv.style.display = 'block';
  contentDiv.innerHTML = '<div class="spinner"></div>';
  
  const data = await apiCall('/api/bm/check', { text, type });
  if (data.error) { showToast(data.error); return; }
  
  let html = `<div class="result-label">Checked at ${data.time}</div>`;
  data.results.forEach(r => {
    const statusClass = r.status.toLowerCase().replace(/\s+/g, '-');
    html += `<div class="result-row">
      <span class="label">${escHtml(r.bm_id)}</span>
      <span class="value">${escHtml(r.input)}</span>
      <span class="status-badge ${statusClass}">${escHtml(r.status)}</span>
    </div>`;
  });
  contentDiv.innerHTML = html;
}

// ══════ Instagram ══════════════════════════════════════

function showIGTab(tab) {
  document.querySelectorAll('#ig-tabs .tab-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('ig-tab-check').style.display = tab === 'check' ? '' : 'none';
  document.getElementById('ig-tab-download').style.display = tab === 'download' ? '' : 'none';
}

async function checkIG() {
  const text = document.getElementById('ig-text').value.trim();
  if (!text) { showToast('Please enter usernames'); return; }
  
  const resultDiv = document.getElementById('ig-result');
  const contentDiv = document.getElementById('ig-result-content');
  resultDiv.style.display = 'block';
  contentDiv.innerHTML = '<div class="spinner"></div>';
  
  const data = await apiCall('/api/ig/check', { text });
  if (data.error) { showToast(data.error); return; }
  
  let html = `<div class="result-label">Checked at ${data.time}</div>`;
  data.results.forEach(r => {
    const statusClass = r.status.toLowerCase().replace(/[^a-z]/g, '-');
    const followers = r.followers ? ` · ${r.followers.toLocaleString()} followers` : '';
    html += `<div class="result-row">
      <span class="label">@${escHtml(r.username)}</span>
      <span class="status-badge ${statusClass}">${escHtml(r.status)}</span>
      <span class="value" style="color:var(--text-dim);font-size:11px">${followers}</span>
    </div>`;
  });
  contentDiv.innerHTML = html;
}

async function downloadIG() {
  const url = document.getElementById('ig-dl-url').value.trim();
  if (!url) { showToast('Please enter an Instagram URL'); return; }
  
  const type = document.querySelector('input[name="ig-type"]:checked').value;
  
  const resultDiv = document.getElementById('ig-dl-result');
  const contentDiv = document.getElementById('ig-dl-result-content');
  resultDiv.style.display = 'block';
  contentDiv.innerHTML = '<div class="spinner"></div>';
  
  const data = await apiCall('/api/ig/download', { url, type });
  if (data.error) { showToast(data.error); return; }
  
  let html = `
    <div class="result-row"><span class="label">Type</span><span class="value">${data.content_type}</span></div>
    <div class="result-row"><span class="label">Resolution</span><span class="value">${data.resolution}</span></div>
    <div class="result-row"><span class="label">Format</span><span class="value">${data.format}</span></div>
    <div class="result-row"><span class="label">File</span><span class="value">${escHtml(data.file_name)}</span></div>
    <div class="result-row"><span class="label">Status</span><span class="status-badge ready">${data.status}</span></div>
  `;
  contentDiv.innerHTML = html;
}

// ══════ Utilities ══════════════════════════════════════

function escHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ══════ Init ══════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
  showPage('dashboard');
});
